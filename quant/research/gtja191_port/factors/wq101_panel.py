"""
WorldQuant Alpha101 面板引擎（E4 批次1，2026-10-08）

公式源：《101 Formulaic Alphas》Zura Kakushadze, arXiv:1601.00991 (Wilmott 2016)
  —— 从 arXiv PDF 文本层逐字直抄（pdftotext），非凭记忆移植（调研勘误纪律）。
  每个因子的 docstring 保留论文原文公式，翻译要点写在实现处。

为什么是"面板引擎"而非逐标的 port（与 gtja191_port 的差异）：
  Alpha101 的 rank()/scale() 是**横截面算子**（论文 A.1：rank(x)=cross-sectional rank；
  scale(x,a)=sum(abs(x))=a 按截面重缩放），逐标的 calc(df) 无法忠实还原。
  本模块在 date×sym 宽面板上实现全部算子，横截面算子按行（axis=1）计算。

算子语义（论文 A.1 逐条对照）：
  rank(x)=截面排名 → 本实现用 pct rank（0~1，与公开实现惯例一致；进入 census 时
    再 winsorize+rank_standardize，对 IC 无影响）
  delay(x,d)=x 的 d 天前值；delta(x,d)=x-delay(x,d)
  correlation/covariance(x,y,d)=过去 d 天时序 Pearson 相关/协方差（min_periods=d 严格窗）
  ts_rank(x,d)=当日值在过去 d 天窗口内的时序排名（除 NaN 外含自身的计位/窗长）
  ts_argmax/ts_argmin(x,d)=窗口内最大/最小值的位置（0=窗口最旧日，np.argmax 语义，
    与 qlib 公开实现同约定；对 IC 只差符号，方向由实测定）
  decay_linear(x,d)=权重 d,d-1,…,1（归一化）线性衰减加权均值
  scale(x,a=1)=按截面 abs 值和重缩放到 a；signedpower(x,a)=sign(x)·|x|^a
  非整数窗 d 一律 floor（批次1 全为整数窗）
  returns=close 一日收益（pct_change）

批次1 范围（36 个）：纯 OHLCV、整数窗、无 vwap/adv{d}/cap/IndClass 的全部因子：
  1,2,3,4,6,8,9,10,12,13,14,16,18,19,20,22,23,24,30,33,34,35,37,38,40,
  44,45,46,49,51,52,53,54,55,60,101
（#3/#6 与生产 gtja_alpha105/139 同族，留作跨库对照组；#54 open^5/close^5 按
  字面实现——比值形式量纲自然消去，无溢出风险。）
（vwap/adv 依赖的留批次2——批次F 已有真实 amount→VWAP 基建；IndClass/cap 跳过。）

用法：
  from factors.wq101_panel import build_panel, WQ_ALPHAS
  P = build_panel(price_dfs)          # 一次建面板（宽表缓存复用）
  f = WQ_ALPHAS[1](P)                 # 全历史宽面板（index=date, columns=symbol）
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------- 面板构建 ----------------

def build_panel(price_dfs: dict) -> dict:
    """price_dfs: {sym: df(date,open,high,low,close,volume,...)} → 宽面板字典。"""
    fields = ["open", "high", "low", "close", "volume"]
    P: dict[str, pd.DataFrame] = {}
    for f in fields:
        P[f] = pd.DataFrame({s: d.set_index("date")[f].astype(float)
                             for s, d in price_dfs.items()
                             if d is not None and not d.empty})
        P[f] = P[f].sort_index()
    P["returns"] = P["close"].pct_change()
    return P


# ---------------- 算子（输入输出均为宽 DataFrame：index=date, columns=symbol） ----------------

def cs_rank(x: pd.DataFrame) -> pd.DataFrame:
    """rank(x)=cross-sectional rank（pct 0~1；NaN 保持 NaN）。"""
    return x.rank(axis=1, pct=True)


def delay(x: pd.DataFrame, d: int) -> pd.DataFrame:
    return x.shift(d)


def delta(x: pd.DataFrame, d: int) -> pd.DataFrame:
    return x - x.shift(d)


def ts_corr(x: pd.DataFrame, y: pd.DataFrame, d: int) -> pd.DataFrame:
    """注意：pandas 滚动相关遇零方差窗口（某输入在窗内恒定，如排名不变）会得 ±inf
    （实为未定义），统一替换为 NaN——冒烟实测 000028 连续 5 日量排名垫底触发。"""
    r = x.rolling(d, min_periods=d).corr(y)
    return r.replace([np.inf, -np.inf], np.nan)


def ts_cov(x: pd.DataFrame, y: pd.DataFrame, d: int) -> pd.DataFrame:
    r = x.rolling(d, min_periods=d).cov(y)
    return r.replace([np.inf, -np.inf], np.nan)


def ts_stddev(x: pd.DataFrame, d: int) -> pd.DataFrame:
    return x.rolling(d, min_periods=d).std(ddof=1)


def ts_sum(x: pd.DataFrame, d: int) -> pd.DataFrame:
    return x.rolling(d, min_periods=d).sum()


def ts_min(x: pd.DataFrame, d: int) -> pd.DataFrame:
    return x.rolling(d, min_periods=d).min()


def ts_max(x: pd.DataFrame, d: int) -> pd.DataFrame:
    return x.rolling(d, min_periods=d).max()


def ts_rank(x: pd.DataFrame, d: int) -> pd.DataFrame:
    """当日值在过去 d 天窗口内的排名比例（含自身）。O(d) 移位实现，严格窗（缺值→NaN）。

    注：pandas 比较遇 NaN 得 False（不计位），窗口缺值由 valid<d 置 NaN 兜底。"""
    cur = x
    le = pd.DataFrame(0.0, index=x.index, columns=x.columns)
    valid = pd.DataFrame(0.0, index=x.index, columns=x.columns)
    for k in range(d):
        sh = x.shift(k)
        le = le + (sh <= cur).where(sh.notna(), 0.0).astype(float)
        valid = valid + sh.notna().astype(float)
    res = le / d
    res = res.where(valid >= d)
    res[cur.isna()] = np.nan
    return res


def ts_argmax(x: pd.DataFrame, d: int) -> pd.DataFrame:
    """窗口内最大值位置（0=窗口最旧日，np.argmax 同约定；并列取最旧）。"""
    mx = x.rolling(d, min_periods=d).max()
    res = pd.DataFrame(np.nan, index=x.index, columns=x.columns)
    for k in range(d):  # k=0 是 d-1 天前（窗口最旧端）→ 命中最早出现的最大值
        hit = (x.shift(d - 1 - k) == mx) & res.isna()
        res[hit] = k
    return res


def ts_argmin(x: pd.DataFrame, d: int) -> pd.DataFrame:
    mn = x.rolling(d, min_periods=d).min()
    res = pd.DataFrame(np.nan, index=x.index, columns=x.columns)
    for k in range(d):
        hit = (x.shift(d - 1 - k) == mn) & res.isna()
        res[hit] = k
    return res


def decay_linear(x: pd.DataFrame, d: int) -> pd.DataFrame:
    """权重 d,d-1,…,1（归一化）线性衰减加权：k 天前权重 d-k。"""
    num = pd.DataFrame(np.zeros(x.shape), index=x.index, columns=x.columns)
    valid = pd.DataFrame(np.zeros(x.shape), index=x.index, columns=x.columns)
    for k in range(d):
        sh = x.shift(k)
        num = num + (d - k) * sh
        valid = valid + sh.notna().astype(float)
    denom = d * (d + 1) / 2.0
    res = num / denom
    return res.where(valid >= d)


def scale(x: pd.DataFrame, a: float = 1.0) -> pd.DataFrame:
    """截面重缩放：每行 sum(abs(x))=a。行和为 0 → NaN。"""
    s = x.abs().sum(axis=1)
    out = x.mul(a / s.replace(0, np.nan), axis=0)
    return out


def signedpower(x: pd.DataFrame, a: float) -> pd.DataFrame:
    return np.sign(x) * np.abs(x) ** a


def log(x: pd.DataFrame) -> pd.DataFrame:
    return np.log(x.where(x > 0))


def sign(x: pd.DataFrame) -> pd.DataFrame:
    return np.sign(x)


def _where(cond: pd.DataFrame, a, b) -> pd.DataFrame:
    """x ? y : z 三元（a/b 可为 DataFrame 或标量）。"""
    a_f = a if isinstance(a, pd.DataFrame) else pd.DataFrame(np.full(cond.shape, float(a)),
                                                             index=cond.index, columns=cond.columns)
    b_f = b if isinstance(b, pd.DataFrame) else pd.DataFrame(np.full(cond.shape, float(b)),
                                                             index=cond.index, columns=cond.columns)
    return a_f.where(cond, b_f)


def _or(c1: pd.DataFrame, c2: pd.DataFrame) -> pd.DataFrame:
    return c1 | c2


# ---------------- 因子实现（公式逐字引自 arXiv:1601.00991 文本层） ----------------

def alpha_1(P):
    # Alpha#1: (rank(Ts_ArgMax(SignedPower(((returns < 0) ? stddev(returns, 20) : close), 2.), 5)) - 0.5)
    ret, close = P["returns"], P["close"]
    inner = _where(ret < 0, ts_stddev(ret, 20), close)
    return cs_rank(ts_argmax(signedpower(inner, 2.0), 5)) - 0.5


def alpha_2(P):
    # Alpha#2: (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))
    vol, close, open_ = P["volume"], P["close"], P["open"]
    return -1 * ts_corr(cs_rank(delta(log(vol), 2)), cs_rank((close - open_) / open_), 6)


def alpha_3(P):
    # Alpha#3: (-1 * correlation(rank(open), rank(volume), 10))
    return -1 * ts_corr(cs_rank(P["open"]), cs_rank(P["volume"]), 10)


def alpha_4(P):
    # Alpha#4: (-1 * Ts_Rank(rank(low), 9))
    return -1 * ts_rank(cs_rank(P["low"]), 9)


def alpha_6(P):
    # Alpha#6: (-1 * correlation(open, volume, 10))
    return -1 * ts_corr(P["open"], P["volume"], 10)


def alpha_8(P):
    # Alpha#8: (-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10))))
    prod = ts_sum(P["open"], 5) * ts_sum(P["returns"], 5)
    return -1 * cs_rank(prod - delay(prod, 10))


def alpha_9(P):
    # Alpha#9: ((0 < ts_min(delta(close, 1), 5)) ? delta(close, 1) : ((ts_max(delta(close, 1), 5) < 0) ?
    #           delta(close, 1) : (-1 * delta(close, 1))))
    dc = delta(P["close"], 1)
    mn, mx = ts_min(dc, 5), ts_max(dc, 5)
    inner = _where(mx < 0, dc, -1 * dc)
    return _where(0 < mn, dc, inner)


def alpha_10(P):
    # Alpha#10: rank(((0 < ts_min(delta(close, 1), 4)) ? delta(close, 1) : ((ts_max(delta(close, 1), 4) < 0)
    #            ? delta(close, 1) : (-1 * delta(close, 1)))))
    dc = delta(P["close"], 1)
    mn, mx = ts_min(dc, 4), ts_max(dc, 4)
    inner = _where(mx < 0, dc, -1 * dc)
    return cs_rank(_where(0 < mn, dc, inner))


def alpha_12(P):
    # Alpha#12: (sign(delta(volume, 1)) * (-1 * delta(close, 1)))
    return sign(delta(P["volume"], 1)) * (-1 * delta(P["close"], 1))


def alpha_13(P):
    # Alpha#13: (-1 * rank(covariance(rank(close), rank(volume), 5)))
    return -1 * cs_rank(ts_cov(cs_rank(P["close"]), cs_rank(P["volume"]), 5))


def alpha_14(P):
    # Alpha#14: ((-1 * rank(delta(returns, 3))) * correlation(open, volume, 10))
    return (-1 * cs_rank(delta(P["returns"], 3))) * ts_corr(P["open"], P["volume"], 10)


def alpha_16(P):
    # Alpha#16: (-1 * rank(covariance(rank(high), rank(volume), 5)))
    return -1 * cs_rank(ts_cov(cs_rank(P["high"]), cs_rank(P["volume"]), 5))


def alpha_18(P):
    # Alpha#18: (-1 * rank(((stddev(abs((close - open)), 5) + (close - open)) + correlation(close, open, 10))))
    co = P["close"] - P["open"]
    inner = ts_stddev(co.abs(), 5) + co + ts_corr(P["close"], P["open"], 10)
    return -1 * cs_rank(inner)


def alpha_19(P):
    # Alpha#19: ((-1 * sign(((close - delay(close, 7)) + delta(close, 7)))) * (1 + rank((1 + sum(returns, 250)))))
    close = P["close"]
    s = (-1 * sign((close - delay(close, 7)) + delta(close, 7)))
    return s * (1 + cs_rank(1 + ts_sum(P["returns"], 250)))


def alpha_20(P):
    # Alpha#20: (((-1 * rank((open - delay(high, 1)))) * rank((open - delay(close, 1)))) * rank((open - delay(low, 1))))
    open_ = P["open"]
    return (-1 * cs_rank(open_ - delay(P["high"], 1))) * cs_rank(open_ - delay(P["close"], 1)) \
        * cs_rank(open_ - delay(P["low"], 1))


def alpha_22(P):
    # Alpha#22: (-1 * (delta(correlation(high, volume, 5), 5) * rank(stddev(close, 20))))
    c = ts_corr(P["high"], P["volume"], 5)
    return -1 * (delta(c, 5) * cs_rank(ts_stddev(P["close"], 20)))


def alpha_23(P):
    # Alpha#23: (((sum(high, 20) / 20) < high) ? (-1 * delta(high, 2)) : 0)
    cond = (ts_sum(P["high"], 20) / 20) < P["high"]
    return _where(cond, -1 * delta(P["high"], 2), 0)


def alpha_24(P):
    # Alpha#24: ((((delta((sum(close, 100) / 100), 100) / delay(close, 100)) < 0.05) ||
    #             ((delta((sum(close, 100) / 100), 100) / delay(close, 100)) == 0.05)) ?
    #            (-1 * (close - ts_min(close, 100))) : (-1 * delta(close, 3)))
    ma100 = ts_sum(P["close"], 100) / 100
    chg = delta(ma100, 100) / delay(P["close"], 100)
    cond = _or(chg < 0.05, chg == 0.05)
    return _where(cond, -1 * (P["close"] - ts_min(P["close"], 100)), -1 * delta(P["close"], 3))


def alpha_30(P):
    # Alpha#30: (((1.0 - rank(((sign((close - delay(close, 1))) + sign((delay(close, 1) - delay(close, 2)))) +
    #             sign((delay(close, 2) - delay(close, 3)))))) * sum(volume, 5)) / sum(volume, 20))
    close = P["close"]
    s = sign(close - delay(close, 1)) + sign(delay(close, 1) - delay(close, 2)) \
        + sign(delay(close, 2) - delay(close, 3))
    return (1.0 - cs_rank(s)) * ts_sum(P["volume"], 5) / ts_sum(P["volume"], 20)


def alpha_33(P):
    # Alpha#33: rank((-1 * ((1 - (open / close))^1)))
    return cs_rank(-1 * (1 - (P["open"] / P["close"])) ** 1)


def alpha_34(P):
    # Alpha#34: rank(((1 - rank((stddev(returns, 2) / stddev(returns, 5)))) + (1 - rank(delta(close, 1)))))
    r2 = ts_stddev(P["returns"], 2) / ts_stddev(P["returns"], 5)
    return cs_rank((1 - cs_rank(r2)) + (1 - cs_rank(delta(P["close"], 1))))


def alpha_35(P):
    # Alpha#35: ((Ts_Rank(volume, 32) * (1 - Ts_Rank(((close + high) - low), 16))) * (1 - Ts_Rank(returns, 32)))
    a = ts_rank(P["volume"], 32)
    b = 1 - ts_rank(P["close"] + P["high"] - P["low"], 16)
    c = 1 - ts_rank(P["returns"], 32)
    return a * b * c


def alpha_37(P):
    # Alpha#37: (rank(correlation(delay((open - close), 1), close, 200)) + rank((open - close)))
    return cs_rank(ts_corr(delay(P["open"] - P["close"], 1), P["close"], 200)) \
        + cs_rank(P["open"] - P["close"])


def alpha_38(P):
    # Alpha#38: ((-1 * rank(Ts_Rank(close, 10))) * rank((close / open)))
    return (-1 * cs_rank(ts_rank(P["close"], 10))) * cs_rank(P["close"] / P["open"])


def alpha_40(P):
    # Alpha#40: ((-1 * rank(stddev(high, 10))) * correlation(high, volume, 10))
    return (-1 * cs_rank(ts_stddev(P["high"], 10))) * ts_corr(P["high"], P["volume"], 10)


def alpha_44(P):
    # Alpha#44: (-1 * correlation(high, rank(volume), 5))
    return -1 * ts_corr(P["high"], cs_rank(P["volume"]), 5)


def alpha_45(P):
    # Alpha#45: (-1 * ((rank((sum(delay(close, 5), 20) / 20)) * correlation(close, volume, 2)) *
    #             rank(correlation(sum(close, 5), sum(close, 20), 2))))
    a = cs_rank(ts_sum(delay(P["close"], 5), 20) / 20)
    b = ts_corr(P["close"], P["volume"], 2)
    c = cs_rank(ts_corr(ts_sum(P["close"], 5), ts_sum(P["close"], 20), 2))
    return -1 * (a * b * c)


def alpha_46(P):
    # Alpha#46: ((0.25 < (((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10))) ?
    #            (-1 * 1) : (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < 0) ?
    #            1 : ((-1 * 1) * (close - delay(close, 1)))))
    close = P["close"]
    slope = ((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)
    inner = _where(slope < 0, 1, -1 * (close - delay(close, 1)))
    return _where(0.25 < slope, -1, inner)


def alpha_49(P):
    # Alpha#49: (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.1)) ?
    #            1 : ((-1 * 1) * (close - delay(close, 1))))
    close = P["close"]
    slope = ((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)
    return _where(slope < -0.1, 1, -1 * (close - delay(close, 1)))


def alpha_51(P):
    # Alpha#51: (((((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)) < (-1 * 0.05)) ?
    #            1 : ((-1 * 1) * (close - delay(close, 1))))
    close = P["close"]
    slope = ((delay(close, 20) - delay(close, 10)) / 10) - ((delay(close, 10) - close) / 10)
    return _where(slope < -0.05, 1, -1 * (close - delay(close, 1)))


def alpha_52(P):
    # Alpha#52: ((((-1 * ts_min(low, 5)) + delay(ts_min(low, 5), 5)) *
    #             rank(((sum(returns, 240) - sum(returns, 20)) / 220))) * ts_rank(volume, 5))
    a = (-1 * ts_min(P["low"], 5)) + delay(ts_min(P["low"], 5), 5)
    b = cs_rank((ts_sum(P["returns"], 240) - ts_sum(P["returns"], 20)) / 220)
    c = ts_rank(P["volume"], 5)
    return a * b * c


def alpha_53(P):
    # Alpha#53: (-1 * delta((((close - low) - (high - close)) / (close - low)), 9))
    inner = ((P["close"] - P["low"]) - (P["high"] - P["close"])) / (P["close"] - P["low"])
    return -1 * delta(inner, 9)


def alpha_54(P):
    # Alpha#54: ((-1 * ((low - close) * (open^5))) / ((low - high) * (close^5)))
    return (-1 * (P["low"] - P["close"]) * P["open"] ** 5) / ((P["low"] - P["high"]) * P["close"] ** 5)


def alpha_55(P):
    # Alpha#55: (-1 * correlation(rank(((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12)))),
    #             rank(volume), 6))
    rng = ts_max(P["high"], 12) - ts_min(P["low"], 12)
    a = cs_rank((P["close"] - ts_min(P["low"], 12)) / rng)
    return -1 * ts_corr(a, cs_rank(P["volume"]), 6)


def alpha_60(P):
    # Alpha#60: (0 - (1 * ((2 * scale(rank(((((close - low) - (high - close)) / (high - low)) * volume)))) -
    #             scale(rank(ts_argmax(close, 10))))))
    inner = (((P["close"] - P["low"]) - (P["high"] - P["close"])) / (P["high"] - P["low"])) * P["volume"]
    return 0 - (1 * ((2 * scale(cs_rank(inner))) - scale(cs_rank(ts_argmax(P["close"], 10)))))


def alpha_101(P):
    # Alpha#101: ((close - open) / ((high - low) + .001))
    return (P["close"] - P["open"]) / ((P["high"] - P["low"]) + 0.001)


WQ_ALPHAS: dict[int, callable] = {
    1: alpha_1, 2: alpha_2, 3: alpha_3, 4: alpha_4, 6: alpha_6, 8: alpha_8,
    9: alpha_9, 10: alpha_10, 12: alpha_12, 13: alpha_13, 14: alpha_14, 16: alpha_16,
    18: alpha_18, 19: alpha_19, 20: alpha_20, 22: alpha_22, 23: alpha_23, 24: alpha_24,
    30: alpha_30, 33: alpha_33, 34: alpha_34, 35: alpha_35, 37: alpha_37, 38: alpha_38,
    40: alpha_40, 44: alpha_44, 45: alpha_45, 46: alpha_46, 49: alpha_49, 51: alpha_51,
    52: alpha_52, 53: alpha_53, 54: alpha_54, 55: alpha_55, 60: alpha_60, 101: alpha_101,
}
