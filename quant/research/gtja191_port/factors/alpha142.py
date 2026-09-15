"""
GTJA191 Alpha142 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  (((-1 * RANK(TSRANK(CLOSE,10))) * RANK(DELTA(DELTA(CLOSE,1),1))) * RANK(TSRANK((VOLUME/MEAN(VOLUME,20)),5)))
DolphinDB:
  def gtjaAlpha142(close, vol){
      return -1 * rowRank(mrank(close, true, 10), percent=true)
               * rowRank(close - mfirst(close, 2) - mfirst(close - mfirst(close, 2), 2), percent=true)
               * rowRank(mrank(vol \ mavg(vol, 20), true, 5), percent=true)
  }

翻译要点:
- TSRANK(CLOSE,10)=ts_rank(close,10)；外层 RANK → rolling pct rank（含前导NaN用 min_periods=1）。
- DELTA(DELTA(CLOSE,1),1) = delta(close,1) - delay(delta(close,1),1)
  DolphinDB: close-mfirst(close,2) [=delta1] 再减 mfirst(delta1,2)[=delay(delta1,1)]。
- TSRANK(VOL/MEAN(VOL,20),5)=ts_rank(vol/mavg(vol,20), 5)；外层 RANK → rolling pct rank。
- 三项相乘取负。
- 最长链：mavg(20)+mrank(5) ≈ 25；mrank(10) 项 ≈ 10；delta 项需 delay(1)+delay(1)。

语义: "收盘时序排名的排名" × "收盘二阶差分排名" × "量比时序排名的排名"，取负。
      价量同向+二阶动量的三因子交叉，方向以 IC 实测定。
      含多层横截面 rowRank 近似（有损）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_rank


class Alpha142Factor(FactorBase):
    name = "gtja_alpha142"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 25:  # mavg(20)+mrank(5)
            return None
        close, vol = df["close"], df["volume"]

        tsr_c = ts_rank(close, 10)
        r1 = tsr_c.rolling(10, min_periods=1).rank(pct=True)

        delta1 = close - close.shift(1)
        dd = delta1 - delta1.shift(1)   # DELTA(DELTA(CLOSE,1),1)
        r2 = dd.rolling(10, min_periods=1).rank(pct=True)

        vol_ratio = vol / vol.rolling(20).mean()
        tsr_vr = ts_rank(vol_ratio, 5)
        r3 = tsr_vr.rolling(10, min_periods=1).rank(pct=True)

        val = (-r1 * r2 * r3).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
