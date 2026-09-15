"""
GTJA191 Alpha21 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: REGBETA(MEAN(CLOSE,6),SEQUENCE(6))
DolphinDB:
  def gtjaAlpha21(close){
      return linearTimeTrend(close,6)[1]
  }

翻译要点:
- DolphinDB linearTimeTrend(x,n)[1]=回归斜率（[0]为截距）=regbeta(x,n)。
- 研报公式对 MEAN(CLOSE,6) 做 REGBETA；DolphinDB 实现直接对 close 做 linearTimeTrend。
  两者口径不同：研报是"6日均价序列 vs 1..6"斜率（但单点均价序列只有1个值，研报公式本身存疑），
  DolphinDB 是"过去6日close vs 1..6"的回归斜率。以 DolphinDB 为准（与 base.py regbeta 语义一致）。
- regbeta: 过去 n 期 close 对 1..n 的最小二乘斜率，反映6日内价格趋势陡峭度。
- 无横截面算子，单标的可忠实还原。

语义: 6日价格趋势斜率。斜率为正→上升趋势；为负→下降趋势。
  属趋势动量因子，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, regbeta


class Alpha21Factor(FactorBase):
    name = "gtja_alpha21"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:  # regbeta(6)
            return None
        close = df["close"]
        val = regbeta(close, 6).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
