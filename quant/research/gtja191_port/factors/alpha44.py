"""
GTJA191 Alpha44 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: TSRANK(CORR(LOW,SUM(AVG(VOL,10),7),6),3) + TSRANK(AVG(VWAP-DELAY(VWAP,3),11),15)
DolphinDB:
  def gtjaAlpha44(low, vol, vwap){
      return mrank(mavg(mcorr(low, mavg(vol,10), 7), 1..6), true, 4) + mrank(mavg(vwap-mfirst(vwap,4), 1..10), true, 15)
  }

翻译要点:
- 第一项：mavg(vol,10)=10日量均；mcorr(low, 量均, 7)=7日低价与量均的时序相关；
  mavg(...,1..6) 加权均；mrank(...,true,4)=过去4日升序排名（绝对位置）。
- 第二项：vwap-mfirst(vwap,4)=3日VWAP变化；mavg(...,1..10) 加权均；mrank(...,true,15)=15日升序排名。
- 注：研报 TSRANK 归一化到(0,1)，DolphinDB mrank 返回绝对排名1..n；按源码用 mrank 绝对排名口径。
  两项排名口径不同（4日 vs 15日），量纲不一致，直接相加，忠实源码。

语义: 低价-量相关时序的4日排名 + VWAP变化的15日排名。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_mean, mavg_weighted, mfirst, mrank


class Alpha44Factor(FactorBase):
    name = "gtja_alpha44"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 25:
            return None
        low, vol, vwap = df["low"], df["volume"], df["vwap"]
        vmean10 = ts_mean(vol, 10)
        corr7 = ts_corr(low, vmean10, 7)
        t1 = mavg_weighted(corr7, list(range(1, 7)))
        r1 = mrank(t1, True, 4)
        d = vwap - mfirst(vwap, 4)
        t2 = mavg_weighted(d, list(range(1, 11)))
        r2 = mrank(t2, True, 15)
        val = (r1 + r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
