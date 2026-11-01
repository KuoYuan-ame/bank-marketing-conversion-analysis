"""Import prepared UCI Bank Marketing CSV into an existing local MySQL table.

Usage (from the project root):
    python -m pip install mysql-connector-python
    python 03_import_bank_to_mysql.py

Reads data/bank_mysql_import.csv (made by 02_prepare_mysql_import.py).
Requires the table defined by sql/01_create_database.sql.
Prompts for password at runtime; does not save any credentials.
"""

from __future__ import annotations

import csv
from getpass import getpass
from pathlib import Path

import mysql.connector
from mysql.connector import Error

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "data" / "bank_mysql_import.csv"
COLUMNS = [
    "record_id", "age", "job", "marital", "education", "default", "balance",
    "housing", "loan", "contact", "day", "month", "duration", "campaign",
    "pdays", "previous", "poutcome", "y",
]
INT_COLUMNS = {
    "record_id", "age", "balance", "day", "duration", "campaign",
    "pdays", "previous",
}
SQL_COLUMNS = ", ".join(f"`{column}`" for column in COLUMNS)
PLACEHOLDERS = ", ".join(["%s"] * len(COLUMNS))
INSERT_SQL = (
    f"INSERT INTO `bank_marketing` ({SQL_COLUMNS}) VALUES ({PLACEHOLDERS})"
)
BATCH_SIZE = 1000


def main() -> None:
    if not CSV_PATH.is_file():
        raise FileNotFoundError(
            f"缺少 {CSV_PATH}。请先运行 python 02_prepare_mysql_import.py"
        )

    print("导入目标：本地 MySQL / bank_marketing_project.bank_marketing")
    username = input("MySQL 用户名 [root]：").strip() or "root"
    password = getpass("MySQL 密码（输入时不会显示）：")
    connection = None
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=username,
            password=password,
            database="bank_marketing_project",
            autocommit=False,
            connection_timeout=10,
        )
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM `bank_marketing`")
        existing = cursor.fetchone()[0]
        if existing:
            print(f"检测到目标表中已有 {existing:,} 条记录。为避免重复导入，已停止。")
            return

        inserted = 0
        with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != COLUMNS:
                raise ValueError(
                    f"CSV 列名或顺序不符合预期：\n实际：{reader.fieldnames}\n预期：{COLUMNS}"
                )
            batch = []
            for row_number, row in enumerate(reader, start=1):
                values = tuple(
                    int(row[name]) if name in INT_COLUMNS else row[name]
                    for name in COLUMNS
                )
                batch.append(values)
                if len(batch) == BATCH_SIZE:
                    cursor.executemany(INSERT_SQL, batch)
                    inserted += len(batch)
                    batch.clear()
                    print(f"已处理 {inserted:,} 行", end="\r")
            if batch:
                cursor.executemany(INSERT_SQL, batch)
                inserted += len(batch)
        if inserted != 45211:
            raise ValueError(f"文件共有 {inserted:,} 行，不是预期的 45,211 行，已回滚。")

        cursor.execute(
            "SELECT COUNT(*), SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) "
            "FROM `bank_marketing`"
        )
        total, successes = cursor.fetchone()
        if (total, successes) != (45211, 5289):
            raise ValueError(
                f"导入验证失败：总行数={total}、签约记录={successes}；预期为 45211、5289。已回滚。"
            )
        connection.commit()
        print(f"\n导入成功：{total:,} 行，签约 {successes:,} 行，转化率 {successes / total:.2%}")
    except (Error, OSError, ValueError) as error:
        if connection and connection.is_connected():
            connection.rollback()
        print(f"\n导入失败，已尝试回滚：{error}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
