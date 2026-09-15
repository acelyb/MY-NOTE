"""
GTJA191 Alpha23 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE:20),0),20,1)
           /(SMA((CLOSE>DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1)
             +SMA((CLOSE<=DELAY(CLOSE,1)?STD(CLOSE,20):0),20,1))*100
DolphinDB:
  def gtjaAlpha23(close){
      A = iif(close > move(close,1), mstd(close,20), 0)
      B = iif(close <= move(close,1), mstd(close,20), 0)
      return ewmMean(A,alpha=1\20)\(ewmMean(A,alpha=1\20) + ewmMean(B,alpha=1\20))*100
  }

翻译要点:
- move(close,1)=delay(close,1)；mstd(close,20)=ts_std(close,20)。
- A: 上涨日的20日std，否则0；B: 下跌/持平日的20日std，否则0。
- ewmMean(alpha=1/20)=ema_mean(...,1/20)=sma_recursive(...,20,1)（adjust=False 递归 EWM）。
- 因子 = EWM(A)/(EWM(A)+EWM(B))*100，即上涨日波动占比（%）。
- 除零：EWM(A)+EWM(B) 为0用 replace(0,np.nan) 规避 inf。
- 无横截面算子，单标的可忠实还原。

语义: 上涨日波动占近期总波动的比例（%）。值大→上涨波动主导（强势）；值小→下跌波动主导（弱势）。
  属波动结构因子，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, delay, ts_std, ema_mean


class Alpha23Factor(FactorBase):
    name = "gtja_alpha23"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # delay(1)+std(20)+ewm
            return None
        close = df["close"]
        prev = delay(close, 1)
        std20 = ts_std(close, 20)
        A = pd.Series(np.where(close > prev, std20, 0.0), index=close.index)
        B = pd.Series(np.where(close <= prev, std20, 0.0), index=close.index)
        ewm_a = ema_mean(A, 1 / 20)
        ewm_b = ema_mean(B, 1 / 20)
        denom = (ewm_a + ewm_b).replace(0, np.nan)
        val = (ewm_a / denom * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
