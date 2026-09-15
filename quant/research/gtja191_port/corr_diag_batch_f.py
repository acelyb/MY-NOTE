"""批次F 4个显著因子(132/95/70/144)相关性诊断 —— 彼此相关性 + vs quant_system 现有因子。

目的:
1. 132/95/70 均基于 vol*vwap 成交额代理, 确认是否高度相关(冗余→合并取最强一个);
2. 4 因子 vs quant_system 现有因子(low_vol/momentum/reversal/overnight/shadow/liq/price),
   检测是否已被覆盖或为流动性/规模效应伪装。

口径同 corr_diag_v3: 跨采样时点算截面 Spearman 取均值。
  |corr|>0.5 高相关(疑似变体); >0.3 中相关; <=0.3 低相关独立。
加载: GTJA 批次F 因子需 vwap → load_batch_daily_with_vwap_index;
      quant_system 现有因子需 OHLCV → 同一 df 也含这些列, 可共用。
只读 quant_system 缓存 + 只读 import, 不改源码。
"""
from __future__ import annotations
import sys
from pathlib import Path
from multiprocessing import Pool

PORT_DIR = Path("/home/cambricon/Documents/code/survey/gtja191_port")
sys.path.insert(0, str(PORT_DIR))
QUANT_ROOT = PORT_DIR.parents[1] / "quant_system"

import numpy as np
import pandas as pd
import importlib.util
import warnings; warnings.filterwarnings("ignore")
from scipy.stats import spearmanr

from cache_reader import load_constituents, load_batch_daily_with_vwap_index

