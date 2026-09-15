"""
GTJA191 Alpha87 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (RANK(AVG(DELAY(VWAP,4),7)) + TSRANK(AVG(((LOW*0.9+LOW*0.1-VWAP)/(OPEN-((HIGH+LOW)/2))),11),7)) * -1
DolphinDB:
  def gtjaAlpha87(open, high, low, vwap){
      return (rowRank(mavg(vwap-mfirst(vwap,5), 1..7), percent=true) + mrank(mavg((low*0.9+low*0.1-vwap)\(open-(high+low)\2), 1..11), true, 7)) * (-1)
  }

翻译要点:
- 第一项：vwap-mfirst(vwap,5)=4日VWAP变化（研报 DELAY(VWAP,4) 在 AVG 内即 VWAP-前4日）；
  mavg(...,1..7) 加权均；rowRank 排名。
- 第二项：low*0.9+low*0.1 = low（笔误式恒等，忠实源码）；分子=low-vwap；
  分母=open-(H+L)/2；mavg(比值,1..11) 加权均；mrank(...,true,7)=7日升序排名。
- 两项相加后取负。

语义: VWAP变化平滑排名 + (低价-VWAP)/(开盘-典型价) 平滑的7日排名，取负。
  rank 近似（有损），分母0需防护，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, mfirst, mavg_weighted, mrank


class Alpha87Factor(FactorBase):
    name = "gtja_alpha87"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 18:
            return None
        op, high, low, vwap = df["open"], df["high"], df["low"], df["vwap"]
        d = vwap - mfirst(vwap, 5)
        r1 = mavg_weighted(d, list(range(1, 8))).rolling(7, min_periods=1).rank(pct=True)
        mid = (high + low) / 2
        ratio = (low * 0.9 + low * 0.1 - vwap) / (op - mid).replace(0, np.nan)
        r2 = mrank(mavg_weighted(ratio, list(range(1, 12))), True, 7)
        val = ((r1 + r2) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
