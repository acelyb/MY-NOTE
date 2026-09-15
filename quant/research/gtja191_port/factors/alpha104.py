"""
GTJA191 Alpha104 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  -1 * (CORR(HIGH,VOL,5) - DELTA(CORR(HIGH,VOL,5),5)) * RANK(STD(CLOSE,20))
DolphinDB:
  def gtjaAlpha104(close, high, vol){
      return -1 * (mcorr(high, vol, 5) - mfirst(mcorr(high, vol, 5), 5))
              * rowRank(mstd(close, 20), percent=true)
  }

翻译要点:
- mcorr(high, vol, 5)=过去5日(高价 vs 成交量)的时序相关 c。
- mfirst(c, 5)=5日前的 c，故 (c - c_{t-5}) = DELTA(c, 5) = 高价量相关的5日变化。
- mstd(close,20)=20日收盘标准差；rowRank(...,percent=true) 横截面排名。
  单标的用 rolling(5) 时序 pct rank 近似（与 alpha10 同思路，有损）。
- 整体取负：(量高相关的变化) × (波动率排名) × -1。

语义: "高价-量相关性的5日变化" × "波动率排名"，取负。
  量价相关上升(放量推高)+高波动 → 取负后因子小 → 预期未来收益低（高位放量高波动反转）。
  与 alpha99(量价协方差水平) 不同：alpha104 看"量高相关的变化(动量)"×波动率，是量价动态×波动交叉。
  含横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha104Factor(FactorBase):
    name = "gtja_alpha104"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 25:  # mcorr(5) + delta(5) + mstd(20) + rank(5)
            return None
        close, high, vol = df["close"], df["high"], df["volume"]
        c = high.rolling(5).corr(vol)              # CORR(HIGH,VOL,5)
        dc = c - c.shift(5)                        # DELTA(c, 5)
        std20 = close.rolling(20).std()
        r = std20.rolling(5).rank(pct=True)        # RANK(STD(CLOSE,20)) 近似
        val = (-(dc) * r).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
