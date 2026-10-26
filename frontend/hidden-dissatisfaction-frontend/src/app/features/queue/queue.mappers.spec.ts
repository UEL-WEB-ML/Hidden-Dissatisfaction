import { QueueOrderDto } from '../../core/api-dtos';
import { toQueueOrderVm } from './queue.mappers';

const order = (overrides: Partial<QueueOrderDto> = {}): QueueOrderDto => ({
  order_id: 'a3f9c0ffee1234567890abcdef123456', case_id: 'case-1', risk_score: .84, risk_level: 'HIGH', status: 'PENDING',
  assignee_name: null, sla_state: 'over', aging_hours: 49, self_claim_allowed: false, ...overrides
});

describe('toQueueOrderVm', () => {
  it('keeps display mapping pure and exposes safe specialist actions', () => {
    const vm = toQueueOrderVm(order({ risk_level: 'MEDIUM', self_claim_allowed: true }), 'SPECIALIST');
    expect(vm.score).toBe('84%');
    expect(vm.sla).toBe('Overdue');
    expect(vm.canClaim).toBeTrue();
    expect(vm.owner).toBe('Unassigned');
  });

  it('does not expose claim for high risk or closed cases', () => {
    expect(toQueueOrderVm(order(), 'SPECIALIST').canClaim).toBeFalse();
    expect(toQueueOrderVm(order({ status: 'COMPLETED', assignee_name: 'A' }), 'MANAGER').canAssign).toBeFalse();
  });
});
