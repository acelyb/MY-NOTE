"""
GTJA191 Alpha89 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: 2*(SMA(CLOSE,13,2)-SMA(CLOSE,27,2)-SMA(SMA(CLOSE,13,2)-SMA(CLOSE,27,2),10,2))
DolphinDB:
  def gtjaAlpha89(close){
      A = ewmMean(close,alpha=2\13)
      B = ewmMean(A,alpha=2\27)
      return 2*(A - B - ewmMean(A-B,alpha=2\10))
  }

翻译要点:
- SMA(x,n,m)=ewmMean(alpha=m/n)，adjust=False 递归式。SMA(CLOSE,13,2)→alpha=2/13。
- ⚠️ DolphinDB 源码实现与研报公式有歧义：研报第二项是 SMA(CLOSE,27,2)，
  源码却是 B=ewmMean(A,alpha=2/27)（对 A 再做 SMA，不是对 close）。
  本移植按 DolphinDB 源码忠实翻译（与"移植自 DolphinDB"约束一致），即第二项是 A 的27期SMA。
  这与 alpha155(纯量版) 不同——alpha155 的中间项是 ewmMean(vol,alpha=2/27) 对原序列，
  而 alpha89 源码第二项是对 A 做 ewmMean。差异在 docstring 注明，以 IC 实测定口径。
- 第三项 ewmMean(A-B, alpha=2/10)。整体 *2。

语义: 双均线(13/27)差再经10期平滑的 MACD 类柱状图(*2)。
  快线高于慢线且差值为正→因子大→预期未来收益高（趋势跟随）。
  翻译不确定点：研报与源码第二项口径不同，此处按源码。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ema_mean


class Alpha89Factor(FactorBase):
    name = "gtja_alpha89"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 5:  # ewm 递归只需少量起算，给 5 行稳定末位
            return None
        close = df["close"]
        A = ema_mean(close, 2 / 13)          # SMA(CLOSE,13,2)
        B = ema_mean(A, 2 / 27)              # 源码：SMA(A,27,2)（非 SMA(CLOSE,27,2)）
        diff = A - B
        smooth = ema_mean(diff, 2 / 10)      # SMA(A-B,10,2)
        val = (2 * (diff - smooth)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
