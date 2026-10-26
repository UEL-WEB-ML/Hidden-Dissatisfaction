import { Routes } from '@angular/router';
import { authGuard, managerGuard } from './core/guards';
import { AppShellComponent } from './layout/app-shell.component';

export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./features/auth/login.component').then(m => m.LoginComponent) },
  { path: '', component: AppShellComponent, canActivate: [authGuard], children: [
    { path: '', pathMatch: 'full', redirectTo: 'queue' },
    { path: 'queue', loadComponent: () => import('./features/queue/queue.component').then(m => m.QueueComponent) },
    { path: 'orders/:orderId', loadComponent: () => import('./features/order-detail/order-detail.component').then(m => m.OrderDetailComponent), data: { title: 'Order detail', eyebrow: 'CASE CONTEXT' } },
    { path: 'dashboard', canActivate: [managerGuard], loadComponent: () => import('./features/placeholder/placeholder.component').then(m => m.PlaceholderComponent), data: { title: 'Risk overview', eyebrow: 'MANAGER VIEW' } },
    { path: 'audit', canActivate: [managerGuard], loadComponent: () => import('./features/placeholder/placeholder.component').then(m => m.PlaceholderComponent), data: { title: 'Audit history', eyebrow: 'READ-ONLY TRAIL' } },
    { path: 'parameters', canActivate: [managerGuard], loadComponent: () => import('./features/placeholder/placeholder.component').then(m => m.PlaceholderComponent), data: { title: 'Parameters', eyebrow: 'OPERATING RULES' } },
    { path: 'profile', loadComponent: () => import('./features/profile/profile.component').then(m => m.ProfileComponent) }
  ]}, { path: '**', redirectTo: '' }
];
