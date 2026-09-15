"""
GTJA191 Alpha113 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1*((RANK(SUM(DELAY(CLOSE,5),20)/20))*CORR(CLOSE,VOLUME,2)*RANK(CORR(SUM(CLOSE,5),SUM(CLOSE,20),2)))
DolphinDB:
  def gtjaAlpha113(close, vol){
      return -1 * rowRank(msum(mfirst(close, 6), 20) \ 20, percent=true) * mcorr(close, vol, 2) * rowRank(mcorr(msum(close, 5), msum(close, 20), 2), percent=true)
  }

翻译要点:
- mfirst(close,6)=delay(close,5)；msum(delay(close,5),20)/20 = 过去20日的"5日前收盘"均值。
- mcorr(close, vol, 2)=2日(收盘,量)时序相关。
- mcorr(msum(close,5), msum(close,20), 2)=2日(5日收盘和, 20日收盘和)时序相关。
- 三个因子相乘取负；rowRank 横截面排名 → rolling 时序 pct rank 近似（有损）。
- ⚠️ mcorr(2) 仅2日窗口，末位极易因 NaN 失效；rowRank 含前导 NaN 用 min_periods=1。
  rowRank 窗口选择：内层算子最深链 msum(20)+delay(5)=25，取与 alpha83/99 一致的 rolling(5) 近似。

语义: "20日前收盘均值排名" × "2日量价相关" × "5日vs20日收盘和相关性排名"，取负。
  量价同向+长短期和同向→因子绝对值大→取负后方向以 IC 实测定。
  含多层横截面 rowRank 近似（有损）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_corr, ts_sum


class Alpha113Factor(FactorBase):
    name = "gtja_alpha113"

    def calc(self, df: pd.DataFrame) -> float | None:
        # 最长链: msum(delay(close,5),20) 需 5+20=25 行；ts_corr(2) 末位
        if len(df) < 25:
            return None
        close, vol = df["close"], df["volume"]
        c5 = close.shift(5)   # DELAY(CLOSE,5)
        s_c5_20 = ts_sum(c5, 20) / 20                    # SUM(DELAY(CLOSE,5),20)/20
        r1 = s_c5_20.rolling(5, min_periods=1).rank(pct=True)  # rowRank 近似
        corr_cv = ts_corr(close, vol, 2)                 # CORR(CLOSE,VOL,2)
        s5 = ts_sum(close, 5)
        s20 = ts_sum(close, 20)
        corr_5520 = ts_corr(s5, s20, 2)                  # CORR(SUM(C5),SUM(C20),2)
        r2 = corr_5520.rolling(5, min_periods=1).rank(pct=True)
        val = (-r1 * corr_cv * r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
