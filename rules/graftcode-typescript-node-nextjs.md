# Graftcode Rules for AI Coding Agents

## TypeScript / Node.js / Next.js

This file defines mandatory architectural rules, workflows, and prompt helpers for AI coding agents working on TypeScript, Node.js, and Next.js repositories that use Graftcode.

The goal is to build clean, composable distributed systems using Graftcode as the primary integration mechanism between:

- Node.js services
- TypeScript modules
- Next.js applications
- frontend and backend code
- backend-to-backend microservices

Graftcode must be treated as the default integration mechanism.

Do not design REST-first services unless the task explicitly requires an HTTP API for an external reason.

---

## 0. Authoritative Documentation - Must Read for the Specific Use Case

AI coding agents working in this repository must treat the Graftcode documentation as the source of truth.

Do not read only the root README and then guess the workflow.

Before implementing, choose the documentation page that matches:

1. the use case
2. the language
3. the runtime

Use these sources first:

- Quick Start Guide  
  https://github.com/grft-dev/graftcode-quick-start-guide

- Full Documentation  
  https://github.com/grft-dev/graftcode-documentation

For JavaScript, TypeScript, and Node.js work, prefer the JavaScript-specific quick start pages.

Examples:

- Expose a backend service with JavaScript  
  https://github.com/grft-dev/graftcode-quick-start-guide/blob/main/2-expose-backend/javascript.md

- Connect microservices with JavaScript  
  https://github.com/grft-dev/graftcode-quick-start-guide/blob/main/3-connect-microservices/javascript.md

- Use modules from any technology with JavaScript  
  https://github.com/grft-dev/graftcode-quick-start-guide/blob/main/4-use-modules-from-any-technology/javascript.md

- Expose MCP with JavaScript  
  https://github.com/grft-dev/graftcode-quick-start-guide/blob/main/5-expose-mcp/javascript.md

- Switch between monolith and microservices with JavaScript  
  https://github.com/grft-dev/graftcode-quick-start-guide/blob/main/6-switch-between-monolith-and-microservices/javascript.md

For Next.js frontend work, use the frontend / React guide when no Next.js-specific guide exists:

- Connect frontend to backend with React  
  https://github.com/grft-dev/graftcode-quick-start-guide/blob/main/1-connect-frontend-to-backend/react.md

When documentation and assumptions conflict, documentation wins.

---

## 1. Role of the AI Coding Agent

Design systems as Graftcode-exposed TypeScript / JavaScript modules, not REST-first applications.

Use public methods as the integration contract.

For this repository:

- Use TypeScript by default.
- Use Node.js-compatible modules.
- Keep public exported methods simple and intentional.
- Treat public classes, public functions, and public methods as the integration surface.
- Keep framework, transport, database, and infrastructure details out of the public surface.
- Use Grafts to connect services and consumers.
- Do not create custom SDKs when a Graft can be used.

The public method shape is the contract.

---

## 2. Golden Rules

### Service = Plain TypeScript / JavaScript Module

A service should be a plain module exposing public methods.

Good:

~~~ts
export class EnergyPriceCalculator {
  static getPrice(): number {
    return Math.floor(Math.random() * 5) + 100;
  }
}
~~~

Good:

~~~ts
export class CustomerService {
  async getCustomerName(customerId: string): Promise<string> {
    return "Example Customer";
  }
}
~~~

Good:

~~~ts
export function calculateTotal(amount: number, taxRate: number): number {
  return amount + amount * taxRate;
}
~~~

Bad:

~~~ts
export async function GET(request: Request) {
  // Do not use a route handler as the Graftcode contract.
}
~~~

Bad:

~~~ts
export function handler(req: NextApiRequest, res: NextApiResponse) {
  // Do not expose framework request / response objects.
}
~~~

---

## 3. Public Methods Define the Contract

Allowed public contract shapes:

- public class methods
- static public methods
- exported functions
- simple parameters
- simple return values
- objects only when the documentation and generated Graft support the shape
- async methods returning `Promise<T>`

Forbidden as public contract:

- Next.js route handlers
- Express handlers
- REST controllers
- `Request`
- `Response`
- `NextRequest`
- `NextResponse`
- `NextApiRequest`
- `NextApiResponse`
- database clients
- ORM models
- sockets
- streams
- buffers
- files
- framework-specific abstractions
- infrastructure handles

Internal implementation may use these types.

Public Graftcode-facing methods must not expose them.

---

## 4. Data Shape Rules

Do not force REST-style DTOs.

