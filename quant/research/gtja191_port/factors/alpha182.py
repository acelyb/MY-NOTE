"""
GTJA191 Alpha182 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: COUNT((CLOSE>OPEN AND INDEX_CLOSE>INDEX_OPEN) OR (CLOSE<OPEN AND INDEX_CLOSE<INDEX_OPEN), 20) / 20
DolphinDB:
  def gtjaAlpha182(open, close, index_open, index_close){
      return mcount(iif(iif(close>open,1,0)*iif(index_close>index_open,1,0) || iif(close<open,1,0)*iif(index_close<index_open,1,0),1,0), 20) \ 20
  }

翻译要点:
- 同向共动：(个股涨 且 指数涨) 或 (个股跌 且 指数跌) → 计数1。
- mcount(同向日, 20) / 20 = 过去20日个股与指数同向的比例。
- 衡量个股与市场的同动性（co-movement），高=跟随市场、低=独立行情。

语义: 20日内个股与指数同向涨跌的比例（同动率）。无横截面 rank，单标的可忠实还原。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha182Factor(FactorBase):
    name = "gtja_alpha182"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:
            return None
        op, close = df["open"], df["close"]
        io, ic = df["index_open"], df["index_close"]
        up_up = ((close > op) & (ic > io)).astype("float64")
        down_down = ((close < op) & (ic < io)).astype("float64")
        same = up_up + down_down  # 同向日=1（两条件互斥，不会=2）
        cnt = same.rolling(20).sum()
        val = (cnt / 20).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
