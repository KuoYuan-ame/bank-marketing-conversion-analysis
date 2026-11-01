"""Convert the UCI legacy bank-full.csv to a MySQL Workbench-friendly CSV.

Input:  data/bank-full.csv (semicolon-delimited)
Output: data/bank_mysql_import.csv (comma-delimited, UTF-8)

record_id is a synthetic *row* identifier for SQL use, NOT a customer ID.
No personally identifying account data or credentials are required.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'data' / 'bank-full.csv'
TARGET = ROOT / 'data' / 'bank_mysql_import.csv'
EXPECTED_COLUMNS = [
    'age', 'job', 'marital', 'education', 'default', 'balance',
    'housing', 'loan', 'contact', 'day', 'month', 'duration',
    'campaign', 'pdays', 'previous', 'poutcome', 'y',
]


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(
            f'未找到 {SOURCE}。请先将 UCI 的 bank-full.csv 放到 data 文件夹。'
        )

    # No changes are made to the source CSV. The extra ID identifies rows,
    # and exists only to provide a primary key in the MySQL analysis table.
    rows_written = 0
    with SOURCE.open('r', encoding='utf-8-sig', newline='') as input_file:
        reader = csv.DictReader(input_file, delimiter=';')
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(
                'CSV 的字段或顺序不符合预期。'
                f'\n预期：{EXPECTED_COLUMNS}\n实际：{reader.fieldnames}'
            )

        TARGET.parent.mkdir(parents=True, exist_ok=True)
        with TARGET.open('w', encoding='utf-8', newline='') as output_file:
            writer = csv.writer(output_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['record_id', *EXPECTED_COLUMNS])
            for row_number, row in enumerate(reader, start=1):
                writer.writerow([row_number, *(row[column] for column in EXPECTED_COLUMNS)])
                rows_written += 1

    print('========== MySQL 导入文件准备完成 ==========')
    print(f'原始文件：{SOURCE}')
    print(f'导入文件：{TARGET}')
    print(f'总记录数：{rows_written:,}')
    print('字段数量：18（新增 record_id + 原始 17 列）')
    print('CSV 分隔符：英文逗号；文本编码：UTF-8')
    print('提醒：record_id 是人为添加的行主键，不表示唯一客户。')
    if rows_written != 45211:
        print('警告：数据量不是预期的 45,211，请确认原始文件版本。')


if __name__ == '__main__':
    main()
