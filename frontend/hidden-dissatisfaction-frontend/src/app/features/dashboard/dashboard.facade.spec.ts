import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiClient } from '../../core/api-client.service';
import { DashboardFacade } from './dashboard.facade';

describe('DashboardFacade', () => {
  let facade: DashboardFacade; let http: HttpTestingController;
  beforeEach(() => { TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [ApiClient, DashboardFacade] }); facade = TestBed.inject(DashboardFacade); http = TestBed.inject(HttpTestingController); });
  afterEach(() => http.verify());
  it('sends compatible view and filter parameters and exposes the response', () => {
    facade.load({ view: 'product', days: 3, level: 'HIGH', seller: 's-1', status: 'OPEN' });
    const request = http.expectOne(r => r.url === '/api/v1/dashboard');
    expect(request.request.params.get('view')).toBe('product'); expect(request.request.params.get('days')).toBe('3'); expect(request.request.params.get('seller')).toBe('s-1');
    request.flush({ totals: { cases: 0 }, view: 'product' });
    expect(facade.loading()).toBeFalse(); expect(facade.data()?.view).toBe('product'); expect(facade.isEmpty()).toBeTrue();
  });
  it('turns API failures into an actionable error state', () => { facade.load(); http.expectOne(request => request.url === '/api/v1/dashboard').flush({ error: { message: 'No access' } }, { status: 403, statusText: 'Forbidden' }); expect(facade.error()).toBe('No access'); });
});
