"""
GTJA191 Alpha39 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (RANK(AVG(DELTA(CLOSE,2),8)) - RANK(AVG(CORR(VWAP*0.3+OPEN*0.7, SUM(AVG(VOL,180),37),14),12))) * -1
DolphinDB:
  def gtjaAlpha39(open, close, vol, vwap){
      return (rowRank(mavg(close-mfirst(close,3), 1..8), percent=true) - rowRank(mavg(mcorr(vwap*0.3+open*0.7, msum(mavg(vol,180),37), 14), 1..12), percent=true)) * (-1)
  }

翻译要点:
- mfirst(close,3)=delay(close,2)=DELTA(CLOSE,2)；close-mfirst(close,3)=2日涨跌额。
- mavg(X, 1..8)=以 1..8 为权重的加权移动均（线性递增窗权重），用 mavg_weighted 近似。
- 第二项：vwap*0.3+open*0.7 = VWAP与开盘加权；mavg(vol,180)=180日量均；msum(...,37)=37日累加；
  mcorr(混合价, 37日累加量均, 14)=14日时序相关；再 mavg(...,1..12) 加权均。
- 两层 rowRank 相减后取负。
- 长链：180+37+14，需 ≥231 行。

语义: 短期2日动量平滑排名 - VWAP/开盘混合价与长周期量结构的14日相关平滑排名，取负。
  多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mfirst, mavg_weighted, ts_mean, ts_sum, ts_corr


class Alpha39Factor(FactorBase):
    name = "gtja_alpha39"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 231:
            return None
        op, close, vol, vwap = df["open"], df["close"], df["volume"], df["vwap"]
        d2 = close - mfirst(close, 3)
        r1 = mavg_weighted(d2, list(range(1, 9))).rolling(8, min_periods=1).rank(pct=True)
        mix = vwap * 0.3 + op * 0.7
        vol180 = ts_mean(vol, 180)
        sv = ts_sum(vol180, 37)
        corr14 = ts_corr(mix, sv, 14)
        r2 = mavg_weighted(corr14, list(range(1, 13))).rolling(12, min_periods=1).rank(pct=True)
        val = ((r1 - r2) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
