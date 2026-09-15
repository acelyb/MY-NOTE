"""相关性诊断 v3 —— 41 个本批新显著因子 vs quant_system 现有因子 + liq/price 代理。

并行版(fork+COW): 父进程 1× 载缓存 → 阶段1 串行算现有因子基线截面(10个,跨时点) →
阶段2 fork+COW 并行按因子算 41 个 GTJA 因子截面, 各自与基线算 Spearman。
缓存 I/O 仍 1×(父进程单次载入, 子进程 COW 继承)。

判定口径与 v2 一致:
  |corr|>0.5 高相关(疑似变体, 若IC更强=可替代)
  |corr|>0.3 中相关(部分重叠)
  |corr|<=0.3 低相关(独立新维度)
另查 liq/price 代理, 检测规模/流动性效应伪装(alpha150 教训)。

只读 quant_system 缓存 + 只读 import 因子定义, 不改源码。
"""
from __future__ import annotations
import sys
from pathlib import Path
from multiprocessing import Pool

PORT_DIR = Path("/home/cambricon/Documents/code/survey/gtja191_port")
sys.path.insert(0, str(PORT_DIR))
QUANT_ROOT = PORT_DIR.parents[1] / "quant_system"
sys.path.insert(0, str(QUANT_ROOT))

import numpy as np
import pandas as pd
import importlib.util
import warnings; warnings.filterwarnings("ignore")

from cache_reader import load_constituents, load_batch_daily

# ---- GTJA 因子: importlib 显式加载, 规避与 quant_system factors 包名冲突 ----
sys.path.insert(0, str(PORT_DIR))

def _load(modname, relpath):
    p = PORT_DIR / relpath
    spec = importlib.util.spec_from_file_location(modname, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod

_load("gtja_base", "base.py")  # alpha 模块 from base import ... 需 base 在 path 首

def _load_alpha(n):
    return _load(f"gtja_alpha{n}", f"factors/alpha{n}.py")

NEW_SIG = [187,175,161,159,189,129,174,160,153,173,93,126,97,100,81,122,151,
           88,94,118,106,55,67,59,116,147,110,134,165,71,169,79,152,58,109,
           56,98,133,136,139,164]
GTJA = {f"alpha{n}": getattr(_load_alpha(n), f"Alpha{n}Factor")() for n in NEW_SIG}

# ---- quant_system 真实因子: importlib 显式加载, 临时前置 QUANT_ROOT ----
def _load_qs(modname, relpath):
    p = QUANT_ROOT / relpath
    sys.path.insert(0, str(QUANT_ROOT))
    for k in list(sys.modules):
        if k == "factors" or k.startswith("factors."):
            sys.modules.pop(k, None)
    spec = importlib.util.spec_from_file_location(modname, p)
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
}
EXIST_NAMES = list(EXISTING)

# ---- 全局: 父进程载入后子进程 COW 继承 ----
_SYM_DATA=None; _DATES=None; _EXIST_CS=None

def _cs_one_factor(args):
    """单因子跨所有采样时点的截面值: 返回 {date: {sym: val}}"""
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
    print(f"csi1000: {len(syms)} 只, 读缓存(1× I/O)...", flush=True)
    pdfs = load_batch_daily(syms)
    _SYM_DATA = {s: df.set_index("date") for s,df in pdfs.items() if not df.empty}
    all_dates = sorted(set().union(*[set(d.index) for d in _SYM_DATA.values()]))
    _DATES = all_dates[:-21:21]
    print(f"采样 {len(_DATES)} 个时点", flush=True)

    # 阶段1: 现有因子基线截面(串行, 10个因子×N时点, 量小)
    print(f"\n[1/2] 算 {len(EXISTING)} 个现有因子基线截面...", flush=True)
    _EXIST_CS = {}
    for name, fac in EXISTING.items():
        _, cs = _cs_one_factor((name, fac))
        _EXIST_CS[name] = cs

    # 阶段2: GTJA 新因子并行(fork+COW)
    print(f"[2/2] fork+COW 并行算 {len(GTJA)} 个新因子截面 vs 基线...", flush=True)
    with Pool(8) as pool:
        gtja_cs = dict(pool.map(_cs_one_factor, list(GTJA.items()), chunksize=1))

    # 汇总: 每个新因子在每个时点, 与每个现有因子算 Spearman, 跨时点取均值
    print("\n=== 新显著因子 vs 现有因子(跨时点平均 Spearman |corr|) ===", flush=True)
    print(f"{'因子':<10}" + "".join(f"{n:>14}" for n in EXIST_NAMES) + "  判定", flush=True)
    print("-"*150, flush=True)
    rows = []
    for gname in GTJA:
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
                c,_ = __import__("scipy.stats",fromlist=["spearmanr"]).spearmanr(g.loc[common], e.loc[common])
                if not np.isnan(c): corrs[n].append(c)
        mean = {n: (np.mean(v) if v else np.nan) for n,v in corrs.items()}
        absmax = max((abs(v) for v in mean.values() if not np.isnan(v)), default=0)
        partner = min(mean, key=lambda n: abs(mean[n]) if not np.isnan(mean[n]) else 9) if any(not np.isnan(v) for v in mean.values()) else "NA"
        # 最大 |corr| 的 partner
        partner = max(mean, key=lambda n: abs(mean[n]) if not np.isnan(mean[n]) else -1)
        cval = mean[partner]
        if absmax > 0.5:
            tag = f"高相关·{partner}变体"
        elif absmax > 0.3:
            tag = f"中相关·{partner}重叠"
        else:
            tag = "低相关·独立新维度"
        print(f"{gname:<10}" + "".join(f"{mean[n]:>+14.3f}" for n in EXIST_NAMES) + f"  {tag}(max|{absmax:.2f}|@{partner}{cval:+.2f})", flush=True)
        rows.append((gname, mean, absmax, partner, cval, tag))

    # 汇总: 独立新维度清单
    indep = [r for r in rows if r[5].startswith("低相关")]
    print(f"\n=== 低相关·独立新维度(|corr|<=0.3) 共 {len(indep)} 个 ===", flush=True)
    for gname, mean, absmax, partner, cval, tag in indep:
        print(f"  {gname:<10} max|corr|={absmax:.3f}@{partner}", flush=True)

if __name__=="__main__": main()
