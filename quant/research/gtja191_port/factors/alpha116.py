"""
GTJA191 Alpha116 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: REGBETA(CLOSE,SEQUENCE,20)
DolphinDB:
  def gtjaAlpha116(close){
      return linearTimeTrend(close,20)[1]
  }

翻译要点:
- linearTimeTrend(x,20)[1] = 过去20期 x 对 1..20 的线性回归斜率 = regbeta(x,20)。
- DolphinDB 示例脚本曾标"未完成"，但此函数体本身完整且只需 close 列，本移植直接实现。
- base.regbeta 在 rolling 内做最小二乘，NaN 任意位返回 NaN。

语义: 20日收盘价对时间序列的回归斜率。上涨趋势→斜率正→因子大→预期未来收益高（趋势动量）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, regbeta


class Alpha116Factor(FactorBase):
    name = "gtja_alpha116"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # regbeta(20) 需要 20 行
            return None
        close = df["close"]
        val = regbeta(close, 20).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
