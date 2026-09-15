"""
GTJA191 Alpha6 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(SIGN(DELTA(((OPEN*0.85)+(HIGH*0.15))), 4))) * -1
DolphinDB:
  def gtjaAlpha6(open, high){
      delta = (open*0.85 + high*0.15) - mfirst((open*0.85+high*0.15), 5)
      return -1 * rowRank(sign(delta), percent=true)
  }

翻译要点:
- 合成价 P = OPEN*0.85 + HIGH*0.15（开盘为主、掺点最高价）
- DELTA(P,4) = P_t - P_{t-4}（mfirst(x,5) 即 x.shift(4)，注意 DolphinDB mfirst(x,n) 取 n-1 期前）
- SIGN 取符号（+1/0/-1），再横截面 RANK，整体取负
- 单标的口径：因子内 RANK 在 DolphinDB 是横截面（rowRank 跨股票）；
  本框架单标的 calc 返回标量，截面 RANK 由 IC 的 spearmanr 完成。
  故这里只返回 SIGN(DELTA(P,4)) 的符号值（已含取负语义？否——见下）。

方向勘误（重要）:
  研报公式整体 * -1，即 SIGN(DELTA(P,4)) 越大（合成价4日上涨）→ 因子越小。
  "值越大越好"约定下：因子 = -SIGN(DELTA(P,4))，即合成价4日下跌→因子大→预期涨（反转逻辑）。
  但单标的返回 -sign(delta) 的标量，截面 rank 由 spearmanr 处理，等价。
  最终方向以本池 IC 实测为准。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha6Factor(FactorBase):
    name = "gtja_alpha6"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 5:
            return None
        p = df["open"] * 0.85 + df["high"] * 0.15
        delta4 = p.iloc[-1] - p.iloc[-5]  # DELTA(P,4): 当日 - 4日前
        return -float(1 if delta4 > 0 else (-1 if delta4 < 0 else 0))
