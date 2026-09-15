"""
GTJA191 Alpha154 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((VWAP-MIN(VWAP,16)) < CORR(VWAP,MEAN(VOL,180),18))  [布尔]
DolphinDB:
  def gtjaAlpha154(vol, vwap){
      return (vwap - min(vwap,16)) < mcorr(vwap, mavg(vol,180), 18)
  }

翻译要点:
- vwap - ts_min(vwap,16)=VWAP相对16日最低溢价。
- mavg(vol,180)=180日量均；mcorr(vwap, 量均, 18)=18日相关。
- 比较：< 为真→1（True），否则0（False）。布尔因子，值域{0,1}。长链180。

语义: VWAP溢价 < VWAP-长均量18日相关 时取1。布尔因子，无横截面 rank，单标的可忠实还原。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_min, ts_mean, ts_corr


class Alpha154Factor(FactorBase):
    name = "gtja_alpha154"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 198:
            return None
        vol, vwap = df["volume"], df["vwap"]
        premium = vwap - ts_min(vwap, 16)
        corr18 = ts_corr(vwap, ts_mean(vol, 180), 18)
        val = (premium < corr18).astype(float).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
