# Password Strength Checker — Graftcode Gateway Demo

> **A plain JavaScript class, remotely callable — zero HTTP framework required.**

This demo shows how [Graftcode Gateway](https://github.com/grft-dev/graftcode-gateway) (`gg`) exposes a pure JavaScript class as a remotely callable service without Express, Fastify, Koa, Hono, or any other HTTP framework. You write business logic; Graftcode handles the transport.

---

## Overview

`PasswordChecker` is a zero-dependency password strength analyser that supports:

| Operation | Method |
|---|---|
| Full strength analysis | `checkStrength(password)` |
| Numeric strength score (0–5) | `getScore(password)` |
| Human-readable label | `getLabel(password)` |
| Common password detection | `isCommonPassword(password)` |
| Input validation with issue list | `validate(password)` |

### Strength Scoring

One point is awarded per satisfied criterion:

| Criterion | Requirement |
|---|---|
| Length | ≥ 8 characters |
| Uppercase | At least one `A–Z` |
| Lowercase | At least one `a–z` |
| Digit | At least one `0–9` |
| Special character | At least one of `!@#$%^&*` etc. |

### Strength Labels

| Score | Label |
|---|---|
| 0–1 | **Weak** |
| 2 | **Fair** |
| 3 | **Strong** |
| 4–5 | **Very Strong** |

---

## Why No HTTP Framework Is Required

Traditional service communication looks like this:

```
Your Class → Express/Fastify → HTTP Routes → JSON → HTTP Client → Consumer
```

With Graftcode Gateway it looks like this:

```
Your Class → gg (Gateway binary) → Strongly-typed Graft → Consumer
```

The `gg` binary **introspects** the public method signatures of `PasswordChecker` at startup. It reads the JSDoc type annotations, generates typed clients (Grafts), and exposes every public method as a callable endpoint — all without you writing a single route, schema, or serialisation layer.

From the consumer's side a remote call looks identical to a local function call:

```javascript
// With a Graft (remote)                  // Without a Graft (local)
checker.checkStrength("P@ssw0rd!")        checker.checkStrength("P@ssw0rd!")
```

The networking, serialisation, and transport stay entirely outside your business logic.

---

## High Level Architecture Diagram

### Traditional REST vs Graftcode Gateway

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TRADITIONAL REST APPROACH                           │
│                                                                         │
│  ┌──────────────┐   routes/   ┌──────────────┐  HTTP/JSON  ┌─────────┐ │
│  │ PasswordCh-  │  schemas/   │  Express /   │ ──────────► │Consumer │ │
│  │ ecker class  │ ──────────► │  Fastify /   │             │(any     │ │
│  │  (business   │  boilerpl.  │  Hono app    │ ◄────────── │ lang)   │ │
│  │   logic)     │             │  (HTTP layer)│             │         │ │
│  └──────────────┘             └──────────────┘             └─────────┘ │
│                                                                         │
│  You maintain: routes, schemas, serialisation, versioning, HTTP client  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     GRAFTCODE GATEWAY APPROACH                          │
│                                                                         │
│  ┌──────────────┐  JSDoc      ┌──────────────┐  Hypertube™ ┌─────────┐ │
│  │ PasswordCh-  │  introspect │  Graftcode   │ ──────────► │ Typed   │ │
│  │ ecker class  │ ──────────► │  Gateway     │             │  Graft  │ │
│  │  (business   │             │  (gg binary) │ ◄────────── │(auto-   │ │
│  │   logic)     │             │  port 5002   │             │generated│ │
│  └──────────────┘             └──────────────┘             └─────────┘ │
│                                                                         │
│  You maintain: ONLY the JavaScript class. Zero routes, zero schemas.   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Request Flow — How a Remote Call Works

```
                      CALLER SIDE                      SERVICE SIDE
                ┌─────────────────┐              ┌─────────────────────┐
                │                 │              │  Docker Container   │
Consumer code   │  Graft Client   │              │  ┌───────────────┐  │
──────────────► │  (auto-gen'd    │              │  │  gg binary    │  │
checker.        │   typed client) │  Hypertube™  │  │  (Gateway)    │  │
checkStrength(  │                 │ ────────────►│  └──────┬────────┘  │
"P@ssw0rd!")    │                 │◄─────────────│         │ invokes   │
                └─────────────────┘   response  │  ┌──────▼────────┐  │
                                                 │  │ PasswordCh-   │  │
                                                 │  │ ecker.        │  │
                                                 │  │ checkStrength │  │
                                                 │  │ (plain JS)    │  │
                                                 │  └───────────────┘  │
                                                 └─────────────────────┘
```

### Component Responsibilities

| Component | Role | Your Code? |
|---|---|---|
| `PasswordChecker` class | Business logic only | ✅ Yes |
| `gg` (Gateway binary) | Transport, serialisation, routing | ❌ Provided by Graftcode |
| Graft client | Typed remote caller, auto-generated | ❌ Generated by Graftcode |
| Docker container | Packages `gg` + your module | ✅ Dockerfile (5 lines of config) |
| Hypertube™ | Runtime-level bridge between processes | ❌ Built into Graftcode |

---

## Project Structure

```
password-strength-checker/
├── AGENTS.md                          # Dev conventions (Node 20+, node:test, JSDoc)
├── password_checker/
│   └── checker.js                     # PasswordChecker class — zero HTTP imports
├── tests/
│   └── test_password_checker.js       # node:test suite (offline, no Docker needed)
├── Dockerfile                         # gg + Node.js 20 runtime image
├── docker-compose.yml                 # one-command local run
├── package.json                       # scripts only, zero runtime dependencies
├── .gitignore
└── README.md
```

---

## Installation

### 1. Clone the repo (if you haven't already)

```bash
git clone https://github.com/grft-dev/graftcode-demos
cd "graftcode-demos/password-strength-checker"
```

### 2. Verify Node.js version

```bash
node --version
# Must be v20.0.0 or higher
```

No `npm install` is needed — there are **zero runtime dependencies**.

---

## Running Locally (Without Gateway)

You can `require` and call `PasswordChecker` directly — it is a plain JavaScript class:

```javascript
const { PasswordChecker } = require('./password_checker/checker');

const checker = new PasswordChecker();

// Full analysis
const result = checker.checkStrength('P@ssw0rd!');
console.log(result);
// {
//   score: 5,
//   label: 'Very Strong',
//   isCommon: false,
//   criteria: {
//     minLength: true,
//     hasUppercase: true,
//     hasLowercase: true,
//     hasDigit: true,
//     hasSpecial: true
//   },
//   feedback: []
// }

// Quick score
console.log(checker.getScore('abc123'));     // 2
console.log(checker.getLabel('abc123'));     // 'Fair'

// Common password detection
console.log(checker.isCommonPassword('password'));  // true
console.log(checker.isCommonPassword('Xk9#mP2@')); // false

// Validation
const { isValid, issues } = checker.validate('abc');
console.log(isValid);  // false
console.log(issues);
// [
//   'Password must be at least 8 characters long.',
//   'Password must contain at least one uppercase letter.',
//   'Password must contain at least one digit.',
//   'Password must contain at least one special character.'
// ]
```

Or run inline from the terminal:

```bash
node -e "
  const { PasswordChecker } = require('./password_checker/checker');
  const c = new PasswordChecker();
  console.log(JSON.stringify(c.checkStrength('P@ssw0rd!'), null, 2));
"
```

---

## Running Through Graftcode Gateway

### Option A — Docker Compose (recommended)

```bash
docker compose up --build
```

The gateway starts on **port 5002**.

### Option B — Docker directly

```bash
docker build -t password-strength-checker .
docker run -p 5002:5002 password-strength-checker
```

### Option C — `gg` binary on the host

Install `gg` from the [latest release](https://github.com/grft-dev/graftcode-gateway/releases/latest), then:

```bash
gg --runtime node --modules password_checker/checker.js --port 5002
```

Once running, connect any Graftcode-compatible client to `localhost:5002` to call `PasswordChecker` methods as if they were local.

---

## Running Tests

```bash
npm test
# or equivalently
node --test tests/test_password_checker.js
```

For verbose per-test output:

```bash
npm run test:verbose
# or
node --test --reporter=spec tests/test_password_checker.js
```

All tests are **offline** and **fast** — no network calls, no running Gateway or Docker container required.

Expected output (all passing):

```
▶ checkStrength
  ✔ throws TypeError for null input (Xms)
  ✔ throws TypeError for undefined input (Xms)
  ✔ returns score 0 and label Weak for empty string (Xms)
  ✔ returns Weak for a single lowercase letter (Xms)
  ✔ returns Fair for password meeting 2 criteria (Xms)
  ✔ returns Strong for password meeting 3 criteria (Xms)
  ✔ returns Very Strong for password meeting all 5 criteria (Xms)
  ...
▶ getScore
  ...
▶ getLabel
  ...
▶ isCommonPassword
  ...
▶ validate
  ...
▶ Edge cases
  ...
ℹ tests 40
ℹ pass 40
ℹ fail 0
```

---

## Example Requests / Responses

The examples below contrast the **traditional REST** pattern with the **Graftcode Graft** pattern. Notice that Graftcode has no HTTP method, URL, or JSON schema on the service side.

### Traditional REST (hypothetical — not what this demo does)

```http
POST /password/check HTTP/1.1
Content-Type: application/json

{ "password": "P@ssw0rd!" }
```

```json
{
  "score": 5,
  "label": "Very Strong",
  "isCommon": false
}
```

### Via Graftcode Graft (typed, no HTTP boilerplate)

```javascript
// Consumer code — looks like a local method call
const result = checker.checkStrength("P@ssw0rd!");
```

```javascript
// Response — strongly typed JavaScript object, no JSON parsing needed
{
  score: 5,
  label: "Very Strong",
  isCommon: false,
  criteria: {
    minLength: true,
    hasUppercase: true,
    hasLowercase: true,
    hasDigit: true,
    hasSpecial: true
  },
  feedback: []
}
```

### Error handling — same as local JavaScript

```javascript
checker.checkStrength(null);
// Throws: TypeError: password must be a string, got null

checker.checkStrength(42);
// Throws: TypeError: password must be a string, got number
```

### Validation result

```javascript
checker.validate("abc");
// {
//   isValid: false,
//   issues: [
//     "Password must be at least 8 characters long.",
//     "Password must contain at least one uppercase letter.",
//     "Password must contain at least one digit.",
//     "Password must contain at least one special character."
//   ]
// }
```

### Common password detection

```javascript
checker.isCommonPassword("password");  // true  (in built-in list)
checker.isCommonPassword("PASSWORD");  // true  (case-insensitive)
checker.isCommonPassword("Xk9#mP2@"); // false (unique)
```

---

## Key Points

- **Zero HTTP framework code** — `checker.js` imports nothing from Express, Fastify, Koa, or Hono.
- **Pure stdlib** — no `dependencies` at runtime; `devDependencies` is also empty.
- **JSDoc throughout** — required by AGENTS.md; also what `gg` uses for introspection.
- **Offline by design** — common password list is hardcoded, keeping tests and local runs network-free.
- **Mirrors stock portfolio tracker** — same Dockerfile pattern, same `gg` invocation flags, same README structure.
- **First JavaScript demo** in the `graftcode-demos` repo — uses `--runtime node` instead of `--runtime python`.

---

## References

- [Graftcode Gateway — GitHub](https://github.com/grft-dev/graftcode-gateway)
- [Graftcode Documentation](https://docs.graftcode.com)
- [What is Graftcode](https://docs.graftcode.com/introduction/what-is-graftcode)
