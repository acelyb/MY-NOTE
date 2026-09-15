"""
GTJA191 Alpha140 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  MIN(RANK(DECAYLINEAR(((RANK(OPEN)+RANK(LOW))-(RANK(HIGH)+RANK(CLOSE))), 8)),
      TSRANK(DECAYLINEAR(CORR(TSRANK(CLOSE,8), TSRANK(MEAN(VOLUME,60),20), 8), 7), 3))
DolphinDB:
  def gtjaAlpha140(open, close, high, low, vol){
      return min(rowRank(mavg(rowRank(open, percent=true) + rowRank(low, percent=true)
                              - (rowRank(high, percent=true) + rowRank(close, percent=true)), 1..8), percent=true),
                 mrank(mavg(mcorr(mrank(close, true, 8), mrank(mavg(vol, 60), true, 20), 8), 1..7), true, 3))
  }

翻译要点:
- 左侧 = RANK(DECAYLINEAR((RANK(OPEN)+RANK(LOW))-(RANK(HIGH)+RANK(CLOSE)), 8))
  内层4个 rowRank 横截面 → rolling 时序 pct rank 近似（有损，含前导NaN用 min_periods=1）。
  DECAYLINEAR(.,8) 按研报用 decay_linear（递减权重8..1）；DolphinDB mavg(1..8) 为递增权重，差异注明。
  外层再 RANK → rolling pct rank。
- 右侧 = TSRANK(DECAYLINEAR(CORR(TSRANK(CLOSE,8), TSRANK(MEAN(VOL,60),20), 8), 7), 3)
  mrank(x,true,n)=ts_rank；mcorr(.,8) 后 DECAYLINEAR(.,7)→decay_linear；外层 ts_rank(.,3)。
- min(左,右) 逐元素取小。
- 最长链：右侧 mavg(60)+mrank(20)+mcorr(8)+decay(7)+ts_rank(3) ≈ 98 行。

语义: 两项"价量结构"因子的较小值。左项=(开盘+低价排名)-(高价+收盘排名)的衰减均值排名，
      右项=收盘时序排名与长均量时序排名相关的衰减均值的时序排名。
      取小强调两者同时偏弱。含多层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, decay_linear, ts_corr, ts_rank


class Alpha140Factor(FactorBase):
    name = "gtja_alpha140"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 98:  # mavg(60)+mrank(20)+mcorr(8)+decay(7)+ts_rank(3)
            return None
        op, close, high, low, vol = df["open"], df["close"], df["high"], df["low"], df["volume"]

        # 左侧
        r_op = op.rolling(10, min_periods=1).rank(pct=True)
        r_lo = low.rolling(10, min_periods=1).rank(pct=True)
        r_hi = high.rolling(10, min_periods=1).rank(pct=True)
        r_cl = close.rolling(10, min_periods=1).rank(pct=True)
        inner = r_op + r_lo - (r_hi + r_cl)
        decay8 = decay_linear(inner, 8)
        left = decay8.rolling(10, min_periods=1).rank(pct=True)

        # 右侧
        tsr_c = ts_rank(close, 8)
        mv60 = vol.rolling(60).mean()
        tsr_v = ts_rank(mv60, 20)
        corr8 = ts_corr(tsr_c, tsr_v, 8)
        decay7 = decay_linear(corr8, 7)
        right = ts_rank(decay7, 3)

        val = np.minimum(left, right).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
