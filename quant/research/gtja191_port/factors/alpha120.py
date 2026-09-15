"""
GTJA191 Alpha120 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(VWAP-CLOSE) / RANK(VWAP+CLOSE)
DolphinDB:
  def gtjaAlpha120(close, vwap){
      return rowRank(vwap - close, percent=true) \ rowRank(vwap + close, percent=true)
  }

翻译要点:
- vwap-close=VWAP偏离收盘（核心 alpha：尾盘相对均价的偏离，正=收盘低于均价/尾盘杀跌）。
- vwap+close=VWAP与收盘之和（价格水平代理）。
- 两项各自 rowRank 后相除。分母排名∈(0,1) 不为0，安全。

语义: VWAP-收盘偏离排名 / 价格水平排名。纯 VWAP-CLOSE 偏离信号的标准化。
  横截面 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha120Factor(FactorBase):
    name = "gtja_alpha120"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:
            return None
        close, vwap = df["close"], df["vwap"]
        r1 = (vwap - close).rolling(10, min_periods=1).rank(pct=True)
        r2 = (vwap + close).rolling(10, min_periods=1).rank(pct=True)
        val = (r1 / r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
