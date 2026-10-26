export type Role = 'SPECIALIST' | 'MANAGER';
export type Language = 'vi' | 'en';
export interface UserDto { user_id: string; username: string; full_name: string; role: Role; preferred_language: Language | null; created_at: string; active_count?: number | null; capacity?: number | null; slots_left?: number | null; }
export interface LoginRequest { username: string; password: string; }
export interface LoginResponse { token: string; user: UserDto; }
export interface ApiErrorBody { error?: { code?: string; message?: string; details?: Record<string, unknown> | null }; }
export type RiskLevel = 'HIGH' | 'MEDIUM' | 'LOW';
export type OrderStatus = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'SKIPPED';
export type SlaState = 'ok' | 'soon' | 'over' | 'none';
export interface QueueOrderDto { order_id: string; case_id: string; risk_score: number; risk_level: RiskLevel; status: OrderStatus; assignee_id?: string | null; assignee_name: string | null; sla_state: SlaState; sla_hours_left?: number | null; aging_hours: number; is_escalated?: boolean; is_stale?: boolean; needs_decision?: boolean; contact_count?: number; max_contact?: number; self_claim_allowed?: boolean; top_item?: { product_item_id: string; category: string; risk_score: number; risk_level: string; synthetic_data_flag: boolean }; }
export interface QueuePageDto { items: QueueOrderDto[]; total: number; limit: number; offset: number; }
export interface QueueSummaryDto { high_pending: number; high_pending_overdue: number; overdue: number; escalated: number; stale: number; needs_decision: number; first_pending: QueueOrderDto | null; me: UserDto | null; }
export interface QueueFilterOptionsDto { sellers: string[]; categories: string[]; }

export type SuggestedAction = 'CONTACT' | 'MONITOR' | 'NO_ACTION';
export interface OrderItemDto { product_item_id: string; product_id?: string; category: string; price?: number | null; weight_g?: number | null; photos?: number | null; risk_score: number; risk_level: RiskLevel; top_factors: string[]; suggested_action?: SuggestedAction; model_version?: string; predicted_at?: string; synthetic_data_flag: boolean; data_source?: 'olist_order_items' | 'synthetic_v1'; }
export interface OrderDetailDto extends QueueOrderDto {
  aggregation_rule: string; top_factors: string[]; suggested_action: SuggestedAction; model_version: string; predicted_at: string; threshold_version: string;
  items_count: number; top_item: OrderItemDto; has_synthetic_item: boolean; items: OrderItemDto[]; seller_id?: string; customer_city?: string; customer_state?: string;
  order_value?: number | null; freight?: number | null; purchase_at?: string | null; approved_at?: string | null; carrier_at?: string | null; delivered_at?: string | null; estimated_at?: string | null;
  cycle_no: number; queued_at: string; original_queued_at: string; total_aging_hours?: number; stale_hours?: number | null; outcome?: string | null; skip_reason?: string | null; updated_at?: string; closed_at?: string | null; reopen_count?: number; parameter_version?: string; sla_due_at?: string | null;
}
export interface OrderCycleDto { cycle_no: number; started_at: string; ended_at?: string | null; contact_count: number; parameter_version: string; }
export type ContactMethod = 'PHONE' | 'EMAIL' | 'CHAT' | 'OTHER';
export type ContactResult = 'REACHED' | 'NO_ANSWER' | 'CALLBACK' | 'WRONG_NUMBER';
export interface EvidenceDto { file_id: string; file_name: string; file_type: string; file_size: number; url?: string | null; }
export interface UploadResponse extends EvidenceDto {}
export interface ContactDto { contact_id: string; cycle_no: number; attempt_no: number; contacted_at: string; method: string; result: string; note?: string | null; next_contact_date?: string | null; evidence?: EvidenceDto[]; evidence_ref?: string | null; created_by_name: string; }
export interface ContactRequest { contacted_at: string; method: ContactMethod; result: ContactResult; note?: string; next_contact_date?: string | null; evidence: Array<Pick<EvidenceDto, 'file_id' | 'file_name' | 'file_type' | 'file_size'>>; evidence_ref?: string; }
export interface ContactResponse { contact: ContactDto; order: OrderDetailDto; }
export interface CommentDto { created_at: string; author_id: string; author_name: string; author_role: Role; text: string; }
export interface DecisionDto { created_at: string; actor_id: string; actor_name: string; cycle_no: number; decision: string; reason: string; next_step: string; next_step_assignee_name?: string | null; due_date?: string | null; note?: string | null; }
export type ManagerDecision = 'NO_FURTHER_ACTION' | 'FOLLOW_UP_CUSTOMER' | 'WORK_WITH_SELLER' | 'REFER_AFTER_SALES';
export interface DecisionRequest { decision: ManagerDecision; reason: string; next_step: string; next_step_assignee_id?: string | null; due_date?: string | null; note?: string | null; }
export interface DecisionResponse { decision: DecisionDto; order: OrderDetailDto; }
export interface DecisionListPageDto extends QueuePageDto {}
export interface StatusHistoryDto { created_at: string; actor_name: string; event_type: string; old_value: string; new_value: string; }
export interface ModelNoteDto { created_at: string; author_name: string; note: string; }
export interface OrderDetailResponseDto { order: OrderDetailDto; cycles: OrderCycleDto[]; contacts: ContactDto[]; comments: CommentDto[]; decisions: DecisionDto[]; next_step: DecisionDto | null; status_history: StatusHistoryDto[]; model_notes: ModelNoteDto[]; audit_events: unknown[] | null; seller_open_count: number; }
export interface AssignOrderRequest { assignee_id: string; reason: string; override_capacity: boolean; }
export interface CompleteOrderRequest { outcome: string; note: string; }
export interface SkipOrderRequest { reason: string; note?: string; }
export interface ReopenOrderRequest { reason: string; review_confirmed: boolean; }
export interface CommentRequest { text: string; }
export interface ModelNoteRequest { note: string; }
export interface OrderMutationResponse { order: OrderDetailDto; }
export interface ClaimResponse { order: QueueOrderDto; me: UserDto; }
export interface AssignResponse { order: OrderDetailDto; previous_assignee_name?: string | null; }
export interface CommentResponse { comment: CommentDto; }
export interface ModelNoteResponse { model_note: ModelNoteDto; }

