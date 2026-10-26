import { Injectable, computed, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';
import { ApiClient } from '../../core/api-client.service';
import { AuthStore } from '../../core/auth.store';
import { ContactRequest, EvidenceDto, OrderDetailResponseDto, UploadResponse } from '../../core/api-dtos';

export interface EvidenceUpload { file: File; value?: UploadResponse; state: 'ready' | 'uploading' | 'uploaded' | 'error'; error?: string; }

@Injectable()
export class AttemptFacade {
  private readonly api = inject(ApiClient);
  private readonly auth = inject(AuthStore);
  readonly detail = signal<OrderDetailResponseDto | null>(null);
  readonly loading = signal(false);
  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);
  readonly uploads = signal<EvidenceUpload[]>([]);
  readonly evidence = computed(() => this.uploads().filter(item => item.state === 'uploaded' && item.value).map(item => item.value!));
  readonly canEdit = computed(() => { const order = this.detail()?.order; return !!order && order.status === 'IN_PROGRESS' && order.assignee_id === (this.auth.user()?.user_id ?? this.currentUserId); });
  currentUserId = '';

  constructor() {}
  load(orderId: string, userId: string): void { this.currentUserId = userId; this.loading.set(true); this.error.set(null); this.api.orderDetail(orderId).pipe(finalize(() => this.loading.set(false))).subscribe({ next: value => this.detail.set(value), error: error => this.error.set(error?.error?.error?.message ?? (error?.status === 404 ? 'This order could not be found.' : 'Unable to load this order.')) }); }
  addFiles(files: FileList | File[]): void {
    const incoming = Array.from(files); const existing = this.uploads();
    if (existing.length + incoming.length > 3) { this.error.set('You can attach up to 3 evidence files.'); return; }
    const accepted: EvidenceUpload[] = []; const allowed = ['image/png', 'image/jpeg', 'application/pdf'];
    incoming.forEach(file => { if (!allowed.includes(file.type)) accepted.push({ file, state: 'error', error: 'Use a PNG, JPG, or PDF file.' }); else if (file.size > 5 * 1024 * 1024) accepted.push({ file, state: 'error', error: 'Each file must be 5 MB or smaller.' }); else accepted.push({ file, state: 'ready' }); });
    this.uploads.set([...existing, ...accepted]); accepted.forEach(item => { if (item.state === 'ready') this.upload(item.file); });
  }
  retry(index: number): void { const item = this.uploads()[index]; if (item) { this.replace(index, { ...item, state: 'ready', error: undefined }); this.upload(item.file, index); } }
  remove(index: number): void { this.uploads.update(items => items.filter((_, itemIndex) => itemIndex !== index)); }
  submit(orderId: string, body: Omit<ContactRequest, 'evidence'>, done: (orderStatus: string) => void): void {
    if (this.submitting() || !this.canEdit()) return;
    const evidence: EvidenceDto[] = this.evidence(); if (this.uploads().some(item => item.state === 'uploading' || item.state === 'ready')) { this.error.set('Wait for evidence uploads to finish.'); return; }
    if (this.uploads().some(item => item.state === 'error')) { this.error.set('Remove or retry invalid evidence before saving.'); return; }
    this.submitting.set(true); this.error.set(null); this.api.contact(orderId, { ...body, evidence: evidence.map(({ file_id, file_name, file_type, file_size }) => ({ file_id, file_name, file_type, file_size })) }).pipe(finalize(() => this.submitting.set(false))).subscribe({ next: response => { this.detail.update(value => value ? { ...value, order: response.order, contacts: [...value.contacts, response.contact] } : value); done(response.order.status); }, error: error => this.error.set(error?.error?.error?.message ?? (error?.status === 409 ? 'This case changed elsewhere. Refresh and review the latest state.' : 'Unable to save this attempt.')) });
  }
  private upload(file: File, index?: number): void {
    const position = index ?? this.uploads().findIndex(item => item.file === file); if (position < 0) return; this.replace(position, { ...this.uploads()[position], state: 'uploading', error: undefined });
    this.api.uploadEvidence(file).subscribe({ next: value => this.replace(position, { ...this.uploads()[position], value, state: 'uploaded' }), error: error => this.replace(position, { ...this.uploads()[position], state: 'error', error: error?.error?.error?.message ?? 'Upload failed. Retry this file.' }) });
  }
  private replace(index: number, value: EvidenceUpload): void { this.uploads.update(items => items.map((item, itemIndex) => itemIndex === index ? value : item)); }
}
