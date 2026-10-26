import { OrderDetailResponseDto } from '../../core/api-dtos';
import { OrderDetailVm } from './order-detail.models';

export function toOrderDetailVm(response: OrderDetailResponseDto): OrderDetailVm {
  const order = response.order;
  return {
    order, score: `${Math.round(order.risk_score * 100)}%`, status: order.status.replace('_', ' '), riskLabel: `${order.risk_level} RISK`,
    location: [order.customer_city, order.customer_state].filter(Boolean).join(', ') || 'Location not available',
    value: order.order_value == null ? '—' : `R$ ${order.order_value.toFixed(2)}`,
    topFactors: order.top_factors ?? [], items: order.items ?? [], cycles: response.cycles ?? [], history: response.status_history ?? []
  };
}
