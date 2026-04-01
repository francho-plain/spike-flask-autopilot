import csv
import os
import tempfile
from typing import Dict, List, Optional


class CsvSessionStore:
    FIELDNAMES = ["id", "start_at", "end_at", "created_at"]

    def __init__(self, path: str) -> None:
        self.path = path
        self._ensure_file()

    def _ensure_file(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=self.FIELDNAMES)
                writer.writeheader()

    def _read_rows(self) -> List[Dict[str, str]]:
        self._ensure_file()
        with open(self.path, "r", newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def _atomic_write(self, rows: List[Dict[str, str]]) -> None:
        directory = os.path.dirname(self.path)
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=directory, newline="", encoding="utf-8"
        ) as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
            temp_path = temp_file.name
        os.replace(temp_path, self.path)

    def get_all_sessions(self) -> List[Dict[str, str]]:
        rows = self._read_rows()
        return sorted(rows, key=lambda row: row["start_at"], reverse=True)

    def get_open_session(self) -> Optional[Dict[str, str]]:
        for row in self._read_rows():
            if not row["end_at"]:
                return row
        return None

    def start_session(self, start_at: str) -> Dict[str, str]:
        rows = self._read_rows()
        if any(not row["end_at"] for row in rows):
            raise ValueError("Ya hay una sesión abierta")

        next_id = str(max((int(row["id"]) for row in rows), default=0) + 1)
        new_row = {
            "id": next_id,
            "start_at": start_at,
            "end_at": "",
            "created_at": start_at,
        }
        rows.append(new_row)
        self._atomic_write(rows)
        return new_row

    def end_open_session(self, end_at: str) -> Dict[str, str]:
        rows = self._read_rows()
        for row in reversed(rows):
            if not row["end_at"]:
                row["end_at"] = end_at
                self._atomic_write(rows)
                return row
        raise ValueError("No hay sesión abierta para cerrar")
