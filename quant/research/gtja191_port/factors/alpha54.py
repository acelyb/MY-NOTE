"""
GTJA191 Alpha54 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * RANK((STD(ABS(CLOSE-OPEN)) + (CLOSE-OPEN)) + CORR(CLOSE, OPEN, 10))
DolphinDB:
  def gtjaAlpha54(open, close){
      return -1 * rowRank(mstd(abs(close - open),10) + close - open + mcorr(close, open, 10), percent=true)
  }

翻译要点:
- STD(ABS(CLOSE-OPEN), 10)=10日内|收-开|的标准差（日内振幅波动）。
- (CLOSE-OPEN)=当日日内涨幅。
- CORR(CLOSE, OPEN, 10)=10日内收盘价与开盘价的时序相关。
- 三者相加后做横截面 RANK；单标的用 rolling 时序 pct rank 近似（有损）。
  ⚠️ 含前导 NaN（std/corr 前9位为 NaN），必须用 min_periods=1 以与 DolphinDB 忽略 NaN 语义一致。
- 整体取负。
- 与 alpha99(-RANK(STD(HIGH,10))) 不同：alpha54 组合了日内振幅波动 + 当日日内涨幅 + 收开盘相关。
  是"日内形态"的多因子合成，强调日内价格行为而非日内极值。

语义: 日内振幅波动+当日日内涨幅+收盘盘口相关，横截面排名取负。
  日内振幅大+当日收阳+收开正相关→值大→取负后小→预期未来收益低（日内过激反转）。
  含一层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha54Factor(FactorBase):
    name = "gtja_alpha54"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:  # std(10)+corr(10)+rank(10)
            return None
        op, close = df["open"], df["close"]
        std10 = (close - op).abs().rolling(10).std()
        co = close - op
        corr10 = close.rolling(10).corr(op)
        composite = std10 + co + corr10
        # 含前导 NaN，min_periods=1 与 DolphinDB 忽略 NaN 语义一致
        r = composite.rolling(10, min_periods=1).rank(pct=True)
        val = (-r).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
