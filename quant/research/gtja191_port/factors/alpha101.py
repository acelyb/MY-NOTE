"""
GTJA191 Alpha101 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((RANK(CORR(CLOSE,SUM(MEAN(VOL,30),37),15)) < RANK(CORR(RANK(HIGH*0.1+VWAP*0.9),RANK(VOL),11))) * -1)
DolphinDB:
  def gtjaAlpha101(close, high, vol, vwap){
      return (rowRank(mcorr(close, msum(mavg(vol,30),37), 15), percent=true) < rowRank(mcorr(rowRank(high*0.1+vwap*0.9,percent=true), rowRank(vol,percent=true), 11), percent=true)) * (-1)
  }

翻译要点:
- 第一项：mavg(vol,30)=30日量均；msum(...,37)=37日累加；mcorr(close, …, 15)=15日相关；rowRank 排名。
- 第二项：mix=high*0.1+vwap*0.9（VWAP主导高价混合）；rowRank(mix)/rowRank(vol) 排名；
  mcorr(...,11)=11日相关；rowRank 排名。
- 两项比较：< 为真→1，否则0；整体乘 -1。
  即第一项排名 < 第二项排名 时取 -1，否则 0（布尔×-1）。

语义: 量价结构相关排名 vs 高价混合-量排名相关排名 的比较，取负（布尔因子，值域{-1,0}）。
  多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_mean, ts_sum


class Alpha101Factor(FactorBase):
    name = "gtja_alpha101"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 82:  # 30+37+15
            return None
        close, high, vol, vwap = df["close"], df["high"], df["volume"], df["vwap"]
        c1 = ts_corr(close, ts_sum(ts_mean(vol, 30), 37), 15)
        r1 = c1.rolling(15, min_periods=1).rank(pct=True)
        mix = high * 0.1 + vwap * 0.9
        rm = mix.rolling(11, min_periods=1).rank(pct=True)
        rv = vol.rolling(11, min_periods=1).rank(pct=True)
        c2 = ts_corr(rm, rv, 11)
        r2 = c2.rolling(11, min_periods=1).rank(pct=True)
        cond = (r1 < r2).astype(float)
        val = (cond * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
