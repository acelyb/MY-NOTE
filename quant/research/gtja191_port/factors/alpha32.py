"""
GTJA191 Alpha32 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (-1 * SUM(RANK(CORR(RANK(HIGH), RANK(VOLUME), 3)), 3))
DolphinDB:
  def gtjaAlpha32(high, vol){
      return -1 * msum(rowRank(mcorr(rowRank(high, percent=true), rowRank(vol, percent=true), 3), percent=true), 3)
  }

翻译要点:
- rowRank 横截面排名 → 单标的用 rolling pct rank 近似（有损）。
- 内层 rowRank(high)/rowRank(vol) 用 rolling(3) pct rank 近似。
- mcorr(高价排名, 量排名, 3)=过去3日两排名的时序相关。
- 外层 rowRank(corr, percent=true) 再用 rolling(3) pct rank 近似。
- msum(...,3)=ts_sum(...,3)，过去3日求和。
- 整体取负。
- 窗口选择：内层 rank 用 rolling(3)（与 corr 窗口一致），外层 rank 用 rolling(3)（与 sum 窗口一致）。

语义: 高价排名与量排名的3日相关，排名后取3日和，取负。
  高价与量同向（量价齐升）→ 相关高 → 排名后取和 → 取负 → 小值 → 预期未来收益低（反转）。
  含多层横截面 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, ts_sum


class Alpha32Factor(FactorBase):
    name = "gtja_alpha32"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 9:  # rank(3)+corr(3)+rank(3)+sum(3) 最深约 3+3+3
            return None
        high, vol = df["high"], df["volume"]
        rh = high.rolling(3, min_periods=1).rank(pct=True)   # rowRank(high) 近似
        rv = vol.rolling(3, min_periods=1).rank(pct=True)    # rowRank(vol) 近似
        corr3 = ts_corr(rh, rv, 3)            # mcorr(...,3)
        r_corr = corr3.rolling(3, min_periods=1).rank(pct=True)  # rowRank(corr) 近似
        val = (-ts_sum(r_corr, 3)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
