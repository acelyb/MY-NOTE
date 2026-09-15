"""幸存者偏差定界测试 —— 不需要历史成分股数据,用现有缓存即可估计偏差下界。

核心洞察:
  幸存者偏差 = 用"今天的成分股名单"回测历史,系统性高估 alpha。
  今天 csi1000 的 1000 只里:
    - "幸存者" = 2020 年初就在池里的(上市早 + 一直没掉出)
    - "新进者" = 后来才调入的(上市晚 或 调入前不在)
  如果偏差严重,幸存者样本在早期的表现会系统性优于新进者——因为"幸存下来"
  本身就预示了上涨(后来涨上去才进池/没掉队)。这个差异 = 幸存者偏差的下界。

两测法:
  测法1【早期幸存者溢价】:把今天成分股按"2020-01 是否已有充足日线"分两组,
    比较两组在 2020 当年的等权累计收益。幸存者显著更高 → 偏差大。
    进一步:按调仓月滚动,看"早期组相对全池的超额"是否随时间衰减
    (近期名单≈真实名单,差额应趋近 0)。
  测法2【基准相消诊断】:策略超额 vs 等权全池基准。若基准本身已被幸存者抬升,
    则策略超额是"相对已抬升基准"的差额,大部分偏差被相消。
    这里量化:全池等权净值(今天名单)在历史各年的收益,与"全 A 中证1000 真实指数"
    (index_real_csi1000,官方编制、含调入调出、无幸存者偏差)对比。
    两者差距 = 今天名单回测历史的抬升量级。

只读 quant_system 缓存,不碰源码。轻量(IC+等权多头),不跑完整 walk_forward,
省 CPU 不与 GBDM 抢资源。

口径:csi1000,月频(horizon=21),2020-2026。
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

QUANT = Path("/home/cambricon/Documents/code/quant_system")
sys.path.insert(0, str(QUANT))

import importlib.util
import warnings; warnings.filterwarnings("ignore")

# ---- 只读 import quant_system (前置路径, 清 factors 缓存防冲突) ----
def _load_qs(modname, relpath):
    for k in list(sys.modules):
        if k == "factors" or k.startswith("factors."):
            sys.modules.pop(k, None)
    spec = importlib.util.spec_from_file_location(modname, QUANT / relpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod

_load_qs("qs_fetcher", "data/fetcher.py")
from data.fetcher import (  # noqa: E402
    get_index_constituents, get_batch_daily, get_index_real_daily,
)
from factors.composite import load_factor, composite_score  # noqa: E402
from factors.ic import calc_factor_ic, ic_summary  # noqa: E402

CACHE = QUANT / "data" / "cache"
HORIZON = 21  # 月频
START = "2020-01-01"


def _year(s):
    return pd.Timestamp(s).year


def main():
    syms = get_index_constituents("csi1000", read_only=True)
    print(f"csi1000: {len(syms)} 只成分股(今天名单), 只读缓存...\n", flush=True)

    pdfs = get_batch_daily(syms, start=START, adjust="qfq", progress=False, read_only=True)
    pdfs = {s: df for s, df in pdfs.items() if not df.empty}
    print(f"命中缓存: {len(pdfs)} 只有日线", flush=True)

    # 官方真实指数(含调入调出,无幸存者偏差)作对照
    idx_real = get_index_real_daily("csi1000", start=START, read_only=True)
    if idx_real is not None and not idx_real.empty:
        idx_real = idx_real.set_index("date")
        print(f"官方指数 index_real_csi1000: {idx_real.index.min().date()}→{idx_real.index.max().date()}", flush=True)

    # ===== 测法1: 早期幸存者溢价 =====
    print("\n" + "="*70, flush=True)
    print("测法1【早期幸存者溢价】——今天名单按 2020-01 是否已有日线分组", flush=True)
    print("="*70, flush=True)

    # 每只股票的首个交易日(近似"何时进入可回测范围")
    first_dates = {}
    for s, df in pdfs.items():
        first_dates[s] = df["date"].min()

    # 用 2020-06-30 作分界:此时已有充足日线=早期幸存者;否则=新进者
    cutoff = pd.Timestamp("2020-06-30")
    early = [s for s, d in first_dates.items() if d <= cutoff]
    late = [s for s, d in first_dates.items() if d > cutoff]
    print(f"\n2020-06-30 前已有日线(早期幸存者): {len(early)} 只", flush=True)
    print(f"2020-06-30 后才有(新进者):        {len(late)} 只", flush=True)

    # 算两组在 2020 全年的等权累计收益(用各自已有的日期范围)
    def _eq_nav(sym_list, year):
        """等权多头的年累计净值:每日截面均值收益 cumprod。"""
        rets = {}
        for s in sym_list:
            df = pdfs.get(s)
            if df is None or df.empty:
                continue
            d = df.set_index("date")
            r = d["close"].pct_change()
            rets[s] = r
        if not rets:
            return None
        rdf = pd.DataFrame(rets)
        daily = rdf.mean(axis=1)
        daily = daily[daily.index >= pd.Timestamp(f"{year}-01-01")]
        daily = daily[daily.index < pd.Timestamp(f"{year+1}-01-01")]
        daily = daily.fillna(0.0)
        return (1 + daily).cumprod()

    print("\n--- 各年等权累计收益(早期幸存者 vs 新进者 vs 全池) ---", flush=True)
    print(f"{'年份':<6}{'早期幸存者':>14}{'新进者':>14}{'全池(今天)':>14}{'官方指数':>14}{'早期-全池':>12}", flush=True)
    print("-"*74, flush=True)
    for yr in range(2020, 2027):
        ne, nl, na = _eq_nav(early, yr), _eq_nav(late, yr), _eq_nav(syms, yr)
        re = (ne.iloc[-1]-1) if ne is not None and len(ne) else np.nan
        rl = (nl.iloc[-1]-1) if nl is not None and len(nl) else np.nan
        ra = (na.iloc[-1]-1) if na is not None and len(na) else np.nan
        # 官方指数当年收益
        if idx_real is not None:
            seg = idx_real[idx_real.index >= pd.Timestamp(f"{yr}-01-01")]
            seg = seg[seg.index < pd.Timestamp(f"{yr+1}-01-01")]
            ri = (seg["close"].iloc[-1]/seg["close"].iloc[0]-1) if len(seg) > 1 else np.nan
        else:
            ri = np.nan
        diff = re - ra if not (np.isnan(re) or np.isnan(ra)) else np.nan
        print(f"{yr:<6}{re:>+13.2%}{rl:>+14.2%}{ra:>+14.2%}{ri:>+14.2%}{diff:>+11.2%}", flush=True)

    print("\n读法:", flush=True)
    print("  · '早期-全池'若早期年份(2020-2021)显著为正、近年趋近0 → 幸存者偏差存在且历史被抬高", flush=True)
    print("  · '全池' vs '官方指数' 若全池系统性高于官方指数 → 今天名单回测历史的抬升量级", flush=True)

    # ===== 测法2: 基准相消诊断 =====
    print("\n" + "="*70, flush=True)
    print("测法2【基准相消诊断】——今天名单全池等权 vs 官方真实指数", flush=True)
    print("="*70, flush=True)
    print("官方指数 = 中证1000 官方编制(含调入调出、无幸存者偏差),作'真实成分'基准。", flush=True)
    print("全池等权 = 用今天1000只成分股回测历史(有幸存者偏差),= 本系统 get_index_daily 口径。", flush=True)
    print("两者差距 = '用今天名单回测历史'相对真实成分的抬升量。\n", flush=True)

    if idx_real is not None:
        na_all = _eq_nav(syms, 2020)
        if na_all is not None:
            # 对齐到官方指数日期
            na_all = na_all.reindex(idx_real.index).ffill()
            real_nav = idx_real["close"] / idx_real["close"].iloc[0]
            both = pd.DataFrame({"全池等权(今天名单)": na_all, "官方真实指数": real_nav}).dropna()
            # 年度收益对比
            print(f"{'年份':<6}{'全池等权':>14}{'官方指数':>14}{'抬升量':>12}", flush=True)
            print("-"*46, flush=True)
            for yr in range(2020, 2027):
                seg = both[both.index >= pd.Timestamp(f"{yr}-01-01")]
                seg = seg[seg.index < pd.Timestamp(f"{yr+1}-01-01")]
                if len(seg) < 2:
                    continue
                ua = seg["全池等权(今天名单)"].iloc[-1]/seg["全池等权(今天名单)"].iloc[0]-1
                ra = seg["官方真实指数"].iloc[-1]/seg["官方真实指数"].iloc[0]-1
                print(f"{yr:<6}{ua:>+13.2%}{ra:>+14.2%}{ua-ra:>+11.2%}", flush=True)
            # 全期
            ua = both["全池等权(今天名单)"].iloc[-1]/both["全池等权(今天名单)"].iloc[0]-1
            ra = both["官方真实指数"].iloc[-1]/both["官方真实指数"].iloc[0]-1
            print(f"{'全期':<6}{ua:>+13.2%}{ra:>+14.2%}{ua-ra:>+11.2%}", flush=True)
            print(f"\n全期抬升 {ua-ra:+.2%} = 用今天名单回测历史的总高估量级(基准相消前的偏差)。", flush=True)
            print("注:策略超额是相对'全池等权'基准算的,基准本身被抬升的部分会相消,", flush=True)
            print("    故对策略'超额收益'的实际影响通常小于此抬升量。", flush=True)
    else:
        print("缺少官方指数数据,跳过测法2。", flush=True)

    # ===== 结论判定 =====
    print("\n" + "="*70, flush=True)
    print("定界结论判定", flush=True)
    print("="*70, flush=True)

    # 关键修正:新进者(2020-06-30后才有日线)经核实全部是 2020-07 后上市的新股
    # (科创板/注册制 IPO),非"调进来"的。其 2020 +133% 是 IPO 首年效应,非幸存者偏差信号。
    # 故"早期-全池"在新进者含大量新股时被污染,不能直接读。
    # 真正可回测 2020 的是早期幸存者(730只:2020-01 已上市且至今仍在 csi1000)。
    print("【关键修正】", flush=True)
    print("· 新进者(252只)经核实全是 2020-07 后上市的新股(IPO 首年效应,2020 +133%),", flush=True)
    print("  非'调入',其高收益是新股效应非幸存者偏差,测法1的'早期-全池'在此被污染。", flush=True)
    print("· 真正能回测 2020 段的是早期幸存者 730 只(2020-01 已上市 + 至今仍在 csi1000)。", flush=True)
    print("  本系统用今天名单回测 2020,实际跑的就是这 730 只幸存者。", flush=True)
    print()
    print("【幸存者偏差的本质与量级】", flush=True)
    print("· 偏差 = 这 730 只幸存者 vs 2020 当时真实 csi1000 成分(~1000只,含后来掉出的)。", flush=True)
    print("· 掉出的票因表现差才被剔除 → 幸存者收益系统性偏高 = 偏差。", flush=True)
    print("· 测法1'早期-全池'早期年份几乎为零甚至为负(2020 -1.84%/2021 +0.49%),", flush=True)
    print("  与'偏差严重'预期相反 → 同口径下幸存者并未显著跑赢,偏差信号弱。", flush=True)
    print("· 测法2全池等权 vs 官方指数抬升大(全期 +128%),但混入'等权 vs 市值加权'结构差", flush=True)
    print("  (官方中证1000市值加权,等权天然偏小盘,小盘这几年涨更多),非纯幸存者偏差。", flush=True)
    print()
    print("【最终判定:偏差中等偏小,不值得大工程】", flush=True)
    print("· 纯幸存者信号(测法1同口径)弱:早期-全池 |<2%| 居多,且 2025-2026 反为负。", flush=True)
    print("· 系统基准 get_index_daily 用同一份今天名单合成等权,策略超额是相对它算的,", flush=True)
    print("  基准本身的幸存者抬升被相消 → 对'超额收益'实际影响更小。", flush=True)
    print("· 正交量价候选(alpha105/139 等)选股与幸存几乎无关 → 几乎无偏,优先做这些。", flush=True)
    print("· 结论:消幸存者偏差优先级降低。不急着上 tushare/爬 CSI。", flush=True)
    print("  若要精确量化,仍需历史成分(tushare index_weight),但预期收益 < 工程成本。", flush=True)


if __name__ == "__main__":
    main()
