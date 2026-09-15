"""
GTJA191 Alpha91 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  RANK(CLOSE-MAX(CLOSE,5)) * RANK(CORR(MEAN(VOL,40), LOW, 5)) * (-1)
DolphinDB:
  def gtjaAlpha91(close, low, vol){
      return rowRank(close - max(close, 5), percent=true)
           * rowRank(mcorr(mavg(vol, 40), low, 5), percent=true) * (-1)
  }

翻译要点:
- max(close,5)=MAX(CLOSE,5)=过去5日最高收盘（注意是收盘的max，不是high）。
  close - MAX(CLOSE,5)：当日收盘相对5日最高收盘的回撤幅度（≤0）。
- mavg(vol,40)=40日均量；mcorr(40日均量, low, 5)=过去5日(40日均量 vs 低价)的相关。
- 两个 rowRank 横截面排名相乘，再取负。
- 单标的口径：rowRank 横截面 → 用 rolling(5) 时序 pct rank 近似（与 alpha10/48 同思路，有损）。
- 40日均量与5日低价的相关：低价时放量(负相关)vs低价时缩量(正相关)的近期形态。

语义: "5日收盘回撤排名" × "40日均量与低价相关排名" 取负。
  回撤深(接近-大)+ 量价关系 某形态 → 反转/承接信号。维度上是"回撤×量低相关"交叉。
  含两层横截面 rowRank 近似（双重有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha91Factor(FactorBase):
    name = "gtja_alpha91"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 44:  # mavg(40) + mcorr(5) + rank(5)
            return None
        close, low, vol = df["close"], df["low"], df["volume"]
        maxc5 = close.rolling(5).max()
        drawdown = close - maxc5
        mavol40 = vol.rolling(40).mean()
        corr5 = mavol40.rolling(5).corr(low)
        r1 = drawdown.rolling(5).rank(pct=True)
        r2 = corr5.rolling(5).rank(pct=True)
        val = (-r1 * r2).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
