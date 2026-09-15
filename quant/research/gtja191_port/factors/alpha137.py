"""
GTJA191 Alpha137 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式(长，见 DolphinDB 注释):
  16*(CLOSE-DELAY(CLOSE,1)+(CLOSE-OPEN)/2+DELAY(CLOSE,1)-DELAY(OPEN,1))
  / ( iif(con1, A, iif(con2, B, C)) ) * MAX(ABS(HIGH-DELAY(CLOSE,1)), ABS(LOW-DELAY(CLOSE,1)))
  其中：
    con1 = ABS(HIGH-DC1)>ABS(LOW-DC1) && ABS(HIGH-DC1)>ABS(HIGH-DL1)
    con2 = ABS(LOW-DC1)>ABS(HIGH-DL1) && ABS(LOW-DC1)>ABS(HIGH-DC1)
    A = ABS(HIGH-DC1) + ABS(LOW-DC1)/2 + ABS(DC1-DO1)/4
    B = ABS(LOW-DC1) + ABS(HIGH-DC1)/2 + ABS(DC1-DO1)/4
    C = ABS(HIGH-DL1) + ABS(DC1-DO1)/4
  (DC1=DELAY(CLOSE,1), DO1=DELAY(OPEN,1), DL1=DELAY(LOW,1))
DolphinDB:
  def gtjaAlpha137(open, close, high, low){...}

翻译要点:
- DolphinDB `\` 优先级高于 `+`，故 abs(x)\2 先除后加：abs(low-dc1)/2。
- tmp1 = 16*(close-dc1+(close-open)/2+dc1-do1)，含 dc1 抵消，但忠实翻译不化简。
- tmp2 为三段条件取值（iif 嵌套），按真实波幅中最大振幅分支选择加权。
- tmp3 = max(abs(high-dc1), abs(low-dc1))。
- 除零：tmp2 可能为 0 时置 NaN。
- 需 delay(1) 各项，2 行起算。

语义: 真实波幅加权的日内动量(类 Williams/Chaikin 振荡)。方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha137Factor(FactorBase):
    name = "gtja_alpha137"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 2:  # 仅需 delay(1)
            return None
        op, close, high, low = df["open"], df["close"], df["high"], df["low"]
        dc1 = close.shift(1)   # DELAY(CLOSE,1)
        do1 = op.shift(1)      # DELAY(OPEN,1)
        dl1 = low.shift(1)     # DELAY(LOW,1)

        tmp1 = 16 * (close - dc1 + (close - op) / 2 + dc1 - do1)
        ah = (high - dc1).abs()
        al = (low - dc1).abs()
        adh = (high - dl1).abs()
        adco = (dc1 - do1).abs()
        con1 = (ah > al) & (ah > adh)
        con2 = (al > adh) & (al > ah)
        br1 = ah + al / 2 + adco / 4
        br2 = al + ah / 2 + adco / 4
        br3 = adh + adco / 4
        tmp2 = pd.Series(np.where(con1, br1, np.where(con2, br2, br3)), index=df.index)
        tmp3 = np.maximum(ah, al)
        val = (tmp1 / pd.Series(tmp2, index=df.index).replace(0, np.nan) * pd.Series(tmp3, index=df.index)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
