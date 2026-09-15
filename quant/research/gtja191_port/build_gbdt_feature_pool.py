"""GBDT 候选特征池构建器 —— 把 survey 候选因子算成截面特征面板,备 LightGBM 离线试。

为什么要这个文件(任务 C,见 量化工程调研.md §5.1 落地顺序第3步):
  用户正在跑 LightGBM 基线。若基线 vs 线性 ICIR 差距小 → 说明现有因子信息量饱和,
  需补特征。此时不能临时算(算一遍要几分钟),故现在把候选池备好存盘,差距小即取用。

  候选池两类(均来自 GTJA191 survey,未进 quant_system config,故不能走 live ML 路径):
    A. 独立新维度候选(alpha5/42/99/136/143/176):survey IC 实测显著且与现有因子正交。
    B. 降级"同族冗余"因子(alpha2/40/52/69/84):线性下因 corr>0.6 同源被降级,但 GBDT
       不怕冗余、可作交互特征重评(线性下的垃圾,树里可能免费增量,见 §5.1)。

口径对齐(逐字复刻 quant_system/backtest/walk_forward.py:_train_ml_model):
  - 日期轴 = 所有股票日期并集;采样 freq=5 天(去自相关,同 calc_factor_ic)。
  - 标签 = _future_return(close, t, horizon) = close[t+h]/close[t]-1,horizon=10(config 默认)。
  - 特征 = 各因子截面值(原始值,NaN 不预填——LightGBM 原生吃 NaN;live 侧在
    _build_feature_matrix 做 NaN→列均值填,这里存原始值留最大灵活,喂模型时再填)。
  - per-symbol 计算 = survey calc_value(d.iloc[:pos+1]) ≡ live calc_cross_section 的逐标的口径。

性能(关键):naive 逐采样日×逐股票 calc_value 是 O(n^2)/股票(321采样日×1000股≈4min/因子单进程)。
  本构建器用 series_fn 一次算整列 rolling 序列再按日期取值——O(n)/股票,理论快 ~321×。
  已实测 alpha5 全列 vs 逐日 mismatch=0(rolling 不依赖未来,iloc[:pos+1]末位 == 全列第pos位)。
  11 因子全量 ~1-2min 单进程完成,无 I/O 压力,守"慢慢来"约束。

输出: data_gbdt/feature_pool.parquet,长表 (date, symbol, <11因子列>, fwd_ret)。
  只读 quant_system 缓存,输出独立目录,绝不写 quant_system。供离线 walk-forward GBDT 试用。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PORT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PORT_DIR))

from cache_reader import load_constituents, load_batch_daily
from base import ts_corr  # 研报算子,供 series_fn 复用

# ---- ML 口径参数(对齐 config.yaml walk_forward.ml + run_walk_forward 默认) ----
HORIZON = 10   # 标签持有期(config --horizon 默认 10)
FREQ = 5       # 采样频率(去自相关,ml.freq=5)
UNIVERSE = "csi1000"

# ---- 候选因子: series_fn 复刻各 alpha calc 的内部 rolling 序列,返回整列(不取 iloc[-1]) ----
# 每个 series_fn(df) 输入单只股票日线(已含 date 列或已 set_index),返回 pd.Series(同 df 行数)。
# 已对照各 factors/alphaN.py 的 calc 逻辑逐字复刻,仅末步不取末位而返全列。
# 注:NaN 保留(数据不足段为 NaN),喂模型时再按列均值填。


def _s_alpha5(d):
    # -1 * TSMAX(CORR(TSRANK(VOL,5), TSRANK(HIGH,5), 5), 3)
    rv = d["volume"].rolling(5).rank(pct=True)
    rh = d["high"].rolling(5).rank(pct=True)
    return -(rv.rolling(5).corr(rh)).rolling(3).max()


def _s_alpha42(d):
    # -1 * RANK(STD(HIGH,10)) * CORR(HIGH, VOL, 10)  —— 逐字复刻 alpha42.py calc
    high, vol = d["high"], d["volume"]
    std10 = high.rolling(10).std()
    r = std10.rolling(10).rank(pct=True)
    corr10 = high.rolling(10).corr(vol)
    return -r * corr10


def _s_alpha99(d):
    # -1 * COV(RANK(CLOSE,5), RANK(VOL,5), 5)
    rc = d["close"].rolling(5).rank(pct=True)
    rv = d["volume"].rolling(5).rank(pct=True)
    return -(rc.rolling(5).cov(rv))


def _s_alpha136(d):
    # -1 * RANK(DELTA(RET,3)) * CORR(OPEN,VOL,10)
    r = d["close"].pct_change()
    dret3 = r - r.shift(3)
    r_rank = dret3.rolling(10, min_periods=1).rank(pct=True)
    corr_ov = ts_corr(d["open"], d["volume"], 10)
    return -r_rank * corr_ov


def _s_alpha143(d):
    # 自递归: Y_0=1.0; 涨(r_t>1) → Y_t=(r_t-1)*Y_{t-1}; 跌/平 → Y_t=Y_{t-1}(冻结)
    # 逐字复刻 alpha143.py calc(含递归,逐行循环;但每股票只跑1次,仍 O(n))。
    close = d["close"]
    r = close / close.shift(1)  # r_t = close_t/close_{t-1}
    n = len(d)
    y_arr = np.full(n, np.nan)
    if n == 0:
        return pd.Series(y_arr, index=d.index)
    y = 1.0
    y_arr[0] = y
    for t in range(1, n):
        rv = r.iloc[t]
        if pd.isna(rv):
            y_arr[t] = y
            continue
        if rv > 1:
            y = (rv - 1) * y
        y_arr[t] = y
    return pd.Series(y_arr, index=d.index)


def _s_alpha176(d):
    # CORR(RANK(收盘在12日(HIGH,LOW)区间位置), RANK(VOL), 6)  —— 逐字复刻 alpha176.py calc
    close, high, low, vol = d["close"], d["high"], d["low"], d["volume"]
    lo12 = low.rolling(12).min()
    hi12 = high.rolling(12).max()
    rng = (hi12 - lo12).replace(0, np.nan)
    pos = (close - lo12) / rng
    r1 = pos.rolling(6).rank(pct=True)
    r2 = vol.rolling(6).rank(pct=True)
    return r1.rolling(6).corr(r2)


def _s_alpha52(d):
    # 昨日典型价多空力道比×100  —— 逐字复刻 alpha52.py calc
    close, high, low = d["close"], d["high"], d["low"]
    tp = (high + low + close) / 3
    tp1 = tp.shift(1)
    up = (high - tp1).clip(lower=0)       # 多头力
    dn = (tp1 - low).clip(lower=0)        # 空头力
    sup = up.rolling(26).sum()
    sdn = dn.rolling(26).sum().replace(0, np.nan)
    return sup / sdn * 100


def _s_alpha69(d):
    # 开盘缺口方向多空力量比(20日)  —— 逐字复刻 alpha69.py calc
    op, high, low = d["open"], d["high"], d["low"]
    o1 = op.shift(1)
    dtm = pd.Series(
        np.where((op <= o1).values, 0.0, np.maximum((high - op).values, (op - o1).values)),
        index=op.index,
    )
    dbm = pd.Series(
        np.where((op >= o1).values, 0.0, np.maximum((op - low).values, (o1 - op).values)),
        index=op.index,
    )
    sdtm = dtm.rolling(20).sum()
    sdbm = dbm.rolling(20).sum()
    diff = sdtm - sdbm
    denom = pd.Series(
        np.where((sdtm > sdbm).values, sdtm.values,
                 np.where((sdtm == sdbm).values, 1.0, sdbm.values)),
        index=op.index,
    )
    denom = denom.replace(0, np.nan)
    return diff / denom


def _s_alpha40(d):
    # 26日上涨/下跌量比×100  —— 逐字复刻 alpha40.py calc
    close, vol = d["close"], d["volume"]
    prev = close.shift(1)
    up = pd.Series(pd.to_numeric((close > prev), errors="coerce"), index=close.index) * vol
    dn = pd.Series(pd.to_numeric((close <= prev), errors="coerce"), index=close.index) * vol
    up_sum = up.rolling(26).sum()
    dn_sum = dn.rolling(26).sum()
    denom = dn_sum.replace(0, pd.NA)
    return up_sum / denom * 100


def _s_alpha84(d):
    # 20日带符号量累积(OBV类)。见 factors/alpha84.py calc 复刻。
    ret = d["close"].pct_change()
    signed = d["volume"].where(ret > 0, -d["volume"]).where(ret != 0, 0)
    return signed.rolling(20).sum()


def _s_alpha2(d):
    # 收盘日内位置一阶差分·取负  —— 逐字复刻 alpha2.py calc
    close, high, low = d["close"], d["high"], d["low"]
    denom = (high - low).replace(0, pd.NA)
    tmp = ((close - low) - (high - close)) / denom
    delta = tmp - tmp.shift(1)
    return -delta


# 因子注册表:(name, series_fn, 类别) —— 类别仅元信息,输出里不区分
CANDIDATES = [
    ("gtja_alpha5", _s_alpha5, "indep"),
    ("gtja_alpha42", _s_alpha42, "indep"),
    ("gtja_alpha99", _s_alpha99, "indep"),
    ("gtja_alpha136", _s_alpha136, "indep"),
    ("gtja_alpha143", _s_alpha143, "indep"),
    ("gtja_alpha176", _s_alpha176, "indep"),
    ("gtja_alpha2", _s_alpha2, "redundant"),
    ("gtja_alpha40", _s_alpha40, "redundant"),
    ("gtja_alpha52", _s_alpha52, "redundant"),
    ("gtja_alpha69", _s_alpha69, "redundant"),
    ("gtja_alpha84", _s_alpha84, "redundant"),
]


def _future_return(closes: pd.Series, idx: int, n: int) -> float | None:
    """idx 位置未来 n 日收益(复刻 ic._future_return)。"""
    if idx + n >= len(closes):
        return None
    c0, c1 = closes.iloc[idx], closes.iloc[idx + n]
    if c0 <= 0:
        return None
    return c1 / c0 - 1


def build():
    out_dir = PORT_DIR / "data_gbdt"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "feature_pool.parquet"

    syms = load_constituents(UNIVERSE)
    print(f"{UNIVERSE}: {len(syms)} 只成分股,只读 quant_system 缓存(1× I/O,不拉网)...", flush=True)
    pdfs = load_batch_daily(syms)
    print(f"缓存命中: {len(pdfs)}/{len(syms)}", flush=True)

    # set_index 一次(后续 series_fn 直接用)
    sym_data = {s: df.set_index("date") for s, df in pdfs.items() if not df.empty}
    all_dates = sorted(set().union(*[set(d.index) for d in sym_data.values()]))
    n_dates = len(all_dates)
    print(f"日期范围: {all_dates[0].date()} ~ {all_dates[-1].date()} ({n_dates} 个交易日)", flush=True)

    # 采样网格(对齐 _train_ml_model: range(0, len(all_dates)-horizon, freq))
    sample_idx = list(range(0, n_dates - HORIZON, FREQ))
    sample_dates = [all_dates[i] for i in sample_idx]
    print(f"采样: freq={FREQ}, horizon={HORIZON} → {len(sample_dates)} 个采样日", flush=True)
    print(f"候选因子: {len(CANDIDATES)} 个 "
          f"({sum(1 for _,_,c in CANDIDATES if c=='indep')} 独立新维度 + "
          f"{sum(1 for _,_,c in CANDIDATES if c=='redundant')} 降级冗余)", flush=True)
    print("-" * 70, flush=True)

    # 每只股票每因子算一次全列 series(O(n)/股票),按采样日取值 + 未来收益标签
    factor_names = [c[0] for c in CANDIDATES]
    rows = []  # 每行: (date, symbol, *11因子, fwd_ret)
    t0 = time.time()
    n_sym_done = 0
    for sym, d in sym_data.items():
        closes = d["close"]
        idx_arr = d.index.values
        # 该股票在各采样日的位置(存在则可取值): 预建采样日→位置映射,避免内层重复 searchsorted
        pos_map = {}
        for date in sample_dates:
            pos = int(np.searchsorted(idx_arr, np.datetime64(date)))
            if pos < len(d) and d.index[pos] == date:
                pos_map[date] = pos

        # 各因子全列 series(每股票每因子算1次)
        series_cache = {}
        for fname, sfn, _ in CANDIDATES:
            try:
                series_cache[fname] = sfn(d)
            except Exception:
                series_cache[fname] = pd.Series(np.nan, index=d.index)

        # 按存在的采样日组装行
        sym_rows = []
        for date, pos in pos_map.items():
            fr = _future_return(closes, pos, HORIZON)
            if fr is None or np.isnan(fr):
                continue
            row = {"date": date, "symbol": sym}
            for fname, _, _ in CANDIDATES:
                s = series_cache[fname]
                v = s.iloc[pos] if pos < len(s) else np.nan
                row[fname] = float(v) if not pd.isna(v) else np.nan
            row["fwd_ret"] = float(fr)
            sym_rows.append(row)
        rows.extend(sym_rows)
        n_sym_done += 1
        if n_sym_done % 100 == 0:
            el = time.time() - t0
            print(f"  已处理 {n_sym_done}/{len(sym_data)} 只,累计 {len(rows)} 行,耗时 {el:.0f}s", flush=True)

    el = time.time() - t0
    print("-" * 70, flush=True)
    print(f"完成: {len(sym_data)} 只股票, {len(rows)} 行样本, 耗时 {el:.0f}s", flush=True)

    df = pd.DataFrame(rows)
    df = df.sort_values(["date", "symbol"]).reset_index(drop=True)

    # 列序: date, symbol, *因子, fwd_ret
    df = df[["date", "symbol"] + factor_names + ["fwd_ret"]]
    df.to_parquet(out_path, index=False)

    # 摘要
    n_dates_actual = df["date"].nunique()
    print(f"\n写出: {out_path}", flush=True)
    print(f"  样本数: {len(df)}  |  采样日: {n_dates_actual}  |  股票数: {df['symbol'].nunique()}", flush=True)
    print(f"  日期范围: {df['date'].min().date()} ~ {df['date'].max().date()}", flush=True)
    print(f"  因子列({len(factor_names)}): {', '.join(factor_names)}", flush=True)
    print(f"  标签: fwd_ret (horizon={HORIZON}日未来收益)", flush=True)
    print(f"\n各因子非空率(截面覆盖率,数据不足段为 NaN):", flush=True)
    for f in factor_names:
        nn = df[f].notna().mean()
        print(f"    {f:<16} {nn:>6.1%}", flush=True)
    print(f"\n用法: 离线 walk-forward GBDT 试,按 date 切训练/测试窗,特征=因子列,标签=fwd_ret。", flush=True)
    print(f"      NaN 喂 LightGBM 原生支持;若走 live _build_feature_matrix 口径则按列均值填。", flush=True)
    print(f"      独立新维度({[c[0] for c in CANDIDATES if c[2]=='indep']})优先加;", flush=True)
    print(f"      降级冗余({[c[0] for c in CANDIDATES if c[2]=='redundant']})作交互特征重评(线性下垃圾,树里可能免费)。", flush=True)


if __name__ == "__main__":
    build()
