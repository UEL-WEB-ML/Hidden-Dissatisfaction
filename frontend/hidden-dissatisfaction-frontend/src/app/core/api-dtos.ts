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
