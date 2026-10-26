import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthStore } from './core/auth.store';
@Component({ selector: 'hd-root', standalone: true, imports: [RouterOutlet], template: '<router-outlet />' })
export class AppComponent { private readonly auth = inject(AuthStore); constructor() { this.auth.restore(); } }
