"""
GTJA191 Alpha115 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  RANK(CORR(((HIGH*0.9)+(CLOSE*0.1)), MEAN(VOLUME,30), 10))
  ^ RANK(CORR(TSRANK(((HIGH+LOW)/2),4), TSRANK(VOLUME,10),7))
DolphinDB:
  def gtjaAlpha115(close, high, low, vol){
      return pow(rowRank(mcorr(high * 0.9 + close * 0.1, mavg(vol, 30), 10), percent=true),
                 rowRank(mcorr(mrank((high + low) \ 2, true, 4), mrank(vol, true, 10), 7), percent=true))
  }

翻译要点:
- 底数 = RANK(CORR(HIGH*0.9+CLOSE*0.1, MEAN(VOL,30), 10))
  = 过去10日 (高收加权价 vs 30日量均值) 的时序相关，再做横截面排名。
- 指数 = RANK(CORR(TSRANK((H+L)/2,4), TSRANK(VOL,10), 7))
  = 过去7日 ((H+L)/2的4日时序排名 vs VOL的10日时序排名) 的相关，再做横截面排名。
- rowRank 横截面 → rolling 时序 pct rank 近似（有损）。
- TSRANK 用 base.ts_rank 对应；mrank(x,true,n) 即时序 pct rank。
- ⚠️ pow 底数为负且指数为非整数时会产生 NaN（pandas 默认行为）。
  含多层前导 NaN，rowRank 用 min_periods=1。

语义: 量价相关(长窗) 的排名 为底，量价时序排名相关(短窗) 的排名 为指数的幂。
  底数大(量价正相关)+指数大(量价排名同动)→因子大→预期未来收益高。
  含多层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_corr, ts_rank


class Alpha115Factor(FactorBase):
    name = "gtja_alpha115"

    def calc(self, df: pd.DataFrame) -> float | None:
        # 最长链: mavg(30)+mcorr(10) → 40；mrank(10)+mcorr(7) → 17；rowRank 滚动
        if len(df) < 40:
            return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        x1 = high * 0.9 + close * 0.1
        mv30 = vol.rolling(30).mean()                 # MEAN(VOL,30)
        corr1 = ts_corr(x1, mv30, 10)                 # CORR(...,10)
        base = corr1.rolling(10, min_periods=1).rank(pct=True)   # RANK 近似
        hl2 = (high + low) / 2
        tsr_hl = ts_rank(hl2, 4)                      # TSRANK((H+L)/2,4)
        tsr_v = ts_rank(vol, 10)                      # TSRANK(VOL,10)
        corr2 = ts_corr(tsr_hl, tsr_v, 7)             # CORR(...,7)
        expo = corr2.rolling(10, min_periods=1).rank(pct=True)   # RANK 近似
        val = (base ** expo).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
