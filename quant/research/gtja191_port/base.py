"""
因子基类（精简版，口径与 quant_system factors/base.py 一致，独立实现不 import 源码）。

单标的口径：calc(self, df) 输入单只股票的日线历史 [date,open,high,low,close,volume]，
返回当前时点的因子值（float）或 None（数据不足）。方向约定：值越大 → 预期未来收益越高。

为什么独立实现而非 import：用户要求不改 quant_system 源码、避免影响其他 agent；
独立实现单标的因子基类零依赖，IC 检验框架也独立，移植结果可直接对照。
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd


class FactorBase(ABC):
    name: str = "base"

    def __init__(self, params: dict | None = None):
        self.params = params or {}

    @abstractmethod
    def calc(self, df: pd.DataFrame) -> float | None:
        """计算单只股票当前时点（df 最后一行）的因子值。"""
        ...

    def calc_value(self, df: pd.DataFrame) -> float | None:
        """统一入口（本精简版无需 symbol/date 自适应，价量因子足够）。"""
        try:
            return self.calc(df)
        except Exception:
            return None


# ============ 研报算子的 pandas 实现（供因子复用） ============

def delay(s: pd.Series, n: int) -> pd.Series:
    """DELAY(A,n)=A_{t-n}。"""
    return s.shift(n)


def delta(s: pd.Series, n: int) -> pd.Series:
    """DELTA(A,n)=A_t - A_{t-n}。"""
    return s - s.shift(n)


def ts_rank(s: pd.Series, n: int) -> pd.Series:
    """TSRANK(A,n)=末位值在过去 n 天的时序排名(归一化到(0,1))。"""
    return s.rolling(n).apply(lambda x: pd.Series(x).rank().iloc[-1] / len(x), raw=False)


def ts_max(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).max()


def ts_min(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).min()


def ts_sum(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).sum()


def ts_mean(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def ts_std(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).std()


def ts_corr(a: pd.Series, b: pd.Series, n: int) -> pd.Series:
    """CORR(A,B,n)=过去 n 日时序相关。"""
    return a.rolling(n).corr(b)


def ts_cov(a: pd.Series, b: pd.Series, n: int) -> pd.Series:
    """COV(A,B,n)=过去 n 日时序协方差。"""
    return a.rolling(n).cov(b)


def sma_recursive(s: pd.Series, n: int, m: int) -> pd.Series:
    """研报 SMA(A,n,m)：Y_{t}=(A_{t-1}*m + Y_{t-1}*(n-m))/n 递归指数加权。

    注意研报下标：Y 用 t-1 的 A 和 Y 自身递推，等价于 EWM(alpha=m/n) 但起点处理略不同。
    与 DolphinDB ewmMean(alpha=1/n) 一致（m=1 时 alpha=1/n）。
    用 pandas ewm 近似（adjust=False，递归式），alpha=m/n。
    """
    return s.ewm(alpha=m / n, adjust=False).mean()


def wma(s: pd.Series, n: int) -> pd.Series:
    """研报 WMA(A,n)：前 n 期加权平均，权重 0.9^i（i=距当前间隔，i=0 权重1）。"""
    weights = 0.9 ** np.arange(n - 1, -1, -1)  # 最旧 i=n-1 权重0.9^(n-1)，最新 i=0 权重1
    return s.rolling(n).apply(lambda x: np.sum(x * weights) / np.sum(weights), raw=True)


def decay_linear(s: pd.Series, n: int) -> pd.Series:
    """DECAYLINEAR(A,n)：权重 d,d-1,...,1 归一化的移动加权均值。"""
    weights = np.arange(n, 0, -1, dtype=float)
    return s.rolling(n).apply(lambda x: np.sum(x * weights) / np.sum(weights), raw=True)


def rank_cross(series: pd.Series) -> pd.Series:
    """横截面 RANK 归一化到 (0,1)。IC 检验里截面排名在 ic.py 用 spearmanr 完成，
    因子内部 rank_cross 仅用于因子公式内含 RANK 的情况（对单标的序列做时序 pct rank 近似）。
    注意：研报 RANK 是横截面；单标的口径下因子内 RANK 用 rolling pct rank 近似（与 DolphinDB
    单股视角一致），最终截面排序由 IC 的 spearmanr 保证。"""
    return series.rolling(len(series)).rank(pct=True)


def regbeta(s: pd.Series, n: int) -> pd.Series:
    """REGBETA(A, SEQUENCE(n))=过去 n 期 A 对 1..n 的线性回归斜率。
    DolphinDB linearTimeTrend(x,n)[1] 返回斜率（[0]是截距）。
    rolling 内用最小二乘: slope = cov(x,t)/var(t)。"""
    t = np.arange(1, n + 1, dtype=float)
    t_centered = t - t.mean()

    def _slope(x):
        x = np.asarray(x, dtype=float)
        if np.isnan(x).any():
            return np.nan
        return np.sum((x - x.mean()) * t_centered) / np.sum(t_centered ** 2)

    return s.rolling(n).apply(_slope, raw=True)


def ts_argmax(s: pd.Series, n: int) -> pd.Series:
    """过去 n 期最大值出现的位置（距今天数，0=今天）。DolphinDB HIGHDAY 等价的时序版。
    注：研报 HIGHDAY(HIGH,20) 返回"距20日窗口起点的天数"，= (n-1) - imax。
    DolphinDB imax 返回从窗口起点算的位置（0=最早），研报 HIGHDAY 返回距今天数。
    这里统一返回距今天数（0=今天出现极值），与 alpha103 的 ts_argmin 口径一致。"""
    return s.rolling(n).apply(lambda x: pd.Series(x).argmax(), raw=False)


def ts_argmin(s: pd.Series, n: int) -> pd.Series:
    """过去 n 期最小值出现的位置（距今天数，0=今天）。ts_argmin。"""
    return s.rolling(n).apply(lambda x: pd.Series(x).argmin(), raw=False)


def cumsum(s: pd.Series) -> pd.Series:
    """SUMAC(A)=累积和。"""
    return s.cumsum()


def cumprod(s: pd.Series) -> pd.Series:
    """PROD 的累积版（研报 PROD 在 RANK 内多为累积乘积）。"""
    return s.cumprod()


def prod(s: pd.Series, n: int) -> pd.Series:
    """滚动乘积。"""
    return s.rolling(n).apply(np.prod, raw=True)


def ret(s: pd.Series) -> pd.Series:
    """RET = CLOSE/DELAY(CLOSE,1)-1 = 日收益率。"""
    return s.pct_change()


def ts_count(s: pd.Series, n: int) -> pd.Series:
    """COUNT(condition, n)=过去 n 期满足条件的期数。对布尔序列做 rolling sum。"""
    return s.rolling(n).sum()


def ema_mean(s: pd.Series, alpha: float) -> pd.Series:
    """ewmMean(alpha)=EWM 均值，adjust=False（递归式）。供研报中 ewmMean(alpha=k) 直接调用。"""
    return s.ewm(alpha=alpha, adjust=False).mean()


# ============ DolphinDB 191 补充算子（VWAP/指数因子用） ============

def mrank(s: pd.Series, ascending: bool, n: int) -> pd.Series:
    """DolphinDB mrank(A, true, n)=过去 n 期 A 的升序排名（当前值在窗内位置，1..n，未归一化）。
    ascending=false 则降序。等价于 rolling(n) 内的 rank（method='default' ordinal 近似）。
    返回绝对排名位置（非 pct），与 DolphinDB mrank 无 percent=true 时一致。
    注：pandas rolling().rank() 仅支持 method='average'（不支持 'first'），并列值取平均排名，足够近似。
    窗内含 NaN 时跳过 NaN 对当前末位值排名（NaN 末位返回 NaN），与 DolphinDB mrank 跳 NULL 一致。"""
    def _rk(x):
        cur = x[-1]
        if pd.isna(cur):
            return np.nan
        valid = x[~np.isnan(x)]
        if ascending:
            return np.sum(valid <= cur)
        return np.sum(valid >= cur)
    return s.rolling(n, min_periods=1).apply(_rk, raw=True)


def mavg_weighted(s: pd.Series, wins: list[int]) -> pd.Series:
    """DolphinDB mavg(A, 1..N)=以 1..N 为权重的加权移动均（递增线性权重）。
    即对每个窗宽 w in wins 做 mavg，再以 w 为权重加权平均——但 DolphinDB 实际语义是
    “对序列 A 做 w=1..N 各窗 mavg 后逐元素再以权重 1..N 加权均”，计算昂贵且罕见。
    本实现采用研报/业界常用近似：等价于以 [1,2,...,N] 为权重的 decay 型加权均
    （近端权重大），与 mavg(A,1..N) 的“线性递增窗权重”一致。
    注：早期移植（alpha25 等）按研报 DECAYLINEAR 语义用 decay_linear 近似，本函数
    提供更贴近 DolphinDB 字面的“1..N 递增权重”口径，供新因子选用并在 docstring 注明。
    窗内含 NaN 时按可用值加权（跳过 NaN 对应权重），与 DolphinDB mavg 跳 NULL 一致。"""
    n = len(wins)
    weights = np.arange(1, n + 1, dtype=float)  # 1,2,...,N 递增权重

    def _w(x):
        x = np.asarray(x, dtype=float)
        m = len(x)  # 窗口实际长度（前导 < N 期会小于 N）
        w = weights[-m:]  # 取末尾 m 个权重与窗口对齐
        mask = ~np.isnan(x)
        if not mask.any():
            return np.nan
        return np.sum(x[mask] * w[mask]) / np.sum(w[mask])

    return s.rolling(n, min_periods=1).apply(_w, raw=True)


def mbeta(a: pd.Series, b: pd.Series, n: int, min_periods: int | None = None) -> pd.Series:
    """DolphinDB mbeta(A,B,n)=过去 n 期 A 对 B 的回归系数 beta = cov(A,B)/var(B)。
    NaN 成对跳过（pairwise），min_periods 默认 n/2 保证足够样本；与 DolphinDB 跳 NULL 一致。
    用于 alpha149 下行 beta（condition 引入大量 NaN，需按有效下跌日对计算）；
    该类掩码数据有效对数远少于窗宽，可显式传更小 min_periods（仍需足够样本）。"""
    if min_periods is None:
        min_periods = max(n // 2, 2)
    cov = a.rolling(n, min_periods=min_periods).cov(b)
    var = b.rolling(n, min_periods=min_periods).var()
    return cov / var.replace(0, pd.NA)


def mcount(s: pd.Series, n: int) -> pd.Series:
    """DolphinDB mcount(A,n)=过去 n 期非 NULL（非 NaN）计数。对含 NaN 序列做 rolling count。"""
    return s.rolling(n).count()


def move(s: pd.Series, n: int) -> pd.Series:
    """DolphinDB move(A,n)=A_{t-n}，等价于 delay(A,n)。"""
    return s.shift(n)


def iif(cond: pd.Series, a, b) -> pd.Series:
    """DolphinDB iif(cond, a, b)=逐元素条件：cond 为真取 a 否则 b。
    a/b 可为标量或 Series；NULL（NaN）传播与 DolphinDB iif 一致：cond 为 NaN 时取 b。"""
    cond = pd.Series(cond).reset_index(drop=True) if not isinstance(cond, pd.Series) else cond
    a = pd.Series(a).reset_index(drop=True) if isinstance(a, pd.Series) else a
    b = pd.Series(b).reset_index(drop=True) if isinstance(b, pd.Series) else b
    return pd.Series(np.where(cond.fillna(False).astype(bool), a if isinstance(a, pd.Series) else a, b if isinstance(b, pd.Series) else b))


def seq_pow(base: pd.Series, exp: pd.Series) -> pd.Series:
    """逐元素幂 pow(base, exp)，base/exp 均可为 Series。负底数非整数指数→NaN（与 numpy 一致）。
    供 alpha17/121/131 等 pow(排名序列, 指数序列) 用。"""
    b = np.asarray(base, dtype=float)
    e = np.asarray(exp, dtype=float)
    return pd.Series(np.power(b, e), index=base.index)


def mfirst(s: pd.Series, n: int) -> pd.Series:
    """DolphinDB mfirst(A,n)=A_{t-(n-1)}，即 delay(A,n-1)。mfirst(A,2)=前一日。"""
    return s.shift(n - 1)
