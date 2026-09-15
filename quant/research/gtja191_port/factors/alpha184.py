"""
GTJA191 Alpha184 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (RANK(CORR(DELAY((OPEN - CLOSE),1), CLOSE, 200)) + RANK((OPEN - CLOSE)))
DolphinDB:
  def gtjaAlpha184(open, close){
      return rowRank(mcorr(mfirst(open - close, 2), close, 200), percent=true) + rowRank(open - close, percent=true)
  }

翻译要点:
- mfirst(open-close,2)=delay(open-close,1)=前日(开-收)。
- mcorr(前日(开-收), close, 200)=200日时序相关。
- 两项各自 rowRank 横截面排名 → rolling(10) 时序 pct rank 近似（含前导NaN用 min_periods=1）。
- 第一项：前日"开-收"与今日收盘的200日相关，排名。
- 第二项：当日"开-收"，排名。
- 最长链：delay(1)+mcorr(200)+rolling_rank(10) = 210 行起算。

语义: "前日开-收 vs 今日收盘"200日相关的排名 + 当日开-收的排名。
      日内反转(开-收)与后续收盘的共振，方向以 IC 实测定。
      含两层横截面 rowRank 近似（有损）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr


class Alpha184Factor(FactorBase):
    name = "gtja_alpha184"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 210:  # delay(1)+mcorr(200)+rolling_rank(10)
            return None
        op, close = df["open"], df["close"]
        oc = op - close
        doc1 = oc.shift(1)                          # DELAY((OPEN-CLOSE),1)
        corr200 = ts_corr(doc1, close, 200)         # CORR(., CLOSE, 200)
        r1 = corr200.rolling(10, min_periods=1).rank(pct=True)
        r2 = oc.rolling(10, min_periods=1).rank(pct=True)
        val = (r1 + r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
