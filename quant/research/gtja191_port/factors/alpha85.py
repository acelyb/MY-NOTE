"""
GTJA191 Alpha85 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: RANK(VOLUME/MA(VOLUME,20), 20) * RANK(-1*(CLOSE-DELAY(CLOSE,8)), 8)
DolphinDB:
  def gtjaAlpha85(close, vol){
      return mrank(vol \ mavg(vol, 20), true, 20) * mrank(-1 * (close - mfirst(close, 8)), true, 8)
  }

翻译要点:
- vol/mavg(vol,20)=量比(当日量/20日均量)；mrank(...,true,20)=过去20日时序升序排名。
  用 rolling(20).rank(pct=True) 近似（mrank 是时序排名，非横截面 rowRank，单标的可忠实还原）。
- -1*(close - close_{t-7}) = 8日反转收益(取负，即8日跌幅)。
  mrank(...,true,8)=过去8日时序升序排名。
- 两者相乘（均为时序排名，单标的可忠实还原，无横截面近似损失）。

语义: 量比的20日时序排名 × 8日反转收益的8日时序排名。
  放量(量比排名高) + 8日超跌(反转排名高) → 因子大 → 预期未来收益高（放量超跌反弹）。
  量价复合维度：量能×反转。无横截面近似（mrank 是时序），单标的可忠实还原。方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha85Factor(FactorBase):
    name = "gtja_alpha85"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 28:  # mavg(20) + rank(20) + mfirst(8) + rank(8)
            return None
        close, vol = df["close"], df["volume"]
        vratio = vol / vol.rolling(20).mean()
        rev8 = -1 * (close - close.shift(7))  # 8日反转(取负)
        r1 = vratio.rolling(20).rank(pct=True)
        r2 = rev8.rolling(8).rank(pct=True)
        val = (r1 * r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
