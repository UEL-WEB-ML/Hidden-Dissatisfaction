import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { AssignOrderRequest, AssignResponse, ClaimResponse, CommentRequest, CommentResponse, CompleteOrderRequest, ContactRequest, ContactResponse, DecisionListPageDto, DecisionRequest, DecisionResponse, LoginRequest, LoginResponse, ModelNoteRequest, ModelNoteResponse, OrderDetailResponseDto, OrderMutationResponse, QueueFilterOptionsDto, QueuePageDto, QueueSummaryDto, ReopenOrderRequest, SkipOrderRequest, UploadResponse, UserDto } from './api-dtos';

@Injectable({ providedIn: 'root' })
export class ApiClient {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;
  login(body: LoginRequest): Observable<LoginResponse> { return this.http.post<LoginResponse>(`${this.baseUrl}/auth/login`, body); }
  logout(): Observable<void> { return this.http.post<void>(`${this.baseUrl}/auth/logout`, {}); }
  me(): Observable<UserDto> { return this.http.get<UserDto>(`${this.baseUrl}/auth/me`); }
  updateLanguage(preferred_language: 'vi' | 'en'): Observable<UserDto> { return this.http.patch<UserDto>(`${this.baseUrl}/auth/me`, { preferred_language }); }
  queue(params: Record<string, string | number | undefined> = {}): Observable<QueuePageDto> {
    let query = new HttpParams(); Object.entries(params).forEach(([key, value]) => { if (value !== undefined) query = query.set(key, String(value)); });
    return this.http.get<QueuePageDto>(`${this.baseUrl}/orders`, { params: query });
  }
  queueSummary(): Observable<QueueSummaryDto> { return this.http.get<QueueSummaryDto>(`${this.baseUrl}/orders/summary`); }
  queueFilterOptions(): Observable<QueueFilterOptionsDto> { return this.http.get<QueueFilterOptionsDto>(`${this.baseUrl}/orders/filter-options`); }
  users(): Observable<UserDto[]> { return this.http.get<UserDto[]>(`${this.baseUrl}/users`); }
  claim(orderId: string): Observable<ClaimResponse> { return this.http.post<ClaimResponse>(`${this.baseUrl}/orders/${orderId}/claim`, {}); }
  assign(orderId: string, body: AssignOrderRequest): Observable<AssignResponse> { return this.http.post<AssignResponse>(`${this.baseUrl}/orders/${orderId}/assign`, body); }
  complete(orderId: string, body: CompleteOrderRequest): Observable<OrderMutationResponse> { return this.http.post<OrderMutationResponse>(`${this.baseUrl}/orders/${orderId}/complete`, body); }
  skip(orderId: string, body: SkipOrderRequest): Observable<OrderMutationResponse> { return this.http.post<OrderMutationResponse>(`${this.baseUrl}/orders/${orderId}/skip`, body); }
  reopen(orderId: string, body: ReopenOrderRequest): Observable<OrderMutationResponse> { return this.http.post<OrderMutationResponse>(`${this.baseUrl}/orders/${orderId}/reopen`, body); }
  comment(orderId: string, body: CommentRequest): Observable<CommentResponse> { return this.http.post<CommentResponse>(`${this.baseUrl}/orders/${orderId}/comments`, body); }
  modelNote(orderId: string, body: ModelNoteRequest): Observable<ModelNoteResponse> { return this.http.post<ModelNoteResponse>(`${this.baseUrl}/orders/${orderId}/model-notes`, body); }
  orderDetail(orderId: string): Observable<OrderDetailResponseDto> { return this.http.get<OrderDetailResponseDto>(`${this.baseUrl}/orders/${orderId}`); }
  uploadEvidence(file: File): Observable<UploadResponse> { const body = new FormData(); body.append('file', file, file.name); return this.http.post<UploadResponse>(`${this.baseUrl}/files`, body); }
  contact(orderId: string, body: ContactRequest): Observable<ContactResponse> { return this.http.post<ContactResponse>(`${this.baseUrl}/orders/${orderId}/contacts`, body); }
  decisions(params: Record<string, string | number | undefined> = {}): Observable<DecisionListPageDto> { let query = new HttpParams().set('needs_decision', 'true'); Object.entries(params).forEach(([key, value]) => { if (value !== undefined) query = query.set(key, String(value)); }); return this.http.get<DecisionListPageDto>(`${this.baseUrl}/orders`, { params: query }); }
  createDecision(orderId: string, body: DecisionRequest): Observable<DecisionResponse> { return this.http.post<DecisionResponse>(`${this.baseUrl}/orders/${orderId}/decisions`, body); }
}
