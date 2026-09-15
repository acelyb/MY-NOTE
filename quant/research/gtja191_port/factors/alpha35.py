"""
GTJA191 Alpha35 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: (MIN(RANK(DECAYLINEAR(DELTA(OPEN,1),15)),
           RANK(DECAYLINEAR(CORR((VOLUME),((OPEN*0.65)+(OPEN*0.35)),17),7))) * -1)
DolphinDB:
  def gtjaAlpha35(open, vol){
      return min(rowRank(mavg(open - mfirst(open, 2), 1..15), percent=true),
                 rowRank(mavg(mcorr(vol, open * 0.65 + open * 0.35, 17), 1..7), percent=true)) * (-1)
  }

翻译要点:
- mfirst(open,2)=delay(open,1)=DELTA(open,1)（研报 DELTA(OPEN,1)）。
- mavg(x, 1..15) / mavg(x, 1..7)：DECAYLINEAR 语义（1..n 线性权重）。
  DolphinDB mavg(x, 1..15) 权重 1..15（递增），研报 DECAYLINEAR 权重递减 15..1。
  以研报为准用 decay_linear（递减权重）。
  注：alpha35/alpha39/alpha44 中 DECAYLINEAR 在 DolphinDB 用 mavg(1..n) 实现，
  严格应按 DolphinDB mavg(1..n)（递增权重）实现；但研报写 DECAYLINEAR（递减）。
  这里以研报为准用 decay_linear，翻译差异在 docstring 注明。
- vol 与 open*0.65+open*0.35 = open*1.0（DolphinDB 原式如此，0.65+0.35=1）。
- rowRank 横截面排名 → rolling pct rank 近似（有损）。
- min(A,B) 逐元素取小，整体取负。

语义: "开盘1日动量衰减加权排名" 与 "量-开盘17日相关衰减加权排名" 取小值，取负。
  两排名中较弱者主导，取负后反映"弱势反转"。含横截面 rank 近似与 DECAYLINEAR 口径差异（有损），
  方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, delay, decay_linear, ts_corr


class Alpha35Factor(FactorBase):
    name = "gtja_alpha35"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 34:  # corr(17)+decay(7)+rank(7) 最深约 17+7+7+3
            return None
        open_, vol = df["open"], df["volume"]
        # 第一项：DECAYLINEAR(DELTA(OPEN,1),15) 的 rank
        d_open1 = open_ - delay(open_, 1)
        decay15 = decay_linear(d_open1, 15)
        r1 = decay15.rolling(15, min_periods=1).rank(pct=True)
        # 第二项：DECAYLINEAR(CORR(vol, open, 17), 7) 的 rank
        corr17 = ts_corr(vol, open_ * 0.65 + open_ * 0.35, 17)
        decay7 = decay_linear(corr17, 7)
        r2 = decay7.rolling(7, min_periods=1).rank(pct=True)
        m = pd.concat([r1, r2], axis=1).min(axis=1)
        val = (-m).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
