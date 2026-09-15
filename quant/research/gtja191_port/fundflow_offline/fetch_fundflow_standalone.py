"""
fetch_fundflow_standalone.py — 主力资金流历史全量拉取(自包含,可在任意能连东财的网络独立跑)

背景
----
本机网络访问 东财 push2his/fflow/daykline 稳定 HTTP 000 断连(见 memory: fund-flow-daily-history-unavailable)。
此脚本是给你拿到"能连东财的网络"上运行的。跑通后把 data_fundflow/ 目录整个给我,我读 parquet
直接回测(接 factor gate:门1 IC → 门2 相关 → 门3 正交 → 门4 组合 A/B,见 new-factor-process-checklist)。

接口(已核实 akshare 1.18.94 源码)
---------------------------------
ak.stock_individual_fund_flow(stock='000012', market='sz')
  - 本质: GET push2his.eastmoney.com/api/qt/stock/fflow/daykline/get
    params lmt=0 拉全历史日频面板(每票一请求,返回当票全部历史交易日的资金流)
  - market 映射: sh→1, sz→0, bj→0 (符号决定 secid 首位)
  - 返回(akshare 清理后 13 列):
      日期 / 收盘价 / 涨跌幅(%) /
      主力净流入-净额 / 主力净流入-净占比(%) /
      超大单净流入-净额 / 超大单净流入-净占比(%) /
      大单净流入-净额 / 大单净流入-净占比(%) /
      中单净流入-净额 / 中单净流入-净占比(%) /
      小单净流入-净额 / 小单净流入-净占比(%)
    (主力 = 超大单 + 大单; 各单净额单位 = 元, 占比单位 = %)

存储格式(单票一 parquet, schema 见下)
--------------------------------------
目录: <脚本同目录>/data_fundflow/
文件: ff_{symbol}.parquet  (symbol 为 6 位不带前缀,如 000012)
列:   date        datetime64[ns]  (交易日,升序)
      close       float64         收盘价(元)
      pct_chg     float64         涨跌幅(%)
      main_amt    float64         主力净流入-净额(元)
      main_pct    float64         主力净流入-净占比(%)
      xlarge_amt  float64         超大单净流入-净额(元)
      xlarge_pct  float64         超大单净流入-净占比(%)
      large_amt   float64         大单净流入-净额(元)
      large_pct   float64         大单净流入-净占比(%)
      mid_amt     float64         中单净流入-净额(元)
      mid_pct     float64         中单净流入-净占比(%)
      small_amt   float64         小单净流入-净额(元)
      small_pct   float64         小单净流入-净占比(%)
主键: date (唯一)

断点续传/防封(与 sync_amount.py 同款语义)
------------------------------------------
- 已有缓存文件的票自动跳过(可中途中断重跑续传)
- 单线程串行 + THROTTLE=0.3s/票 + BAN_MARKERS 识别封禁 + BAN_PAUSE=60s 整体暂停
- 原子写(tempfile + os.replace),崩溃不损坏已有文件

用法
----
【本目录 fundflow_offline/ = 资金流离线层】
  fetch_fundflow_standalone.py   拉取脚本(在能连东财的网络跑)
  csi1000_symbols.txt            csi1000 成分股清单(脚本自动读)
  fundflow_reader.py             读取端(本机回测用,读 data_fundflow/ 下 parquet,不联网)
  data_fundflow/                 ← 本脚本输出目录(全量拉完整个目录拷回本机)

  # 冒烟:在能连东财的网络先拉前 5 只,验证网络通 + 存储格式对
  python fetch_fundflow_standalone.py --limit 5

  # 全量 csi1000(断点续传,中断后重跑接着拉)
  python fetch_fundflow_standalone.py

  # 拉完把整个 data_fundflow/ 拷回本机 fundflow_offline/ 下,本机用 fundflow_reader.py 回测

若你网络也没拉通,会打印类似 "BAN" / fail 累计 → 说明连不上,不落任何半残文件(原子写兜底)。
"""

import argparse
import os
import sys
import time
from pathlib import Path

import pandas as pd

# ---------- 可调参数 ----------
THROTTLE = 0.3        # 每只请求间隔秒(防被限流)
BAN_PAUSE = 60        # 疑似封禁整体暂停秒
BAN_MARKERS = (
    "429", "too many", "请求过于频繁", "Blocked",
    "forbidden", "Your Connection", "Connection aborted",
    "RemoteDisconnected",
)
PORT = Path(__file__).resolve().parent
FF_DIR = PORT / "data_fundflow"          # <- 存储目录,跑通后整体拷给我
SYMS_FILE = PORT / "csi1000_symbols.txt"  # <- 成分股清单(已生成)

