import { Injectable, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';
import { ApiClient } from '../../core/api-client.service';
import { AuditEventDto, AuditQuery } from '../../core/api-dtos';

@Injectable()
export class AuditFacade {
  private readonly api = inject(ApiClient);
  readonly items = signal<AuditEventDto[]>([]); readonly total = signal(0); readonly loading = signal(false); readonly error = signal<string | null>(null); readonly filters = signal<AuditQuery>({ limit: 20, offset: 0 });
  load(filters: AuditQuery = this.filters()): void { this.filters.set(filters); this.loading.set(true); this.error.set(null); this.api.auditEvents(filters).pipe(finalize(() => this.loading.set(false))).subscribe({ next: value => { this.items.set(value.items); this.total.set(value.total); }, error: error => this.error.set(error?.error?.error?.message ?? error?.message ?? 'Unable to load the audit history.') }); }
  page(direction: -1 | 1): void { const nextOffset = Math.max(0, this.filters().offset + direction * this.filters().limit); if (nextOffset !== this.filters().offset) this.load({ ...this.filters(), offset: nextOffset }); }
}
