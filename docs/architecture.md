# Architecture

## Backend: layered, with the repository pattern used selectively

```
app/
├── api/            FastAPI routers — request/response only, no business logic
├── schemas/         Pydantic models — request validation, response shaping
├── services/        Business logic, orchestration, custom exceptions
├── repositories/     Query-building for entities with real query complexity
├── models/           SQLAlchemy ORM models
├── ml/               Pure functions: categorization, forecasting, anomaly detection
├── core/             Config, JWT/password hashing, the get_current_user dependency
└── db/               Engine/session setup, default-category seed data
```

Every request flows `api → services → (repositories |  models) → schemas` back out. Routers never touch the ORM directly; they call a service function and translate its typed exceptions into HTTP status codes (a `CategoryNotFoundError` becomes a 404, a `CategoryTypeMismatchError` becomes a 422, and so on) — this keeps HTTP concerns entirely out of the business logic, which is what makes the service functions callable directly from tests without spinning up the app.

The repository pattern is applied **selectively**, not everywhere, per the brief's instruction to use it "only where it adds genuine value." `transaction_repository.py` is a real repository: transactions have genuinely complex, reusable query needs (filtering, sorting, pagination, per-category monthly aggregates, top-merchant rollups) shared across the transactions, analytics, budgets, predictions, and recommendations features. Categories and savings goals, by contrast, use their service module directly against the ORM — their queries are simple lookups with no reuse pressure, and adding a repository layer there would be indirection with no payoff.

## Frontend: one page per route, colocated API/type modules

```
src/
├── pages/        One component per route (TransactionsPage, BudgetsPage, InsightsPage, ...)
├── api/          One module per backend resource — every HTTP call goes through here, never inline in a component
├── types/        Hand-written interfaces mirroring the backend Pydantic schemas
├── components/   Shared, cross-page UI (ConfirmDialog, AppLayout, chart wrappers)
├── features/     Context providers that need state living above a single page (auth, notifications, toast)
├── hooks/         useAuth, useToast, useNotifications, useDebouncedValue
└── test/          Vitest setup (RTL matchers, jsdom config)
```

Every page component is `React.lazy`-loaded from `App.tsx`, so the production bundle splits per route instead of shipping as one chunk — the largest single chunk is Recharts (~389KB, pulled in only by the pages that actually render a chart), not the whole app. Data fetching follows one consistent shape throughout: local `useState` for `data | null` and `error | null`, a `useEffect` that fetches on mount (or on a dependency change, for filtered/paginated pages), and a loading spinner shown until the first fetch resolves — no data-fetching library, since nothing in this app needs cross-component cache invalidation or background refetching.

## Auth

JWT bearer tokens (`python-jose`), bcrypt password hashing via the `bcrypt` library directly (not `passlib`, which doesn't support recent bcrypt versions cleanly). `get_current_user` is a single FastAPI dependency every protected route declares; it decodes the token, loads the user, and rejects inactive accounts, all before the route body runs. Every ID-scoped endpoint (a specific transaction, budget, import, notification, ...) checks `resource.user_id == current_user.id` and returns **404**, never 403, when it doesn't match — a 403 would confirm the resource exists but belongs to someone else, which is itself a small information leak in a financial app.

## The three "AI" features are three different techniques, on purpose

The brief asked for AI categorization, spending predictions, and unusual-spending detection. It would have been easy to reach for a model in all three places; instead each uses whichever technique actually fits, and the difference is deliberate:

| Feature | Milestone | Technique | Why |
|---|---|---|---|
| Category suggestion | 8 | scikit-learn `TfidfVectorizer` + `MultinomialNB`, trained per-user, per-request | A real classification problem (which of N categories does this text belong to) with a real per-user training set (that user's own transaction history) |
| Spending forecast | 9 | scikit-learn `LinearRegression` over trailing monthly totals | A real regression problem (extrapolate a trend), same "train fresh, don't persist" reasoning as categorization |
| Unusual spending | 10 | Tukey's IQR fences (`Q3 + 1.5×IQR`), plain statistics | Outlier detection has a well-established statistical answer; dressing this up as ML would be exactly the "fake AI" the brief warned against |
| Budget/trend/savings recommendations | 9 | Threshold rules over data other features already compute | Not AI at all — extrapolating this month's spend-so-far by the fraction of the month elapsed is arithmetic, and calling it AI would be the same mistake as above |

Two more decisions run through all three real-ML features:

- **Nothing is persisted or cached.** Every model trains from scratch on the request that needs it. At this app's scale (a personal expense tracker's transaction history — hundreds of rows, not millions) training takes well under 100ms, so a serialized/versioned model would be meaningful complexity for no measurable benefit.
- **"Not enough data" is an honest, first-class response**, not a low-confidence guess. Categorization needs 10+ transactions across 2+ categories; forecasting needs 3+ months with real activity; anomaly detection needs 5+ prior transactions in a category. Below the threshold, the API returns `insufficient_data` (or, for anomalies, just doesn't flag anything) rather than presenting a number nobody should trust.

## Notifications vs. recommendations: similar-sounding, deliberately different lifecycles

These two features are easy to conflate but solve different problems:

- **Recommendations** (`GET /recommendations`) describe *current state* — is a budget on pace to be exceeded, right now, given today's date. Recomputed fresh on every request; nothing is stored, because storing a "warning" that's true today and false tomorrow would just mean cache invalidation logic for no reason.
- **Notifications** (`GET /notifications`) describe *point-in-time events* — this specific transaction, at the moment it was created, was a statistical outlier. That's a fact about the past, meant to be reviewed and dismissed once, so it's a persisted, `is_read`-tracked row (see `docs/database.md`).

## Testing strategy

Backend tests run against SQLite in-memory (fast, no external dependency) for everything except Alembic migrations themselves, which are verified against a real PostgreSQL 16 instance before being committed — possible because every model uses SQLAlchemy's dialect-agnostic types (`Uuid`, `Numeric`, `Enum(native_enum=False)`, `JSON`) rather than Postgres-only ones. 172 backend tests, 96% coverage. Frontend tests use Vitest + React Testing Library for components and hooks with real logic (forms, contexts, debouncing) — not every presentational component, since a test asserting "renders this text" for a component with no branches or state doesn't catch regressions, it just adds maintenance weight. Every milestone was additionally verified against the real stack once (real Postgres, real FastAPI, a real headless-Chromium browser) before being committed — unit and integration tests catch logic regressions, but only driving the actual UI catches the class of bug that only exists in the gap between "the API returns the right JSON" and "the button actually does the thing" (a few of these turned up during the project: an MUI Select needing `role="combobox"` rather than `input` in test selectors, a Suspense boundary swallowing the entire nav bar during route-level code splitting, a date formatter that choked on full ISO timestamps).