# ---- GTJA 批次F 因子: importlib 显式加载(规避与 quant_system factors 包名冲突) ----
def _load(modname, relpath):
    p = PORT_DIR / relpath
    spec = importlib.util.spec_from_file_location(modname, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod

_load("gtja_base", "base.py")
SIG_F = [75]
def _load_alpha(n):
    return _load(f"gtja_alpha{n}", f"factors/alpha{n}.py")
GTJA = {f"alpha{n}": getattr(_load_alpha(n), f"Alpha{n}Factor")() for n in SIG_F}

# ---- quant_system 现有因子: 临时前置 QUANT_ROOT, 清 factors 缓存 ----
def _load_qs(modname, relpath):
    sys.path.insert(0, str(QUANT_ROOT))
    for k in list(sys.modules):
        if k == "factors" or k.startswith("factors."):
            sys.modules.pop(k, None)
    spec = importlib.util.spec_from_file_location(modname, QUANT_ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod

_load_qs("qs_base", "factors/base.py")
LowVolFactor = _load_qs("qs_low_vol", "factors/low_vol.py").LowVolFactor
MomentumFactor = _load_qs("qs_momentum", "factors/momentum.py").MomentumFactor
ReversalFactor = _load_qs("qs_reversal", "factors/reversal.py").ReversalFactor
OvernightReversalFactor = _load_qs("qs_overnight", "factors/overnight_reversal.py").OvernightReversalFactor
_usd = _load_qs("qs_shadow", "factors/shadow_daily.py")
UpperShadowDailyFactor = _usd.UpperShadowDailyFactor
LowerShadowDailyFactor = _usd.LowerShadowDailyFactor
WilliamsUpperShadowFactor = _usd.WilliamsUpperShadowFactor
WilliamsLowerShadowFactor = _usd.WilliamsLowerShadowFactor

class LiquidityProxy:
    name = "liq_proxy"
    def calc_value(self, df):
        if len(df) < 20: return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        tp = (high + low + close) / 3
        return float((tp * vol).rolling(20).mean().iloc[-1])

class PriceScaleProxy:
    name = "price_proxy"
    def calc_value(self, df):
        if len(df) < 20: return None
        return float(df["close"].rolling(20).mean().iloc[-1])

class AmountProxy:
    """vol*vwap 20日均, 与 alpha132 同口径, 验证 alpha132 是否=成交额规模代理。"""
    name = "amt_proxy_20"
    def calc_value(self, df):
        if len(df) < 20: return None
        if "vwap" not in df.columns: return None
        amt = df["volume"] * df["vwap"]
        return float(amt.rolling(20).mean().iloc[-1])

EXISTING = {
    "low_vol": LowVolFactor(),
    "momentum": MomentumFactor(),
    "reversal": ReversalFactor(),
    "overnight_rev": OvernightReversalFactor(),
    "upper_shadow": UpperShadowDailyFactor(),
    "lower_shadow": LowerShadowDailyFactor(),
    "williams_upper": WilliamsUpperShadowFactor(),
    "williams_lower": WilliamsLowerShadowFactor(),
    "liq_proxy": LiquidityProxy(),
    "price_proxy": PriceScaleProxy(),
    "amt_proxy_20": AmountProxy(),
}
EXIST_NAMES = list(EXISTING)

_SYM_DATA=None; _DATES=None; _EXIST_CS=None
def _cs_one_factor(args):
    label, fac = args
    out = {}
    for date in _DATES:
        vals = {}
        for s, d in _SYM_DATA.items():
            pos = int(np.searchsorted(d.index.values, np.datetime64(date)))
            if pos >= len(d) or d.index[pos] != date: continue
            try:
                v = fac.calc_value(d.iloc[:pos+1])
            except Exception:
                v = None
            if v is not None and not (isinstance(v,float) and np.isnan(v)):
                vals[s] = v
        out[date] = pd.Series(vals)
    return (label, out)

def main():
    global _SYM_DATA, _DATES, _EXIST_CS
    syms = load_constituents("csi1000")
    print(f"csi1000: {len(syms)} 只, 读缓存+合并VWAP(1× I/O)...", flush=True)
    pdfs = load_batch_daily_with_vwap_index(syms)
    _SYM_DATA = {s: df.set_index("date") for s,df in pdfs.items() if not df.empty}
    all_dates = sorted(set().union(*[set(d.index) for d in _SYM_DATA.values()]))
    _DATES = all_dates[:-21:21]
    print(f"采样 {len(_DATES)} 个时点", flush=True)

    print(f"\n[1/2] 算 {len(EXISTING)} 个现有/代理因子基线截面(串行)...", flush=True)
    _EXIST_CS = {}
    for name, fac in EXISTING.items():
        _, cs = _cs_one_factor((name, fac))
        _EXIST_CS[name] = cs

    print(f"[2/2] fork+COW 并行算 {len(GTJA)} 个批次F显著因子截面...", flush=True)
    with Pool(6) as pool:
        gtja_cs = dict(pool.map(_cs_one_factor, list(GTJA.items()), chunksize=1))

    # ---- (A) 4 因子彼此相关性 ----
    print("\n=== (A) 批次F显著因子彼此相关性(跨时点平均 Spearman) ===", flush=True)
    gnames = list(GTJA)
    print(f"{'':<10}" + "".join(f"{n:>12}" for n in gnames), flush=True)
    for a in gnames:
        row = []
        for b in gnames:
            cs = []
            for date in _DATES:
                ga, gb = gtja_cs[a].get(date), gtja_cs[b].get(date)
                if ga is None or gb is None: continue
                common = ga.index.intersection(gb.index)
                if len(common) < 10: continue
                c,_ = spearmanr(ga.loc[common], gb.loc[common])
                if not np.isnan(c): cs.append(c)
            row.append(np.mean(cs) if cs else np.nan)
        print(f"{a:<10}" + "".join(f"{v:>12.3f}" for v in row), flush=True)

    # ---- (B) vs 现有因子 ----
    print(f"\n=== (B) 批次F显著因子 vs quant_system 现有因子(跨时点平均 Spearman) ===", flush=True)
    print(f"{'因子':<10}" + "".join(f"{n:>14}" for n in EXIST_NAMES) + "  判定", flush=True)
    print("-"*170, flush=True)
    rows = []
    for gname in gnames:
        gcs = gtja_cs[gname]
        corrs = {n: [] for n in EXIST_NAMES}
        for date in _DATES:
            g = gcs.get(date)
            if g is None or len(g) < 10: continue
            for n in EXIST_NAMES:
                e = _EXIST_CS[n].get(date)
                if e is None or len(e) < 10: continue
                common = g.index.intersection(e.index)
                if len(common) < 10: continue
                c,_ = spearmanr(g.loc[common], e.loc[common])
                if not np.isnan(c): corrs[n].append(c)
        mean = {n: (np.mean(v) if v else np.nan) for n,v in corrs.items()}
        absmax = max((abs(v) for v in mean.values() if not np.isnan(v)), default=0)
        partner = max(mean, key=lambda n: abs(mean[n]) if not np.isnan(mean[n]) else -1)
        cval = mean[partner]
        if absmax > 0.5: tag = f"高相关·{partner}变体"
        elif absmax > 0.3: tag = f"中相关·{partner}重叠"
        else: tag = "低相关·独立新维度"
        print(f"{gname:<10}" + "".join(f"{mean[n]:>+14.3f}" for n in EXIST_NAMES) + f"  {tag}(max|{absmax:.2f}|@{partner}{cval:+.2f})", flush=True)
        rows.append((gname, mean, absmax, partner, cval, tag))

    indep = [r for r in rows if r[5].startswith("低相关")]
    print(f"\n=== 低相关·独立新维度(|corr|<=0.3) 共 {len(indep)} 个 ===", flush=True)
    for gname, mean, absmax, partner, cval, tag in indep:
        print(f"  {gname:<10} max|corr|={absmax:.3f}@{partner}", flush=True)

if __name__=="__main__": main()