try:
    import akshare as ak
except Exception as e:  # pragma: no cover - 环境缺 akshare 时给明确指引
    sys.exit(f"需要 akshare: {e}\npip install akshare==1.18.94")


def _market_of(sym: str) -> str:
    """6开头→sh; 4/8/9开头→bj; 0/3开头→sz。与东财 secid 首位对齐。"""
    if sym.startswith("6"):
        return "sh"
    if sym[0] in ("4", "8", "9"):
        return "bj"
    return "sz"


def _atomic_write(path: Path, df: pd.DataFrame) -> None:
    """临时文件 + os.replace 原子落盘,崩溃不损坏已存在文件。"""
    tmp = path.with_suffix(".parquet.tmp")
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


def _fetch_one(sym: str) -> tuple[bool, pd.DataFrame | None, str]:
    """拉单票全历史。返回 (ok, df, msg)。df 已是英文列 schema。"""
    market = _market_of(sym)
    try:
        raw = ak.stock_individual_fund_flow(stock=sym, market=market)
    except Exception as e:
        msg = str(e)
        if any(m in msg for m in BAN_MARKERS):
            return False, None, "BAN:" + msg
        return False, None, f"ERR:{msg}"

    if raw is None or raw.empty:
        return True, None, "empty"

    df = raw.rename(columns={
        "日期": "date",
        "收盘价": "close",
        "涨跌幅": "pct_chg",
        "主力净流入-净额": "main_amt",
        "主力净流入-净占比": "main_pct",
        "超大单净流入-净额": "xlarge_amt",
        "超大单净流入-净占比": "xlarge_pct",
        "大单净流入-净额": "large_amt",
        "大单净流入-净占比": "large_pct",
        "中单净流入-净额": "mid_amt",
        "中单净流入-净占比": "mid_pct",
        "小单净流入-净额": "small_amt",
        "小单净流入-净占比": "small_pct",
    })
    df["date"] = pd.to_datetime(df["date"])
    for c in df.columns:
        if c != "date":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[["date", "close", "pct_chg",
             "main_amt", "main_pct",
             "xlarge_amt", "xlarge_pct",
             "large_amt", "large_pct",
             "mid_amt", "mid_pct",
             "small_amt", "small_pct"]]
    df = df.sort_values("date").reset_index(drop=True)
    df = df.drop_duplicates(subset="date", keep="last").reset_index(drop=True)
    return True, df, "ok"


def _cache_file(sym: str) -> Path:
    return FF_DIR / f"ff_{sym}.parquet"


def main() -> None:
    ap = argparse.ArgumentParser(description="拉取主力资金流全历史(东财 daykline)")
    ap.add_argument("--limit", type=int, default=0, help="只拉前 N 只(冒烟),0=全量")
    ap.add_argument("--force", action="store_true", help="忽略已有缓存重拉")
    ap.add_argument("--outdir", type=str, default=str(FF_DIR), help="存储目录")
    args = ap.parse_args()

    FF_DIR.mkdir(parents=True, exist_ok=True)

    syms = [s.strip() for s in open(SYMS_FILE) if s.strip()]
    if not syms:
        sys.exit(f"成分股清单为空: {SYMS_FILE}")

    if args.limit > 0:
        syms = syms[: args.limit]

    # 断点续传:跳过已有缓存
    todo = [
        s for s in syms
        if args.force or not _cache_file(s).exists()
    ]
    skipped = len(syms) - len(todo)
    print(f"[init] 共 {len(syms)} 只, 已有缓存跳过 {skipped}, 待拉 {len(todo)}", flush=True)

    ban_until = 0.0
    ok = fresh = fail = 0
    t0 = time.time()
    for i, sym in enumerate(todo, 1):
        if time.time() < ban_until:
            time.sleep(ban_until - time.time())
        good, df, msg = _fetch_one(sym)
        if good and df is not None and not df.empty:
            _atomic_write(_cache_file(sym), df)
            ok += 1
            m = "ok"
        elif good:
            fresh += 1
            m = "empty"
        elif msg.startswith("BAN"):
            ban_until = time.time() + BAN_PAUSE
            fail += 1
            m = "BAN(pause60s)"
        else:
            fail += 1
            m = msg
        if i % 50 == 0 or m != "ok":
            print(f"  [{i}/{len(todo)}] {sym} {m}  "
                  f"(ok={ok} empty={fresh} fail={fail} 用时{time.time()-t0:.0f}s)",
                  flush=True)

    print(f"[done] ok={ok} empty={fresh} fail={fail} 总用时{time.time()-t0:.0f}s", flush=True)
    print(f"[done] 输出目录: {FF_DIR}", flush=True)


if __name__ == "__main__":
    main()
