"""
GTJA191 Alpha172 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  MEAN(ABS(SUM((LD>0 & LD>HD)?LD:0,14)*100/SUM(TR,14)
         - SUM((HD>0 & HD>LD)?HD:0,14)*100/SUM(TR,14))
      / (SUM((LD>0 & LD>HD)?LD:0,14)*100/SUM(TR,14)
         + SUM((HD>0 & HD>LD)?HD:0,14)*100/SUM(TR,14)) * 100, 6)
DolphinDB:
  def gtjaAlpha172(close, high, low){
      HD = high - mfirst(high, 2)
      LD = mfirst(low, 2) - low
      TR = max(max(high - low, abs(high - mfirst(close, 2))), abs(low - mfirst(close, 2)))
      sum1 = msum(iif((LD > 0) && (LD > HD), LD, 0), 14) * 100 \ msum(TR, 14)
      sum2 = msum(iif((HD > 0) && (HD > LD), HD, 0), 14) * 100 \ msum(TR, 14)
      return mavg(abs(sum1 - sum2) \ (sum1 + sum2) * 100, 6)
  }

翻译要点:
- mfirst(x,2)=delay(x,1)=前日值。
- HD=今日高-前日高(上行移动)；LD=前日低-今日低(下行移动)。
- TR=True Range 真实波幅。
- sum1 = -DM 归一化(下行方向移动占真实波幅%) = msum(-DM,14)*100/msum(TR,14)。
- sum2 = +DM 归一化(上行方向移动占真实波幅%)。
- DX = |sum1 - sum2|/(sum1+sum2)*100 = DMI 的方向指标。
- 结果 = MEAN(DX, 6) = 6日平均 DX（类 ADX 短周期版）。
- 除零：msum(TR,14)=0 或 sum1+sum2=0 时置 NaN。
- 最长链：delay(1)+msum(14)+mavg(6) = 21 行起算。

语义: 6日平均方向指标(ADX 短周期)。趋势强（不论涨跌）→DX 大→因子大，
      通常作"趋势强度"维度（非方向），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha172Factor(FactorBase):
    name = "gtja_alpha172"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # delay(1)+msum(14)+mavg(6)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        hd = high - high.shift(1)                 # HD
        ld = low.shift(1) - low                   # LD
        dc1 = close.shift(1)
        tr = pd.Series(
            np.maximum(np.maximum(high - low, (high - dc1).abs()), (low - dc1).abs()),
            index=df.index,
        )
        ndm = pd.Series(np.where((ld > 0) & (ld > hd), ld, 0.0), index=df.index)  # -DM
        pdm = pd.Series(np.where((hd > 0) & (hd > ld), hd, 0.0), index=df.index)  # +DM
        sum_tr = ts_sum(tr, 14).replace(0, np.nan)
        sum1 = ts_sum(ndm, 14) * 100 / sum_tr     # -DI
        sum2 = ts_sum(pdm, 14) * 100 / sum_tr     # +DI
        tot = (sum1 + sum2).replace(0, np.nan)
        dx = (sum1 - sum2).abs() / tot * 100
        val = dx.rolling(6).mean().iloc[-1]       # MEAN(DX,6)
        if pd.isna(val):
            return None
        return float(val)
