"""
GTJA191 Alpha119 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(AVG(CORR(VWAP,SUM(MEAN(VOL,5),26),5),7)) - RANK(AVG(TSRANK(MIN(CORR(RANK(OPEN),RANK(MEAN(VOL,15)),21),9),7),8))
DolphinDB:
  def gtjaAlpha119(open, vol, vwap){
      return rowRank(mavg(mcorr(vwap, msum(mavg(vol,5),26), 5), 1..7), percent=true) - rowRank(mavg(mrank(min(mcorr(rowRank(open,percent=true), rowRank(mavg(vol,15),percent=true), 21), 9), true, 7), 1..8), percent=true)
  }

翻译要点:
- 第一项：mavg(vol,5)=5日量均；msum(...,26)=26日累加；mcorr(vwap, …, 5)=5日相关；mavg(...,1..7) 加权均；rowRank 排名。
- 第二项：mavg(vol,15)=15日量均；rowRank(量均)；rowRank(open)；mcorr(...,21)=21日相关；
  min(...,9)=ts_min(...,9)（9日最小相关）；mrank(...,true,7)=7日升序排名；
  mavg(...,1..8) 加权均；rowRank 排名。
- 两项相减。长链15+21。

语义: VWAP-量结构5日相关平滑排名 - 开盘-长均量21日相关9日最小的7日排名平滑。
  多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_sum, ts_mean, mavg_weighted, ts_min, mrank


class Alpha119Factor(FactorBase):
    name = "gtja_alpha119"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 44:
            return None
        op, vol, vwap = df["open"], df["volume"], df["vwap"]
        c1 = ts_corr(vwap, ts_sum(ts_mean(vol, 5), 26), 5)
        r1 = mavg_weighted(c1, list(range(1, 8))).rolling(7, min_periods=1).rank(pct=True)
        rv15 = ts_mean(vol, 15).rolling(15, min_periods=1).rank(pct=True)
        ro = op.rolling(21, min_periods=1).rank(pct=True)
        c21 = ts_corr(ro, rv15, 21)
        cmin9 = ts_min(c21, 9)
        mr7 = mrank(cmin9, True, 7)
        r2 = mavg_weighted(mr7, list(range(1, 9))).rolling(8, min_periods=1).rank(pct=True)
        val = (r1 - r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
