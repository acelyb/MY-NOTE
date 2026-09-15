"""
GTJA191 Alpha10 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(MAX((RET<0 ? STD(RET,20) : CLOSE)^2, 5))
DolphinDB:
  def gtjaAlpha10(close){
      return rowRank(mmax(pow(iif((ratios(close) - 1) < 0, mstd(ratios(close) - 1, 20), close), 2), 5), percent=true)
  }

翻译要点:
- ratios(close)-1 = close_t/close_{t-1}-1 = 日收益率 RET
- 条件: RET<0(下跌日)取过去20日收益标准差 mstd(RET,20)；否则(涨/平)取当日 close
- 平方后取过去5日最大 mmax(...,5)
- rowRank(percent=true) 横截面排名。

单标的口径关键: rowRank 是横截面排名，单标的无法做。
  处理：用过去5日的时序 pct rank 近似（rolling(5).rank(pct=True)），
  与 alpha99 同思路。横截面排序最终由 IC 的 spearmanr 保证。
  注：单标的近似横截面 rank 本质有损，方向以 IC 实测定。

语义: 下跌日放大波动、涨日取价，取5日最大后排名——波动放大的极端值。
  与 low_vol(纯波动率)不同：这里只在下跌日计入波动，捕捉"下行风险/左尾波动"。
  方向 IC 定夺（研报口径未取负，原始=波动越大因子越大，可能反向）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha10Factor(FactorBase):
    name = "gtja_alpha10"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 25:  # 需 mstd(20) + mmax(5)
            return None
        close = df["close"]
        ret = close / close.shift(1) - 1  # RET
        # 下跌日取20日收益std，否则取当日close
        std20 = ret.rolling(20).std()
        import numpy as np
        a = pd.Series(np.where((ret < 0).values, std20.values, close.values), index=close.index)
        a = pd.to_numeric(a, errors="coerce")
        sq = a.pow(2)
        mx5 = sq.rolling(5).max()
        # 横截面 rowRank 近似为时序5日 pct rank
        ranked = mx5.rolling(5).rank(pct=True)
        val = ranked.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