export type DashboardView = 'order' | 'product';
export interface DashboardQuery { days?: 1 | 3 | 7; level?: RiskLevel; seller?: string; category?: string; assignee?: string; status?: 'OPEN' | OrderStatus; product_item?: string; view: DashboardView; }
export interface DashboardTotals { cases: number; open: number; pending: number; in_progress: number; completed: number; skipped: number; overdue: number; escalated: number; stale: number; needs_decision: number; }
export interface DashboardRates { closed: number | null; overdue: number | null; high: number | null; }
export interface DashboardBucket { key: string; total: number; high: number; open: number; }
export interface DashboardScoreBand { from: number; to: number; count: number; }
export interface DashboardWorkload { user_id: string; full_name: string; active: number; capacity: number | null; overdue: number; }
export interface DashboardAction { code: string; severity: 'danger' | 'warn' | 'info'; count?: number; overdue?: number; suggest?: string | null; user_id?: string; full_name?: string; active?: number; capacity?: number | null; high?: number; total?: number; high_total?: number; hours?: number; seller_id?: string; }
export interface DashboardTrendPoint { date: string; HIGH: number; MEDIUM: number; LOW: number; }
export interface DashboardProductItem { product_item_id: string; order_id: string; category: string | null; risk_score: number; risk_level: RiskLevel; synthetic_data_flag: boolean; order_status: OrderStatus; top_factor: string | null; }
export interface DashboardProduct { totals: { total_items: number; HIGH: number; MEDIUM: number; LOW: number; synthetic: number; orders: number }; by_category: DashboardBucket[]; top_items: DashboardProductItem[]; }
export interface DashboardResponse { as_of: string; from: string | null; view: DashboardView; totals: DashboardTotals; rates: DashboardRates; by_level: Record<RiskLevel, number>; score_bands: DashboardScoreBand[]; by_seller: DashboardBucket[]; by_category: DashboardBucket[]; workload: DashboardWorkload[]; attention: { high_unassigned: number; overdue: number; stale: number; needs_decision: number }; recent_overrides: Array<{ created_at: string; event_type: string; order_id: string; actor_name: string | null; reason: string | null }>; service: { cases: number; contacted: number; reached: number; with_first_contact: number; first_in_sla: number; median_first_contact_hours: number | null; issue_found: number; issue_followed_up: number; high_open_not_contacted: number }; actions: DashboardAction[]; trend: DashboardTrendPoint[]; product?: DashboardProduct; }
export type OperationalParameterKey = 'sla_calendar' | 'sla_hours_high' | 'sla_hours_medium' | 'sla_hours_low' | 'first_touch_hours' | 'soon_hours' | 'stale_hours' | 'capacity' | 'capacity_warn' | 'max_contact' | 'reopen_review_times' | 'retry_gap_days' | 'aging_days' | 'reopen_review_days';
export interface ParameterDto { key: OperationalParameterKey; value: string | number; version: number; effective_at: string; actor_id?: string; actor_name?: string; reason: string; created_at: string; unit: 'hours' | 'days' | 'orders' | 'times' | 'enum'; in_brd: boolean; status: 'ACTIVE' | 'SCHEDULED' | 'SUPERSEDED'; old_value?: string | number; }
export interface ParametersResponse { parameter_version: string; server_time: string; items: ParameterDto[]; history: ParameterDto[]; }
export interface CreateParameterRequest { key: OperationalParameterKey; value: string | number; effective_at: string; reason: string; }
export interface ParameterVersionResponse { key: OperationalParameterKey; value: string; version: number; effective_at: string; actor_id: string; reason: string; created_at: string; }
export interface AuditEventDto { event_id: number; created_at: string; event_type: string; order_id?: string | null; actor_id?: string | null; actor_name?: string | null; reason?: string | null; details?: Record<string, unknown> | null; }
export interface AuditEventsResponse { items: AuditEventDto[]; total: number; limit: number; offset: number; }
export interface AuditQuery { event_type?: string; actor_id?: string; order_id?: string; override_only?: boolean; limit: number; offset: number; }
