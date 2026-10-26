import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ApiClient } from '../../core/api-client.service';
import { OrderDetailStore } from './order-detail.store';
describe('OrderDetailStore', () => { let store: OrderDetailStore; let http: HttpTestingController; beforeEach(() => { TestBed.configureTestingModule({ imports: [HttpClientTestingModule], providers: [ApiClient, OrderDetailStore] }); store = TestBed.inject(OrderDetailStore); http = TestBed.inject(HttpTestingController); }); afterEach(() => http.verify()); it('exposes a forbidden state for a 403 response', () => { store.load('o-1'); http.expectOne('/api/v1/orders/o-1').flush({}, { status: 403, statusText: 'Forbidden' }); expect(store.forbidden()).toBeTrue(); expect(store.error()).toBeNull(); }); });
