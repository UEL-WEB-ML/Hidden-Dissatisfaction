import { Injectable, computed, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';
import { ApiClient } from '../../core/api-client.service';
import { OrderDetailResponseDto } from '../../core/api-dtos';
import { toOrderDetailVm } from './order-detail.mappers';

@Injectable()
export class OrderDetailStore {
  private readonly api = inject(ApiClient);
  readonly loading = signal(false); readonly error = signal<string | null>(null); readonly forbidden = signal(false); readonly response = signal<OrderDetailResponseDto | null>(null);
  readonly view = computed(() => { const value = this.response(); return value ? toOrderDetailVm(value) : null; });
  private orderId = '';
  load(orderId: string): void { this.orderId = orderId; this.loading.set(true); this.error.set(null); this.forbidden.set(false); this.api.orderDetail(orderId).pipe(finalize(() => this.loading.set(false))).subscribe({ next: value => this.response.set(value), error: error => { this.response.set(null); if (error?.status === 403) this.forbidden.set(true); else this.error.set(error?.status === 404 ? 'This order could not be found.' : (error?.error?.error?.message ?? 'Unable to load this order.')); } }); }
  reload(): void { if (this.orderId) this.load(this.orderId); }
}
