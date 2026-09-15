"""
IC 验证：首批 6 个 GTJA191 因子在 csi1000 月频(horizon=21/freq=21)的 Rank IC。

对照现有因子（memory 已知量级）:
- momentum_20: IC≈-0.053 反向显著（本框架自测 -0.0547 已校准）
- reversal(60日): 短期反转，A 股中长周期常反转
- shadow(上下影线): amplitude/upper_shadow 在分钟级 |IC|>0.05

本脚本看：
1. 6 个 GTJA191 因子各自 IC/ICIR/胜率/t 值
2. 哪些显著（|t|>2）、哪些维度是新（量价协同/自递归/递归加权）
3. 是否有现有因子的更好替代（如 Alpha135 长期动量 vs 现有 momentum/reversal）

不改 quant_system 源码，只读缓存，结论独立给出。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from cache_reader import load_constituents, load_batch_daily
from ic import calc_factor_ic, ic_summary, interpret
from factors import (
    Alpha6Factor, Alpha47Factor, Alpha99Factor,
    Alpha135Factor, Alpha143Factor, Alpha167Factor,
    Alpha2Factor, Alpha10Factor, Alpha40Factor, Alpha84Factor,
    Alpha112Factor, Alpha150Factor, Alpha158Factor, Alpha191Factor,
    Alpha4Factor, Alpha5Factor, Alpha11Factor, Alpha28Factor,
    Alpha48Factor, Alpha49Factor, Alpha50Factor, Alpha52Factor,
    Alpha69Factor, Alpha91Factor, Alpha104Factor, Alpha107Factor,
    Alpha1Factor, Alpha3Factor, Alpha9Factor, Alpha33Factor,
    Alpha42Factor, Alpha62Factor, Alpha83Factor, Alpha85Factor,
    Alpha103Factor, Alpha105Factor, Alpha141Factor, Alpha176Factor,
)

# 对照基线：现有 momentum_20（口径已校准 -0.0547）
class Momentum20:
    name = "momentum_20(基线)"
    def calc_value(self, df):
        n = 20
        if len(df) < n + 1:
            return None
        return df["close"].iloc[-1] / df["close"].iloc[-n - 1] - 1

FACTORS = [
    # 首批6个
    ("gtja_alpha6  合成价4日符号·取负", Alpha6Factor()),
    ("gtja_alpha47 收盘6日位置+SMA(9,1)", Alpha47Factor()),
    ("gtja_alpha99 量价协方差·取负", Alpha99Factor()),
    ("gtja_alpha135 20日动量延迟+SMA(20,1)", Alpha135Factor()),
    ("gtja_alpha143 自递归(上涨日复利累积)", Alpha143Factor()),
    ("gtja_alpha167 12日正收益累加", Alpha167Factor()),
    # 扩跑8个
    ("gtja_alpha2  收盘日内位置一阶差分·取负", Alpha2Factor()),
    ("gtja_alpha10 下跌日波动率5日极端·时序rank", Alpha10Factor()),
    ("gtja_alpha40 26日上涨/下跌量比×100", Alpha40Factor()),
    ("gtja_alpha84 20日带符号量累积(OBV类)", Alpha84Factor()),
    ("gtja_alpha112 12日RSI(绝对价差口径)", Alpha112Factor()),
    ("gtja_alpha150 典型价×量(流动性代理)", Alpha150Factor()),
    ("gtja_alpha158 EWM收盘偏离→日内振幅率", Alpha158Factor()),
    ("gtja_alpha191 量-低相关+收盘中点偏离", Alpha191Factor()),
    # 第三批12个
    ("gtja_alpha4  布林带趋势状态机(三态)", Alpha4Factor()),
    ("gtja_alpha5  量-高价排名相关3日峰值·取负", Alpha5Factor()),
    ("gtja_alpha11 收盘日内位置×量6日累加", Alpha11Factor()),
    ("gtja_alpha28 9日区间位置二次EWM(KDJ-J)", Alpha28Factor()),
    ("gtja_alpha48 3日符号和×放量比·rowRank取负", Alpha48Factor()),
    ("gtja_alpha49 DMI下移波幅占比", Alpha49Factor()),
    ("gtja_alpha50 DMI上移-下移波幅占比差", Alpha50Factor()),
    ("gtja_alpha52 昨日典型价多空力道比×100", Alpha52Factor()),
    ("gtja_alpha69 开盘缺口方向多空力量比(20日)", Alpha69Factor()),
    ("gtja_alpha91 5日收盘回撤×40日均量与低价相关·取负", Alpha91Factor()),
    ("gtja_alpha104 高价量相关5日变化×波动率rank·取负", Alpha104Factor()),
    ("gtja_alpha107 开盘相对昨H/L/C三缺口rank乘积·取负", Alpha107Factor()),
    # 第四批12个(聚焦量价相关维度)
    ("gtja_alpha1  量对数变化×日内收益6日相关·取负", Alpha1Factor()),
    ("gtja_alpha3  6日突破锚点距离累加", Alpha3Factor()),
    ("gtja_alpha9  中枢移动×单位量振幅7日EWM", Alpha9Factor()),
    ("gtja_alpha33 5日低点动量×长期收益×量rank", Alpha33Factor()),
    ("gtja_alpha42 高价波动rank×高价量10日相关·取负", Alpha42Factor()),
    ("gtja_alpha62 高价×量排名5日相关·取负", Alpha62Factor()),
    ("gtja_alpha83 高价量协方差rank·取负", Alpha83Factor()),
    ("gtja_alpha85 量比20日rank×8日反转rank", Alpha85Factor()),
    ("gtja_alpha103 20日最低价时效×100", Alpha103Factor()),
    ("gtja_alpha105 开盘rank×量rank10日相关·取负", Alpha105Factor()),
    ("gtja_alpha141 高价与15日均量相关9日rank·取负", Alpha141Factor()),
    ("gtja_alpha176 12日区间位置rank×量rank6日相关", Alpha176Factor()),
    ("momentum_20(现有基线)", Momentum20()),
]


def main():
    syms = load_constituents("csi1000")
    print(f"csi1000: {len(syms)} 只, 读缓存(只读不拉网)...")
    pdfs = load_batch_daily(syms)
    print(f"缓存命中: {len(pdfs)}/{len(syms)}")

    print(f"\n跑 IC (horizon=21, freq=21, 月频, csi1000, 2020-2026)...")
    print("-" * 95)
    print(f"{'因子':<40}{'IC均值':>9}{'ICIR':>8}{'胜率':>7}{'t值':>7}{'n':>5}  判断")
    print("-" * 95)
    rows = []
    for label, fac in FACTORS:
        ic = calc_factor_ic(pdfs, fac, horizon=21, freq=21)
        s = ic_summary(ic["ic"] if not ic.empty else pd.Series(dtype=float))
        rows.append((label, s))
        print(f"{label:<40}{s['ic_mean']:>+9.4f}{s['icir']:>+8.3f}"
              f"{s['win_rate']:>7.1%}{s['t_stat']:>+7.2f}{s['n']:>5}  {interpret(s)}")
    print("-" * 95)
    print("判定: |IC|>0.03弱/>0.05中/>0.1强; |ICIR|>0.5稳定; |t|>2显著")
    print("方向以本池 IC 实测为准（研报符号不可照搬）。\n")

    # 汇总：显著因子
    sig = [(l, s) for l, s in rows if not pd.isna(s["t_stat"]) and abs(s["t_stat"]) > 2]
    if sig:
        print(f"=== 显著因子（|t|>2）共 {len(sig)} 个 ===")
        for l, s in sig:
            print(f"  {l}: IC={s['ic_mean']:+.4f} t={s['t_stat']:+.2f} {'正向' if s['ic_mean']>0 else '反向'}")
    else:
        print("=== 无显著因子（|t|>2）===")


if __name__ == "__main__":
    main()
