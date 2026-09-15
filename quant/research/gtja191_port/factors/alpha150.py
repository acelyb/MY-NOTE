"""
GTJA191 Alpha150 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (CLOSE+HIGH+LOW)/3 * VOLUME
DolphinDB:
  def gtjaAlpha150(close, high, low, vol){
      return (close + high + low) \\ 3 * vol
  }

翻译要点:
- 典型价 typical = (HIGH+LOW+CLOSE)/3（K线常用中枢价）
- 乘以当日成交量 → 典型价×量 ≈ 当日"成交金额"代理（典型价替代成交均价）
- 无窗口、无横截面算子，单标的可忠实还原。

语义: 典型价×成交量，是日内流动性/成交额的代理指标（缓存无 amount/vwap 时的替代）。
  绝对量纲（与股价×量级相关），截面排序时由 IC 的 spearmanr 处理。
  高值=当日成交活跃/资金流入大。方向 IC 定夺。
  注：与系统 size 因子可能相关（大市值股成交额天然大），相关性诊断会暴露。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha150Factor(FactorBase):
    name = "gtja_alpha150"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 1:
            return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        typical = (high + low + close) / 3
        val = (typical * vol).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
