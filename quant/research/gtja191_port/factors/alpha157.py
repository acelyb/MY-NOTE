"""
GTJA191 Alpha157 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  (MIN(PROD(RANK(RANK(LOG(SUM(TSMIN(RANK(RANK((-1 * RANK(DELTA((CLOSE - 1), 5)))), 2), 1)))), 1), 5)
   + TSRANK(DELAY((-1 * RET), 6), 5))
DolphinDB:
  def gtjaAlpha157(close){
      return min(rowRank(rowRank(log(mmin(rowRank(rowRank(-1 * rowRank(close - 1 - mfirst(close - 1, 6),
                          percent=true), percent=true), percent=true), 2)), percent=true), percent=true), 5)
             + mrank(mfirst(-1 * (ratios(close) - 1), 7), true, 5)
  }

翻译要点:
- CLOSE-1 = 收盘价减常量1（研报笔误风格，忠实按 DolphinDB close-1）；mfirst(.,6)=delay(.,5)。
- DELTA((CLOSE-1),5) = (close-1) - delay(close-1,5)。
- -1*RANK(.) 后连续多层 rowRank（横截面→rolling pct rank 近似，含前导NaN用 min_periods=1）。
- mmin(.,2)=2日最小值；log(.)=自然对数。
- min(.,5)=mmin(.,5)=5日滚动最小值（DolphinDB滚动min，非逐元素）。
- 右侧 mrank(delay(-ret,6), true, 5) = ts_rank(delay(-ret,6), 5)。
- ⚠️ log 输入可能 ≤0 产生 NaN（多层排名后虽多为正但非保证）；按源码忠实翻译，NaN 守卫。
- 最长链：delay(5)+多层rank(用rolling5近似)+mmin(2)+mmin(5) ≈ 12；右侧 delay(6)+ts_rank(5)=11。

语义: 多层排名-log-滚动最小 的复合反转因子 + 负收益6日延迟的5日时序排名。
      公式高度非线性，方向以 IC 实测定。含多层横截面 rowRank 近似（有损），可能因 log 产生 NaN。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_rank


class Alpha157Factor(FactorBase):
    name = "gtja_alpha157"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 16:  # delay(5) + 滚动排名近似 + mmin(2) + mmin(5)
            return None
        close = df["close"]

        # 左侧
        cm1 = close - 1
        d5 = cm1 - cm1.shift(5)                           # DELTA((CLOSE-1),5)
        r1 = (-d5).rolling(5, min_periods=1).rank(pct=True)    # -1*RANK
        r2 = r1.rolling(5, min_periods=1).rank(pct=True)       # RANK
        r3 = r2.rolling(5, min_periods=1).rank(pct=True)       # RANK
        mm2 = r3.rolling(2).min()                          # TSMIN(.,2)
        lg = np.log(mm2)                                  # LOG
        r4 = lg.rolling(5, min_periods=1).rank(pct=True)       # RANK
        r5 = r4.rolling(5, min_periods=1).rank(pct=True)       # RANK
        left = r5.rolling(5).min()                        # MIN(.,5) = mmin

        # 右侧
        nret = -close.pct_change()                        # -1*RET
        dnret = nret.shift(6)                             # DELAY(-RET,6)
        right = ts_rank(dnret, 5)                         # TSRANK(.,5)

        val = (left + right).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
