import { Injectable, computed, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';
import { ApiClient } from '../../core/api-client.service';
import { DashboardQuery, DashboardResponse } from '../../core/api-dtos';

@Injectable()
export class DashboardFacade {
  private readonly api = inject(ApiClient);
  readonly data = signal<DashboardResponse | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly filters = signal<DashboardQuery>({ view: 'order', days: 7, status: 'OPEN' });
  readonly isEmpty = computed(() => !!this.data() && this.data()!.totals.cases === 0);

  load(filters: DashboardQuery = this.filters()): void {
    this.filters.set(filters); this.loading.set(true); this.error.set(null);
    this.api.dashboard(filters).pipe(finalize(() => this.loading.set(false))).subscribe({ next: value => this.data.set(value), error: error => this.error.set(error?.error?.error?.message ?? error?.message ?? 'Unable to load the dashboard.') });
  }
  update(filters: Partial<DashboardQuery>): void { this.load({ ...this.filters(), ...filters }); }
}
