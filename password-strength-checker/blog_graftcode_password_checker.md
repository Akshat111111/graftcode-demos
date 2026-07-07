# Stop Writing Express Routes for Every Internal Service — Use Graftcode Instead

> *A deep-dive into the Password Strength Checker demo — how a plain JavaScript class becomes a fully remotely callable service without a single line of HTTP framework code.*

---

## Introduction

There is a ritual JavaScript developers know well. You write a business-logic class in an afternoon. It is clean, it is focused, and it does exactly one thing. Then comes the wrapping.

`const app = express()`. `app.post('/password/check', ...)`. A request body parser. Input validation middleware. A response serializer. A custom error handler. An OpenAPI spec so consumers know what to send. A client library on the other side that reconstructs — from scratch — the exact method signature you already wrote.

By the time you are done, the integration code outweighs the business logic by a factor of three.

This is not a criticism of Express, Fastify, Koa, or Hono. Each is excellent at what it does. The problem is structural: the REST-over-HTTP model forces you to encode your interface *twice* — once as code, once as a protocol layer — and then keep them in sync forever. Every new method means a new route, a new body schema, a new response shape, and a new client call-site. The protocol plumbing is not your product. It is overhead.

**Graftcode** challenges this assumption. Instead of asking you to wrap your class in a framework, it introspects the class at runtime — reads its public method signatures and JSDoc type annotations — and generates a strongly-typed remote callable called a **Graft**. The transport, the serialization, and the client stub all disappear from your code. From the consumer's perspective, calling a remote service is byte-for-byte identical to calling a local object.

The **Password Strength Checker** demo makes this concrete. It is a working password analysis service — five public methods, a scoring algorithm, common-password detection, input validation, 54 unit tests, Docker packaging, and full Graftcode Gateway integration — without importing Express, Fastify, Koa, Hono, or a single npm HTTP package.

This post walks through every layer.

---

## The Problem with Traditional HTTP Services in JavaScript

Let's be specific. Suppose you want to expose a password strength analysis method:

```javascript
checkStrength(password) {
  // Returns: { score, label, isCommon, criteria, feedback }
}
```

In an Express service, that becomes:

```javascript
// routes/password.js
const express = require('express');
const router = express.Router();
const { PasswordChecker } = require('../password_checker/checker');

const checker = new PasswordChecker();

router.post('/password/check', (req, res) => {
  const { password } = req.body;

  if (typeof password !== 'string') {
    return res.status(400).json({ error: 'password must be a string' });
  }

  try {
    const result = checker.checkStrength(password);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;

// app.js
const express = require('express');
const app = express();
app.use(express.json());
app.use('/api', require('./routes/password'));
app.listen(3000);
```

And on the client side:

```javascript
// client.js
async function checkStrength(password) {
  const resp = await fetch('http://service-host/api/password/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}
```

Count the accidental complexity: route definitions, body parsing middleware, manual type-checking that duplicates the validation already in the class, HTTP status code conventions, JSON serialization and deserialization in both directions, and a client function that re-exposes the exact same signature you already wrote.

And this is for **one method**. `PasswordChecker` has **five** public methods. Multiply this pattern across all of them, then multiply it across every microservice in your system.

The deeper problem: none of this code is *yours*. It is all glue. Your business logic — the scoring algorithm, the common-password set, the validation rules — lives in `checkStrength`. Everything else exists only because the HTTP protocol demands it.

---

## How Graftcode Eliminates the Glue

Graftcode's core insight is that **JSDoc type annotations already contain all the information a transport layer needs**: argument names, argument types, and return types. If the runtime can read those annotations, it can generate the transport layer itself.

The **Graftcode Gateway** (`gg`) is a binary that:

1. **Introspects** the public method signatures of your class using the language runtime.
2. **Generates typed Graft clients** — remote stubs that expose your methods as if they were local objects.
3. **Handles transport** via its proprietary **Hypertube™** protocol — a runtime-level bridge that connects processes without requiring your code to know anything about networking.
4. **Serializes and deserializes** arguments and return values automatically, using the type hints as the schema.

You write this:

```javascript
class PasswordChecker {
  /**
   * @param {string} password
   * @returns {{ score: number, label: string, isCommon: boolean, ... }}
   */
  checkStrength(password) { ... }
}
module.exports = { PasswordChecker };
```

