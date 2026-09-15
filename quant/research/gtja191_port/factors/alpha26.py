"""
GTJA191 Alpha26 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM(CLOSE,7)/7 - CLOSE + CORR(VWAP, DELTA(CLOSE,5), 230)
DolphinDB:
  def gtjaAlpha26(close, vwap){
      return msum(close,7)\7 - close + mcorr(vwap, mfirst(close,6), 230)
  }

翻译要点:
- msum(close,7)/7 - close = 7日均价与当前收盘的偏离（反转：高于均价→正）。
- mfirst(close,6)=delay(close,5)=DELTA(CLOSE,5)。
- mcorr(vwap, DELTA(close,5), 230)=过去230日 VWAP 与5日涨跌额的时序相关（长周期量价结构）。
- 230日长窗，需 ≥236 行数据；真实数据1613行 OK，但样本量（时点数）会受限。

语义: 短期均价偏离 + 长周期 VWAP-动量 相关。无横截面 rank，单标的可忠实还原。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_sum, ts_corr, mfirst


class Alpha26Factor(FactorBase):
    name = "gtja_alpha26"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 236:  # mcorr(230) + mfirst(6) 对齐
            return None
        close, vwap = df["close"], df["vwap"]
        val = (ts_sum(close, 7) / 7 - close + ts_corr(vwap, mfirst(close, 6), 230)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
