import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiClient } from '../../core/api-client.service';
import { OrderActionsFacade } from './order-actions.facade';

describe('OrderActionsFacade', () => {
  let facade: OrderActionsFacade;
  let http: HttpTestingController;
  beforeEach(() => { TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [ApiClient, OrderActionsFacade] }); facade = TestBed.inject(OrderActionsFacade); http = TestBed.inject(HttpTestingController); });
  afterEach(() => http.verify());

  it('requires an outcome and note before completing', () => {
    facade.open('complete'); facade.submit('o-1', () => undefined);
    expect(facade.fieldErrors()).toEqual({ outcome: 'Choose an outcome.', note: 'Add a completion note.' });
    expect(() => http.expectOne('/api/v1/orders/o-1/complete')).toThrow();
  });

  it('keeps entered values after a server conflict', () => {
    facade.open('comment'); facade.update({ text: 'Keep this review context.' }); facade.submit('o-1', () => undefined);
    http.expectOne('/api/v1/orders/o-1/comments').flush({ error: { code: 'CONFLICT', message: 'Changed' } }, { status: 409, statusText: 'Conflict' });
    expect(facade.form().text).toBe('Keep this review context.');
    expect(facade.error()).toContain('Changed');
  });
});