Graftcode is based on exposing public methods directly. The contract should be the public method signature, not a manually designed REST request / response model.

Prefer simple parameters when they are clear:

~~~ts
export class PricingService {
  static calculatePrice(basePrice: number, discountPercent: number): number {
    return basePrice * (1 - discountPercent / 100);
  }
}
~~~

Use object parameters only when they make the method easier to understand or maintain:

~~~ts
export type CalculatePriceInput = {
  basePrice: number;
  discountPercent: number;
};

export class PricingService {
  static calculatePrice(input: CalculatePriceInput): number {
    return input.basePrice * (1 - input.discountPercent / 100);
  }
}
~~~

Do not call these objects DTOs unless the project already uses that convention.

Use names like:

- `Input`
- `Result`
- `Options`
- `Params`
- domain-specific names

Examples:

~~~ts
export type CreateInvoiceInput = {
  customerId: string;
  amount: number;
};

export type CreateInvoiceResult = {
  invoiceId: string;
  status: string;
};
~~~

Avoid:

~~~ts
export type CreateInvoiceRequestDto = {
  // REST-style naming unless the project already uses it.
};

export type CreateInvoiceResponseDto = {
  // REST-style naming unless the project already uses it.
};
~~~

---

## 5. Supported Type Guidance

Use simple, serializable values in public method signatures.

Preferred:

- `string`
- `number`
- `boolean`
- arrays of supported values
- plain objects composed of supported values
- `Promise<T>` for async results

Use with care:

- `Date`
- optional fields
- nested objects
- unions
- enums

Before using advanced TypeScript shapes, verify support in the JavaScript / TypeScript Graftcode documentation or generated Graft output.

Avoid in public signatures:

- `any`
- `unknown`
- `object`
- `Map`
- `Set`
- `Buffer`
- `ReadableStream`
- `Blob`
- `File`
- `FormData`
- class instances with hidden runtime state
- functions / callbacks
- symbols
- circular structures

If unsure, simplify the public method signature.

---

## 6. No REST-First Design

Do not start with:

- API routes
- REST endpoints
- OpenAPI specs
- request / response DTOs
- generated SDKs
- hand-written HTTP clients
- fetch wrappers
- route-based service contracts

Start with:

1. a plain TypeScript / JavaScript module
2. public methods
3. simple inputs and outputs
4. Graftcode Gateway exposure
5. generated Graft consumption

Only add HTTP routes when explicitly required.

---

## 7. Standard Producer Workflow - Exposing a Node.js Service

For every new exposed service:

1. Identify the service boundary.
2. Create or update a plain TypeScript / JavaScript module.
3. Expose public methods intentionally.
4. Keep method inputs and outputs simple.
5. Avoid framework-specific public types.
6. Build or transpile TypeScript if needed.
7. Ensure `package.json` points to the correct module entry.
8. Run Graftcode Gateway using the JavaScript-specific documentation.
9. Open Graftcode Vision.
10. Verify that public methods are discovered correctly.
11. Copy the generated package manager install command from Graftcode Vision or `gg` output.
12. Consume the generated Graft from the target application.

Do not invent package names.

Do not invent registry URLs.

Do not invent generated imports.

---

## 8. Standard Consumer Workflow - Calling a Graft from Node.js / Next.js

For every consumer:

1. Identify which service is being consumed.
2. Open the relevant Graftcode output or Graftcode Vision page.
3. Copy the generated npm install command.
4. Install the generated package.
5. Import the generated class or method exactly as shown.
6. Call the remote method like local code.
7. Configure gateway / host settings only as required by the generated package and documentation.
8. Verify the call with a smoke test.

Do not create a custom SDK.

Do not create a REST client.

Do not hardcode guessed package names.

---

## 9. Node.js Service Pattern

Recommended structure:

~~~txt
src/
  services/
    pricing/
      PricingService.ts
      index.ts
  internal/
    database/
    config/
    utils/
~~~

Example:

~~~ts
// src/services/pricing/PricingService.ts

export type CalculatePriceInput = {
  basePrice: number;
  discountPercent: number;
};

export type CalculatePriceResult = {
  finalPrice: number;
};

export class PricingService {
  static calculatePrice(input: CalculatePriceInput): CalculatePriceResult {
    return {
      finalPrice: input.basePrice * (1 - input.discountPercent / 100),
    };
  }
}
~~~

~~~ts
// src/services/pricing/index.ts

export * from "./PricingService";
~~~

Rules:

- Keep public methods close to the business capability.
- Keep infrastructure in `internal`.
- Do not expose route handlers.
- Do not expose database models.
- Do not expose framework types.
- Keep the public surface small.

