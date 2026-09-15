"""
GTJA191 Alpha162 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  (SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100
   - MIN(SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100,12))
  / (MAX(SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100,12)
     - MIN(SMA(MAX(CLOSE-DELAY(CLOSE,1),0),12,1)/SMA(ABS(CLOSE-DELAY(CLOSE,1)),12,1)*100,12))
DolphinDB:
  def gtjaAlpha162(close){
      A = max((close-move(close,1)),0)
      B = abs(close-move(close,1))
      C = ewmMean(A,alpha=1\12)
      D = ewmMean(B,alpha=1\12)
      return (C\D*100 - mmin((C\D*100),12)) \ (mmax((C\D*100),12) - mmin((C\D*100),12))
  }

翻译要点:
- move(close,1)=delay(close,1)=前日收盘。
- A=正向变动 MAX(涨跌,0); B=绝对变动 ABS(涨跌)。
- C=SMA(A,12,1)=ewmMean(alpha=1/12); D=SMA(B,12,1)=ewmMean(alpha=1/12)。
- RSI类指标 = C/D*100（0-100）。再取 12日 MIN/MAX 做归一化:
  (RSI - mmin(RSI,12)) / (mmax(RSI,12) - mmin(RSI,12)) = RSI 在 12日窗口的 (0,1) 归一化。
- 除零：窗口内 RSI 恒定(极差=0)时置 NaN。
- 最长链：delay(1)+ewm(12 理论全历史)+mmin/mmax(12) ≈ 13 行起算。

语义: RSI(12) 在 12日窗口的归一化位置(类 Stochastic-RSI)。
      RSI 处于近期高位→因子大→预期未来收益高(动量)或超买反转，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive, ts_max, ts_min


class Alpha162Factor(FactorBase):
    name = "gtja_alpha162"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:  # delay(1) + ewm(12) + mmin/mmax(12)
            return None
        close = df["close"]
        chg = close - close.shift(1)           # CLOSE-DELAY(CLOSE,1)
        A = chg.clip(lower=0)                  # MAX(涨跌,0)
        B = chg.abs()                          # ABS(涨跌)
        C = sma_recursive(A, 12, 1)            # SMA(A,12,1)=ewmMean(alpha=1/12)
        D = sma_recursive(B, 12, 1)            # SMA(B,12,1)
        rsi = (C / D.replace(0, np.nan)) * 100  # C/D*100
        rmin = ts_min(rsi, 12)
        rmax = ts_max(rsi, 12)
        spread = (rmax - rmin).replace(0, np.nan)
        val = ((rsi - rmin) / spread).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
