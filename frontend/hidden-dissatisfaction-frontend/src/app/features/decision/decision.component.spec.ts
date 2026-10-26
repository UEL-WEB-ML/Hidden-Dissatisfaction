import { DecisionComponent } from './decision.component';

describe('DecisionComponent', () => {
  it('formats decision codes for the history label', () => {
    expect(DecisionComponent.prototype.label('FOLLOW_UP_CUSTOMER')).toBe('Follow Up Customer');
  });
});