---

## 10. Next.js Pattern

Next.js route handlers, server actions, and React components must not be treated as the primary Graftcode contract.

Use this order:

1. service module
2. public methods
3. Graftcode exposure or consumption
4. Next.js usage
5. optional route handler only when required

Recommended structure:

~~~txt
src/
  app/
    page.tsx
    api/
      legacy-only/
        route.ts
  services/
    customer/
      CustomerService.ts
      index.ts
  graft/
    config.ts
~~~

Good:

~~~ts
// src/services/customer/CustomerService.ts

export class CustomerService {
  static async getCustomerName(customerId: string): Promise<string> {
    return "Example Customer";
  }
}
~~~

Bad:

~~~ts
// Do not use this as the Graftcode contract.

export async function GET(request: NextRequest) {
  return NextResponse.json({});
}
~~~

Route handlers may call services internally, but they must not define the distributed-system contract.

---

## 11. TypeScript Build Rules

If the repository uses TypeScript:

- Confirm how the project compiles TypeScript to JavaScript.
- Confirm the `main` or `exports` field in `package.json`.
- Run the project build before exposing through Graftcode Gateway.
- Point Graftcode Gateway at the correct package entry according to the JavaScript documentation.
- Verify discovered methods in Graftcode Vision.

Do not assume that raw `.ts` files are directly consumed unless the project is configured for that and the documentation supports it.

---

## 12. Gateway / gg Rules

Graftcode Gateway output is the source of truth.

Always copy from Gateway / Vision / `gg` output:

- generated npm install command
- generated package name
- registry location
- import path
- gateway / host configuration if required
- service discovery details

Never guess:

- package names
- registry names
- IDs
- generated imports
- gateway host
- project key
- configuration property names

When using a Project Key:

- create or use the project from the Graftcode portal
- pass the project key exactly as documented
- store the key in secure environment configuration
- do not hardcode it in source code

---

## 13. Configuration Rules

Use environment variables for deployment-specific configuration.

Do not hardcode production gateway values.

For Next.js:

- do not expose server-only gateway configuration through `NEXT_PUBLIC_` unless browser-side usage is explicitly required
- prefer server-side Graft usage when possible
- configure generated Graft settings once, close to application startup or in a dedicated config module
- follow the exact generated package documentation for configuration names

Example structure:

~~~txt
src/
  graft/
    config.ts
~~~

Do not scatter Graft configuration across components, route handlers, and services.

---

## 14. Prompt Helpers

For every implementation task, the AI coding agent must answer in this order:

1. What is the service boundary?
2. Is this producer-side or consumer-side work?
3. Which JavaScript / TypeScript Graftcode documentation page applies?
4. What public methods are exposed or consumed?
5. What input and output shapes are used?
6. Where is internal implementation placed?
7. How is Graftcode Gateway started?
8. Where does the generated npm install command come from?
9. Where is configuration set, if required?
10. How is the integration verified?

Every answer must include:

1. exposed or consumed public methods
2. relevant JavaScript / TypeScript Graftcode documentation page
3. Gateway / `gg` startup instructions
4. source of generated npm install command
5. configuration location, if required
6. verification steps

---

## 15. Verification Checklist

Before considering the task done, verify:

- the correct JavaScript-specific documentation page was used
- public methods are visible and intentional
- public method inputs and outputs are simple
- no framework request / response types are exposed
- no REST route is used as the primary integration contract
- no custom SDK was created
- generated install command was copied from Gateway / Vision / `gg` output
- generated imports were not guessed
- gateway / host configuration was not guessed
- Next.js server-only configuration is not leaked to the browser
- a smoke test calls the generated Graft successfully

Example smoke test:

~~~ts
const price = await EnergyPriceCalculator.getPrice();

console.log(price);
~~~

---

## 16. Anti-Patterns

Do not:

- default to REST
- start with API routes
- expose Next.js route handlers as contracts
- expose Express handlers as contracts
- expose `Request` / `Response`
- expose `NextRequest` / `NextResponse`
- expose database clients
- expose ORM entities
- expose streams, buffers, files, or sockets
- force REST-style DTOs
- invent generated package names
- invent registry URLs
- invent import paths
- invent configuration names
- skip Graftcode Vision verification
- skip the JavaScript-specific documentation
- build custom SDKs when a Graft can be used

---

## Final Rule

If something can be integrated via a Graft, it must not be integrated via hand-written REST, custom SDKs, or framework-specific API routes.