"""
GTJA191 Alpha156 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MAX(RANK(AVG(DELAY(VWAP,5),3)), RANK(AVG((OPEN*0.15+LOW*0.85-DELAY(OPEN*0.15+LOW*0.85,3))/(OPEN*0.15+LOW*0.85)*-1,3))) * -1
DolphinDB:
  def gtjaAlpha156(open, low, vwap){
      return max(rowRank(mavg(vwap-mfirst(vwap,6), 1..3), percent=true), rowRank(mavg((open*0.15+low*0.85-mfirst(open*0.15+low*0.85,3))\(open*0.15+low*0.85)*(-1), 1..3), percent=true)) * (-1)
  }

翻译要点:
- 第一项：vwap-mfirst(vwap,6)=5日VWAP变化；mavg(...,1..3) 加权均；rowRank 排名。
- 第二项：mix=open*0.15+low*0.85（低价主导）；(mix-前3日mix)/mix*-1=负的3日变化率；mavg(...,1..3) 加权均；rowRank 排名。
- 两项取 max 后取负。分母 mix 可能为0（极端），需防护。

语义: VWAP5日变化平滑排名 与 低价混合负3日变化率平滑排名 的最大值，取负。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mfirst, mavg_weighted


class Alpha156Factor(FactorBase):
    name = "gtja_alpha156"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 9:
            return None
        op, low, vwap = df["open"], df["low"], df["vwap"]
        t1 = mavg_weighted(vwap - mfirst(vwap, 6), list(range(1, 4))).rolling(3, min_periods=1).rank(pct=True)
        mix = op * 0.15 + low * 0.85
        chg = (mix - mfirst(mix, 3)) / mix.replace(0, pd.NA) * (-1)
        t2 = mavg_weighted(chg, list(range(1, 4))).rolling(3, min_periods=1).rank(pct=True)
        val = (pd.concat([t1, t2], axis=1).max(axis=1) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
