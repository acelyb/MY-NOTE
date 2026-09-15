"""
GTJA191 Alpha165 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MAX(SUMAC(CLOSE-MEAN(CLOSE,48)))-MIN(SUMAC(CLOSE-MEAN(CLOSE,48)))/STD(CLOSE,48)
DolphinDB:
  def gtjaAlpha165(close){
      return rowMax(msum((close - mavg(close,48)), 48)) - rowMin(msum((close - mavg(close,48)), 48)) \ mstd(close,48)
  }

翻译要点:
- ⚠️ 研报用 SUMAC（累积和），DolphinDB 用 msum(.,48)（48日滚动和）；本移植按 DolphinDB 实现。
- mavg(close,48)=48日收盘均值；close-mavg 为偏离；msum(.,48)=48日偏离和（近似 cumsum 局部段）。
- rowMax/rowMin 横截面行最大/最小 → 单标的用 ts_max/ts_min(.,48) 近似（48日窗口内偏离和的极值）。
- DolphinDB `\` 优先级高于 `-`：表达式 = rowMax - (rowMin / mstd(close,48))。
- 除零：mstd(close,48)=0 时置 NaN。
- 最长链：mavg(48)+msum(48)+ts_max/ts_min(48) = 144 行起算。

语义: (48日偏离和的最大值) - (最小值/48日收盘标准差)。
      复合形式，方向以 IC 实测定。含 rowMax/rowMin 横截面→时序近似（有损）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_max, ts_min, ts_std, ts_sum


class Alpha165Factor(FactorBase):
    name = "gtja_alpha165"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 144:  # mavg(48)+msum(48)+ts_max/min(48)
            return None
        close = df["close"]
        dev = close - close.rolling(48).mean()      # close - mavg(close,48)
        cumdev = ts_sum(dev, 48)                    # msum(dev, 48)
        rmax = ts_max(cumdev, 48)                   # rowMax 近似
        rmin = ts_min(cumdev, 48)                   # rowMin 近似
        std48 = ts_std(close, 48).replace(0, np.nan)
        val = (rmax - rmin / std48).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
