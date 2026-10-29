import { Component, inject, ChangeDetectionStrategy } from '@angular/core';

import { AuthStore } from '../../core/auth.store';
@Component({
    selector: 'hd-profile', imports: [], changeDetection: ChangeDetectionStrategy.Eager,
 template: `<div class="page-heading"><div><p class="eyebrow">ACCOUNT</p><h1>Your profile</h1><p class="lede">Personal settings for the operations workspace.</p></div></div><section class="profile-card"><div class="profile-hero"><div class="avatar large">{{ initials }}</div><div><h2>{{ auth.user()?.full_name }}</h2><p>{{ auth.user()?.username }} · {{ auth.user()?.role }}</p></div></div><div class="profile-details"><div><span>Preferred language</span><strong>{{ auth.language() === 'en' ? 'English' : 'Tiếng Việt' }}</strong></div><div><span>Workspace role</span><strong>{{ auth.user()?.role }}</strong></div></div></section>`
})
export class ProfileComponent { readonly auth = inject(AuthStore); get initials(): string { return this.auth.user()?.full_name.split(' ').map(x => x[0]).slice(-2).join('').toUpperCase() ?? ''; } }
