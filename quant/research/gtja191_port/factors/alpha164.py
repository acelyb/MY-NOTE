"""
GTJA191 Alpha164 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  SMA((((CLOSE>DELAY(CLOSE,1))?1/(CLOSE-DELAY(CLOSE,1)):1)
       - MIN(((CLOSE>DELAY(CLOSE,1))?1/(CLOSE-DELAY(CLOSE,1)):1),12))
      / (HIGH-LOW)*100, 13, 2)
DolphinDB:
  def gtjaAlpha164(close, high, low){
      A = iif(close>move(close,1),1\(close-move(close,1)),1)
      B = (A - mmin(A,12))\(high-low)*100
      return ewmMean(B,alpha=2\13)
  }

翻译要点:
- move(close,1)=delay(close,1)=前日收盘。
- A = iif(close>dc1, 1/(close-dc1), 1): 上涨日取涨幅倒数,否则记1（研报笔误但忠实 DolphinDB）。
- mmin(A,12)=12日 A 的最小值。
- B = (A - mmin(A,12))/(high-low)*100，再用 SMA(B,13,2)=ewmMean(alpha=2/13) 平滑。
- 除零：close-dc1=0 时 1/0→inf（但 iif 条件 close>dc1 排除等于），high-low=0 时置 NaN。
- 最长链：delay(1)+mmin(12)+ewm(13 理论全历史) ≈ 13 行起算。

语义: 上涨日涨幅倒数相对12日最小的归一化(以日内振幅标尺)再指数平滑。
      高度非线性，方向以 IC 实测定。注意 1/(close-dc1) 在微涨时极大，可能产生异常值。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, sma_recursive, ts_min


class Alpha164Factor(FactorBase):
    name = "gtja_alpha164"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:  # delay(1) + mmin(12) + ewm(13)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        dc1 = close.shift(1)
        diff = close - dc1
        # iif(close>dc1, 1/diff, 1)：上涨取倒数，否则1
        A = pd.Series(np.where(close > dc1, 1.0 / diff, 1.0), index=df.index)
        amin = ts_min(A, 12)
        hl = (high - low).replace(0, np.nan)
        B = (A - amin) / hl * 100
        val = sma_recursive(B, 13, 2).iloc[-1]   # SMA(B,13,2)=ewmMean(alpha=2/13)
        if pd.isna(val):
            return None
        return float(val)
