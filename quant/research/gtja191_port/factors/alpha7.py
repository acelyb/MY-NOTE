"""
GTJA191 Alpha7 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((RANK(MAX((VWAP-CLOSE),3)) + RANK(MIN((VWAP-CLOSE),3))) * RANK(DELTA(VOLUME,3)))
DolphinDB:
  def gtjaAlpha7(close, vol, vwap){
      return rowRank(mmax(vwap-close,3),percent=true) + rowRank(mmin(vwap-close,3),percent=true) * rowRank(vol-mfirst(vol,4),percent=true)
  }

翻译要点:
- vwap-close=VWAP 偏离收盘（正=当日收盘低于均价，尾盘杀跌；负=收盘高于均价）。
- mmax(vwap-close,3)/mmin(...,3)=过去3日最大/最小偏离。
- mfirst(vol,4)=delay(vol,3)=DELTA(VOLUME,3) 的前值项，vol-mfirst(vol,4)=DELTA(VOL,3)。
- 三层 rowRank → rolling pct rank 近似（min_periods=1）。
- 注：研报公式是 (RANK(MAX)+RANK(MIN))*RANK(DELTA)，即乘积；DolphinDB 实现 RANK(MAX)+RANK(MIN)*RANK(DELTA)
  缺一对括号（+ 优先级低于 *，故 = RANK(MAX) + (RANK(MIN)*RANK(DELTA))），与研报 (A+B)*C 不同。
  按 DolphinDB 源码忠实翻译（与既有批次口径一致）。

语义: VWAP-CLOSE 偏离的3日极值排名与量变化的交叉。含横截面 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_max, ts_min, mfirst


class Alpha7Factor(FactorBase):
    name = "gtja_alpha7"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 4:
            return None
        close, vol, vwap = df["close"], df["volume"], df["vwap"]
        d = vwap - close
        r_max = ts_max(d, 3).rolling(3, min_periods=1).rank(pct=True)
        r_min = ts_min(d, 3).rolling(3, min_periods=1).rank(pct=True)
        r_dvol = (vol - mfirst(vol, 4)).rolling(4, min_periods=1).rank(pct=True)
        val = (r_max + r_min * r_dvol).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
