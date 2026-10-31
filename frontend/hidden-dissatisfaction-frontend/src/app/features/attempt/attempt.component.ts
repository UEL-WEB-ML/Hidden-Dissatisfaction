import { DatePipe } from '@angular/common';
import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthStore } from '../../core/auth.store';
import { EmptyComponent, LoadingComponent } from '../../shared/states.component';
import { AttemptFacade } from './attempt.facade';

@Component({
    selector: 'hd-attempt', providers: [AttemptFacade], imports: [DatePipe, ReactiveFormsModule, RouterLink, LoadingComponent, EmptyComponent], changeDetection: ChangeDetectionStrategy.Eager,
 template: `
@if (facade.loading()) {
  <div><hd-loading label="Loading review activity…"/></div>
}
@if (!facade.loading() && facade.detail(); as vm) {
  <div class="page-heading attempt-heading"><div><a class="back-link" [routerLink]="['/orders', orderId]">← Case detail</a><p class="eyebrow">REVIEW ACTIVITY <span class="dot"></span> NEW ATTEMPT</p><h1>Add a contact attempt</h1><p class="lede">Record one append-only contact for <span class="mono">{{ vm.order.order_id }}</span>.</p></div><span class="attempt-counter">{{ vm.order.contact_count || 0 }} / {{ vm.order.max_contact || '—' }} this cycle</span></div>
  @if (!facade.canEdit()) {
    <div class="detail-disclaimer attempt-guard" role="alert"><b>READ ONLY</b><span>Only the current assignee can add an attempt while this case is IN PROGRESS.</span><a class="text-action" [routerLink]="['/orders', orderId]">Return to case</a></div>
  }
  <div class="attempt-grid"><main><form class="detail-card attempt-form" [formGroup]="form" (ngSubmit)="save()" novalidate>
    <div class="card-heading"><div><p class="eyebrow">CONTACT RECORD</p><h2>What happened?</h2></div><span class="required-note">* Required</span></div>
    <div class="form-grid"><label>Contacted at *<input type="datetime-local" formControlName="contacted_at" [max]="maxDate" aria-describedby="contacted-help"><small id="contacted-help">Use the case server time. Future times are not allowed.</small>@if (invalid('contacted_at')) {
    <small class="field-error">Enter when the contact happened.</small>
    }</label><label>Method *<select formControlName="method"><option value="">Choose a method</option><option value="PHONE">Phone</option><option value="EMAIL">Email</option><option value="CHAT">Chat</option><option value="OTHER">Other</option></select>@if (invalid('method')) {
    <small class="field-error">Choose a contact method.</small>
    }</label><label>Result *<select formControlName="result"><option value="">Choose a result</option><option value="REACHED">Reached</option><option value="NO_ANSWER">No answer</option><option value="CALLBACK">Callback requested</option><option value="WRONG_NUMBER">Wrong number</option></select>@if (invalid('result')) {
    <small class="field-error">Choose the contact result.</small>
    }</label><label>Next contact <input type="date" formControlName="next_contact_date"><small>Leave blank when no follow-up is needed.</small></label></div>
    <label>Note <textarea formControlName="note" rows="5" maxlength="2000" placeholder="Capture the useful context, without sensitive data"></textarea><small>{{ form.controls.note.value.length }}/2000</small></label>
    <div class="evidence-drop"><div><p class="eyebrow">EVIDENCE</p><h3>Attach proof of contact <span>(optional)</span></h3><p>Up to 3 files · PNG, JPG, or PDF · 5 MB each.</p></div><label class="button secondary upload-button">Choose files<input type="file" multiple accept="image/png,image/jpeg,application/pdf" (change)="filesSelected($event)" [disabled]="!facade.canEdit()"></label></div>
    @if (facade.uploads().length) {
      <ul class="upload-list">@for (item of facade.uploads(); track item; let i = $index) {
        <li><span class="file-icon">{{ item.file.type === 'application/pdf' ? 'PDF' : 'IMG' }}</span><div><b>{{ item.file.name }}</b><small>{{ size(item.file.size) }} · {{ item.state === 'uploaded' ? 'Ready' : item.state === 'uploading' ? 'Uploading…' : item.error || 'Waiting' }}</small></div>@if (item.state === 'error') {
        <button type="button" class="text-action" (click)="facade.retry(i)">Retry</button>
        }<button type="button" class="remove-file" (click)="facade.remove(i)" [attr.aria-label]="'Remove ' + item.file.name">×</button></li>
      }</ul>
    }
    @if (facade.error()) {
      <div class="form-error" role="alert">{{ facade.error() }}</div>
      }<div class="modal-actions"><a class="button secondary" [routerLink]="['/orders', orderId]">Cancel</a><button class="button primary" type="submit" [disabled]="!facade.canEdit() || facade.submitting()">{{ facade.submitting() ? 'Saving…' : 'Save attempt' }}</button></div>
      </form></main><aside><section class="detail-card"><div class="card-heading"><div><p class="eyebrow">ATTEMPT HISTORY</p><h2>Read-only timeline</h2></div></div><ol class="timeline">@for (contact of vm.contacts; track contact) {
      <li><span class="timeline-dot"></span><div><b>{{ contact.result.replace('_', ' ') }}</b><p>{{ contact.method }} · Attempt {{ contact.attempt_no }}</p><small>{{ contact.contacted_at | date:'medium' }} · {{ contact.created_by_name }}</small>@if (contact.note) {
      <p class="history-note">{{ contact.note }}</p>
    }</div></li>
    }@if (!vm.contacts.length) {
    <li class="muted">No attempts recorded in this case.</li>
  }</ol></section></aside></div>
  }@if (!facade.loading() && facade.error() && !facade.detail()) {
  <hd-empty title="Unable to open attempt" [message]="facade.error()!"/>
  }@if (!facade.loading() && facade.detail() && !facade.canEdit()) {
  <div class="attempt-footer"><a class="button secondary" [routerLink]="['/orders', orderId]">Back to case</a></div>
}`
})
export class AttemptComponent {
  readonly facade = inject(AttemptFacade); readonly auth = inject(AuthStore); readonly form = inject(FormBuilder).nonNullable.group({ contacted_at: [this.localNow(), Validators.required], method: ['', Validators.required], result: ['', Validators.required], note: ['', Validators.maxLength(2000)], next_contact_date: [''] });
  readonly route = inject(ActivatedRoute); readonly router = inject(Router); readonly orderId = this.route.snapshot.paramMap.get('orderId') ?? ''; readonly maxDate = this.localNow();
  constructor() { this.facade.load(this.orderId, this.auth.user()?.user_id ?? ''); }
  invalid(name: keyof typeof this.form.controls): boolean { const control = this.form.controls[name]; return control.invalid && (control.touched || control.dirty); }
  filesSelected(event: Event): void { const input = event.target as HTMLInputElement; if (input.files) this.facade.addFiles(input.files); input.value = ''; }
  size(bytes: number): string { return bytes < 1024 * 1024 ? `${Math.ceil(bytes / 1024)} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`; }
  save(): void { this.form.markAllAsTouched(); if (this.form.invalid || !this.facade.canEdit()) return; const value = this.form.getRawValue(); this.facade.submit(this.orderId, { contacted_at: value.contacted_at, method: value.method as 'PHONE', result: value.result as 'REACHED', note: value.note.trim() || undefined, next_contact_date: value.next_contact_date || null }, status => this.router.navigate(status === 'SKIPPED' ? ['/queue'] : ['/orders', this.orderId])); }
  private localNow(): string { const date = new Date(); const pad = (v: number) => String(v).padStart(2, '0'); return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`; }
}
