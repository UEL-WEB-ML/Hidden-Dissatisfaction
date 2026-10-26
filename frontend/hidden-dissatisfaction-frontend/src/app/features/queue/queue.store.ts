import { Injectable, computed, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';
import { ApiClient } from '../../core/api-client.service';
import { QueueFilterOptionsDto, QueueOrderDto, QueuePageDto, QueueSummaryDto } from '../../core/api-dtos';
import { QueueQuery } from './queue.models';

@Injectable()
export class QueueStore {
  private readonly api = inject(ApiClient);
  readonly loading = signal(false); readonly loadingMore = signal(false); readonly error = signal<string | null>(null); readonly conflict = signal<string | null>(null);
  readonly orders = signal<QueueOrderDto[]>([]); readonly total = signal(0); readonly summary = signal<QueueSummaryDto | null>(null); readonly options = signal<QueueFilterOptionsDto>({ sellers: [], categories: [] });
  readonly hasMore = computed(() => this.orders().length < this.total());
  private query: QueueQuery | null = null;
  load(query: QueueQuery): void {
    this.query = query; this.loading.set(true); this.loadingMore.set(false); this.error.set(null); this.conflict.set(null);
    this.api.queue(this.toParams(query, 0)).pipe(finalize(() => this.loading.set(false))).subscribe({ next: page => { this.orders.set(this.unique(page.items)); this.total.set(page.total); }, error: error => this.error.set(this.message(error)) });
    this.api.queueSummary().subscribe({ next: value => this.summary.set(value), error: () => undefined });
    this.api.queueFilterOptions().subscribe({ next: value => this.options.set(value), error: () => undefined });
  }
  loadMore(): void { const query = this.query; if (!query || this.loadingMore() || !this.hasMore()) return; this.loadingMore.set(true); this.api.queue(this.toParams(query, this.orders().length)).pipe(finalize(() => this.loadingMore.set(false))).subscribe({ next: page => { this.orders.update(items => this.unique([...items, ...page.items])); this.total.set(page.total); }, error: error => this.error.set(this.message(error)) }); }
  claim(orderId: string): void { this.conflict.set(null); this.api.claim(orderId).subscribe({ next: ({ order }) => this.orders.update(items => items.map(item => item.order_id === order.order_id ? order : item)), error: error => { if (error?.status === 409 || error?.error?.error?.code === 'ALREADY_CLAIMED') this.conflict.set('This case was claimed by someone else. Refresh to see the latest owner.'); else this.error.set(this.message(error)); } }); }
  private toParams(query: QueueQuery, offset: number): Record<string, string | number> { const params: Record<string, string | number> = { status: query.status || 'OPEN', limit: query.limit, offset }; (['q', 'level', 'seller', 'category', 'sla', 'sort'] as const).forEach(key => { if (query[key]) params[key] = query[key]; }); return params; }
  private unique(items: QueueOrderDto[]): QueueOrderDto[] { const seen = new Set<string>(); return items.filter(item => !seen.has(item.order_id) && seen.add(item.order_id)); }
  private message(error: { error?: { error?: { message?: string } }; message?: string }): string { return error?.error?.error?.message ?? error?.message ?? 'Unable to load the risk queue.'; }
}
