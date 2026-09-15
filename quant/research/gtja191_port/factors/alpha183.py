"""
GTJA191 Alpha183 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MAX(SUMAC(CLOSE-MEAN(CLOSE,24)))-MIN(SUMAC(CLOSE-MEAN(CLOSE,24)))/STD(CLOSE,24)
DolphinDB:
  def gtjaAlpha183(close){
      return rowMax(msum((close - mavg(close,24)), 24)) - rowMin(msum((close - mavg(close,24)), 24)) \ mstd(close,24)
  }

翻译要点:
- ⚠️ 研报用 SUMAC（累积和），DolphinDB 用 msum(.,24)（24日滚动和）；本移植按 DolphinDB 实现。
- mavg(close,24)=24日收盘均值；close-mavg 为偏离；msum(.,24)=24日偏离和。
- rowMax/rowMin 横截面行最大/最小 → 单标的用 ts_max/ts_min(.,24) 近似（24日窗口内偏离和的极值）。
- DolphinDB `\` 优先级高于 `-`：表达式 = rowMax - (rowMin / mstd(close,24))。
- 除零：mstd(close,24)=0 时置 NaN。
- 最长链：mavg(24)+msum(24)+ts_max/ts_min(24) = 72 行起算。
- 与 alpha165(窗口48) 同结构。

语义: (24日偏离和的最大值) - (最小值/24日收盘标准差)。
      复合形式，方向以 IC 实测定。含 rowMax/rowMin 横截面→时序近似（有损）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_max, ts_min, ts_std, ts_sum


class Alpha183Factor(FactorBase):
    name = "gtja_alpha183"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 72:  # mavg(24)+msum(24)+ts_max/min(24)
            return None
        close = df["close"]
        dev = close - close.rolling(24).mean()      # close - mavg(close,24)
        cumdev = ts_sum(dev, 24)                    # msum(dev, 24)
        rmax = ts_max(cumdev, 24)                   # rowMax 近似
        rmin = ts_min(cumdev, 24)                   # rowMin 近似
        std24 = ts_std(close, 24).replace(0, np.nan)
        val = (rmax - rmin / std24).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
