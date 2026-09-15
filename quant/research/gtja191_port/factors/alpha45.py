"""
GTJA191 Alpha45 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK((CLOSE*0.6+OPEN*0.4-DELAY((CLOSE*0.6+OPEN*0.4),1))) * RANK(CORR(VWAP, MEAN(VOLUME,150),15))
DolphinDB:
  def gtjaAlpha45(open, close, vol, vwap){
      return rowRank(close*0.6+open*0.4 - mfirst(close*0.6+open*0.4,2), percent=true) * rowRank(mcorr(vwap, mavg(vol,150),15), percent=true)
  }

翻译要点:
- mix=close*0.6+open*0.4（收盘主导的价混合）；mfirst(mix,2)=delay(mix,1)=前一日mix；
  mix-前值=1日变化。
- mavg(vol,150)=150日量均；mcorr(vwap, 量均, 15)=15日 VWAP 与长均量的时序相关。
- 两层 rowRank 相乘。

语义: 价混合1日变化排名 × VWAP-长均量 相关排名。长链150+15。rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mfirst, ts_mean, ts_corr


class Alpha45Factor(FactorBase):
    name = "gtja_alpha45"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 165:
            return None
        op, close, vol, vwap = df["open"], df["close"], df["volume"], df["vwap"]
        mix = close * 0.6 + op * 0.4
        r1 = (mix - mfirst(mix, 2)).rolling(15, min_periods=1).rank(pct=True)
        corr15 = ts_corr(vwap, ts_mean(vol, 150), 15)
        r2 = corr15.rolling(15, min_periods=1).rank(pct=True)
        val = (r1 * r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
