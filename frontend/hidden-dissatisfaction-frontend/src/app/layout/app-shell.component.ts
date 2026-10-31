import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthStore } from '../core/auth.store';
@Component({
    selector: 'hd-app-shell', imports: [RouterOutlet, RouterLink, RouterLinkActive], changeDetection: ChangeDetectionStrategy.Eager,
 template: `
<div class="app-frame"><aside class="side-rail"><a class="brand" routerLink="/queue"><span class="brand-mark">◒</span><span>signal<br><b>desk</b></span></a><div class="rail-label">WORKSPACE</div><nav><a routerLink="/queue" routerLinkActive="active"><span>◎</span>Risk queue</a>@if (auth.role() === 'MANAGER') {
<a routerLink="/dashboard" routerLinkActive="active"><span>◌</span>Overview</a>
}@if (auth.role() === 'MANAGER') {
<a routerLink="/audit" routerLinkActive="active"><span>≡</span>Audit history</a>
}@if (auth.role() === 'MANAGER') {
<a routerLink="/parameters" routerLinkActive="active"><span>⌁</span>Parameters</a>
}</nav><div class="rail-foot"><a routerLink="/profile" routerLinkActive="active"><span class="avatar small">{{ initials }}</span>Profile</a><button class="text-button" (click)="auth.logout()">Sign out <span>↗</span></button></div></aside><main class="main-column"><header class="topbar"><div class="mobile-brand">signal / <b>desk</b></div><div class="topbar-actions"><button class="language" (click)="toggleLanguage()">{{ auth.language() === 'en' ? 'EN' : 'VI' }} <span>⌄</span></button><a class="avatar" routerLink="/profile">{{ initials }}</a></div></header><section class="page-wrap"><router-outlet /></section></main></div>`
})
export class AppShellComponent { readonly auth = inject(AuthStore); get initials(): string { return this.auth.user()?.full_name.split(' ').map(part => part[0]).slice(-2).join('').toUpperCase() ?? '––'; } toggleLanguage(): void { this.auth.setLanguage(this.auth.language() === 'en' ? 'vi' : 'en'); } }
