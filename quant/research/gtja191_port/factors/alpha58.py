"""
GTJA191 Alpha58 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: COUNT(CLOSE>DELAY(CLOSE,1), 20)/20*100
DolphinDB:
  def gtjaAlpha58(close){
      return mcount(iif(close > mfirst(close, 2), 1, NULL), 20) \ 20 * 100
  }

翻译要点:
- 与 alpha53 同源，窗口从12日改为20日。
- mfirst(close,2)=昨收；mcount 统计20日内上涨日数；除20乘100=上涨日占比(%)。
- 无横截面算子，单标的可忠实还原。

语义: 20日内上涨日占比(%)。高值=近期频繁上涨，动量/情绪维度。方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha58Factor(FactorBase):
    name = "gtja_alpha58"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # mfirst(2) + mcount(20)
            return None
        close = df["close"]
        up = (close > close.shift(1)).astype(int)
        cnt = up.rolling(20).sum()
        val = (cnt / 20 * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
