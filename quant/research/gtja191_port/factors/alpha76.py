"""
GTJA191 Alpha76 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: STD(ABS((CLOSE/DELAY(CLOSE,1)-1))/VOLUME, 20) / MEAN(ABS((CLOSE/DELAY(CLOSE,1)-1))/VOLUME, 20)
DolphinDB:
  def gtjaAlpha76(close, vol){
      return mstd(abs(close \ mfirst(close, 2) - 1) \ vol, 20) \ mavg(abs(close \ mfirst(close, 2) - 1) \ vol, 20)
  }

翻译要点:
- mfirst(close,2)=昨收；close/昨收 - 1 = 日收益率。
- |日收益率|/VOLUME = 单位成交额对应的振幅（"每单位量的价格冲击"指标）。
- 分子: 过去20日该指标的标准差；分母: 过去20日该指标的均值。
- 比值 = 该指标的"变异系数 CV"（无量纲），高值=价格冲击不稳定。
- 分母为0时替换 nan；VOLUME 为0时替换 nan。
- 无横截面算子，单标的可忠实还原。

语义: 单位成交量价格冲击的20日变异系数(CV)。
  高值=价格冲击波动大（量价关系不稳定，流动性差）；低值=稳定。流动性维度。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha76Factor(FactorBase):
    name = "gtja_alpha76"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # mfirst(2) + mstd/mavg(20)
            return None
        close, vol = df["close"], df["volume"]
        r = (close / close.shift(1) - 1).abs()
        impact = r / vol.replace(0, np.nan)
        std20 = impact.rolling(20).std()
        mean20 = impact.rolling(20).mean().replace(0, np.nan)
        val = (std20 / mean20).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
