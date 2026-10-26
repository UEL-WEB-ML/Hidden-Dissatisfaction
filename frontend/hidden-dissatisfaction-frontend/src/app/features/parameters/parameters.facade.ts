import { Injectable, computed, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';
import { ApiClient } from '../../core/api-client.service';
import { CreateParameterRequest, ParameterDto, ParametersResponse } from '../../core/api-dtos';

@Injectable()
export class ParametersFacade {
  private readonly api = inject(ApiClient);
  readonly data = signal<ParametersResponse | null>(null); readonly loading = signal(false); readonly saving = signal(false); readonly error = signal<string | null>(null); readonly saveError = signal<string | null>(null); readonly saved = signal(false);
  readonly scheduled = computed(() => this.data()?.history.filter(item => item.status === 'SCHEDULED') ?? []);
  load(): void { this.loading.set(true); this.error.set(null); this.api.parameters().pipe(finalize(() => this.loading.set(false))).subscribe({ next: value => this.data.set(value), error: error => this.error.set(error?.error?.error?.message ?? error?.message ?? 'Unable to load parameters.') }); }
  save(body: CreateParameterRequest): void { this.saving.set(true); this.saveError.set(null); this.saved.set(false); this.api.createParameter(body).pipe(finalize(() => this.saving.set(false))).subscribe({ next: () => { this.saved.set(true); this.load(); }, error: error => this.saveError.set(error?.error?.error?.message ?? error?.error?.detail?.message ?? error?.message ?? 'Parameter could not be scheduled.') }); }
}
