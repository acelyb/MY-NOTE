"""
GTJA191 Alpha40 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM(CLOSE>DELAY(CLOSE,1)?VOLUME:0,26) / SUM(CLOSE<=DELAY(CLOSE,1)?VOLUME:0,26) * 100
DolphinDB:
  def gtjaAlpha40(close, vol){
      return msum(iif(close > mfirst(close, 2), vol, 0), 26) \\ msum(iif(close <= mfirst(close, 2), vol, 0), 26) * 100
  }

翻译要点:
- mfirst(close,2) = close_{t-1}（窗口2的最旧值对齐到当前即前1期）
- 上涨日(close>昨收)量累加 / 下跌平日量累加 × 100 —— 26日上涨量/下跌量比
- 纯量价方向累积，无横截面算子，单标的可忠实还原。

语义: 过去26日"上涨日成交量"与"下跌日成交量"之比×100。
  量价同向：价涨量增>价跌量增 → 因子大；说明上涨放量、下跌缩量（健康上攻）。
  研报未取负，原始=上涨量占优因子越大。方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha40Factor(FactorBase):
    name = "gtja_alpha40"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 27:
            return None
        close, vol = df["close"], df["volume"]
        prev = close.shift(1)
        up = pd.Series(pd.to_numeric((close > prev), errors="coerce"), index=close.index) * vol
        dn = pd.Series(pd.to_numeric((close <= prev), errors="coerce"), index=close.index) * vol
        up_sum = up.rolling(26).sum()
        dn_sum = dn.rolling(26).sum()
        denom = dn_sum.replace(0, pd.NA)
        val = (up_sum / denom * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
