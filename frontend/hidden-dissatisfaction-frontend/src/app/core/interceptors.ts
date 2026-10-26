import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthStore } from './auth.store';

export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const auth = inject(AuthStore); const token = auth.token();
  const withHeaders = request.clone({ setHeaders: { 'Accept-Language': auth.language(), ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
  return next(withHeaders);
};
export const errorInterceptor: HttpInterceptorFn = (request, next) => next(request).pipe(catchError((error: HttpErrorResponse) => { if (error.status === 401) inject(AuthStore).clearSession(); return throwError(() => error); }));
