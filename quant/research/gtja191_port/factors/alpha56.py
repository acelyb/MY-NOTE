"""
GTJA191 Alpha56 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  RANK(OPEN - TSMIN(OPEN, 12)) < RANK( (RANK(CORR(SUM((HIGH+LOW)/2, 19), SUM(MEAN(VOLUME,40), 19), 13))^5) )
DolphinDB:
  def gtjaAlpha56(open, high, low, vol){
      return rowRank(open - mmin(open, 12), percent=true) <
             rowRank(pow(rowRank(mcorr(msum((high + low) \ 2, 19), msum(mavg(vol, 40), 19), 13), percent=true), 5), percent=true)
  }

翻译要点:
- 左侧: RANK(OPEN - TSMIN(OPEN,12)) = 开盘价相对12日开盘最低的溢价，做横截面排名。
- 右侧: 内层 mcorr(SUM((H+L)/2,19), SUM(MEAN(VOL,40),19), 13)
    = 过去13日 [19日(H+L)/2求和 vs 19日(40日量均值)求和] 的时序相关
    rowRank 外层横截面排名后 ^5，再做外层 rowRank 横截面排名。
- 单标的口径：rowRank 用 rolling 时序 pct rank 近似（有损）。
- ⚠️ 含多层前导 NaN：mavg(vol,40) 前39位 NaN → msum(...,19) 进一步前移 → mcorr(13) 再前移；
  内层 rank 后做 ^5（NaN 保持 NaN），外层 rank 含前导 NaN 必须用 min_periods=1。
- 最终返回布尔比较 (left < right)，DolphinDB 下返回 true/false，对应 1/0。
  pandas 下 (left < right) 为 bool Series，取末位转 int/float。

语义: "开盘价12日低位反弹排名" < "中枢-量趋势相关排名(5次方)的再排名"。
  布尔因子(0/1)：当复杂的量价相关排名高于开盘反弹排名时为1，否则0。
  含多层横截面 rowRank 近似（有损），方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha56Factor(FactorBase):
    name = "gtja_alpha56"

    def calc(self, df: pd.DataFrame) -> float | None:
        # 最长链: mavg(40) + msum(19) + mcorr(13) + rank(滚动)
        # 用整窗长 rank，最小数据量约 40+19+13=72；为保证 rank 有意义取 ~80
        if len(df) < 80:
            return None
        op, high, low, vol = df["open"], df["high"], df["low"], df["volume"]
        hl2 = (high + low) / 2
        sum_hl19 = hl2.rolling(19).sum()
        mean_v40 = vol.rolling(40).mean()
        sum_v19 = mean_v40.rolling(19).sum()
        # 内层相关(13) 含前导 NaN，rolling.corr 默认 min_periods=13 可用
        corr13 = sum_hl19.rolling(13).corr(sum_v19)
        # 内层 rank 横截面近似：rolling pct rank（含前导 NaN 用 min_periods=1）
        r_inner = corr13.rolling(len(corr13), min_periods=1).rank(pct=True)
        r_inner_pow = r_inner ** 5
        # 外层 rank
        r_outer = r_inner_pow.rolling(len(r_inner_pow), min_periods=1).rank(pct=True)
        # 左侧 rank(open - ts_min(open,12))
        left = (op - op.rolling(12).min()).rolling(len(op), min_periods=1).rank(pct=True)
        cmp = (left < r_outer).astype(float)
        val = cmp.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
