
import { Component, inject, signal, ChangeDetectionStrategy } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ApiClient } from '../../core/api-client.service';
import { QueueOrderDto } from '../../core/api-dtos';
import { ErrorComponent, LoadingComponent } from '../../shared/states.component';

@Component({
    selector: 'hd-decision-list', imports: [RouterLink, LoadingComponent, ErrorComponent], changeDetection: ChangeDetectionStrategy.Eager,
 template: `
  <div class="page-heading"><div><p class="eyebrow">MANAGER WORKFLOW <span class="dot"></span> F12</p><h1>Decisions to make</h1><p class="lede">Review closed cases and leave a traceable next step.</p></div><button class="button secondary" type="button" (click)="load()">↻ Refresh</button></div>
  <form class="toolbar" (submit)="search($event)" aria-label="Search decision cases"><label class="search-field"><span aria-hidden="true">⌕</span><span class="sr-only">Search cases</span><input #q [value]="term()" placeholder="Search order or product item ID" autocomplete="off"><kbd>↵</kbd></label><select class="decision-filter" #risk [value]="riskLevel()" aria-label="Filter by risk"><option value="">All risk</option><option value="HIGH">High</option><option value="MEDIUM">Medium</option><option value="LOW">Low</option></select><button class="button primary" type="submit">Search</button></form>
  @if (!loading() && !error()) {
    <p class="queue-count">Showing {{ cases().length }} of {{ total() }} cases</p>
    }@if (loading()) {
    <hd-loading/>
    }@if (error()) {
    <hd-error [message]="error()!" (retry)="load()"/>
  }
  @if (!loading() && !error() && cases().length) {
    <section class="table-card decision-table"><div class="table-head"><span>CASE</span><span>RISK</span><span>STATUS</span><span>OWNER</span><span></span></div>@for (item of cases(); track item) {
    <a class="table-row decision-row" [routerLink]="['/orders', item.order_id, 'decision']"><div><b class="mono">{{ item.order_id }}</b><small>{{ item.top_item?.category || 'Order review' }}</small></div><div><span class="risk-dot" [class]="item.risk_level.toLowerCase()"></span><b>{{ item.risk_level }}</b></div><div><span class="pill" [class]="item.status.toLowerCase()">{{ item.status }}</span><small>{{ item.needs_decision ? 'Decision needed' : 'Ready to review' }}</small></div><div><b>{{ item.assignee_name || 'Unassigned' }}</b><small>Needs manager decision</small></div><span class="row-chevron">›</span></a>
  }</section>
  }
  @if (!loading() && !error() && !cases().length) {
    <div class="state-card"><h3>Nothing waiting</h3><p>No cases match this search.</p></div>
  }
  `
})
export class DecisionListComponent {
  private readonly api = inject(ApiClient); readonly cases = signal<QueueOrderDto[]>([]); readonly loading = signal(true); readonly error = signal<string | null>(null); readonly total = signal(0); readonly term = signal(''); readonly riskLevel = signal('');
  constructor() { this.load(); }
  load(): void { this.loading.set(true); this.error.set(null); this.api.decisions({ q: this.term() || undefined, level: this.riskLevel() || undefined, limit: 20 }).subscribe({ next: page => { this.cases.set(page.items); this.total.set(page.total); this.loading.set(false); }, error: e => { this.error.set(e?.error?.error?.message || 'Could not load decision cases.'); this.loading.set(false); } }); }
  search(event: Event): void { event.preventDefault(); const form = event.target as HTMLFormElement; this.term.set((form.querySelector('input') as HTMLInputElement).value.trim()); this.riskLevel.set((form.querySelector('select') as HTMLSelectElement).value); this.load(); }
}
