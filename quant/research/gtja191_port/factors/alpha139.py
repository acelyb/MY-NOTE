"""
GTJA191 Alpha139 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (-1 * CORR(OPEN, VOLUME, 10))
DolphinDB:
  def gtjaAlpha139(open, vol){
      return -1 * mcorr(open, vol, 10)
  }

翻译要点:
- mcorr(open,vol,10)=10日(开盘,量)时序相关，取负。
- 与 alpha1(alpha1 用日内收益) 不同：alpha139 直接用开盘价水平与量的相关。

语义: 开盘价与成交量的10日时序相关，取负。
      开盘走高+放量→相关高→取负后小→预期未来收益低（开盘量价同动反转）。
      方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr


class Alpha139Factor(FactorBase):
    name = "gtja_alpha139"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:  # corr(10)
            return None
        op, vol = df["open"], df["volume"]
        val = (-ts_corr(op, vol, 10)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
