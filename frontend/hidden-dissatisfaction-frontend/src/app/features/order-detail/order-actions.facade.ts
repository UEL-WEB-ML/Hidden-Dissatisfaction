import { Injectable, inject, signal } from '@angular/core';
import { Observable, finalize } from 'rxjs';
import { ApiClient } from '../../core/api-client.service';
import { UserDto } from '../../core/api-dtos';

export type ActionKind = 'assign' | 'complete' | 'skip' | 'reopen' | 'comment' | 'model-note';
export interface ActionForm { assigneeId: string; reason: string; outcome: string; note: string; text: string; overrideCapacity: boolean; reviewConfirmed: boolean; }
const emptyForm = (): ActionForm => ({ assigneeId: '', reason: '', outcome: '', note: '', text: '', overrideCapacity: false, reviewConfirmed: false });

@Injectable()
export class OrderActionsFacade {
  private readonly api = inject(ApiClient);
  readonly kind = signal<ActionKind | null>(null);
  readonly form = signal<ActionForm>(emptyForm());
  readonly users = signal<UserDto[]>([]);
  readonly submitting = signal(false);
  readonly loadingUsers = signal(false);
  readonly error = signal<string | null>(null);
  readonly fieldErrors = signal<Record<string, string>>({});

  open(kind: ActionKind): void { this.kind.set(kind); this.error.set(null); this.fieldErrors.set({}); this.form.set(emptyForm()); if (kind === 'assign' && !this.users().length) { this.loadingUsers.set(true); this.api.users().pipe(finalize(() => this.loadingUsers.set(false))).subscribe({ next: users => this.users.set(users.filter(user => user.role === 'SPECIALIST' && user.active_count !== null)) }); } }
  close(): void { if (!this.submitting()) this.kind.set(null); }
  update(patch: Partial<ActionForm>): void { this.form.update(value => ({ ...value, ...patch })); this.error.set(null); }
  submit(orderId: string, onSuccess: () => void): void {
    const kind = this.kind(); const value = this.form(); if (!kind || this.submitting()) return;
    const invalid = this.validate(kind, value); if (Object.keys(invalid).length) { this.fieldErrors.set(invalid); return; }
    this.submitting.set(true); this.error.set(null); this.fieldErrors.set({});
    const request: Observable<unknown> = kind === 'assign' ? this.api.assign(orderId, { assignee_id: value.assigneeId, reason: value.reason.trim(), override_capacity: value.overrideCapacity })
      : kind === 'complete' ? this.api.complete(orderId, { outcome: value.outcome, note: value.note.trim() })
      : kind === 'skip' ? this.api.skip(orderId, { reason: value.reason.trim(), note: value.note.trim() || undefined })
      : kind === 'reopen' ? this.api.reopen(orderId, { reason: value.reason.trim(), review_confirmed: value.reviewConfirmed })
      : kind === 'comment' ? this.api.comment(orderId, { text: value.text.trim() })
      : this.api.modelNote(orderId, { note: value.note.trim() });
    request.pipe(finalize(() => this.submitting.set(false))).subscribe({ next: () => { this.kind.set(null); onSuccess(); }, error: error => this.captureError(error) });
  }
  private validate(kind: ActionKind, value: ActionForm): Record<string, string> {
    const errors: Record<string, string> = {}; const required = (key: string, message: string, input: string) => { if (!input.trim()) errors[key] = message; };
    if (kind === 'assign') { required('assigneeId', 'Choose a specialist.', value.assigneeId); required('reason', 'A reason is required for assignment.', value.reason); }
    if (kind === 'complete') { required('outcome', 'Choose an outcome.', value.outcome); required('note', 'Add a completion note.', value.note); }
    if (kind === 'skip') { required('reason', 'A skip reason is required.', value.reason); if (value.reason === 'OTHER') required('note', 'Explain the other reason.', value.note); }
    if (kind === 'reopen') { required('reason', 'A reason is required to reopen.', value.reason); }
    if (kind === 'comment') required('text', 'Write a comment.', value.text);
    if (kind === 'model-note') required('note', 'Add a model note.', value.note);
    return errors;
  }
  private captureError(error: { error?: { error?: { code?: string; message?: string; details?: Record<string, unknown> | null } }; status?: number }): void {
    const body = error?.error?.error; const details = body?.details ?? {}; const fields: Record<string, string> = {};
    Object.entries(details).forEach(([key, value]) => { if (typeof value === 'string') fields[key] = value; });
    this.fieldErrors.set(fields); this.error.set(body?.message ?? (error?.status === 409 ? 'This case changed elsewhere. Refresh and review the latest state.' : 'We could not save this action. Check the form and try again.'));
  }
}
