# Database Design

PostgreSQL 16, accessed through SQLAlchemy 2.0 (typed `Mapped[...]` models) with Alembic migrations. This document covers the schema as of Milestone 2.

## Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ CATEGORIES : "owns (custom)"
    USERS ||--o{ TRANSACTIONS : "owns"
    USERS ||--o{ BUDGETS : "owns"
    USERS ||--o{ SAVINGS_GOALS : "owns"
    CATEGORIES ||--o{ TRANSACTIONS : "classifies"
    CATEGORIES ||--o{ BUDGET_CATEGORIES : "limited by"
    BUDGETS ||--o{ BUDGET_CATEGORIES : "has"

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        bool is_active
        datetime created_at
        datetime updated_at
    }

    CATEGORIES {
        uuid id PK
        uuid user_id FK "null = system default"
        string name
        enum type "income | expense"
        string icon
        string color
        bool is_default
        datetime created_at
        datetime updated_at
    }

    TRANSACTIONS {
        uuid id PK
        uuid user_id FK
        uuid category_id FK
        enum type "income | expense"
        numeric amount "> 0"
        string payee "merchant or income source"
        text description
        date transaction_date
        enum payment_method "nullable, expense only"
        bool is_recurring
        enum recurring_frequency "required if is_recurring"
        datetime created_at
        datetime updated_at
    }

    BUDGETS {
        uuid id PK
        uuid user_id FK
        int month "1-12"
        int year
        numeric overall_amount "nullable"
        datetime created_at
        datetime updated_at
    }

    BUDGET_CATEGORIES {
        uuid id PK
        uuid budget_id FK
        uuid category_id FK
        numeric amount "> 0"
        datetime created_at
        datetime updated_at
    }

    SAVINGS_GOALS {
        uuid id PK
        uuid user_id FK
        string name
        numeric target_amount "> 0"
        numeric current_amount ">= 0"
        date target_date "nullable"
        text description
        datetime created_at
        datetime updated_at
    }
```

## Design Decisions

### UUID primary keys

Every table uses a UUID primary key (SQLAlchemy's database-agnostic `Uuid` type, backed by native `uuid` on Postgres) instead of an autoincrement integer. In a financial app, a sequential ID in a URL (`/transactions/1847`) leaks how many records exist and invites enumeration. UUIDs close that off. Every query is still scoped by `user_id` server-side — the UUID choice is defense in depth, not a substitute for that check.

### Transactions: one table, not two

Income and expenses live in a single `transactions` table, discriminated by a `type` column, rather than separate `incomes` / `expenses` tables. The API exposes one `/transactions` collection, and cash-flow totals, search, filtering, and recurring-transaction logic all need to reason about both kinds together — splitting them would mean duplicating that logic across two tables for no real benefit. The one field that differs semantically by type, `payee`, is documented as "merchant for an expense, income source for income" rather than kept as two sparse nullable columns — the frontend labels it appropriately based on `type`.

### Enums stored as `VARCHAR` + `CHECK`, not native Postgres `ENUM`

`TransactionType`, `PaymentMethod`, `RecurringFrequency`, and `CategoryType` are all implemented with SQLAlchemy's `Enum(..., native_enum=False)`, which stores the value as a `VARCHAR` with a `CHECK` constraint instead of a Postgres native enum type. Native enums require an `ALTER TYPE ... ADD VALUE` migration to add a new value later (e.g. a new payment method), which can't run inside a transaction in older Postgres versions and is generally awkward. A check-constrained varchar is a plain, reversible column-level change. The trade-off is a marginally less strict type at the storage layer — enforcement is identical in practice, since the API validates the same enum via Pydantic before it ever reaches the database.

### Money as `Numeric(12, 2)`

All monetary amounts use `Numeric(12, 2)` (fixed-point decimal), never `Float`. Binary floating point cannot represent most decimal currency values exactly, which is unacceptable for anything tracking money. `Decimal` is used consistently in the Python layer as well.

### `Transaction.amount` is always positive

The sign of a transaction is carried by `type` (`income`/`expense`), not by the amount itself — enforced with `CHECK (amount > 0)`. This avoids the classic bug class where a transaction's direction depends on remembering to negate a number somewhere in application code; cash-flow math instead branches explicitly on `type`.

### Recurring metadata lives on the transaction row (for now)

`is_recurring` and `recurring_frequency` are columns on `transactions` rather than a separate `recurring_transaction_rules` table, enforced together by a `CHECK` constraint (`is_recurring = true` requires a non-null `recurring_frequency`, and vice versa). This is sufficient through the transaction, budget, and dashboard milestones. A dedicated rules table becomes worthwhile once we build "upcoming recurring transaction" projection and notifications (Milestone 10), where we need to track a rule's *next due date* independently of the historical instances already recorded — that table will be introduced there rather than speculatively now.

### Categories: system defaults + user-owned custom categories, one table

`categories.user_id` is nullable: `NULL` means a system default category (seeded by the initial migration, `is_default = true`), a real UUID means a user-created custom category. This avoids a separate "default categories" table/enum while still letting users add their own. A unique constraint on `(user_id, name, type)` stops a user from creating duplicate categories, while still allowing different users to each have their own "Freelance" category, and allowing the same name to exist as both an income and an expense category.

### Budgets: month/year row + per-category limits

`budgets` holds one row per user per calendar month (`UNIQUE(user_id, month, year)`) with an optional `overall_amount`. Category-level limits live in a separate `budget_categories` join table (`budget_id`, `category_id`, `amount`) rather than as columns on `budgets`, since the set of budgeted categories is user-defined and variable — a fixed column per category would not scale and would waste space for users who only budget a few categories.

### Tables deliberately not created yet

`transaction_imports`, `category_predictions`, and `notifications` are part of the eventual design but are **not** created in this migration. Each is only meaningful once its owning feature exists (CSV import in Milestone 7, AI categorization audit trail in Milestone 8, in-app notifications in Milestone 10), and creating them now would mean empty, unused tables — the schema is expected to grow incrementally, migration by migration, alongside the features that need it.

### Referential integrity

- `users → categories/transactions/budgets/savings_goals`: `ON DELETE CASCADE`. Deleting a user removes their financial data (no orphaned rows).
- `categories → transactions`: `ON DELETE RESTRICT`. A category that has transactions pointing to it cannot be deleted outright — this forces an explicit reassignment/cleanup decision rather than silently orphaning or cascading a delete through a user's transaction history.
- `budgets → budget_categories`: `ON DELETE CASCADE`. A budget's category limits have no independent meaning once the budget itself is gone.

### Indexes

Beyond primary keys and the unique constraints above: `users.email` (login lookups), `categories.user_id`, `savings_goals.user_id`, and three composite indexes on `transactions` — `(user_id, transaction_date)`, `(user_id, category_id)`, `(user_id, type)` — covering the access patterns the app will actually use: a user's transaction history in date order, spend-by-category rollups, and income-vs-expense filtering.

## Default category seed data

The initial migration seeds 14 default expense categories and 5 default income categories (matching the project's category list) via `app.db.seed.seed_default_categories()`, called once from the migration's `upgrade()`. The function is idempotent — safe to call again — and is unit-tested independently of the migration itself (`tests/test_models.py`).

## Testing strategy

Model and constraint tests (`tests/test_models.py`) run against an in-memory SQLite database rather than Postgres, which is possible specifically because every model uses SQLAlchemy's database-agnostic types (`Uuid`, `Numeric`, `Enum(native_enum=False)`) instead of Postgres-only dialect types. This keeps the test suite fast with no external service dependency, while the Alembic migration itself is verified against a real PostgreSQL 16 instance (both `upgrade` and `downgrade`) before being committed.

## Known limitations / future work

- No soft-delete: deletions are hard deletes (constrained by the FK behavior above). Acceptable for a portfolio project; a real product might add `deleted_at` to `transactions` for recoverability.
- No multi-currency support — all amounts are assumed to be a single implicit currency.
- `budgets` are calendar-month only; no support for custom budget periods (e.g. a 4-week cycle).
