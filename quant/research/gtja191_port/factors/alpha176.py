"""
GTJA191 Alpha176 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  CORR(RANK((CLOSE-MIN(LOW,12))/(MAX(HIGH,12)-MIN(LOW,12))), RANK(VOLUME), 6)
DolphinDB:
  def gtjaAlpha176(close, high, low, vol){
      return mcorr(rowRank((close - mmin(low, 12)) \ (mmax(high, 12) - mmin(low, 12)), percent=true), rowRank(vol, percent=true), 6)
  }

翻译要点:
- (CLOSE-MIN(LOW,12))/(MAX(HIGH,12)-MIN(LOW,12)) = 收盘在12日(高,低)区间的位置∈[0,1]（随机%K式）。
- rowRank(区间位置)/rowRank(vol) 横截面排名 → rolling(6) 时序 pct rank 近似。
- mcorr(位置排名, 量排名, 6)=过去6日两者的时序相关。
- 无外层取负（研报原式为正）。

语义: 收盘在12日区间的位置排名 与 量排名 的6日时序相关。
  位置高(接近12日高)且放量→相关高→因子大。捕捉"强势位置×放量"的同步性。
  与 alpha91(回撤×量低相关) 不同：alpha176 用"区间位置"而非回撤，且不取负。
  含两层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha176Factor(FactorBase):
    name = "gtja_alpha176"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 18:  # min/max(12) + rank(6) + corr(6)
            return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        lo12 = low.rolling(12).min()
        hi12 = high.rolling(12).max()
        rng = (hi12 - lo12).replace(0, np.nan)
        pos = (close - lo12) / rng
        r1 = pos.rolling(6).rank(pct=True)
        r2 = vol.rolling(6).rank(pct=True)
        val = r1.rolling(6).corr(r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
