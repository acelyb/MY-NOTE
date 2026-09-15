"""
GTJA191 Alpha9 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA(((HIGH+LOW)/2-(DELAY(HIGH,1)+DELAY(LOW,1))/2)*(HIGH-LOW)/VOLUME, 7, 2)
DolphinDB:
  def gtjaAlpha9(high, low, vol){
      A = ((high + low) \ 2 - (mfirst(high, 2) + mfirst(low, 2)) \ 2) * (high - low) \ vol
      return ewmMean(A,alpha=2\7)
  }

翻译要点:
- (H+L)/2 = 当日中枢；(H1+L1)/2 = 昨日中枢。中枢移动 = 当日中枢-昨日中枢。
- (HIGH-LOW)/VOL = 振幅/量 = 单位量的价格振幅（量价动能）。
- A = 中枢移动 × (振幅/量) = "中枢方向 × 单位量振幅"。
- SMA(A,7,2)=研报递归加权 Y=(A*2+Y*5)/7，alpha=m/n=2/7。
  DolphinDB ewmMean(alpha=2/7)，一致。用 sma_recursive(A,7,2)（alpha=2/7）。
- vol=0 时 A 为 nan（停牌/零量），自然剔除。

语义: "中枢移动×单位量振幅"的7日递归平滑——量价动能的趋势值。
  中枢上移+单位量振幅大→A正大；中枢下移→A负。是"价动×量能"的动能维度。
  与 alpha11(收盘位置×量累加) 不同：alpha9 用中枢移动(非收盘位置)+振幅/量(单位量动能)。
  无横截面算子，单标的可忠实还原。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive


class Alpha9Factor(FactorBase):
    name = "gtja_alpha9"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 9:  # mfirst(2) + ewm 暖机
            return None
        high, low, vol = df["high"], df["low"], df["volume"]
        pivot = (high + low) / 2
        pivot1 = pivot.shift(1)
        vol_safe = vol.replace(0, np.nan)
        A = (pivot - pivot1) * (high - low) / vol_safe
        val = sma_recursive(A, 7, 2).iloc[-1]  # alpha=2/7
        if pd.isna(val):
            return None
        return float(val)
