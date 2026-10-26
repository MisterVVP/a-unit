# React and TypeScript: practical engineering guide

Use this guidance for React work in either JavaScript/JSX or TypeScript/TSX. Respect the repository's React version, framework, configuration, and conventions.

## Component design and rendering
- Make rendering deterministic from props, state, and context. Never trigger requests, mutate external state, or mutate props/state while rendering.
- Keep each component focused on a user-facing responsibility. Compose components instead of creating generic frameworks; extract a custom Hook only for reusable stateful behavior.
- Keep the minimal state necessary to represent the UI. Compute filtered, formatted, and other derived values during render instead of mirroring props into state.
- Lift shared state to the nearest appropriate owner. Use stable identity-based keys for list items, not array positions when items can move.

## Hooks, events, and effects
- Call Hooks only at the top level of a React component or custom Hook, before conditional returns.
- Put user-triggered actions in event handlers. Use an Effect only to synchronize with something outside React, such as a subscription, network connection, or browser API.
- Include reactive dependencies, clean up subscriptions and listeners, and prevent stale async responses from overwriting newer state. Use cancellation or result-ignoring patterns where appropriate.
- Do not add memoization by default. Measure a meaningful performance problem before introducing caching or memoized callbacks.

## TypeScript and TSX
- Use `.tsx` when the file contains JSX and `.ts` for TypeScript without JSX. Do not migrate working JavaScript solely for typing.
- Explicitly describe public component props and callback contracts; let the compiler infer local types when unambiguous.
- Type events, form values, refs, context, and state according to actual data. Model distinct request states with discriminated unions when useful.
- Avoid `any`, unsafe type assertions, and non-null assertions that conceal uncertain values. Narrow unknown inputs before using them.
- Preserve existing `tsconfig`, React types, and type-check scripts; use project-supported JSX settings and React versions.

## Accessibility and verification
- Use native semantic elements, associated form labels, accessible error/status messages, keyboard interactions, and deliberate focus behavior.
- Represent loading, empty, failure, success, and retry flows where relevant.
- Test user-observable behavior and critical interactions; run available React Hooks linting, type checks, and browser tests. State what was actually exercised.
