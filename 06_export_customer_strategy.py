"""Export three customer-segmentation queries from MySQL to reproducible CSV outputs.

Requires pandas and mysql-connector-python. Credentials are entered interactively.
No database writes are performed.
"""
from getpass import getpass
from pathlib import Path
import re

import mysql.connector
import pandas as pd

ROOT = Path(__file__).resolve().parent
SQL_FILE = ROOT / "sql" / "05_customer_strategy.sql"
OUTPUT_DIR = ROOT / "outputs"
EXPECTED_RECORDS = 45211
EXPECTED_CONVERSIONS = 5289


def read_queries(path: Path):
    content = path.read_text(encoding="utf-8-sig")
    matches = list(re.finditer(r"(?m)^-- QUERY: ([a-z][a-z0-9_]*)\s*$", content))
    if len(matches) != 3:
        raise ValueError("Expected 3 queries marked by '-- QUERY: name'")
    for i, match in enumerate(matches):
        name = match.group(1)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sql = content[match.end():end].strip().rstrip(";").strip()
        if not sql:
            raise ValueError(f"Empty query: {name}")
        yield name, sql


def validate_complete_groups(df, name):
    n = int(df["records"].sum())
    y = int(df["conversions"].sum())
    if (n, y) != (EXPECTED_RECORDS, EXPECTED_CONVERSIONS):
        raise ValueError(
            f"{name}: totals do not reconcile: records={n}, conversions={y}"
        )


def main():
    if not SQL_FILE.exists():
        raise FileNotFoundError(f"Missing SQL file: {SQL_FILE}")
    user = input("MySQL username [root]: ").strip() or "root"
    password = getpass("MySQL password (not shown): ")
    queries = list(read_queries(SQL_FILE))
    conn = mysql.connector.connect(
        host="127.0.0.1", port=3306, user=user,
        password=password, database="bank_marketing_project",
    )
    try:
        cursor = conn.cursor()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for name, sql in queries:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(cursor.fetchall(), columns=columns)
            if name in {"previous_outcome", "housing_previous_segments"}:
                validate_complete_groups(df, name)
            outpath = OUTPUT_DIR / f"{name}.csv"
            df.to_csv(outpath, index=False, encoding="utf-8-sig")
            print(f"\n{name}: {len(df)} groups -> {outpath}")
            if name == "candidate_segments":
                print(
                    "Coverage of filtered segments: "
                    f"{int(df['records'].sum()):,}/{EXPECTED_RECORDS:,} "
                    "observations (not expected to equal full data)."
                )
            print(df.head(12).to_string(index=False))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
