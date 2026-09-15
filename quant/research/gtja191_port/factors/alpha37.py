"""
GTJA191 Alpha37 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (-1 * RANK(((SUM(OPEN,5)*SUM(RET,5)) - DELAY((SUM(OPEN,5)*SUM(RET,5)),10))))
DolphinDB:
  def gtjaAlpha37(open, close){
      return -1 * rowRank(msum(open, 5) * msum(ratios(close) - 1, 5)
                          - mfirst(msum(open, 5) * msum(ratios(close) - 1, 5), 11), percent=true)
  }

翻译要点:
- ratios(close)-1=ret(close)=日收益。
- msum(open,5)=ts_sum(open,5)；msum(ret,5)=ts_sum(ret,5)。
- A = SUM(OPEN,5)*SUM(RET,5)；mfirst(A,11)=delay(A,10)=DELAY(A,10)。
- 因子 = RANK(A - DELTA(A,10))，取负。
- rowRank 横截面排名 → rolling pct rank 近似（有损）。窗口用足够长（与 rank_cross 一致用全样本）。

语义: 5日开盘和×5日累计收益 的10日变化，排名取负。
  量(开盘和)×收益动量的中期变化，取负为反转逻辑。含横截面 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_sum, ret, delay


class Alpha37Factor(FactorBase):
    name = "gtja_alpha37"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # sum(5)+delay(10)+rank
            return None
        open_, close = df["open"], df["close"]
        A = ts_sum(open_, 5) * ts_sum(ret(close), 5)
        diff = A - delay(A, 10)
        r = diff.rolling(len(diff), min_periods=1).rank(pct=True)  # rowRank 近似（全样本窗口）
        val = (-r).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
