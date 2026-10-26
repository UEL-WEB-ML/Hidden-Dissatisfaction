import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthStore } from './auth.store';
export const authGuard: CanActivateFn = (_route, state) => { const auth = inject(AuthStore); return auth.isAuthenticated() ? true : inject(Router).createUrlTree(['/login'], { queryParams: { returnUrl: state.url } }); };
export const managerGuard: CanActivateFn = () => inject(AuthStore).role() === 'MANAGER' || inject(Router).createUrlTree(['/queue']);