You run this:

```bash
gg --runtime node --modules password_checker/checker.js --port 5002
```

A consumer calls this:

```javascript
checker.checkStrength("P@ssw0rd!")  // Looks local. Is remote.
```

Zero routes. Zero schemas. Zero HTTP client code. The method signature *is* the contract.

---

## The Password Strength Checker — A Real Example

### What It Does

`PasswordChecker` is a zero-dependency password analysis service. It scores passwords against five security criteria, labels them from Weak to Very Strong, detects common passwords from a built-in list, and validates input with human-readable error messages. The entire common-password list is hardcoded in the class — no database, no network call.

The complete public API:

| Method | Signature | Purpose |
|---|---|---|
| `checkStrength` | `(password: string) → object` | Full analysis: score, label, criteria, feedback |
| `getScore` | `(password: string) → number` | Numeric score 0–5 |
| `getLabel` | `(password: string) → string` | Weak / Fair / Strong / Very Strong |
| `isCommonPassword` | `(password: string) → boolean` | True if password is in common list |
| `validate` | `(password: string) → object` | `{ isValid, issues[] }` |

### The Core Class — Zero HTTP Imports

The entire [`checker.js`](https://github.com/grft-dev/graftcode-demos/blob/main/password-strength-checker/password_checker/checker.js) file begins with:

```javascript
"use strict";
```

That is the only top-level statement before the business logic begins. No `require('express')`. No `require('fastify')`. No `require('http')`. The `package.json` makes this contract explicit:

```json
{
  "dependencies": {},
  "devDependencies": {}
}
```

Zero runtime dependencies. Zero dev dependencies. Tests run via Node's built-in `node:test` runner.

### The Scoring Algorithm

The scoring logic uses five boolean criteria, each worth one point:

```javascript
const _hasMinLength = (password) => password.length >= 8;
const _hasUppercase = (password) => /[A-Z]/.test(password);
const _hasLowercase = (password) => /[a-z]/.test(password);
const _hasDigit     = (password) => /[0-9]/.test(password);
const _hasSpecial   = (password) => /[!@#$%^&*()\-_=+...].test(password);
```

The score is the count of satisfied criteria (0–5). The label maps cleanly:

```
0–1 → Weak
  2 → Fair
  3 → Strong
4–5 → Very Strong
```

No arbitrary weights. No magic constants. Pure, testable logic.

### The Public Class

```javascript
class PasswordChecker {
  /**
   * Perform a full password strength analysis.
   *
   * @param {string} password - The password to analyse.
   * @returns {{
   *   score: number,
   *   label: string,
   *   isCommon: boolean,
   *   criteria: {
   *     minLength: boolean,
   *     hasUppercase: boolean,
   *     hasLowercase: boolean,
   *     hasDigit: boolean,
   *     hasSpecial: boolean
   *   },
   *   feedback: string[]
   * }}
   * @throws {TypeError} If password is not a string.
   */
  checkStrength(password) {
    this._assertString(password);

    const criteria = {
      minLength:    _hasMinLength(password),
      hasUppercase: _hasUppercase(password),
      hasLowercase: _hasLowercase(password),
      hasDigit:     _hasDigit(password),
      hasSpecial:   _hasSpecial(password),
    };

    const score    = Object.values(criteria).filter(Boolean).length;
    const label    = _scoreToLabel(score);
    const isCommon = this.isCommonPassword(password);
    const feedback = [];

    if (!criteria.minLength)    feedback.push("Use at least 8 characters.");
    if (!criteria.hasUppercase) feedback.push("Add an uppercase letter.");
    if (!criteria.hasLowercase) feedback.push("Add a lowercase letter.");
    if (!criteria.hasDigit)     feedback.push("Add a number.");
    if (!criteria.hasSpecial)   feedback.push("Add a special character.");
    if (isCommon)               feedback.push("Avoid commonly used passwords.");

    return { score, label, isCommon, criteria, feedback };
  }
}
```

Notice the JSDoc `@param` and `@returns` blocks. These are not optional decoration — they are the mechanism by which `gg` understands the method's interface and generates typed Grafts on the consumer side.

### Common Password Detection

A hardcoded `Set` of 33 well-known bad passwords handles detection. The lookup is O(1) and case-insensitive:

```javascript
const COMMON_PASSWORDS = new Set([
  "password", "password123", "123456", "qwerty",
  "letmein", "admin", "welcome", "iloveyou", "trustno1",
  // ... 24 more
]);

isCommonPassword(password) {
  this._assertString(password);
  return COMMON_PASSWORDS.has(password.toLowerCase());
}
```

`"PASSWORD"`, `"Password"`, and `"pAsSwOrD"` all return `true`. No network call required.

### Input Validation

Every public method guards its input before doing any work:

```javascript
_assertString(value, paramName = "password") {
  if (typeof value !== "string") {
    throw new TypeError(
      `${paramName} must be a string, got ${value === null ? "null" : typeof value}`
    );
  }
  return value;
}
```

When `gg` calls a method with the wrong argument type — either from a misbehaving Graft or a direct call — the error propagates cleanly back to the caller as a structured exception, not an unhandled crash.

---

## The Architecture — What gg Actually Does

Understanding why you do not need a framework requires understanding what `gg` replaces.

### Traditional Architecture

```
┌──────────────┐   define    ┌──────────────┐   HTTP/JSON   ┌──────────────┐
│PasswordCheck │  ────────►  │ Express app  │  ──────────►  │  Consumer    │
│ er class     │  routes &   │ (route layer)│               │  (fetch/axios│
│ (your code)  │  schemas    │              │  ◄──────────  │   client)    │
└──────────────┘             └──────────────┘               └──────────────┘

 You maintain: routes, middleware, body parsing, error mapping,
               JSON schemas, client code, and HTTP status conventions.
```

### Graftcode Architecture

```
┌──────────────┐  JSDoc      ┌──────────────┐  Hypertube™   ┌──────────────┐
│PasswordCheck │ introspect  │  Graftcode   │  ──────────►  │ Typed Graft  │
│ er class     │ ──────────► │  Gateway     │               │ (auto-gen'd  │
│ (your code)  │             │  (gg binary) │  ◄──────────  │  client)     │
└──────────────┘             └──────────────┘               └──────────────┘

 You maintain: ONLY the JavaScript class. Nothing else.
```

`gg` reads the class, reads the JSDoc, and produces a Graft. The Graft is a typed client stub — generated by Graftcode, not written by you — that makes calling a remote `PasswordChecker` method look exactly like calling a local one.

### Component Responsibilities

| Component | Role | Written by you? |
|---|---|---|
| `PasswordChecker` class | Business logic — scoring, labelling, validation | ✅ Yes |
| `gg` (Gateway binary) | Introspection, transport, serialization, routing | ❌ Graftcode provides it |
| Graft client | Typed remote stub, auto-generated | ❌ Graftcode generates it |
| Docker container | Packages `gg` + your module | ✅ 5-line Dockerfile |
| Hypertube™ | Runtime-level bridge between processes | ❌ Built into Graftcode |

---

## The Docker Setup

The Dockerfile is deliberately minimal. It mirrors the pattern established by every other demo in the repository:

```dockerfile
FROM node:20-slim

RUN mkdir -p /usr/app \
    && apt-get update \
    && apt-get install -y wget \
    && wget -O /usr/app/gg.deb \
       https://github.com/grft-dev/graftcode-gateway/releases/latest/download/gg_linux_amd64.deb \
    && dpkg -i /usr/app/gg.deb \
    && rm /usr/app/gg.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY password_checker /usr/app/password_checker

CMD ["gg", "--runtime", "node", "--modules", "/usr/app/password_checker/checker.js", "--port", "5002"]
```

Three conceptual steps:
1. Install `gg` from the official GitHub release.
2. Copy your module into the container.
3. Tell `gg` which runtime and which file.

The `CMD` line is the entire Graftcode integration. `gg` does the rest.

Compare this to the equivalent Express server setup: `npm install express`, `Dockerfile` that copies `node_modules`, an `app.js` that registers routes, and a separate `npm start` script. The Graftcode version has none of that.

### One-Command Local Run

```bash
docker compose up --build
```

The gateway starts on port 5002. Connect any Graftcode-compatible client and call `PasswordChecker` methods directly.

---

## The Test Suite — 54 Tests, Zero Dependencies

One of the most important properties of this demo is what the tests *don't* need.

### No Test Framework Required

The test file uses Node.js's built-in `node:test` module, available and stable since Node 20:

```javascript
const { describe, it, before } = require("node:test");
const assert = require("node:assert/strict");
const { PasswordChecker } = require("../password_checker/checker");
```

No `npm install jest`. No `npm install mocha`. No configuration files for test runners. No `devDependencies` at all. The `package.json` `devDependencies` field is an empty object.

Running the tests is a single command:

```bash
node --test tests/test_password_checker.js
```

### No Network Required

The tests are designed to run fully offline — no running Gateway, no Docker container, no internet connection:

```javascript
before(() => {
  checker = new PasswordChecker();   // In-memory. Instant. No network.
});
```

This is intentional. The Graftcode integration is a deployment concern, not a testing concern. Your class's correctness can be verified before any gateway is involved.

### Coverage Across All Five Public Methods

The suite covers 6 test groups and 54 individual assertions:

```
▶ checkStrength    (14 tests)  — empty, null, weak, fair, strong, very strong,
                                 common passwords, feedback generation
▶ getScore          (8 tests)  — each possible score 0–5, boundary conditions
▶ getLabel          (8 tests)  — all four labels, always-valid constraint
▶ isCommonPassword  (9 tests)  — known common entries, case-insensitivity,
                                 non-common passwords, empty string
▶ validate         (10 tests)  — each missing criterion, common password,
                                 valid password, non-string input
▶ Edge cases        (5 tests)  — whitespace-only, very long (1000 chars),
                                 special-char-only, instance independence
```

All 54 pass in under 130 ms.

### What Good Tests Look Like Here

The tests are concise precisely because the class is testable as-is. There is no mocking of HTTP requests. No stubbing of middleware. No spinning up a test server. You create a `PasswordChecker`, call a method, and assert on the return value:

```javascript
it("returns Very Strong for password meeting all 5 criteria", () => {
  const result = checker.checkStrength("P@ssw0rd!");
  assert.equal(result.label, "Very Strong");
  assert.equal(result.score, 5);
});

it("marks a known common password in result", () => {
  const result = checker.checkStrength("password");
  assert.equal(result.isCommon, true);
  assert.ok(result.feedback.some((f) => f.includes("common")));
});

it("throws TypeError for null input", () => {
  assert.throws(() => checker.checkStrength(null), TypeError);
});
```

This is what testability looks like when your class has no framework entanglement.

---

## Running the Demo

### Locally — No Gateway Needed

```javascript
const { PasswordChecker } = require('./password_checker/checker');
const checker = new PasswordChecker();

// Full analysis
console.log(checker.checkStrength('P@ssw0rd!'));
// {
//   score: 5,
//   label: 'Very Strong',
//   isCommon: false,
//   criteria: { minLength: true, hasUppercase: true, hasLowercase: true,
//               hasDigit: true, hasSpecial: true },
//   feedback: []
// }

// Quick label
console.log(checker.getLabel('abc123'));      // 'Fair'

// Common password check
console.log(checker.isCommonPassword('qwerty'));  // true

// Validation
const { isValid, issues } = checker.validate('abc');
console.log(isValid);   // false
console.log(issues);
// [
//   'Password must be at least 8 characters long.',
//   'Password must contain at least one uppercase letter.',
//   'Password must contain at least one digit.',
//   'Password must contain at least one special character.'
// ]
```

No installation needed. `node >= 20`, no `npm install`.

### Via Graftcode Gateway

**Option A — Docker Compose (recommended):**

```bash
docker compose up --build
# Gateway on port 5002
```

**Option B — `gg` binary directly:**

```bash
gg --runtime node --modules password_checker/checker.js --port 5002
```

Once running, connect any Graftcode-compatible client. Your consumer code calls `checker.checkStrength("P@ssw0rd!")` — no HTTP, no fetch, no JSON, no status codes.

---

## What This Demo Teaches

### 1. Framework Imports Are a Choice, Not a Requirement

The assumption that a "service" needs a framework is deeply ingrained in JavaScript culture, but it is not technically necessary. `checker.js` imports nothing. It is a service because `gg` makes it one — not because you added Express.

When framework code is absent, the class is smaller, clearer, and easier to test. Every line does real work.

### 2. JSDoc Is Your Contract

In a REST service, your contract lives in three places simultaneously: the route definition, the request/response schemas, and the client code. They drift. They conflict. You version them separately.

With Graftcode, the JSDoc `@param` and `@returns` blocks on each method **are** the contract. `gg` reads them. The Graft is generated from them. There is a single source of truth.

```javascript
/**
 * @param {string} password
 * @returns {{ score: number, label: string, ... }}
 */
checkStrength(password) { ... }
```

Change the annotation, regenerate the Graft. No separate schema file to update. No client library to republish.

### 3. Tests Get Simpler When the Class Is Pure

In the traditional Express world, testing `checkStrength` means either:
- Unit-testing the class in isolation (fine), *and also*
- Integration-testing the route handler (supertest, mock requests, etc.)

With Graftcode, there is nothing to integration-test on the server side. The route layer does not exist. You write one set of tests for the one set of code that matters. The 54-test suite in this demo covers the class comprehensively in under 130 ms with zero external dependencies.

### 4. The Dockerfile Stays Simple

The `CMD` line of the Dockerfile:

```
CMD ["gg", "--runtime", "node", "--modules", "...", "--port", "5002"]
```

Is functionally equivalent to what an entire Express `app.js` does — accepting connections, routing requests, serializing responses — but it requires **none of that code from you**.

When you switch languages, you change `--runtime python` to `--runtime node` to `--runtime netcore`. The rest of the Dockerfile pattern stays identical. A polyglot architecture that shares one integration model.

---

## Graftcode vs Traditional REST — Side by Side

Here is the cost comparison for adding one new method to an existing service:

### With Express

1. Add the method to your class ✅
2. Write a new route handler
3. Define request body schema (Joi / Zod / manual)
4. Define response shape
5. Add error handling / HTTP status mapping
6. Update the OpenAPI spec
7. Regenerate / update the client library
8. Write route-level integration tests

**8 steps. 6 of them are boilerplate.**

### With Graftcode

1. Add the method to your class ✅
2. Add JSDoc annotations
3. (Re)start `gg`

**3 steps. 2 of them are inherent to the method itself.**

The compounding effect is significant. A service with 10 methods using Express has ~10× the overhead of one with Graftcode. A team managing 20 microservices has 200 endpoints to maintain, version, document, and keep synchronized. Graftcode reduces that to 20 classes.

---

## Positioning: Who Should Use This

Graftcode Gateway is not a replacement for REST or gRPC in every scenario. Public-facing APIs, browser clients, third-party integrations, and existing infrastructure all have good reasons to use HTTP. Graftcode does not ask you to throw those away.

Where Graftcode excels is **internal service-to-service communication** — the layer of calls that happens behind your API gateway, between services that you own and can instrument:

- Backend microservices calling each other
- Data pipeline stages invoking processing services
- A monolith extracting a business function into an isolated service
- Teams building new services that need to be callable from a polyglot system

In these scenarios, HTTP is protocol overhead. You control both sides. The consumer and the service are both written by your team. The only reason HTTP is in the picture is because "that is how services communicate." With Graftcode, it does not have to be.

---

## Example Request / Response Comparison

### Traditional REST (hypothetical — not what this demo does)

**Request:**
```http
POST /password/check HTTP/1.1
Content-Type: application/json

{ "password": "P@ssw0rd!" }
```

**Response:**
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
  "score": 5,
  "label": "Very Strong",
  "isCommon": false,
  "criteria": {
    "minLength": true,
    "hasUppercase": true,
    "hasLowercase": true,
    "hasDigit": true,
    "hasSpecial": true
  },
  "feedback": []
}
```

### Via Graftcode Graft (typed, no HTTP boilerplate)

```javascript
// Consumer code — identical to a local method call
const result = checker.checkStrength("P@ssw0rd!");

