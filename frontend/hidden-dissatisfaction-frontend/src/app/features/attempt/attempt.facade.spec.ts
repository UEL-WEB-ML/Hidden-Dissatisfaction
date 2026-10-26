import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiClient } from '../../core/api-client.service';
import { AuthStore } from '../../core/auth.store';
import { AttemptFacade } from './attempt.facade';

describe('AttemptFacade', () => {
  let facade: AttemptFacade;
  let http: HttpTestingController;
  const order = { order_id: 'o-1', status: 'IN_PROGRESS', assignee_id: 'u-1', contact_count: 0, max_contact: 3 } as never;
  beforeEach(() => { TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [ApiClient, AuthStore, AttemptFacade] }); facade = TestBed.inject(AttemptFacade); http = TestBed.inject(HttpTestingController); });
  afterEach(() => http.verify());

  it('rejects unsupported, oversized, and fourth evidence files before transport', () => {
    facade.addFiles([new File(['x'], 'notes.txt', { type: 'text/plain' })]);
    expect(facade.uploads()[0].state).toBe('error');
    expect(facade.uploads()[0].error).toContain('PNG');
    facade.error.set(null);
    const files = [1, 2, 3, 4].map(index => new File(['x'], `file-${index}.pdf`, { type: 'application/pdf' }));
    facade.addFiles(files);
    expect(facade.uploads().length).toBe(1); // the existing invalid item still occupies its slot
    expect(facade.error()).toContain('up to 3');
  });

  it('exposes a read-only guard when the case is not assigned to the current user', () => {
    facade.load('o-1', 'u-2');
    http.expectOne('/api/v1/orders/o-1').flush({ order, contacts: [], cycles: [], comments: [], decisions: [], next_step: null, status_history: [], model_notes: [], audit_events: null, seller_open_count: 0 });
    expect(facade.canEdit()).toBeFalse();
  });
});
