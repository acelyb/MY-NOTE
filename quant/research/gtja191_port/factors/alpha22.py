"""
GTJA191 Alpha22 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMEAN(((CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6)-DELAY((CLOSE-MEAN(CLOSE,6))/MEAN(CLOSE,6),3)),12,1)
DolphinDB:
  @state
  def gtjaAlpha22(close){
      A = (close - mavg(close,6)) \ mavg(close,6) - move((close - mavg(close,6)) \ mavg(close,6),3)
      return ewmMean(A,alpha=1\12)
  }

翻译要点:
- mavg(close,6)=ts_mean(close,6)；move(x,3)=delay(x,3)。
- A = 6日收盘偏离率 - 3日前的6日偏离率（偏离率的变化）。
- ewmMean(alpha=1/12)=ema_mean(A,1/12)=sma_recursive(A,12,1)（adjust=False 递归 EWM）。
- 除零：mavg(close,6)为0用 replace(0,np.nan) 规避 inf。
- 无横截面算子，单标的可忠实还原。

语义: 6日收盘偏离率的3日变化，经 EWM(1/12) 平滑。反映"价格相对均值的偏离动量"。
  属变形动量因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_mean, delay, ema_mean


class Alpha22Factor(FactorBase):
    name = "gtja_alpha22"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:  # mavg(6)+delay(3)+ewm
            return None
        close = df["close"]
        mean6 = ts_mean(close, 6).replace(0, np.nan)
        dev = (close - mean6) / mean6
        A = dev - delay(dev, 3)
        val = ema_mean(A, 1 / 12).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
