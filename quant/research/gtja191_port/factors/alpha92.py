"""
GTJA191 Alpha92 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MAX(RANK(AVG((CLOSE*0.35+VWAP*0.65-DELAY(CLOSE*0.35+VWAP*0.65,2)),3)), TSRANK(AVG(ABS(CORR(MEAN(VOL,180),CLOSE,13)),5),15)) * -1
DolphinDB:
  def gtjaAlpha92(close, vol, vwap){
      return max(rowRank(mavg(close*0.35+vwap*0.65 - mfirst(close*0.35+vwap*0.65,3), 1..3), percent=true), mrank(mavg(abs(mcorr(mavg(vol,180),close,13)), 1..5), true, 15)) * (-1)
  }

翻译要点:
- 第一项：mix=close*0.35+vwap*0.65；mix-mfirst(mix,3)=2日变化；mavg(...,1..3) 加权均；rowRank 排名。
- 第二项：mavg(vol,180)=180日量均；mcorr(量均, close, 13)=13日相关；abs；mavg(...,1..5) 加权均；
  mrank(...,true,15)=15日升序排名。
- 两项取 max 后取负。长链180+13。

语义: 价混合2日变化平滑排名 与 长均量-收盘相关绝对值的15日排名，取max后取负。
  rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mfirst, mavg_weighted, ts_mean, ts_corr, mrank


class Alpha92Factor(FactorBase):
    name = "gtja_alpha92"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 198:
            return None
        close, vol, vwap = df["close"], df["volume"], df["vwap"]
        mix = close * 0.35 + vwap * 0.65
        d = mix - mfirst(mix, 3)
        r1 = mavg_weighted(d, list(range(1, 4))).rolling(3, min_periods=1).rank(pct=True)
        c13 = ts_corr(ts_mean(vol, 180), close, 13)
        r2 = mrank(mavg_weighted(c13.abs(), list(range(1, 6))), True, 15)
        val = (pd.concat([r1, r2], axis=1).max(axis=1) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
