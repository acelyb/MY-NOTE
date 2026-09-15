"""
GTJA191 Alpha5 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * TSMAX(CORR(TSRANK(VOLUME,5), TSRANK(HIGH,5), 5), 3)
DolphinDB:
  def gtjaAlpha5(high, vol){
      return -1 * mmax(mcorr(mrank(vol, true, 5), mrank(high, true, 5), 5), 3)
  }

翻译要点:
- mrank(vol, true, 5)：过去5日的时序升序排名（与 TSRANK 同义，true=升序）。
  用 rolling(5).rank(pct=True) 近似（pct rank 升序）。
- mcorr(量排名, 高价排名, 5)：过去5日两个时序排名的相关。
- mmax(...,3)：取过去3日的最大相关。
- 整体取负。
- 这里 mrank 是时序排名（不是横截面 rowRank），单标的可忠实还原。

语义: 量与高价的时序排名相关性的近期峰值，取负。
  量价同向（放量且创新高）时相关高→取负后因子小→预期未来收益低（量价背离反转逻辑）。
  与 alpha99(量价协方差) 不同：这里是"量排名×高价排名"的近期峰值，强调高位放量。
  方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha5Factor(FactorBase):
    name = "gtja_alpha5"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:  # rank(5) + corr(5) + max(3)
            return None
        high, vol = df["high"], df["volume"]
        rv = vol.rolling(5).rank(pct=True)   # TSRANK(VOL,5)
        rh = high.rolling(5).rank(pct=True)  # TSRANK(HIGH,5)
        corr5 = rv.rolling(5).corr(rh)       # CORR(..., 5)
        mx3 = corr5.rolling(3).max()         # TSMAX(..., 3)
        val = mx3.iloc[-1]
        if pd.isna(val):
            return None
        return -float(val)
