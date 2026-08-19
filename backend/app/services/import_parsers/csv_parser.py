import csv
import io

from app.services.import_parsers.base import MissingColumnsError, ParsedRow, TransactionFileParser

REQUIRED_COLUMNS = {"date", "type", "category", "payee", "amount"}
OPTIONAL_COLUMNS = {"description", "payment_method", "is_recurring", "recurring_frequency"}
KNOWN_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS


class CsvTransactionParser(TransactionFileParser):
    def parse(self, file_bytes: bytes) -> list[ParsedRow]:
        text = file_bytes.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        header = {(h or "").strip().lower() for h in (reader.fieldnames or [])}
        missing = REQUIRED_COLUMNS - header
        if missing:
            raise MissingColumnsError(missing)

        rows: list[ParsedRow] = []
        for row_number, raw_row in enumerate(reader, start=1):
            normalized = {
                key.strip().lower(): (value or "").strip()
                for key, value in raw_row.items()
                if key is not None and key.strip().lower() in KNOWN_COLUMNS
            }
            rows.append(ParsedRow(row_number=row_number, raw=normalized))
        return rows
