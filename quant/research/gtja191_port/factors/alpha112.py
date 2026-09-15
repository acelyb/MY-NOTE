"""
GTJA191 Alpha112 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (SUM(CLOSE-DELAY(CLOSE,1)>0 ? CLOSE-DELAY(CLOSE,1) : 0, 12)
          - SUM(CLOSE-DELAY(CLOSE,1)<0 ? |CLOSE-DELAY(CLOSE,1)| : 0, 12))
         / (SUM(...正...,12) + SUM(...负...,12)) * 100
DolphinDB:
  def gtjaAlpha112(close){
      sum1 = msum(iif((close - mfirst(close, 2)) > 0, close - mfirst(close, 2), 0), 12)
      sum2 = msum(iif((close - mfirst(close, 2)) < 0, abs(close - mfirst(close, 2)), 0), 12)
      return (sum1 - sum2) \\ (sum1 + sum2) * 100
  }

翻译要点:
- d = CLOSE - DELAY(CLOSE,1) = 日收益额（绝对价差，非比率）
- sum1 = 过去12日正收益额之和；sum2 = 过去12日负收益额绝对值之和
- (sum1 - sum2)/(sum1 + sum2)*100 —— 即经典 RSI 口径：100 * 上行幅度/(上行+下行幅度)
- 无横截面算子，单标的可忠实还原。值域约[-100,100]。

语义: 12日 RSI（用绝对价差而非比率，等价 RSI 思路）。
  >0 偏强、<0 偏弱。RSI 高=近期涨幅占优（超买预期反转），低=超卖预期反弹。
  与 alpha167(12日正收益累加) 同窗口但口径不同：
  alpha167 只累加正收益(绝对上行强度)，alpha112 是上行/(上行+下行)归一化的 RSI。
  方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha112Factor(FactorBase):
    name = "gtja_alpha112"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:
            return None
        close = df["close"]
        d = close - close.shift(1)  # 日收益额
        pos = d.clip(lower=0)
        neg = (-d).clip(lower=0)  # 负收益额的绝对值
        sum1 = pos.rolling(12).sum()
        sum2 = neg.rolling(12).sum()
        denom = (sum1 + sum2).replace(0, pd.NA)
        val = ((sum1 - sum2) / denom * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
