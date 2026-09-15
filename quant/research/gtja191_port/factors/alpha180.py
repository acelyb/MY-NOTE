"""
GTJA191 Alpha180 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  ((MEAN(VOLUME,20) < VOLUME) ? ((-1 * TSRANK(ABS(DELTA(CLOSE,7)),60)) * SIGN(DELTA(CLOSE,7)))
                              : (-1 * VOLUME))
DolphinDB:
  def gtjaAlpha180(close, vol){
      return iif(mavg(vol, 20) < vol, -1 * mrank(abs(close - mfirst(close, 8)), true, 60) * sign(close - mfirst(close, 8)), -1 * vol)
  }

翻译要点:
- mfirst(close,8)=delay(close,7)=7日前收盘；DELTA(CLOSE,7)=close-delay(close,7)。
- mrank(abs(delta7), true, 60)=ts_rank(abs(delta7), 60)（60日时序排名，true=升序）。
- sign(delta7)=涨跌方向(+1/0/-1)。
- 条件 mavg(vol,20) < vol（当日量>20日均量，放量）：
  - 放量: -1 * ts_rank(|delta7|,60) * sign(delta7) = 带方向的|涨跌幅|时序排名(取负)。
  - 缩量: -1 * vol（负量）。
- 最长链：mavg(20) + (右侧 mfirst(8)+mrank(60)) = 68 行起算。

语义: 放量时取"带方向的7日涨跌幅时序排名(取负)"，缩量时取负成交量。
      高度条件化，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_rank


class Alpha180Factor(FactorBase):
    name = "gtja_alpha180"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 68:  # mavg(20) + delay(7) + ts_rank(60)
            return None
        close, vol = df["close"], df["volume"]
        m20 = vol.rolling(20).mean()
        delta7 = close - close.shift(7)                    # DELTA(CLOSE,7)
        tsr = ts_rank(delta7.abs(), 60)                    # TSRANK(ABS(DELTA,7),60)
        sgn = np.sign(delta7)
        branch_up = -1 * tsr * sgn
        branch_dn = -1 * vol
        val = pd.Series(np.where(m20 < vol, branch_up, branch_dn), index=df.index).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
