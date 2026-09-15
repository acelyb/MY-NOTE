"""
GTJA191 Alpha125 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(AVG(CORR(VWAP,MEAN(VOL,80),17),20)) / RANK(AVG((CLOSE*0.5+VWAP*0.5-DELAY(CLOSE*0.5+VWAP*0.5,3)),16))
DolphinDB:
  def gtjaAlpha125(close, vol, vwap){
      return rowRank(mavg(mcorr(vwap, mavg(vol,80), 17), 1..20), percent=true) \ rowRank(mavg(close*0.5+vwap*0.5 - mfirst(close*0.5+vwap*0.5,4), 1..16), percent=true)
  }

翻译要点:
- 分子：mavg(vol,80)=80日量均；mcorr(vwap, 量均, 17)=17日相关；mavg(...,1..20) 加权均；rowRank 排名。
- 分母：mix=close*0.5+vwap*0.5；mix-mfirst(mix,4)=3日变化；mavg(...,1..16) 加权均；rowRank 排名。
- 分子 / 分母。长链80+17。

语义: VWAP-长均量17日相关平滑排名 / 价混合3日变化平滑排名。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_mean, mavg_weighted, mfirst


class Alpha125Factor(FactorBase):
    name = "gtja_alpha125"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 97:
            return None
        close, vol, vwap = df["close"], df["volume"], df["vwap"]
        c1 = ts_corr(vwap, ts_mean(vol, 80), 17)
        num = mavg_weighted(c1, list(range(1, 21))).rolling(20, min_periods=1).rank(pct=True)
        mix = close * 0.5 + vwap * 0.5
        d = mix - mfirst(mix, 4)
        den = mavg_weighted(d, list(range(1, 17))).rolling(16, min_periods=1).rank(pct=True)
        val = (num / den).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
