import { DatePipe } from '@angular/common';
import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CreateParameterRequest, OperationalParameterKey } from '../../core/api-dtos';
import { EmptyComponent, ErrorComponent, LoadingComponent } from '../../shared/states.component';
import { ParametersFacade } from './parameters.facade';

@Component({
    selector: 'hd-parameters', providers: [ParametersFacade], imports: [FormsModule, DatePipe, LoadingComponent, ErrorComponent, EmptyComponent], template: `
<div class="page-heading parameters-heading"><div><p class="eyebrow">OPERATING RULES <span class="dot"></span> MANAGER ONLY</p><h1>Parameters</h1><p class="lede">Schedule operational changes with a clear effective time. Model risk thresholds stay read-only.</p></div><button class="button secondary" type="button" (click)="facade.load()" [disabled]="facade.loading()">↻ Refresh</button></div>
@if (facade.loading()) {
  <hd-loading label="Loading operating parameters…"/>
  }@if (!facade.loading() && facade.error()) {
  <hd-error [message]="facade.error()!" (retry)="facade.load()"/>
}
@if (facade.data(); as data) {
  @if (!facade.loading() && !facade.error()) {
    <div class="parameter-layout"><main><section class="parameter-card"><div class="card-heading"><div><p class="eyebrow">CURRENT</p><h2>Effective now</h2></div><span class="version">{{ data.parameter_version }}</span></div><div class="parameter-table" role="table" aria-label="Current operational parameters"><div class="parameter-row parameter-head" role="row"><span>Rule</span><span>Value</span><span>Effective</span><span>Status</span></div>@for (item of data.items; track item) {
    <div class="parameter-row" role="row"><span><b>{{ label(item.key) }}</b><small>{{ item.key }} · {{ item.unit }}</small></span><strong>{{ item.value }}</strong><span>{{ item.effective_at | date:'MMM d, y, HH:mm' }}</span><span class="status active">ACTIVE</span></div>
    }</div></section><section class="parameter-card"><div class="card-heading"><div><p class="eyebrow">UPCOMING</p><h2>Scheduled changes</h2></div><span class="muted">{{ facade.scheduled().length }} queued</span></div>@if (!facade.scheduled().length) {
    <hd-empty title="No scheduled changes" message="New versions will appear here until their effective time."/>
    }@if (facade.scheduled().length) {
    <div class="parameter-table" role="table" aria-label="Scheduled parameter changes"><div class="parameter-row parameter-head"><span>Rule</span><span>New value</span><span>Effective</span><span>Reason</span></div>@for (item of facade.scheduled(); track item) {
    <div class="parameter-row"><span><b>{{ label(item.key) }}</b><small>v{{ item.version }} · {{ item.unit }}</small></span><strong>{{ item.value }}</strong><span>{{ item.effective_at | date:'MMM d, y, HH:mm' }}</span><span>{{ item.reason }}</span></div>
  }</div>
  }</section><section class="parameter-card"><div class="card-heading"><div><p class="eyebrow">IMMUTABLE RECORD</p><h2>Version history</h2></div><span class="muted">{{ data.history.length }} versions</span></div><div class="history-list">@for (item of data.history; track item) {
  <article><div><b>{{ label(item.key) }}</b><span class="status" [class]="item.status.toLowerCase()">{{ item.status }}</span></div><p><strong>{{ item.value }}</strong> · v{{ item.version }} · effective {{ item.effective_at | date:'MMM d, y, HH:mm' }}</p><small>{{ item.reason }} · {{ item.actor_name || 'Manager' }}</small></article>
}</div></section></main>
<aside class="parameter-card form-card"><div class="card-heading"><div><p class="eyebrow">NEW VERSION</p><h2>Schedule a change</h2></div></div><p class="form-help">Previous versions cannot be edited or deleted. Effective time must be in the future.</p><form (ngSubmit)="submit()"><label>Operational rule<select name="key" [(ngModel)]="form.key" (ngModelChange)="syncValue()">@for (option of editableKeys; track option) {
<option [ngValue]="option">{{ label(option) }}</option>
}</select><small>{{ form.key }} · {{ unit(form.key) }}</small></label><label>Value@if (form.key !== 'sla_calendar') {
<input name="value" type="number" [(ngModel)]="form.value" required>
}@if (form.key === 'sla_calendar') {
<select name="calendar" [(ngModel)]="form.value"><option value="CALENDAR">Calendar hours</option><option value="BUSINESS_HOURS">Business hours</option></select>
}</label><label>Effective time<input name="effective_at" type="datetime-local" [(ngModel)]="form.effective_at" required><small>Use your local time; the server validates the final timestamp.</small></label><label>Reason<textarea name="reason" [(ngModel)]="form.reason" rows="3" minlength="1" maxlength="1000" required placeholder="Why is this change needed?"></textarea></label>@if (crossFeedback()) {
<p class="cross-feedback">{{ crossFeedback() }}</p>
}@if (facade.saveError()) {
<p class="form-error" role="alert">{{ facade.saveError() }}</p>
}@if (facade.saved()) {
<p class="success-note" role="status">Change scheduled and added to the audit trail.</p>
}<button class="button primary" type="submit" [disabled]="facade.saving() || !form.reason || !form.effective_at">{{ facade.saving() ? 'Scheduling…' : 'Schedule change' }} <span>→</span></button></form></aside></div>
}
}`, changeDetection: ChangeDetectionStrategy.Eager,
 styles: [`.parameter-layout{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(290px,.55fr);gap:18px}.parameter-layout main{display:grid;gap:18px}.parameter-card{padding:21px;border:1px solid var(--line);border-radius:10px;background:#fff;box-shadow:var(--shadow)}.card-heading{display:flex;justify-content:space-between;align-items:start;margin-bottom:18px}.card-heading h2{margin:0;font:700 19px 'Space Grotesk'}.card-heading .eyebrow{margin-bottom:7px}.version,.muted{color:var(--muted);font-size:11px}.parameter-table{display:grid}.parameter-row{display:grid;grid-template-columns:1.4fr .6fr 1fr .7fr;gap:12px;align-items:center;padding:13px 0;border-top:1px solid #edf1f5;font-size:12px}.parameter-row span small{display:block;color:var(--muted);font-size:10px;margin-top:4px}.parameter-row strong{font:700 17px 'Space Grotesk'}.parameter-head{border-top:0;padding-top:0;color:var(--muted);font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase}.status{display:inline-block;width:max-content;padding:4px 7px;border-radius:999px;font-size:9px;font-weight:700;letter-spacing:.5px}.status.active{color:var(--teal);background:#e7f7f6}.status.scheduled{color:#946c0b;background:#fff8df}.status.superseded{color:var(--muted);background:#f1f4f7}.history-list{display:grid;gap:9px}.history-list article{padding:12px 14px;border-left:3px solid var(--line);background:#fbfcfe}.history-list article div{display:flex;justify-content:space-between;gap:10px}.history-list p{margin:7px 0 4px;font-size:12px}.history-list small{color:var(--muted);font-size:10px}.form-card{align-self:start}.form-help{color:var(--muted);font-size:11px;line-height:1.5}.form-card form{display:grid;gap:15px}.form-card label{display:grid;gap:6px;color:var(--ink-soft);font-size:12px;font-weight:700}.form-card input,.form-card select,.form-card textarea{width:100%;padding:10px 11px;border:1px solid var(--line);border-radius:7px;color:var(--ink);background:#fff}.form-card input:focus,.form-card select:focus,.form-card textarea:focus{border-color:var(--teal);outline:0;box-shadow:0 0 0 3px rgba(15,139,141,.12)}.form-card small{color:var(--muted);font-size:10px;font-weight:400}.cross-feedback{padding:10px 12px;margin:0;border-left:3px solid var(--gold);background:#fffaf0;color:#76590a;font-size:11px;line-height:1.45}.form-error{color:var(--coral);font-size:11px}.success-note{padding:10px 12px;margin:0;border-left:3px solid var(--teal);background:#effafa;color:var(--teal);font-size:11px}@media(max-width:800px){.parameter-layout{grid-template-columns:1fr}.parameter-row{grid-template-columns:1.3fr .7fr 1fr}.parameter-row>*:last-child{grid-column:3}.parameter-head>*:last-child{grid-column:auto}}@media(max-width:520px){.parameter-card{padding:16px}.parameter-row{grid-template-columns:1fr 1fr;gap:8px}.parameter-row>*:last-child{grid-column:1/-1}.parameter-head>*:last-child{grid-column:auto}}`]
})
export class ParametersComponent {
  readonly facade = inject(ParametersFacade); readonly editableKeys: OperationalParameterKey[] = ['sla_calendar','sla_hours_high','sla_hours_medium','sla_hours_low','first_touch_hours','soon_hours','stale_hours','capacity','capacity_warn','max_contact','reopen_review_times','retry_gap_days','aging_days','reopen_review_days'];
  readonly form: CreateParameterRequest & { value: string | number } = { key: 'capacity', value: 6, effective_at: '', reason: '' };
  constructor() { this.facade.load(); }
  label(key: string): string { return key.replaceAll('_',' ').replace(/\b\w/g, letter => letter.toUpperCase()); }
  unit(key: string): string { return key === 'sla_calendar' ? 'enum' : key.includes('days') ? 'days' : key.includes('capacity') || key === 'max_contact' ? 'orders' : key.includes('times') ? 'times' : 'hours'; }
  syncValue(): void { this.form.value = this.form.key === 'sla_calendar' ? 'CALENDAR' : 1; }
  crossFeedback(): string { if (this.form.key === 'capacity_warn') return 'Cross-rule check: capacity warning must stay below the current capacity.'; if (this.form.key === 'capacity') return 'Cross-rule check: existing capacity warning will be validated against this future value.'; return ''; }
  submit(): void { this.facade.save({ ...this.form, value: this.form.key === 'sla_calendar' ? this.form.value : Number(this.form.value), effective_at: new Date(this.form.effective_at).toISOString() }); }
}
