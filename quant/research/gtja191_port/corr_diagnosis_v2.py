"""
相关性诊断 v2 —— 用 quant_system 真实因子口径（只 import 不改源码），
与 GTJA191 候选因子算截面相关性，判断"更好替代" vs "独立新维度"。

v1 用了凭记忆重建的 amplitude 口径，与真实 low_vol(60日std) 不符，已弃用。
v2 直接 import quant_system 真实因子类（low_vol/momentum/reversal/overnight/shadow），
仅 ivol 因需市场指数数据较重，这里不纳入相关性（单独评估）。

只读缓存 + 只读 import quant_system 因子定义，不修改其任何源码。
"""
from __future__ import annotations

import sys
from pathlib import Path

PORT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PORT_DIR))
# quant_system 根，用于 import 其因子定义（只读）
QUANT_ROOT = PORT_DIR.parents[1] / "quant_system"
sys.path.insert(0, str(QUANT_ROOT))

import numpy as np
import pandas as pd

from cache_reader import load_constituents, load_batch_daily

# GTJA factors 与 quant_system 的 factors 包同名，sys.path 会互相遮蔽。
# 用 importlib 按 GTJA 自有 base + 各 alpha 文件显式加载，彻底规避包名冲突。
import importlib.util


def _load(modname: str, relpath: str):
    p = PORT_DIR / relpath
    spec = importlib.util.spec_from_file_location(modname, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod

_base = _load("gtja_base", "base.py")
# GTJA alpha 模块依赖 `from base import ...`，需让 base 在搜索路径首位
sys.path.insert(0, str(PORT_DIR))


def _load_alpha(modname: str, relpath: str):
    p = PORT_DIR / relpath
    spec = importlib.util.spec_from_file_location(modname, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod

Alpha6Factor = _load_alpha("gtja_alpha6", "factors/alpha6.py").Alpha6Factor
Alpha47Factor = _load_alpha("gtja_alpha47", "factors/alpha47.py").Alpha47Factor
Alpha99Factor = _load_alpha("gtja_alpha99", "factors/alpha99.py").Alpha99Factor
Alpha135Factor = _load_alpha("gtja_alpha135", "factors/alpha135.py").Alpha135Factor
Alpha143Factor = _load_alpha("gtja_alpha143", "factors/alpha143.py").Alpha143Factor
Alpha167Factor = _load_alpha("gtja_alpha167", "factors/alpha167.py").Alpha167Factor
Alpha2Factor = _load_alpha("gtja_alpha2", "factors/alpha2.py").Alpha2Factor
Alpha10Factor = _load_alpha("gtja_alpha10", "factors/alpha10.py").Alpha10Factor
Alpha40Factor = _load_alpha("gtja_alpha40", "factors/alpha40.py").Alpha40Factor
Alpha84Factor = _load_alpha("gtja_alpha84", "factors/alpha84.py").Alpha84Factor
Alpha112Factor = _load_alpha("gtja_alpha112", "factors/alpha112.py").Alpha112Factor
Alpha150Factor = _load_alpha("gtja_alpha150", "factors/alpha150.py").Alpha150Factor
Alpha158Factor = _load_alpha("gtja_alpha158", "factors/alpha158.py").Alpha158Factor
Alpha191Factor = _load_alpha("gtja_alpha191", "factors/alpha191.py").Alpha191Factor
Alpha4Factor = _load_alpha("gtja_alpha4", "factors/alpha4.py").Alpha4Factor
Alpha5Factor = _load_alpha("gtja_alpha5", "factors/alpha5.py").Alpha5Factor
Alpha11Factor = _load_alpha("gtja_alpha11", "factors/alpha11.py").Alpha11Factor
Alpha28Factor = _load_alpha("gtja_alpha28", "factors/alpha28.py").Alpha28Factor
Alpha48Factor = _load_alpha("gtja_alpha48", "factors/alpha48.py").Alpha48Factor
Alpha49Factor = _load_alpha("gtja_alpha49", "factors/alpha49.py").Alpha49Factor
Alpha50Factor = _load_alpha("gtja_alpha50", "factors/alpha50.py").Alpha50Factor
Alpha52Factor = _load_alpha("gtja_alpha52", "factors/alpha52.py").Alpha52Factor
Alpha69Factor = _load_alpha("gtja_alpha69", "factors/alpha69.py").Alpha69Factor
Alpha91Factor = _load_alpha("gtja_alpha91", "factors/alpha91.py").Alpha91Factor
Alpha104Factor = _load_alpha("gtja_alpha104", "factors/alpha104.py").Alpha104Factor
Alpha107Factor = _load_alpha("gtja_alpha107", "factors/alpha107.py").Alpha107Factor
Alpha1Factor = _load_alpha("gtja_alpha1", "factors/alpha1.py").Alpha1Factor
Alpha3Factor = _load_alpha("gtja_alpha3", "factors/alpha3.py").Alpha3Factor
Alpha9Factor = _load_alpha("gtja_alpha9", "factors/alpha9.py").Alpha9Factor
Alpha33Factor = _load_alpha("gtja_alpha33", "factors/alpha33.py").Alpha33Factor
Alpha42Factor = _load_alpha("gtja_alpha42", "factors/alpha42.py").Alpha42Factor
Alpha62Factor = _load_alpha("gtja_alpha62", "factors/alpha62.py").Alpha62Factor
Alpha83Factor = _load_alpha("gtja_alpha83", "factors/alpha83.py").Alpha83Factor
Alpha85Factor = _load_alpha("gtja_alpha85", "factors/alpha85.py").Alpha85Factor
Alpha103Factor = _load_alpha("gtja_alpha103", "factors/alpha103.py").Alpha103Factor
Alpha105Factor = _load_alpha("gtja_alpha105", "factors/alpha105.py").Alpha105Factor
Alpha141Factor = _load_alpha("gtja_alpha141", "factors/alpha141.py").Alpha141Factor
Alpha176Factor = _load_alpha("gtja_alpha176", "factors/alpha176.py").Alpha176Factor

# 真实 quant_system 因子（只 import 定义，不改源码）。
# GTJA 与 quant_system 的 `factors` 包同名且 PORT_DIR 在 path 首位会遮蔽，
# 故 quant_system 的真实因子模块也用 importlib 按文件显式加载，
# 其内部 `from factors.base import FactorBase` / `from data.fetcher import ...`
# 需 QUANT_ROOT 在 path 首位才能解析，加载时临时前置。
def _load_qs(modname: str, relpath: str):
    p = QUANT_ROOT / relpath
    # 临时把 quant_system 根置顶，让被加载模块内部的绝对 import 命中 quant_system
    sys.path.insert(0, str(QUANT_ROOT))
    # 清掉可能被 GTJA 占用的同名缓存
    for k in list(sys.modules):
        if k == "factors" or k.startswith("factors."):
            sys.modules.pop(k, None)
    spec = importlib.util.spec_from_file_location(modname, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod

_qsb = _load_qs("qs_base", "factors/base.py")
LowVolFactor = _load_qs("qs_low_vol", "factors/low_vol.py").LowVolFactor
MomentumFactor = _load_qs("qs_momentum", "factors/momentum.py").MomentumFactor
ReversalFactor = _load_qs("qs_reversal", "factors/reversal.py").ReversalFactor
OvernightReversalFactor = _load_qs("qs_overnight", "factors/overnight_reversal.py").OvernightReversalFactor
_usd = _load_qs("qs_shadow", "factors/shadow_daily.py")
UpperShadowDailyFactor = _usd.UpperShadowDailyFactor
LowerShadowDailyFactor = _usd.LowerShadowDailyFactor
WilliamsUpperShadowFactor = _usd.WilliamsUpperShadowFactor
WilliamsLowerShadowFactor = _usd.WilliamsLowerShadowFactor

# GTJA 候选
GTJA = {
    "alpha6": Alpha6Factor(),
    "alpha47": Alpha47Factor(),
    "alpha99": Alpha99Factor(),
    "alpha135": Alpha135Factor(),
    "alpha143": Alpha143Factor(),
    "alpha167": Alpha167Factor(),
    "alpha2": Alpha2Factor(),
    "alpha10": Alpha10Factor(),
    "alpha40": Alpha40Factor(),
    "alpha84": Alpha84Factor(),
    "alpha112": Alpha112Factor(),
    "alpha150": Alpha150Factor(),
    "alpha158": Alpha158Factor(),
    "alpha191": Alpha191Factor(),
    # 第三批12个
    "alpha4": Alpha4Factor(),
    "alpha5": Alpha5Factor(),
    "alpha11": Alpha11Factor(),
    "alpha28": Alpha28Factor(),
    "alpha48": Alpha48Factor(),
    "alpha49": Alpha49Factor(),
    "alpha50": Alpha50Factor(),
    "alpha52": Alpha52Factor(),
    "alpha69": Alpha69Factor(),
    "alpha91": Alpha91Factor(),
    "alpha104": Alpha104Factor(),
    "alpha107": Alpha107Factor(),
    # 第四批12个
    "alpha1": Alpha1Factor(),
    "alpha3": Alpha3Factor(),
    "alpha9": Alpha9Factor(),
    "alpha33": Alpha33Factor(),
    "alpha42": Alpha42Factor(),
    "alpha62": Alpha62Factor(),
    "alpha83": Alpha83Factor(),
    "alpha85": Alpha85Factor(),
    "alpha103": Alpha103Factor(),
    "alpha105": Alpha105Factor(),
    "alpha141": Alpha141Factor(),
    "alpha176": Alpha176Factor(),
}

# 流动性/规模代理（检验 alpha150 是否规模/流动性效应伪装）：
# quant_system 真实 size 依赖基本面 market_cap（日线缓存无），无法直接跑；
# 用 20日均成交额(=典型价×量的滚动版)作为流动性代理、20日均收盘价作为价位规模代理。
class LiquidityProxy:
    """20日均成交额（典型价×量的滚动均值）= 流动性代理。"""
    name = "liq_proxy(20日均额)"
    def calc_value(self, df):
        if len(df) < 20: return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        tp = (high + low + close) / 3
        amt = tp * vol
        return float(amt.rolling(20).mean().iloc[-1])

class PriceScaleProxy:
    """20日均收盘价 = 价位规模代理（高价股≠大市值，但截面排序相近）。"""
    name = "price_proxy(20日均收)"
    def calc_value(self, df):
        if len(df) < 20: return None
        return float(df["close"].rolling(20).mean().iloc[-1])

# 真实现有因子（默认参数口径）
EXISTING = {
    "low_vol(60日std取负)": LowVolFactor(),
    "momentum(20日)": MomentumFactor(),
    "reversal(60日取负)": ReversalFactor(),
    "overnight_rev(15日)": OvernightReversalFactor(),
    "upper_shadow_d": UpperShadowDailyFactor(),
    "lower_shadow_d": LowerShadowDailyFactor(),
    "williams_upper_d": WilliamsUpperShadowFactor(),
    "williams_lower_d": WilliamsLowerShadowFactor(),
    "liq_proxy(20日均额)": LiquidityProxy(),
    "price_proxy(20日均收)": PriceScaleProxy(),
}

FACTORS = {**GTJA, **EXISTING}


def cross_section(sym_data, date):
    out = {}
    for fname, fac in FACTORS.items():
        vals = {}
        for s, d in sym_data.items():
            pos = int(np.searchsorted(d.index.values, np.datetime64(date)))
            if pos >= len(d) or d.index[pos] != date:
                continue
            try:
                v = fac.calc_value(d.iloc[:pos + 1])
            except Exception:
                v = None
            if v is not None and not (isinstance(v, float) and np.isnan(v)):
                vals[s] = v
        out[fname] = pd.Series(vals)
    return out


def main():
    syms = load_constituents("csi1000")
    print(f"csi1000: {len(syms)} 只, 读缓存...")
    pdfs = load_batch_daily(syms)
    sym_data = {s: df.set_index("date") for s, df in pdfs.items() if not df.empty}
    all_dates = sorted(set().union(*[set(d.index) for d in sym_data.values()]))
    dates = all_dates[:-21:21]
    print(f"采样 {len(dates)} 个时点算截面相关性...")

    corr_acc = pd.DataFrame(index=list(FACTORS), columns=list(FACTORS), dtype=float)
    cnt = 0
    for date in dates:
        cs = cross_section(sym_data, date)
        mat = pd.DataFrame({n: cs[n] for n in FACTORS})
        if mat.dropna(how="all").shape[0] < 10:
            continue
        c = mat.corr(method="spearman")
        corr_acc = corr_acc.add(c, fill_value=0)
        cnt += 1
    corr_mean = corr_acc / cnt

    print(f"\n有效时点 {cnt}")
    print("\n=== GTJA候选 vs 现有因子（跨时点平均 Spearman）===")
    gtja_names = list(GTJA)
    exist_names = list(EXISTING)
    sub = corr_mean.loc[gtja_names, exist_names]
    print(sub.round(3).to_string())

    print("\n=== 逐个 GTJA 候选的判定 ===")
    for g in gtja_names:
        row = sub.loc[g].dropna()
        maxc = row.abs().max()
        partner = row.abs().idxmax()
        cval = row[partner]
        if maxc > 0.5:
            tag = f"高相关·疑似{partner}的变体(若IC更强=可替代)"
        elif maxc > 0.3:
            tag = f"中相关·与{partner}部分重叠"
        else:
            tag = "低相关·独立新维度"
        print(f"  {g:<10} 最高|corr|={maxc:.3f}({partner}) → {tag}")

    print("\n=== 现有因子间冗余自查（顺带）===")
    inter = corr_mean.loc[exist_names, exist_names]
    print(inter.round(3).to_string())


if __name__ == "__main__":
    main()
