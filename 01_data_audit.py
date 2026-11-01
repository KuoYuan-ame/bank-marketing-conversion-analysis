"""UCI Bank Marketing: source audit and descriptive conversion analysis.

Input:  data/bank-full.csv   (download from UCI, semicolon separated)
Output: outputs/01_*.csv and outputs/01_conversion_by_job.png

No customer identifier is available. Each CSV row is treated as one observation,
not asserted to be a unique customer. This script performs NO causal inference.
"""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "data" / "bank-full.csv"
OUTPUT = ROOT / "outputs"
OUTPUT.mkdir(parents=True, exist_ok=True)

EXPECTED_COLUMNS = [
    "age", "job", "marital", "education", "default", "balance",
    "housing", "loan", "contact", "day", "month", "duration",
    "campaign", "pdays", "previous", "poutcome", "y",
]


def conversion_table(frame: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Aggregate at row / contact-record level, not unique-customer level."""
    summary = (
        frame.groupby(group_col, dropna=False)
        .agg(records=("converted", "size"), conversions=("converted", "sum"))
        .reset_index()
    )
    summary["conversion_rate"] = summary["conversions"] / summary["records"]
    return summary.sort_values("records", ascending=False).reset_index(drop=True)


def main() -> None:
    if not INPUT.is_file():
        raise FileNotFoundError(
            f"未找到数据文件：{INPUT}\n"
            "请从 UCI Bank Marketing 页面下载 bank.zip，解压其中的 bank-full.csv，"
            "放进项目的 data 文件夹。注意不是 bank.csv 或 bank-additional-full.csv。"
        )

    # The legacy bank-full.csv uses semicolon as its delimiter.
    # Preserve text tokens such as 'unknown' and empty strings as written.
    df = pd.read_csv(INPUT, sep=";", keep_default_na=False)
    print("=" * 64)
    print("01 | 数据概况")
    print("=" * 64)
    print("数据规模:", df.shape)
    print("前 5 行:\n", df.head().to_string(index=False))
    print("字段类型:\n", df.dtypes.to_string())

    missing_columns = sorted(set(EXPECTED_COLUMNS) - set(df.columns))
    extra_columns = sorted(set(df.columns) - set(EXPECTED_COLUMNS))
    if missing_columns or extra_columns:
        raise ValueError(f"数据集字段不匹配，缺少: {missing_columns}; 多出: {extra_columns}")
    if df.shape[0] != 45211:
        print("警告：预计 bank-full.csv 有 45,211 行；请检查是否误用了抽样版或其他版本。")

    print("\n" + "=" * 64)
    print("02 | 数据质量检查")
    print("=" * 64)
    na_count = df.isna().sum()
    blank_count = df.select_dtypes(include="object").apply(lambda s: s.str.strip().eq("").sum())
    print("NaN 缺失值：\n", na_count.to_string())
    print("文本空字符串：\n", blank_count.to_string())
    print("完全重复的行:", int(df.duplicated().sum()))
    print("注意：数据没有 user_id，不能检查唯一客户数量；不能未经调查直接删除重复行。")
    print("'unknown' 是业务未知类别，不等同于无缺失信息。")
    special_rows = []
    for col in ["job", "education", "contact", "poutcome"]:
        count = int(df[col].astype(str).str.lower().eq("unknown").sum())
        special_rows.append({"field": col, "special_value": "unknown", "rows": count})
        print(f"{col}: unknown = {count:,}")
    n_uncontacted = int((df["pdays"] == -1).sum())
    special_rows.append({"field": "pdays", "special_value": "-1", "rows": n_uncontacted})
    print(f"pdays: -1（以前未联系）= {n_uncontacted:,}")
    pd.DataFrame(special_rows).to_csv(OUTPUT / "01_special_values.csv", index=False, encoding="utf-8-sig")

    invalid = sorted(set(df["y"].astype(str).unique()) - {"yes", "no"})
    if invalid:
        raise ValueError(f"目标字段 y 包含意外取值: {invalid}")
    df["converted"] = df["y"].eq("yes").astype(int)

    print("\n" + "=" * 64)
    print("03 | 总体营销转化率（记录口径）")
    print("=" * 64)
    records = len(df)
    successes = int(df["converted"].sum())
    rate = successes / records
    print(f"记录数: {records:,}")
    print(f"签约记录数: {successes:,}")
    print(f"转化率: {rate:.2%}")
    pd.DataFrame([{"records": records, "conversions": successes, "conversion_rate": rate}]).to_csv(
        OUTPUT / "01_overall_conversion.csv", index=False, encoding="utf-8-sig"
    )

    print("\n" + "=" * 64)
    print("04 | 分群比较（描述性相关，不是因果效果）")
    print("=" * 64)
    for col in ["job", "housing", "loan", "poutcome"]:
        tbl = conversion_table(df, col)
        tbl.to_csv(OUTPUT / f"01_conversion_by_{col}.csv", index=False, encoding="utf-8-sig")
        print(f"\n按 {col} 分组（转化率仅作描述，不代表该变量导致转化）：")
        print(tbl.to_string(index=False, formatters={"conversion_rate": lambda x: f"{x:.2%}"}))

    job_tbl = conversion_table(df, "job").sort_values("conversion_rate", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(job_tbl["job"], job_tbl["conversion_rate"] * 100)
    ax.set_xlabel("Subscription rate (%)")
    ax.set_ylabel("Job category")
    ax.set_title("Bank Marketing | Subscription rate by job (descriptive)")
    fig.tight_layout()
    fig.savefig(OUTPUT / "01_conversion_by_job.png", dpi=150)
    plt.close(fig)

    print("\n" + "=" * 64)
    print("05 | 数据局限和使用规则")
    print("=" * 64)
    print("- 一行是一条营销记录；数据不包含客户唯一 ID，不能据此算独立客户转化率。")
    print("- 没有完整年月日和实验分组；不能仅凭 month 做严格的时间因果分析或 A/B 实验。")
    print("- duration 是联系结束后才知道的通话时长：若预测联系前的转化意愿，必须排除它。")
    print("- 组间转化率差异只是相关性；不应直接解释为营销策略的因果效果。")
    print(f"结果已保存至：{OUTPUT}")


if __name__ == "__main__":
    main()
