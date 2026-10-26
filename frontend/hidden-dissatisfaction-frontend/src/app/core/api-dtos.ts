export type Role = 'SPECIALIST' | 'MANAGER';
export type Language = 'vi' | 'en';
export interface UserDto { user_id: string; username: string; full_name: string; role: Role; preferred_language: Language | null; created_at: string; active_count?: number | null; capacity?: number | null; slots_left?: number | null; }
export interface LoginRequest { username: string; password: string; }
export interface LoginResponse { token: string; user: UserDto; }
export interface ApiErrorBody { error?: { code?: string; message?: string; details?: Record<string, unknown> | null }; }
export interface QueueOrderDto { order_id: string; case_id: string; risk_score: number; risk_level: 'HIGH' | 'MEDIUM' | 'LOW'; status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'SKIPPED'; assignee_name: string | null; sla_state: 'ok' | 'soon' | 'over' | 'none'; aging_hours: number; top_item?: { product_item_id: string; category: string; risk_score: number; risk_level: string; synthetic_data_flag: boolean }; }
export interface QueuePageDto { items: QueueOrderDto[]; total: number; limit: number; offset: number; }
