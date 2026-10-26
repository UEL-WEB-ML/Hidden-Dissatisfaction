import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiClient } from '../../core/api-client.service';
import { AuditFacade } from './audit.facade';

describe('AuditFacade', () => {
  let facade: AuditFacade; let http: HttpTestingController;
  beforeEach(() => { TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [ApiClient, AuditFacade] }); facade = TestBed.inject(AuditFacade); http = TestBed.inject(HttpTestingController); });
  afterEach(() => http.verify());
  it('loads filtered, paginated events', () => { facade.load({ event_type: 'OVERRIDE', override_only: true, limit: 20, offset: 20 }); const request = http.expectOne(r => r.url === '/api/v1/audit-events'); expect(request.request.params.get('event_type')).toBe('OVERRIDE'); expect(request.request.params.get('override_only')).toBe('true'); expect(request.request.params.get('offset')).toBe('20'); request.flush({ items: [], total: 21, limit: 20, offset: 20 }); expect(facade.total()).toBe(21); });
});
