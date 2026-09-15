"""
GTJA191 Alpha97 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: STD(VOLUME,10)
DolphinDB:
  def gtjaAlpha97(vol){
      return mstd(vol, 10)
  }

翻译要点:
- mstd(vol,10)=10日成交量标准差。直接 rolling(10).std()。

语义: 10日成交量波动。量能波动大→因子大，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_std


class Alpha97Factor(FactorBase):
    name = "gtja_alpha97"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:  # std(10) 需要 10 行
            return None
        vol = df["volume"]
        val = ts_std(vol, 10).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
