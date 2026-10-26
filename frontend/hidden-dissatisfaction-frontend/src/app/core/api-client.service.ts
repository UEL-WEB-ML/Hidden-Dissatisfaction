import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { LoginRequest, LoginResponse, QueueFilterOptionsDto, QueuePageDto, QueueSummaryDto, UserDto } from './api-dtos';

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
  claim(orderId: string): Observable<{ order: QueuePageDto['items'][number]; me: UserDto }> { return this.http.post<{ order: QueuePageDto['items'][number]; me: UserDto }>(`${this.baseUrl}/orders/${orderId}/claim`, {}); }
}
