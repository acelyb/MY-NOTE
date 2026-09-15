"""
GTJA191 Alpha42 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * RANK(STD(HIGH,10)) * CORR(HIGH, VOLUME, 10)
  （研报与 DolphinDB 一致：高价波动率排名 × 高价量相关，取负）
DolphinDB:
  def gtjaAlpha42(high, vol){
      return -1 * rowRank(mstd(high, 10), percent=true) * mcorr(high, vol, 10)
  }

翻译要点:
- mstd(high,10)=10日高价标准差（高价波动）；rowRank 横截面排名 → rolling(10) 时序 pct rank 近似。
- mcorr(high, vol, 10)=过去10日(高价 vs 成交量原值)的时序相关。
- 两者相乘取负。
- 与 alpha104((CORR变化)×STD(CLOSE)rank) 不同：alpha42 用高价波动×高价量相关水平(非变化)。

语义: "高价波动率排名" × "高价-量10日相关"，取负。
  高价剧烈波动 + 高价与量正相关(放量推高) → 乘积大 → 取负后小 → 预期未来收益低
  （高位高波动放量反转）。量价相关×波动交叉维度。
  含一层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha42Factor(FactorBase):
    name = "gtja_alpha42"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # std(10) + rank(10) + corr(10)
            return None
        high, vol = df["high"], df["volume"]
        std10 = high.rolling(10).std()
        r = std10.rolling(10).rank(pct=True)
        corr10 = high.rolling(10).corr(vol)
        val = (-r * corr10).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
