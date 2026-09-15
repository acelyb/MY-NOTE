"""
GTJA191 Alpha53 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: COUNT(CLOSE>DELAY(CLOSE,1), 12)/12*100
DolphinDB:
  def gtjaAlpha53(close){
      return mcount(iif(close > mfirst(close, 2), 1, NULL), 12) \ 12 * 100
  }

翻译要点:
- mfirst(close,2)=delay(close,1)=昨收。
- iif(close>昨收,1,NULL)：上涨日记1，否则记 NULL（DolphinDB mcount 忽略 NULL）。
- mcount(...,12)=过去12日内上涨日数量；除以12乘100=上涨日占比(%)。
- 与 alpha58 同源（窗口不同）：alpha53 用12日，alpha58 用20日。
- 无横截面算子，单标的可忠实还原。

语义: 12日内上涨日占比(%)。高值=近期频繁上涨，动量/情绪维度。方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha53Factor(FactorBase):
    name = "gtja_alpha53"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:  # mfirst(2) + mcount(12)
            return None
        close = df["close"]
        up = (close > close.shift(1)).astype(int)
        cnt = up.rolling(12).sum()
        val = (cnt / 12 * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
