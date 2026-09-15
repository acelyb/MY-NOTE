"""
GTJA191 Alpha117 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (TSRANK(VOLUME,32)*(1-TSRANK(((CLOSE+HIGH)-LOW),16)))*(1-TSRANK(RET,32))
DolphinDB:
  def gtjaAlpha117(close, high, low, vol){
      return mrank(vol, true, 32) * (1 - mrank(close + high - low, true, 16)) * (1 - mrank(ratios(close) - 1, true, 32))
  }

翻译要点:
- mrank(x,true,n)=过去 n 期时序 pct rank = ts_rank。
- TSRANK(VOL,32) × (1 - TSRANK(CLOSE+HIGH-LOW,16)) × (1 - TSRANK(RET,32))。
- ratios(close)-1 = ret = 日收益率。
- 三项相乘，两项为 (1-rank) 形式：当对应值排名低时该因子项大。

语义: 量排名高 × (close+high-low)排名低 × 收益排名低 → 因子大。
  即"放量 + (close+high-low)低位 + 收益低位"的组合，捕捉放量但价格未涨的潜在反转。
  方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_rank


class Alpha117Factor(FactorBase):
    name = "gtja_alpha117"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 32:  # ts_rank(32) 需要 32 行
            return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        r_vol = ts_rank(vol, 32)                       # TSRANK(VOL,32)
        r_chl = ts_rank(close + high - low, 16)        # TSRANK(CLOSE+HIGH-LOW,16)
        r_ret = ts_rank(close.pct_change(), 32)        # TSRANK(RET,32)
        val = (r_vol * (1 - r_chl) * (1 - r_ret)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
