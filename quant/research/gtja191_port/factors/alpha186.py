"""
GTJA191 Alpha186 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  (MEAN(ABS(SUM((LD>0 & LD>HD)?LD:0,14)*100/SUM(TR,14)-SUM((HD>0 & HD>LD)?HD:0,14)*100/SUM(TR,14))
        /(SUM((LD>0 & LD>HD)?LD:0,14)*100/SUM(TR,14)+SUM((HD>0 & HD>LD)?HD:0,14)*100/SUM(TR,14))*100, 6)
   + DELAY(MEAN(ABS(...)/(SUM(...)+SUM(...))*100, 6), 6)) / 2
DolphinDB:
  def gtjaAlpha186(close, high, low){
      HD = high - mfirst(high, 2)
      LD = mfirst(low, 2) - low
      TR = max(max(high - low, abs(high - mfirst(close, 2))), abs(low - mfirst(close, 2)))
      sum1 = msum(iif((LD > 0) && (LD > HD), LD, 0), 14) * 100 \ msum(TR, 14)
      sum2 = msum(iif((HD > 0) && (HD > LD), HD, 0), 14) * 100 \ msum(TR, 14)
      return (mavg(abs(sum1 - sum2) \ (sum1 + sum2) * 100, 6)
              + mfirst(mavg(abs(sum1 - sum2) \ (sum1 + sum2) * 100, 6), 7)) \ 2
  }

翻译要点:
- 前段与 alpha172 完全一致（DMI 的 DX 指标，详见 alpha172）。
- dx = mavg(|sum1-sum2|/(sum1+sum2)*100, 6) = 6日平均 DX。
- mfirst(dx, 7)=delay(dx, 6)=6日前的 dx 值。
- 结果 = (dx + delay(dx,6)) / 2 = 当前ADX 与 6日前 ADX 的均值（ADX 平滑/滞后版）。
- 除零：msum(TR,14)=0 或 sum1+sum2=0 时置 NaN。
- 最长链：delay(1)+msum(14)+mavg(6)+delay(6) = 27 行起算。

语义: 6日平均DX 与其6日滞后值的均值（ADX 的平滑/惯性版）。
      趋势持续性强→因子大，趋势强度维度，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha186Factor(FactorBase):
    name = "gtja_alpha186"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 27:  # delay(1)+msum(14)+mavg(6)+delay(6)
            return None
        close, high, low = df["close"], df["high"], df["low"]
        hd = high - high.shift(1)                 # HD
        ld = low.shift(1) - low                   # LD
        dc1 = close.shift(1)
        tr = pd.Series(
            np.maximum(np.maximum(high - low, (high - dc1).abs()), (low - dc1).abs()),
            index=df.index,
        )
        ndm = pd.Series(np.where((ld > 0) & (ld > hd), ld, 0.0), index=df.index)
        pdm = pd.Series(np.where((hd > 0) & (hd > ld), hd, 0.0), index=df.index)
        sum_tr = ts_sum(tr, 14).replace(0, np.nan)
        sum1 = ts_sum(ndm, 14) * 100 / sum_tr     # -DI
        sum2 = ts_sum(pdm, 14) * 100 / sum_tr     # +DI
        tot = (sum1 + sum2).replace(0, np.nan)
        dx = (sum1 - sum2).abs() / tot * 100
        dx_avg6 = dx.rolling(6).mean()            # mavg(DX,6)
        val = ((dx_avg6 + dx_avg6.shift(6)) / 2).iloc[-1]   # (dx + delay(dx,6))/2
        if pd.isna(val):
            return None
        return float(val)
