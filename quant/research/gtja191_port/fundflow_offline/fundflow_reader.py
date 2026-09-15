"""
fundflow_reader.py — 读取 fetch_fundflow_standalone.py 拉回的资金流历史,供离线因子/回测消费。

【本目录 = 资金流离线层】
  fundflow_offline/
    fetch_fundflow_standalone.py   拉取脚本(在能连东财的网络跑)
    csi1000_symbols.txt            csi1000 成分股清单(拉取脚本自动读)
    fundflow_reader.py             读取端(本机回测用,只读本地 parquet,不联网)
    data_fundflow/                 ← 拉取脚本的输出目录,数据放这里

【用法】
  1) 在能连东财 push2his 的网络:
       python fetch_fundflow_standalone.py --limit 5   # 冒烟:先拉前5只验证通+格式对
       python fetch_fundflow_standalone.py              # 全量 csi1000(断点续传)
  2) 把整个 data_fundflow/ 目录拷回本机 fundflow_offline/ 下
  3) 本机回测:
       from fundflow_reader import load_fundflow, load_panel
       df  = load_fundflow('000012')      # 单票 DataFrame{date, main_pct, ...}
       pan = load_panel(symbols)          # {symbol: df}
数据 schema 见 fetch_fundflow_standalone.py 顶部(存储格式一节)。

设计:接入 factor gate 时(门1 IC → 门2 → 门3 → 门4,见 new-factor-process-checklist),
用 main_pct / main_amt 及各自时序(如 5日/10日累计主力占比)构造截面因子,再走量化系统
verify 框架比对 IC。此处先保证读得进、格式稳定。
"""

from pathlib import Path

import pandas as pd

PORT = Path(__file__).resolve().parent
FF_DIR = PORT / "data_fundflow"

# 主键列 + 数值列(与存储 schema 对齐,严格列序)
COLUMNS = [
    "date", "close", "pct_chg",
    "main_amt", "main_pct",
    "xlarge_amt", "xlarge_pct",
    "large_amt", "large_pct",
    "mid_amt", "mid_pct",
    "small_amt", "small_pct",
]


def load_fundflow(symbol: str) -> pd.DataFrame:
    """读单票资金流,返回升序 date 的唯一主键表。symbol 为 6 位如 '000012'。"""
    p = FF_DIR / f"ff_{symbol}.parquet"
    if not p.exists():
        raise FileNotFoundError(f"缺少资金流缓存: {p} (先用 fetch_fundflow_standalone.py 拉取)")
    df = pd.read_parquet(p)
    # 防御:确保列序/类型稳定
    df = df[[c for c in COLUMNS if c in df.columns]]
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates(subset="date", keep="last")
    return df.reset_index(drop=True)


def load_panel(symbols: list[str]) -> dict[str, pd.DataFrame]:
    """读多票,返回 {symbol: df}。缺失票跳过并返回缺失清单。"""
    panel, missing = {}, []
    for s in symbols:
        try:
            panel[s] = load_fundflow(s)
        except FileNotFoundError:
            missing.append(s)
    if missing:
        print(f"[fundflow] 缺失 {len(missing)}/{len(symbols)} 票, 例: {missing[:10]}")
    return panel


if __name__ == "__main__":
    # 自检:对存在文件读一遍,打印覆盖范围(无文件则提示先跑拉取脚本)
    files = sorted(FF_DIR.glob("ff_*.parquet"))
    print(f"资金流缓存: {len(files)} 票, 目录 {FF_DIR}")
    if not files:
        print("(空 — 先用 fetch_fundflow_standalone.py 在能连东财的网络拉取)")
    else:
        first = files[0].stem[3:]
        df = load_fundflow(first)
        print(f"示例票 {first}: {len(df)} 行, {df['date'].min().date()} → {df['date'].max().date()}")
        print(df.head(3).to_string(index=False))
