"""
GTJA191 Alpha99 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: -1 * RANK(COVIANCE(RANK(CLOSE), RANK(VOLUME), 5))
  （研报笔误 COVIANCE → COVARIANCE）
DolphinDB:
  def gtjaAlpha99(close, vol){
      return -1 * (rowRank(mcovar(rowRank(close, percent=true), rowRank(vol, percent=true), 5), percent=true))
  }

翻译要点:
- RANK(CLOSE)、RANK(VOLUME)：横截面排名（rowRank 跨股票 percent=true）。
- COV(RANK(CLOSE),RANK(VOL),5)=过去5日两个截面排名的时序协方差（mcovar）。
- 整体 RANK 后取负。

单标的口径关键（与 Alpha6 同理）:
  研报的 RANK 是横截面。单标的 calc 无法做横截面排名——这是本框架与研报的固有差异。
  处理：RANK(CLOSE)/RANK(VOL) 用"当日值在过去5日的时序 pct rank"近似
  （rolling(5).rank(pct=True)，窗口小、与 COV 的5日窗口对齐、不会因大窗口全 nan）。
  量价协方差语义：过去5日"价的时序排名"与"量的时序排名"的协方差=量价同涨同跌程度。
  最终横截面排序由 IC 的 spearmanr 保证。

  注：早期版本误用 rolling(len(close)).rank（窗口=全历史，前段几乎全 nan 导致 cov 全 nan、
  n=0），已修正为 rolling(5)。单标的对横截面 RANK 的近似本质上有损，方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha99Factor(FactorBase):
    name = "gtja_alpha99"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 6:
            return None
        close, vol = df["close"], df["volume"]
        # RANK 近似：当日值在过去5日的时序 pct rank（与 COV 窗口对齐）
        rc = close.rolling(5).rank(pct=True)
        rv = vol.rolling(5).rank(pct=True)
        cov = rc.rolling(5).cov(rv)  # 过去5日协方差
        val = cov.iloc[-1]
        if pd.isna(val):
            return None
        return -float(val)  # 公式整体取负
