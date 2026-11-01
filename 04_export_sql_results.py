"""Export bank marketing campaign SQL analysis to reproducible CSV files.

Read-only SQL queries. The database password is prompted at runtime and never saved.
"""
from pathlib import Path
from getpass import getpass
import pandas as pd
import mysql.connector

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_RECORDS = 45_211
EXPECTED_CONVERSIONS = 5_289

QUERIES = {
    "campaign_detail.csv": """
        WITH labeled AS (
            SELECT
                CASE
                    WHEN campaign BETWEEN 1 AND 10 THEN CAST(campaign AS CHAR)
                    ELSE '11+'
                END AS contact_group,
                CASE
                    WHEN campaign BETWEEN 1 AND 10 THEN campaign
                    ELSE 11
                END AS sort_order,
                y
            FROM bank_marketing_project.bank_marketing
        )
        SELECT
            contact_group,
            COUNT(*) AS records,
            SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS conversions,
            ROUND(AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END) * 100, 2)
                AS conversion_rate
        FROM labeled
        GROUP BY contact_group, sort_order
        ORDER BY sort_order
    """,
    "housing_campaign_analysis.csv": """
        WITH labeled AS (
            SELECT
                housing,
                CASE
                    WHEN campaign = 1 THEN '1_contact'
                    WHEN campaign = 2 THEN '2_contacts'
                    WHEN campaign BETWEEN 3 AND 4 THEN '3_4_contacts'
                    ELSE '5_plus_contacts'
                END AS contact_band,
                CASE
                    WHEN campaign = 1 THEN 1
                    WHEN campaign = 2 THEN 2
                    WHEN campaign BETWEEN 3 AND 4 THEN 3
                    ELSE 4
                END AS sort_order,
                y
            FROM bank_marketing_project.bank_marketing
        )
        SELECT
            housing,
            contact_band,
            COUNT(*) AS records,
            SUM(CASE WHEN y = 'yes' THEN 1 ELSE 0 END) AS conversions,
            ROUND(AVG(CASE WHEN y = 'yes' THEN 1.0 ELSE 0.0 END) * 100, 2)
                AS conversion_rate
        FROM labeled
        GROUP BY housing, contact_band, sort_order
        ORDER BY housing, sort_order
    """,
}


def query_frame(cursor, sql):
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    return pd.DataFrame(rows, columns=columns)


def main():
    username = input("MySQL 用户名 [root]：").strip() or "root"
    password = getpass("MySQL 密码（输入不显示）：")
    conn = None
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=username,
            password=password,
            database="bank_marketing_project",
            connection_timeout=15,
        )
        cur = conn.cursor()
        for filename, sql in QUERIES.items():
            df = query_frame(cur, sql)
            n = int(df["records"].sum())
            converted = int(df["conversions"].sum())
            if (n, converted) != (EXPECTED_RECORDS, EXPECTED_CONVERSIONS):
                raise ValueError(
                    f"{filename} 汇总不匹配：记录 {n}，签约 {converted}；"
                    f"预期 {EXPECTED_RECORDS}、{EXPECTED_CONVERSIONS}。"
                )
            target = OUTPUT_DIR / filename
            df.to_csv(target, index=False, encoding="utf-8-sig")
            print("\n" + "=" * 64)
            print(f"已生成：{target}")
            print(f"校验通过：{n:,} 条记录，{converted:,} 条签约")
            print(df.to_string(index=False))
        print("\n两份 CSV 导出完成。")
    except mysql.connector.Error as exc:
        print(f"MySQL 连接或查询失败：{exc}")
        raise
    finally:
        if conn is not None and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    main()
