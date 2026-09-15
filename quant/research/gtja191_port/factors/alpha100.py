"""
GTJA191 Alpha100 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: STD(VOLUME,20)
DolphinDB:
  def gtjaAlpha100(vol){
      return mstd(vol, 20)
  }

翻译要点:
- mstd(vol,20)=20日成交量标准差。直接 rolling(20).std()。

语义: 20日成交量波动。量能波动大→因子大，方向以 IC 实测定。
  与 alpha97(10日) 同族，仅窗口=20。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_std


class Alpha100Factor(FactorBase):
    name = "gtja_alpha100"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # std(20) 需要 20 行
            return None
        vol = df["volume"]
        val = ts_std(vol, 20).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
