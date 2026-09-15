"""
GTJA191 Alpha167 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM((CLOSE-DELAY(CLOSE,1)>0 ? CLOSE-DELAY(CLOSE,1) : 0), 12)
DolphinDB:
  def gtjaAlpha167(close){
      return msum(iif((close - mfirst(close, 2)) > 0, close - mfirst(close, 2), 0), 12)
  }

翻译要点:
- CLOSE-DELAY(CLOSE,1) = 当日收盘 - 昨日收盘 = 日收益（绝对值，非百分比）
- 条件 >0 取正收益、否则取0 → 只累加上涨日的"涨了多少"
- SUM(...,12) = 过去12日正收益（绝对涨幅）之和

语义: 过去12日"只数阳线涨幅"的累加——衡量近期上涨力度（类似 OC 振幅但只计正）。
方向: 累计正涨幅越大→近期越强→动量逻辑（正向？）。IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_sum


class Alpha167Factor(FactorBase):
    name = "gtja_alpha167"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 13:
            return None
        close = df["close"]
        pos_ret = (close - close.shift(1)).clip(lower=0)  # 日正收益（涨的留、跌的归0）
        s = ts_sum(pos_ret, 12)                            # SUM(...,12)
        val = s.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
