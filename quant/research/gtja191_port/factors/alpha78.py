"""
GTJA191 Alpha78 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((HIGH+LOW+CLOSE)/3 - MA((HIGH+LOW+CLOSE)/3, 12)) / (0.015 * MEAN(ABS(CLOSE - MA((HIGH+LOW+CLOSE)/3, 12)), 12))
DolphinDB:
  def gtjaAlpha78(close, high, low){
      return ((high + low + close) \ 3 - mavg((high + low + close) \ 3, 12)) \
             \ (0.015 * mavg(abs(close - mavg((high + low + close) \ 3, 12)), 12))
  }

翻译要点:
- TP=(HIGH+LOW+CLOSE)/3 = 典型价。
- MA(TP,12)=12日典型价均值。
- 分子: TP - MA(TP,12) = 典型价相对其均值的偏离。
- 分母: 0.015 * MEAN(|CLOSE - MA(TP,12)|, 12) = 12日内"收盘价相对TP均线"绝对偏离的均值。
  ⚠️ 注意：标准 CCI 的分母是 MEAN(|TP - MA(TP)|, 12)，但研报/DolphinDB 这里用的是
  CLOSE 而非 TP（abs(close - mavg(TP,12))）。按 DolphinDB 字面翻译，保持口径一致。
- 比值即 CCI 指标（Constant Composite Index / 商品通道指标）变体。
- 分母为0时替换 nan。
- 无横截面算子，单标的可忠实还原。

语义: CCI 指标变体（分母用 CLOSE 而非 TP）。
  高值=典型价高于均线且波动稳定（强势突破），低值=低于均线。超买超卖维度。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha78Factor(FactorBase):
    name = "gtja_alpha78"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 24:  # mavg(TP,12) + mavg(abs(...),12) 需要 12+12-1=23，取24
            return None
        close, high, low = df["close"], df["high"], df["low"]
        tp = (high + low + close) / 3
        ma_tp12 = tp.rolling(12).mean()
        numer = tp - ma_tp12
        denom = (0.015 * (close - ma_tp12).abs().rolling(12).mean()).replace(0, np.nan)
        val = (numer / denom).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
