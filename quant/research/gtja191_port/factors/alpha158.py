"""
GTJA191 Alpha158 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((HIGH-SMA(CLOSE,15,1)) - (LOW-SMA(CLOSE,15,1))) / CLOSE
DolphinDB:
  def gtjaAlpha158(close,high,low){
      A = ewmMean(close,alpha=2\\15)
      return ((high - A) - (low - A)) \\ close
  }

翻译要点:
- SMA(CLOSE,15,1)=研报递归指数加权 Y_t=(C_{t-1}*1+Y_{t-1}*14)/15，等价 EWM(alpha=1/15, adjust=False)
  DolphinDB ewmMean(close,alpha=2/15) —— 注意研报 SMA(A,n,m) 的 EWM 等价 alpha=m/n=1/15，
  但 DolphinDB 这里写 alpha=2/15。研报口径 SMA(CLOSE,15,1) 应 alpha=1/15，
  DolphinDB 用 2/15 是其实现差异（部分研报 SMA 用 2/(n+1) 的"标准EMA"口径，n=15→2/16，
  这里 2/15 近似）。以 DolphinDB 官方实现为准：alpha=2/15。
- A = EWM(close) 平滑收盘；分子 = (HIGH-A)-(LOW-A) = HIGH-LOW（A 相消！）。
  故研报公式 (HIGH-LOW)/CLOSE —— 即当日振幅率。
  DolphinDB 写法展开后 A 相消，数学上等价于 (high-low)/close。

语义: 当日振幅 (HIGH-LOW)/CLOSE。
  与 low_vol(60日收益std)、alpha167(12日正收益累加) 不同维度：
  这是单日价格振幅率（日内波动幅度，非多日收益波动）。
  振幅大=当日剧烈搏杀。研报未取负，原始=振幅越大因子越大。
  方向 IC 定夺（高振幅可能预示反转或波动溢酬）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, sma_recursive


class Alpha158Factor(FactorBase):
    name = "gtja_alpha158"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 2:
            return None
        close, high, low = df["close"], df["high"], df["low"]
        # 研报 SMA(CLOSE,15,1)→EWM alpha=1/15；DolphinDB 用 2/15。
        # 数学上 A 在分子相消，等价 (high-low)/close。这里仍按研报完整算式实现以保留语义，
        # 用 alpha=1/15（研报口径）；若需严格对齐 DolphinDB 改 2/15。
        A = sma_recursive(close, 15, 1)
        num = (high - A) - (low - A)
        denom = close.replace(0, pd.NA)
        val = (num / denom).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
