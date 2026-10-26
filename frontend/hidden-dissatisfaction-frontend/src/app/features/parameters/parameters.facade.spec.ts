import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiClient } from '../../core/api-client.service';
import { ParametersFacade } from './parameters.facade';

describe('ParametersFacade', () => {
  let facade: ParametersFacade; let http: HttpTestingController;
  beforeEach(() => { TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [ApiClient, ParametersFacade] }); facade = TestBed.inject(ParametersFacade); http = TestBed.inject(HttpTestingController); });
  afterEach(() => http.verify());
  it('keeps scheduled versions separate from current parameters', () => { facade.load(); http.expectOne('/api/v1/parameters').flush({ parameter_version: 'current', server_time: '2026-01-01T00:00:00Z', items: [{ key: 'capacity', value: 5, version: 1, effective_at: '2025-01-01T00:00:00Z', reason: 'seed', unit: 'orders', in_brd: true, status: 'ACTIVE' }], history: [{ key: 'capacity', value: 6, version: 2, effective_at: '2027-01-01T00:00:00Z', reason: 'shift', unit: 'orders', in_brd: true, status: 'SCHEDULED' }] }); expect(facade.data()?.items.length).toBe(1); expect(facade.scheduled().length).toBe(1); });
  it('posts only typed operational changes', () => { facade.save({ key: 'capacity', value: 6, effective_at: '2027-01-01T00:00:00Z', reason: 'More coverage' }); const request = http.expectOne('/api/v1/parameters'); expect(request.request.method).toBe('POST'); expect(request.request.body.key).toBe('capacity'); request.flush({ key: 'capacity', value: '6', version: 2, effective_at: '2027-01-01T00:00:00Z', actor_id: 'u1', reason: 'More coverage', created_at: '2026-01-01T00:00:00Z' }); http.expectOne('/api/v1/parameters').flush({ parameter_version: 'current', server_time: '2026-01-01T00:00:00Z', items: [], history: [] }); expect(facade.saved()).toBeTrue(); });
});
