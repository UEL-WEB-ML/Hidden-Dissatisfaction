import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthStore } from './core/auth.store';
@Component({
    selector: 'hd-root', imports: [RouterOutlet], changeDetection: ChangeDetectionStrategy.Eager,
 template: '<router-outlet />'
})
export class AppComponent { private readonly auth = inject(AuthStore); constructor() { this.auth.restore(); } }
