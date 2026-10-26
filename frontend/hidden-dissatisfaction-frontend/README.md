# Hidden Dissatisfaction frontend

P10 Angular production foundation for Signal Desk. Standalone strict TypeScript, lazy feature routes, Signals-based auth state, typed `/api/v1` transport, role guards, language/auth/error interceptors, and a responsive shell are included. Feature routes beyond the queue foundation intentionally remain placeholders.

```bash
npm install
npm start
```

## Acceptance checks

Run these commands from this directory:

```bash
npm run lint
npm test
npm run build
```

Unit tests use Karma's `jsdom` launcher, so CI does not require a system Chrome
installation or a display server. The route acceptance tests cover the public
login entry point, primary destinations, and manager-only route protection.
