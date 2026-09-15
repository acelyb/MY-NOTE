"""
GTJA191 Alpha4 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  RANK( IF(cond1, -1, IF(cond2, 1, IF((VOL/MA(VOL,20)>=1), 1, -1))) )
  其中 cond1 = MA(CLOSE,8)+STD(CLOSE,8) < MA(CLOSE,2)
       cond2 = MA(CLOSE,2) < MA(CLOSE,8) - STD(CLOSE,8)
DolphinDB:
  def gtjaAlpha4(close, vol){
      cond1 = ((msum(close, 8) \ 8 + mstd(close, 8)) < (msum(close, 2) \ 2))
      cond2 = ((msum(close, 2) \ 2) < (msum(close, 8) \ 8 - mstd(close, 8)))
      iffalse2 = iif((1 < (vol \ mavg(vol, 20))) || (vol \ mavg(vol, 20) == 1), 1, -1)
      iffalse1 = iif(cond2, 1, iffalse2)
      return iif(cond1, -1, iffalse1)
  }

翻译要点:
- msum(close,8)/8 = 8日均值；mstd(close,8)=8日标准差；msum(close,2)/2=2日均值。
- cond1: 短期(2日)均线突破上轨(8日均线+8日std) → -1（短期已超涨，看跌）。
- cond2: 短期(2日)均线跌破下轨(8日均线-8日std) → +1（短期已超跌，看涨）。
- 否则看量能：放量(VOL/MA20>=1) → +1，缩量 → -1。
- 研报外层 RANK 横截面排名。DolphinDB 实现未写外层 RANK（直接返回 -1/0/1 三值），
  即把状态信号直接当因子。这里以 DolphinDB 为准返回三态值。
- 无窗口算子除 std/mean 外无横截面算子，单标的可忠实还原。

语义: 布林带式趋势状态机——突破上轨看跌、跌破下轨看涨、区间内看量能放大。
  本质是均值回复(超涨跌反转)+量能确认的组合信号。方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha4Factor(FactorBase):
    name = "gtja_alpha4"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # mstd(8) 与 vol/mavg(vol,20) 都需 ≥20
            return None
        close, vol = df["close"], df["volume"]
        ma8 = close.rolling(8).mean()
        std8 = close.rolling(8).std()
        ma2 = close.rolling(2).mean()
        mavol20 = vol.rolling(20).mean()

        cond1 = (ma8 + std8) < ma2
        cond2 = ma2 < (ma8 - std8)
        vol_ratio = vol / mavol20
        iffalse2 = (vol_ratio >= 1).astype(int) * 2 - 1  # True→1, False→-1
        # iffalse1 = iif(cond2, 1, iffalse2)
        iffalse1 = pd.Series(np.where(cond2.values, 1, iffalse2.values), index=close.index)
        # ret = iif(cond1, -1, iffalse1)
        ret = pd.Series(np.where(cond1.values, -1, iffalse1.values), index=close.index)
        val = ret.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
