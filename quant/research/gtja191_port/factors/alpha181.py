"""
GTJA191 Alpha181 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM(((CLOSE/DELAY(CLOSE,1)-1)-MEAN(CLOSE/DELAY(CLOSE,1)-1,20)) - POW(INDEX_CLOSE-MEAN(INDEX_CLOSE,20),2), 20) / SUM(POW(INDEX_CLOSE-MEAN(INDEX_CLOSE,20),3), 20)
DolphinDB:
  def gtjaAlpha181(close, index_close){
      return msum(((close\move(close,1)-1)-mavg(close\move(close,1)-1,20)) - pow(index_close-mavg(index_close,20),2), 20) \ msum(pow(index_close-mavg(index_close,20),3), 20)
  }

翻译要点:
- stock_ret=close/前日-1=个股收益；mavg(stock_ret,20)=20日均值；去均值=个股超额收益成分。
- idx_dev=index_close - mavg(index_close,20)=指数偏离20日均值。
- 分子：msum( (个股去均值收益) - idx_dev^2 , 20)。
- 分母：msum( idx_dev^3 , 20)。
- 分子/分母。本质是对指数偏离的非线性（二阶/三阶）暴露的某种比率，研报原意近似个股对指数波动的协偏度暴露。
- 分母可能0或负，需防护（用 replace(0,NA) 防0除；负值保留）。

语义: 个股去均值收益与指数偏离平方之差的20日累加 / 指数偏离立方的20日累加。
  无横截面 rank，单标的可忠实还原。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, move, ts_mean, ts_sum


class Alpha181Factor(FactorBase):
    name = "gtja_alpha181"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 41:
            return None
        close, ic = df["close"], df["index_close"]
        stock_ret = close / move(close, 1) - 1
        sr_dm = stock_ret - ts_mean(stock_ret, 20)
        idx_dev = ic - ts_mean(ic, 20)
        num = ts_sum(sr_dm - idx_dev ** 2, 20)
        den = ts_sum(idx_dev ** 3, 20)
        val = (num / den.replace(0, pd.NA)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
