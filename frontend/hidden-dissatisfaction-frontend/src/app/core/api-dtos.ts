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
