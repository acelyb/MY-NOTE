"""
GTJA191 Alpha48 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  -1 * RANK(SIGN(CLOSE-DELAY(CLOSE,1)) + SIGN(DELAY(CLOSE,1)-DELAY(CLOSE,2))
            + SIGN(DELAY(CLOSE,2)-DELAY(CLOSE,3))) * SUM(VOLUME,5)/SUM(VOLUME,20)
DolphinDB:
  def gtjaAlpha48(close, vol){
      return -1 * rowRank(sign(close - mfirst(close, 2)) + sign(mfirst(close, 2) - mfirst(close, 3))
                          + sign(mfirst(close, 3) - mfirst(close, 4)), percent=true) * msum(vol, 5) \ msum(vol, 20)
  }

翻译要点:
- mfirst(close,2)=昨收 close_{t-1}，mfirst(close,3)=close_{t-2}，mfirst(close,4)=close_{t-3}。
- 三阶符号和 = SIGN(C-C1)+SIGN(C1-C2)+SIGN(C2-C3)：过去3日逐日涨跌方向的累积符号 ∈[-3,3]。
  连涨→+3，连跌→-3，反映短期趋势"惯性强度"。
- rowRank(三阶符号和, percent=true)：横截面排名。单标的用 rolling(5) 时序 pct rank 近似（与 alpha10 同思路）。
- 乘以 SUM(VOL,5)/SUM(VOL,20)：5日量能/20日量能 = 短期放量程度。
- 整体取负。

语义: 短期趋势惯性(3日符号和) × 短期放量程度，取负。
  连涨且放量→三阶符号和高、量比高→取负后因子小→预期未来收益低（短期过热反转）。
  与 alpha84(20日OBV) 不同：alpha48 用"价格方向符号序列"而非带符号量，且乘放量比。
  含横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha48Factor(FactorBase):
    name = "gtja_alpha48"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 24:  # sign 序列 + rank(5) + msum(20)
            return None
        close, vol = df["close"], df["volume"]
        s1 = np.sign(close - close.shift(1))
        s2 = np.sign(close.shift(1) - close.shift(2))
        s3 = np.sign(close.shift(2) - close.shift(3))
        signs = s1 + s2 + s3  # 三阶符号和 ∈[-3,3]
        # rowRank 横截面排名 → 时序 pct rank 近似
        ranked = signs.rolling(5).rank(pct=True)
        vol_ratio = vol.rolling(5).sum() / vol.rolling(20).sum()
        val = (-ranked * vol_ratio).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
