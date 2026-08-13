from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.enums import CategoryType

DEFAULT_EXPENSE_CATEGORIES: list[tuple[str, str, str]] = [
    ("Housing", "Home", "#6D4C41"),
    ("Utilities", "Bolt", "#F9A825"),
    ("Groceries", "ShoppingCart", "#43A047"),
    ("Restaurants", "Restaurant", "#FB8C00"),
    ("Transportation", "DirectionsCar", "#1E88E5"),
    ("Entertainment", "Theaters", "#8E24AA"),
    ("Healthcare", "LocalHospital", "#E53935"),
    ("Shopping", "LocalMall", "#D81B60"),
    ("Education", "School", "#3949AB"),
    ("Travel", "Flight", "#00897B"),
    ("Insurance", "Shield", "#546E7A"),
    ("Debt", "CreditCard", "#B71C1C"),
    ("Subscriptions", "Autorenew", "#5E35B1"),
    ("Other", "Category", "#757575"),
]

DEFAULT_INCOME_CATEGORIES: list[tuple[str, str, str]] = [
    ("Salary", "Payments", "#2E7D32"),
    ("Freelance", "Work", "#00838F"),
    ("Investment Income", "TrendingUp", "#1565C0"),
    ("Gifts", "CardGiftcard", "#AD1457"),
    ("Other", "Category", "#757575"),
]


def seed_default_categories(db: Session) -> list[Category]:
    """Insert the system default categories if they don't already exist.

    Idempotent: safe to call multiple times (e.g. on repeated migration
    runs or in tests) since it checks for existing default rows first.
    """
    existing = {
        (c.name, c.type) for c in db.query(Category).filter(Category.is_default.is_(True)).all()
    }

    created: list[Category] = []
    for name, icon, color in DEFAULT_EXPENSE_CATEGORIES:
        if (name, CategoryType.EXPENSE) in existing:
            continue
        created.append(
            Category(name=name, type=CategoryType.EXPENSE, icon=icon, color=color, is_default=True)
        )
    for name, icon, color in DEFAULT_INCOME_CATEGORIES:
        if (name, CategoryType.INCOME) in existing:
            continue
        created.append(
            Category(name=name, type=CategoryType.INCOME, icon=icon, color=color, is_default=True)
        )

    db.add_all(created)
    db.flush()
    return created
