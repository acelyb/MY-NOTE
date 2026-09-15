"""
GTJA191 Alpha25 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((-1 * RANK((DELTA(CLOSE,7) * (1 - RANK(DECAYLINEAR((VOLUME/MEAN(VOLUME,20)),9))))))
           * (1 + RANK(SUM(RET,250))))
DolphinDB:
  def gtjaAlpha25(close, vol){
      return -1 * rowRank((close - mfirst(close, 8)) * (1 - rowRank(mavg(vol \ mavg(vol, 20), 1..9), percent=true)), percent=true)
             * (1 + rowRank(msum(ratios(close) - 1, 250), percent=true))
  }

翻译要点:
- mfirst(close,8)=delay(close,7)=DELTA(close,7)（研报 DELTA(close,7)）。
- mavg(vol/mavg(vol,20), 1..9)：对 vol/mean(vol,20) 做 DECAYLINEAR(...,9)（0.9^i 权重，对应 SEQUENCE 1..9）。
  注：DolphinDB mavg(x, 1..9) 是以 1..9 为权重的加权均；但 base.py 的 wma 用 0.9^i 权重，
  与 DECAYLINEAR 研报语义不同。这里研报写 DECAYLINEAR，DolphinDB 用 mavg(1..9)（线性权重）。
  按 DolphinDB 源码口径：mavg(x, 1..9) 是以 1..9 为权重的加权均，等价于 decay_linear 的"线性递减"变体
  （但 1..9 是递增权重，非递减）。为忠实 DolphinDB，用 decay_linear 不可直接替换；
  这里按研报 DECAYLINEAR 语义用 decay_linear（递减权重 9..1）近似，并在 docstring 注明差异。
  实际上 DolphinDB mavg(x, 1..9) 权重是 1,2,...,9（递增），与 DECAYLINEAR(递减) 相反；
  但研报明确写 DECAYLINEAR，这里以研报为准用 decay_linear。
- ratios(close)-1=ret(close)=日收益；msum(ret,250)=过去250日累计收益。
- rowRank 横截面排名 → 单标的用 rolling pct rank 近似（有损）。
- 外层两层 rowRank 嵌套，内层 rank(DECAYLINEAR) 用 rolling(9) 近似，
  中层 rank(动量×(1-rank)) 用 rolling 窗口近似，外层 rank(SUM(RET,250)) 用 rolling(250) 近似。
- 窗口选择：内层 rank_cross 近似用全样本（与 base.py rank_cross 一致），但为可计算性用足够长窗口。
  这里遵循 alpha42 风格：对每个 rowRank 用 rolling(对应数据窗口) pct rank 近似。

语义: 7日动量 × (1 - 量比衰减加权排名) 的排名 × (1 + 长期累计收益排名)，取负。
  量价动量与长期收益的交叉，取负后为反转逻辑。含多层横截面 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import (
    FactorBase,
    delay,
    ts_mean,
    decay_linear,
    ts_sum,
    ret,
)


class Alpha25Factor(FactorBase):
    name = "gtja_alpha25"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 250:  # 长期收益250日是主导约束
            return None
        close, vol = df["close"], df["volume"]
        # DECAYLINEAR(vol/mean(vol,20), 9)
        mean_vol20 = ts_mean(vol, 20).replace(0, np.nan)
        vol_ratio = vol / mean_vol20
        decay9 = decay_linear(vol_ratio, 9)
        # rowRank 近似：rolling pct rank；min_periods=1 让含前导 NaN 的窗口也能出排名
        r_decay = decay9.rolling(9, min_periods=1).rank(pct=True)
        d7 = delay(close, 7)
        inner = d7 * (1 - r_decay)
        r_inner = inner.rolling(9, min_periods=1).rank(pct=True)
        sum_ret250 = ts_sum(ret(close), 250)
        r_sum = sum_ret250.rolling(250, min_periods=1).rank(pct=True)
        val = (-r_inner * (1 + r_sum)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
