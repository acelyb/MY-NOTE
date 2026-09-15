"""
GTJA191 Alpha83 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * RANK(COV(RANK(HIGH), RANK(VOLUME), 5))
DolphinDB:
  def gtjaAlpha83(high, vol){
      return -1 * rowRank(mcovar(rowRank(high, percent=true), rowRank(vol, percent=true), 5), percent=true)
  }

翻译要点:
- 与 alpha99(-RANK(COV(RANK(CLOSE),RANK(VOL),5))) 同构，仅把 CLOSE 换成 HIGH。
- rowRank(high)/rowRank(vol) 横截面排名 → rolling(5) 时序 pct rank 近似。
- mcovar(高价排名, 量排名, 5)=过去5日两者的时序协方差。
- 外层 rowRank 横截面排名 → rolling(5) 时序 pct rank 近似。
- 整体取负。

语义: 高价排名与量排名的5日协方差，截面排名后取负。
  与 alpha99(用收盘) 对比：alpha83 用高价，捕捉"高位放量"的协方差强度。
  两者量价协方差同族，可验证 HIGH vs CLOSE 口径哪个更有效。
  含三层横截面 rowRank 近似（三重有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha83Factor(FactorBase):
    name = "gtja_alpha83"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 10:  # rank(5) + cov(5) + rank(5)
            return None
        high, vol = df["high"], df["volume"]
        rh = high.rolling(5).rank(pct=True)
        rv = vol.rolling(5).rank(pct=True)
        cov5 = rh.rolling(5).cov(rv)
        ranked = cov5.rolling(5).rank(pct=True)
        val = (-ranked).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
