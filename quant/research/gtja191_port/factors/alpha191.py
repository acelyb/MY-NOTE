"""
GTJA191 Alpha191 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: CORR(MEAN(VOLUME,20), LOW, 5) + ((HIGH+LOW)/2 - CLOSE)
DolphinDB:
  def gtjaAlpha191(close, high, low, vol){
      return mcorr(mavg(vol, 20), low, 5) + (high + low) \\ 2 - close
  }

翻译要点:
- 项1: CORR(MEAN(VOL,20), LOW, 5) —— 过去20日均量 与 过去5日低价 的时序相关
  （mavg(vol,20) 是滚动20日均量序列，与 low 做5日窗口时序相关）
- 项2: (HIGH+LOW)/2 - CLOSE —— 当日中点与收盘的偏离（收盘中点之上为正）
- 两项相加。无横截面算子，单标的可忠实还原。

语义: 量-低价相关性 + 收盘相对中点偏离。
  项1: 量与低价正相关=放量时低价也抬高（量价同向偏强）；负相关=放量伴随低价走低（抛压）。
  项2: 收盘低于中点=日内冲高回落（偏弱，负值）；高于中点=尾盘走强（正值）。
  合成: 量价结构因子。方向 IC 定夺（研报口径未取负）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha191Factor(FactorBase):
    name = "gtja_alpha191"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 24:  # 需 mavg(20) 再 corr(5)
            return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        vol20 = vol.rolling(20).mean()
        corr = vol20.rolling(5).corr(low)
        mid_dev = (high + low) / 2 - close
        val = (corr + mid_dev).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
