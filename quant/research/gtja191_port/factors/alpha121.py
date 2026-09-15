"""
GTJA191 Alpha121 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (RANK((VWAP-MIN(VWAP,12)))^TSRANK(CORR(TSRANK(VWAP,20),TSRANK(MEAN(VOL,60),2),18),3)) * -1
DolphinDB:
  def gtjaAlpha121(vol, vwap){
      return pow(rowRank(vwap - min(vwap,12), percent=true), mrank(mcorr(mrank(vwap,true,20), mrank(mavg(vol,60),true,2), 18), true, 3)) * (-1)
  }

翻译要点:
- 底：vwap - ts_min(vwap,12)=VWAP相对12日最低的溢价；rowRank 排名（∈(0,1)）。
- 指数：mrank(vwap,true,20)=20日VWAP升序排名；mrank(mavg(vol,60),true,2)=60日量均的2日排名；
  mcorr(...,18)=18日相关；mrank(...,true,3)=3日升序排名。
- pow(底, 指数) 逐元素幂；整体取负。长链60+18。

语义: VWAP溢价排名，以 VWAP-量均 相关的3日排名为幂，取负。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_min, ts_mean, ts_corr, mrank, seq_pow


class Alpha121Factor(FactorBase):
    name = "gtja_alpha121"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 80:
            return None
        vol, vwap = df["volume"], df["vwap"]
        base = (vwap - ts_min(vwap, 12)).rolling(12, min_periods=1).rank(pct=True)
        rvw = mrank(vwap, True, 20)
        rvmean = mrank(ts_mean(vol, 60), True, 2)
        c18 = ts_corr(rvw, rvmean, 18)
        exp = mrank(c18, True, 3)
        val = (seq_pow(base, exp) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
