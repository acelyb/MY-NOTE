"""
GTJA191 Alpha64 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: MAX(RANK(CORR(RANK(VWAP),RANK(VOL),4),4), RANK(AVG(MAX(CORR(RANK(CLOSE),RANK(MEAN(VOL,60)),4),13),14))) * -1
DolphinDB:
  def gtjaAlpha64(close, vol, vwap){
      return max(rowRank(mavg(mcorr(rowRank(vwap,percent=true),rowRank(vol,percent=true),4),1..4),percent=true), rowRank(mavg(max(mcorr(rowRank(close,percent=true),rowRank(mavg(vol,60),percent=true),4),13),1..14),percent=true)) * (-1)
  }

翻译要点:
- 第一项：rowRank(vwap)/rowRank(vol) 排名；mcorr(...,4)=4日相关；mavg(...,1..4) 加权均；rowRank 排名。
- 第二项：mavg(vol,60)=60日量均；rowRank(量均)；mcorr(rowRank(close), rowRank(量均), 4)=4日相关；
  mmax(...,13)=13日最大；mavg(...,1..14) 加权均；rowRank 排名。
- 两项取 max 后取负。长链60+13。

语义: VWAP-量排名相关平滑 与 收盘-长均量排名相关13日最大的平滑，取max后取负。
  多层 rank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, ts_corr, mavg_weighted, ts_mean, ts_max


class Alpha64Factor(FactorBase):
    name = "gtja_alpha64"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 87:
            return None
        close, vol, vwap = df["close"], df["volume"], df["vwap"]
        rvw = vwap.rolling(4, min_periods=1).rank(pct=True)
        rv = vol.rolling(4, min_periods=1).rank(pct=True)
        t1 = mavg_weighted(ts_corr(rvw, rv, 4), list(range(1, 5))).rolling(4, min_periods=1).rank(pct=True)
        vmean60 = ts_mean(vol, 60)
        rv60 = vmean60.rolling(60, min_periods=1).rank(pct=True)
        rc = close.rolling(4, min_periods=1).rank(pct=True)
        c4 = ts_corr(rc, rv60, 4)
        cmax13 = ts_max(c4, 13)
        t2 = mavg_weighted(cmax13, list(range(1, 15))).rolling(14, min_periods=1).rank(pct=True)
        val = (pd.concat([t1, t2], axis=1).max(axis=1) * (-1)).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
