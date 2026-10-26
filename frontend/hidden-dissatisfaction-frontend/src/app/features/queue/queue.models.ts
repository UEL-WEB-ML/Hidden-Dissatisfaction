import { OrderStatus, QueueOrderDto, RiskLevel, SlaState } from '../../core/api-dtos';

export interface QueueQuery { q: string; level: RiskLevel | ''; status: 'OPEN' | OrderStatus | ''; seller: string; category: string; assignee: string; needs_decision: '' | 'true'; sla: 'over' | 'soon' | 'esc' | 'stale' | ''; sort: '' | 'sla' | 'aging'; limit: number; offset: number; }
export interface QueueOrderVm { id: string; shortId: string; category: string; itemId: string; risk: RiskLevel; score: string; status: string; statusCode: OrderStatus; owner: string; sla: string; slaCode: SlaState; aging: string; escalated: boolean; stale: boolean; needsDecision: boolean; canClaim: boolean; canAssign: boolean; }
