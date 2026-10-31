import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { ApiClient } from './api-client.service';
import { Language, LoginRequest, Role, UserDto } from './api-dtos';

const TOKEN_KEY = 'hd_access_token';
const LANGUAGE_KEY = 'hd_language';

@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly api = inject(ApiClient);
  private readonly router = inject(Router);
  readonly user = signal<UserDto | null>(null);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly token = signal<string | null>(localStorage.getItem(TOKEN_KEY));
  readonly isAuthenticated = computed(() => Boolean(this.token()));
  readonly role = computed<Role | null>(() => this.user()?.role ?? null);
  readonly language = signal<Language>((localStorage.getItem(LANGUAGE_KEY) as Language | null) ?? 'en');

  login(credentials: LoginRequest): void {
    this.loading.set(true); this.error.set(null);
    this.api.login(credentials).pipe(finalize(() => this.loading.set(false))).subscribe({ next: response => { localStorage.setItem(TOKEN_KEY, response.token); this.token.set(response.token); this.user.set(response.user); this.persistLanguage(response.user.preferred_language ?? this.language()); }, error: error => this.error.set(error?.message ?? 'Unable to sign in') });
  }
  restore(): void { if (!this.token()) return; this.api.me().subscribe({ next: user => { this.user.set(user); this.persistLanguage(user.preferred_language ?? this.language()); }, error: () => this.clearSession() }); }
  setLanguage(language: Language): void { this.persistLanguage(language); if (this.user()) this.api.updateLanguage(language).subscribe({ next: user => this.user.set(user) }); }
  logout(): void {
    this.api.logout().subscribe({ error: () => undefined });
    this.clearSession();
    void this.router.navigateByUrl('/login');
  }
  clearSession(): void { localStorage.removeItem(TOKEN_KEY); this.token.set(null); this.user.set(null); }
  private persistLanguage(language: Language): void { localStorage.setItem(LANGUAGE_KEY, language); this.language.set(language); }
}
