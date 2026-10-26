import { QueueOrderDto, Role } from '../../core/api-dtos';
import { QueueOrderVm } from './queue.models';

const title = (value: string): string => value.toLowerCase().replaceAll('_', ' ').replace(/\b\w/g, char => char.toUpperCase());
export function toQueueOrderVm(order: QueueOrderDto, role: Role | null): QueueOrderVm {
  return {
    id: order.order_id, shortId: `${order.order_id.slice(0, 12)}…`,
    category: order.top_item?.category ?? 'Order context', itemId: order.top_item?.product_item_id ?? '',
    risk: order.risk_level, score: `${Math.round(order.risk_score * 100)}%`, status: title(order.status), statusCode: order.status,
    owner: order.assignee_name ?? 'Unassigned', sla: order.sla_state === 'none' ? 'Closed' : order.sla_state === 'over' ? 'Overdue' : order.sla_state === 'soon' ? 'Due soon' : 'On track',
    slaCode: order.sla_state, aging: `${Math.round(order.aging_hours)}h`, escalated: Boolean(order.is_escalated), stale: Boolean(order.is_stale), needsDecision: Boolean(order.needs_decision),
    canClaim: role === 'SPECIALIST' && order.status === 'PENDING' && order.risk_level !== 'HIGH' && order.self_claim_allowed !== false,
    canAssign: role === 'MANAGER' && order.status !== 'COMPLETED' && order.status !== 'SKIPPED'
  };
}
