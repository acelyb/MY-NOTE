"""
GTJA191 Alpha147 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: REGBETA(MEAN(CLOSE,12), SEQUENCE(12))
DolphinDB:
  def gtjaAlpha147(close){
      return linearTimeTrend(mavg(close,12),12)[1]
  }

翻译要点:
- mavg(close,12)=过去12日收盘均值；linearTimeTrend(x,12)[1]=对1..12的回归斜率=regbeta(x,12)。
- 即先对收盘做12日平滑，再求平滑序列对时间的12日回归斜率。
- DolphinDB 示例脚本曾标"未完成"，但此函数体完整且只需 close 列，本移植直接实现（与 alpha116 同类）。
- base.regbeta 在 rolling 内做最小二乘，NaN 任意位返回 NaN。
- 最长链 mavg(12)+regbeta(12)=23 行起算。

语义: 12日平滑收盘价对时间的回归斜率。上涨趋势→斜率正→因子大→预期未来收益高（平滑趋势动量）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, regbeta


class Alpha147Factor(FactorBase):
    name = "gtja_alpha147"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 23:  # mavg(12) + regbeta(12) = 23
            return None
        close = df["close"]
        mc12 = close.rolling(12).mean()
        val = regbeta(mc12, 12).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
