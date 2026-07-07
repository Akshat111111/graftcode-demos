# AGENTS.md

- Target path: `graftcode-demos/password-strength-checker`
- Node.js 20+; use JSDoc `@param` / `@returns` annotations so Graftcode Gateway can introspect public method signatures
- Use `"use strict"` at the top of every `.js` file
- Zero runtime npm dependencies — pure Node.js built-ins only
- Test with Node's built-in `node:test` runner (`node --test tests/`); no external test frameworks (Jest, Mocha, etc.)
- Keep unit tests fast and offline — no network calls, no dependency on a running Gateway or Docker container
- Graftcode Gateway binary is `gg`. Reference: https://github.com/grft-dev/graftcode-gateway and https://docs.graftcode.com — verify current flags before relying on anything cached
