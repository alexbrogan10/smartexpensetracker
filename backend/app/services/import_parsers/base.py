from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ParsedRow:
    """One row of a transaction import file, before business-rule validation.

    `raw` holds normalized (lowercase-keyed, stripped) string values exactly
    as read from the file — semantic validation (dates, amounts, category
    lookups, duplicates) happens in the import service, not here, so that
    adding a new file format only means implementing `parse()`.
    """

    row_number: int
    raw: dict[str, str] = field(default_factory=dict)


class MissingColumnsError(Exception):
    """Raised when a file is missing one or more required columns."""

    def __init__(self, missing_columns: set[str]):
        self.missing_columns = missing_columns
        super().__init__(f"Missing required columns: {', '.join(sorted(missing_columns))}")


class TransactionFileParser(ABC):
    """Turns raw file bytes into normalized rows. One implementation per format."""

    @abstractmethod
    def parse(self, file_bytes: bytes) -> list[ParsedRow]:
        """Parse `file_bytes` into rows, or raise MissingColumnsError."""
