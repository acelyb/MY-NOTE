"""
GTJA191 Alpha33 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  (-MIN(LOW,5)+DELAY(MIN(LOW,5),6)) * RANK(SUM(RET,240)-SUM(RET,20)/220) * RANK(VOLUME)
  （长短期收益差 × 5日低点动量 × 量排名）
DolphinDB:
  def gtjaAlpha33(close, low, vol){
      return (-1 * mmin(low, 5) + mfirst(mmin(low, 5), 6)) * rowRank(msum(ratios(close) - 1, 240) - msum(ratios(close) - 1, 20) \ 220, percent=true) * mrank(vol, true, 5)
  }

翻译要点:
- (-mmin(low,5) + mfirst(mmin(low,5),6)) = MIN(LOW,5)_{t-6} - MIN(LOW,5)_t
  = 6日前5日低点 - 当前5日低点（>0 表示低点上移/走强，<0 表示低下移/走弱）。
- msum(RET,240) - msum(RET,20)/220 = 240日累计收益 - 20日累计收益/220
  ≈ 长期收益主导(240日)减去一个小的20日调整。本质是长期收益的截面排名。
- rowRank(长期收益差) 横截面排名 → rolling 近似；mrank(vol,true,5)=量5日时序排名。
- 三项相乘。
- ⚠️ 240日窗口较长，需 ≥240 日数据才出值；缓存(2020起,约1600日)够用。

语义: 5日低点动量(低点上移) × 长期收益排名 × 量排名 的复合。
  低点上移+长期上涨+放量 → 因子大。多因子复合，维度是"低点趋势×长期动量×量能"。
  含一层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha33Factor(FactorBase):
    name = "gtja_alpha33"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 246:  # msum(240) + rank + mmin(5)/mfirst(6) + rank(5)
            return None
        close, low, vol = df["close"], df["low"], df["volume"]
        minlow5 = low.rolling(5).min()
        low_mom = (-minlow5 + minlow5.shift(6))  # 6日前5日低点 - 当前5日低点
        ret = close / close.shift(1) - 1
        long_short = ret.rolling(240).sum() - ret.rolling(20).sum() / 220
        r_long = long_short.rolling(20).rank(pct=True)   # rowRank 近似
        r_vol = vol.rolling(5).rank(pct=True)            # mrank 时序(5)
        val = (low_mom * r_long * r_vol).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