// result is already a typed JavaScript object — no JSON.parse needed
console.log(result.label);  // "Very Strong"
console.log(result.score);  // 5
```

The difference is not just syntactic. With Graftcode:
- You call a method, not a URL
- You receive a typed object, not a JSON string
- You get type errors at code time, not HTTP 400s at runtime
- Your consumer code has no `fetch`, no `try/catch` around status codes, no JSON parsing

### Error Handling

```javascript
// TypeError propagates back to the consumer as a typed exception
checker.checkStrength(null);
// TypeError: password must be a string, got null

// Identical to local behaviour
checker.checkStrength(42);
// TypeError: password must be a string, got number
```

Errors are not HTTP status codes. They are JavaScript exceptions — the same exceptions that would be thrown if the method were called locally. No mapping between `ValueError → 422`, no parsing `error.response.data.detail`. Just catch a `TypeError`.

---

## The Project Structure

```
password-strength-checker/
├── AGENTS.md                          # Dev conventions (Node 20+, node:test, JSDoc)
├── password_checker/
│   └── checker.js                     # PasswordChecker class — zero HTTP imports
├── tests/
│   └── test_password_checker.js       # 54 node:test assertions, zero dependencies
├── Dockerfile                         # node:20-slim + gg, 25 lines
├── docker-compose.yml                 # port 5002, restart unless-stopped
├── package.json                       # { "dependencies": {}, "devDependencies": {} }
├── .gitignore
└── README.md
```

The folder structure mirrors `stock portfolio tracker` (the canonical Python reference demo) and `sdn-currency-converter`. Same shape. Different language. Same `gg` invocation pattern with `--runtime node` in place of `--runtime python`.

This is the Graftcode polyglot promise in action: one binary, one flag, every language.

---

## Key Takeaways

- **Zero HTTP framework code** — `checker.js` does not import Express, Fastify, Koa, Hono, or any HTTP library. It is a plain JavaScript class from start to finish.

- **Zero npm dependencies** — no `npm install` at runtime or at test time. `node:test` is part of the Node.js standard library.

- **JSDoc is the contract** — the `@param` and `@returns` annotations on each method serve the same role as Pydantic schemas or Protocol Buffer definitions, but without a separate file, without a separate compilation step, and without a separate versioning lifecycle.

- **Tests are faster and simpler** — 54 tests, 130 ms, no supertest, no mock HTTP server, no Docker required to run them.

- **The Dockerfile is five logical lines** — install `gg`, copy the module, run `gg`. No application server configuration. No route registration. No middleware stack.

- **One gateway binary, any language** — `--runtime python`, `--runtime node`, `--runtime netcore`. The same operational model regardless of what language your service is written in.

---

## Conclusion

The Password Strength Checker demo is deliberately small. A class with five methods, a list of bad passwords, and a scoring algorithm. But the structural lesson it demonstrates scales to any size of service.

When you remove the HTTP framework from a service, you are left with what the service actually is: a class with methods. That class is easier to read, easier to test, easier to refactor, and easier to reason about. The Graftcode Gateway takes that class and makes it callable from anywhere — without asking you to add a single line of routing code.

The routing code you did not write is the routing code you will never have to debug, version, document, or keep synchronized with a schema. That is the Graftcode value proposition in one sentence.

If you are building internal services — services that talk to other services you own, in a system where you control both the caller and the callee — the overhead of REST is optional. `gg` makes it removable.

---

## Get Started

**Clone the demo:**

```bash
git clone https://github.com/grft-dev/graftcode-demos
cd graftcode-demos/password-strength-checker
```

**Run the tests:**

```bash
node --test tests/test_password_checker.js
# 54 passing
```

**Run via Graftcode Gateway:**

```bash
docker compose up --build
# Gateway on localhost:5002
```

**Try it locally:**

```javascript
const { PasswordChecker } = require('./password_checker/checker');
const checker = new PasswordChecker();
console.log(checker.checkStrength('P@ssw0rd!'));
```

---

## References

- [Graftcode Gateway — GitHub](https://github.com/grft-dev/graftcode-gateway)
- [Graftcode Documentation](https://docs.graftcode.com)
- [What is Graftcode](https://docs.graftcode.com/introduction/what-is-graftcode)
- [Password Strength Checker — Source Code](https://github.com/grft-dev/graftcode-demos/tree/main/password-strength-checker)
- [Stock Portfolio Tracker Demo](https://github.com/grft-dev/graftcode-demos/tree/main/stock%20portfolio%20tracker) — Python reference demo
