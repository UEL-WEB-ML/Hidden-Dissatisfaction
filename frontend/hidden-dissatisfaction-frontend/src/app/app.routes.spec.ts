import { routes } from './app.routes';

describe('application routes', () => {
  it('exposes the public login route and the primary authenticated destinations', () => {
    const shell = routes.find(route => route.path === '');
    const childPaths = shell?.children?.map(route => route.path) ?? [];

    expect(routes.some(route => route.path === 'login')).toBeTrue();
    expect(childPaths).toEqual(jasmine.arrayContaining(['queue', 'profile', 'dashboard', 'audit', 'parameters']));
  });

  it('protects manager-only destinations with the manager guard', () => {
    const shell = routes.find(route => route.path === '');
    const managerPaths = ['decisions', 'dashboard', 'audit', 'parameters'];

    for (const path of managerPaths) {
      const route = shell?.children?.find(child => child.path === path);
      expect(route?.canActivate).toBeTruthy();
    }
  });
});
