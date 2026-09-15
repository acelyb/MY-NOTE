"""
GTJA191 Alpha141 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * RANK(CORR(RANK(HIGH), RANK(MEAN(VOLUME,15)), 9))
DolphinDB:
  def gtjaAlpha141(high, vol){
      return rowRank(mcorr(rowRank(high, percent=true), rowRank(mavg(vol, 15), percent=true), 9), percent=true) * (-1)
  }

翻译要点:
- mavg(vol,15)=15日均量；rowRank(高价)/rowRank(15日均量) 横截面排名 → rolling 近似。
- mcorr(高价排名, 均量排名, 9)=过去9日两者的时序相关。
- 外层 rowRank 横截面排名 → rolling(9) 时序 pct rank 近似。
- 整体取负。
- 与 alpha62/83 不同：用15日均量(而非当日量)，捕捉高价与"中期量能水平"的相关。

语义: 高价排名与15日均量排名的9日相关，截面排名后取负。
  高价持续上行+均量持续放大→相关高→取负后小→预期未来收益低（中期量价同步过热反转）。
  含三层横截面 rowRank 近似（三重有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha141Factor(FactorBase):
    name = "gtja_alpha141"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 33:  # mavg(15) + rank(9) + corr(9) + rank(9)
            return None
        high, vol = df["high"], df["volume"]
        mavol15 = vol.rolling(15).mean()
        rh = high.rolling(9).rank(pct=True)
        rm = mavol15.rolling(9).rank(pct=True)
        corr9 = rh.rolling(9).corr(rm)
        ranked = corr9.rolling(9).rank(pct=True)
        val = (-ranked).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
