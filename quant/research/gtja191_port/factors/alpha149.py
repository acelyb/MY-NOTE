"""
GTJA191 Alpha149 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: REGBETA(RET*CONDITION, INDEX_RET*CONDITION, 252)，CONDITION=INDEX_CLOSE<DELAY(INDEX_CLOSE,1)
DolphinDB:
  def gtjaAlpha149(close, index_close){
      condition = iif(index_close<move(index_close,1), 1, NULL)
      return mbeta((close\move(close,1)-1)*condition, ((index_close\move(index_close,1)-1)*condition), 252)
  }

翻译要点:
- condition：指数下跌日=1，否则 NULL（NaN）。
- 个股收益 × condition、指数收益 × condition（仅指数下跌日保留收益，其余 NaN）。
- mbeta(个股下跌日收益, 指数下跌日收益, 252)=252日内个股对指数的下跌市 beta。
- 即"下行 beta"（downside beta），衡量个股在市场下跌时的相对弹性。
- 252日长窗，需 ≥253 行；NaN 由 condition 引入，mbeta 的 cov/var 会因 NaN 对减少有效样本。
  pandas rolling cov/var 默认跳过 NaN（pairwise），故有效对数决定可用性。
  下跌日约占半数（~114/252），默认 min_periods=n/2=126 会导致末窗 NaN；故传 60，
  在保足够样本（≥60 个下跌日对）的同时让近期可出值。

语义: 252日下行 beta（个股在指数下跌日的相对敏感度）。无横截面 rank，单标的可忠实还原。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, move, mbeta


class Alpha149Factor(FactorBase):
    name = "gtja_alpha149"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 253:
            return None
        close, ic = df["close"], df["index_close"]
        cond = (ic < move(ic, 1)).astype("float64").where(ic < move(ic, 1), float("nan"))
        stock_ret = (close / move(close, 1) - 1) * cond
        idx_ret = (ic / move(ic, 1) - 1) * cond
        val = mbeta(stock_ret, idx_ret, 252, min_periods=60).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
