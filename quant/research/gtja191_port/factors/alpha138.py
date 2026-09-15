"""
GTJA191 Alpha138 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((RANK(AVG(LOW*0.7+VWAP*0.3-DELAY(LOW*0.7+VWAP*0.3,4),20))) - TSRANK(AVG(TSRANK(CORR(TSRANK(LOW,8),TSRANK(MEAN(VOL,60),17),5),19),16),7)) * -1
DolphinDB:
  def gtjaAlpha138(low, vol, vwap){
      return (rowRank(mavg(low*0.7+vwap*0.3 - mfirst(low*0.7+vwap*0.3,4), 1..20), percent=true) - mrank(mavg(mrank(mcorr(mrank(low,true,8), mrank(mavg(vol,60),true,17), 5), true, 19), 1..16), true, 7)) * (-1)
  }

翻译要点:
- 第一项：mix=low*0.7+vwap*0.3；mix-mfirst(mix,4)=3日变化；mavg(...,1..20) 加权均；rowRank 排名。
- 第二项（深嵌套）：mrank(low,true,8)=8日低价排名；mrank(mavg(vol,60),true,17)=60日量均的17日排名；
  mcorr(...,5)=5日相关；mrank(...,true,19)=19日排名；mavg(...,1..16) 加权均；mrank(...,true,7)=7日排名。
- 两项相减后取负。长链60+17。

语义: 低价混合3日变化平滑排名 - 低价-长均量相关深嵌套排名的7日排名，取负。
  多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mfirst, mavg_weighted, ts_mean, ts_corr, mrank


class Alpha138Factor(FactorBase):
    name = "gtja_alpha138"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 83:
            return None
        low, vol, vwap = df["low"], df["volume"], df["vwap"]
        mix = low * 0.7 + vwap * 0.3
        d = mix - mfirst(mix, 4)
        r1 = mavg_weighted(d, list(range(1, 21))).rolling(20, min_periods=1).rank(pct=True)
        rl = mrank(low, True, 8)
        rv = mrank(ts_mean(vol, 60), True, 17)
        c5 = ts_corr(rl, rv, 5)
        m19 = mrank(c5, True, 19)
        a16 = mavg_weighted(m19, list(range(1, 17)))
        r2 = mrank(a16, True, 7)
        val = ((r1 - r2) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
