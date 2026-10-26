import { OrderDetailDto, OrderItemDto, OrderCycleDto, StatusHistoryDto } from '../../core/api-dtos';

export interface OrderDetailVm { order: OrderDetailDto; score: string; status: string; riskLabel: string; location: string; value: string; topFactors: string[]; items: OrderItemDto[]; cycles: OrderCycleDto[]; history: StatusHistoryDto[]; }
