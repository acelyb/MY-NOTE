"""
GTJA191 Alpha74 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(CORR(SUM((LOW*0.35+VWAP*0.65),20), SUM(MEAN(VOL,40),20),7)) + RANK(CORR(RANK(VWAP),RANK(VOL),6))
DolphinDB:
  def gtjaAlpha74(low, vol, vwap){
      return rowRank(mcorr(msum(low*0.35+vwap*0.65,20), msum(mavg(vol,40),20), 7), percent=true) + rowRank(mcorr(rowRank(vwap,percent=true), rowRank(vol,percent=true), 6), percent=true)
  }

翻译要点:
- 第一项：mix=low*0.35+vwap*0.65（VWAP主导的低价混合）；msum(mix,20)=20日累加；
  msum(mavg(vol,40),20)=40日量均再20日累加；mcorr(…,…,7)=7日相关；rowRank 排名。
- 第二项：rowRank(vwap)/rowRank(vol) 排名；mcorr(...,6)=6日相关；rowRank 排名。
- 两项相加。长链40+20。

语义: 低价混合累加与长均量累加的7日相关排名 + VWAP-量排名6日相关排名。
  多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_sum, ts_mean


class Alpha74Factor(FactorBase):
    name = "gtja_alpha74"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 67:
            return None
        low, vol, vwap = df["low"], df["volume"], df["vwap"]
        mix = low * 0.35 + vwap * 0.65
        c1 = ts_corr(ts_sum(mix, 20), ts_sum(ts_mean(vol, 40), 20), 7)
        r1 = c1.rolling(7, min_periods=1).rank(pct=True)
        rvw = vwap.rolling(6, min_periods=1).rank(pct=True)
        rv = vol.rolling(6, min_periods=1).rank(pct=True)
        r2 = ts_corr(rvw, rv, 6).rolling(6, min_periods=1).rank(pct=True)
        val = (r1 + r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
