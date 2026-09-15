"""
GTJA191 Alpha166 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  -20*(20-1)^1.5 * SUM(CLOSE/DELAY(CLOSE,1)-1 - MEAN(CLOSE/DELAY(CLOSE,1)-1,20), 20)
  / ((20-1)*(20-2)*(SUM((CLOSE/DELAY(CLOSE,1))^2, 20))^1.5)
  （研报括号有歧义，以 DolphinDB 实现为准）
DolphinDB:
  def gtjaAlpha166(close){
      return -20 * pow((20 - 1), 1.5) * msum(close \ mfirst(close, 2) - 1 - mavg(close \ mfirst(close, 2) - 1, 20), 20)
             \ ((20 - 1) * (20 - 2) * pow((msum(pow(mavg(close \ mfirst(close, 2), 20), 2), 20)), 1.5))
  }

翻译要点:
- mfirst(close,2)=delay(close,1)=前日收盘；ratio=close/delay(close,1)。
- 分子: -20*(19)^1.5 * msum(ratio-1 - mavg(ratio-1,20), 20)
  = -20*19^1.5 * 20日(日收益-20日均值)之和 = -20*19^1.5 * 20日偏差和。
- 分母: (19)*(18) * [msum( (mavg(ratio,20))^2, 20 )]^1.5
  ⚠️ DolphinDB 分母内层是 pow(mavg(ratio,20), 2)（20日均比率的平方）再 msum(.,20) 求和，
  非研报字面的 SUM(ratio^2,20)。按 DolphinDB 实现。
- 除零：分母为 0 时置 NaN；pow(.,1.5) 底数为负会产生 NaN（均比率非负，一般安全）。
- 最长链：delay(1)+mavg(20)+msum(20) = 41 行起算。

语义: 收益偏差和的标准化偏度类指标（取负放大）。
      偏度正（右尾大）→ 分子正 → 取负后小 → 预期未来收益低，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha166Factor(FactorBase):
    name = "gtja_alpha166"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 41:  # delay(1)+mavg(20)+msum(20)
            return None
        close = df["close"]
        ratio = close / close.shift(1)             # close/delay(close,1)
        ret = ratio - 1                            # 日收益
        mean20 = ret.rolling(20).mean()            # mavg(ratio-1,20)
        num = -20 * (19 ** 1.5) * ts_sum(ret - mean20, 20)
        mean_ratio20 = ratio.rolling(20).mean()    # mavg(ratio,20)
        sq_sum = ts_sum(mean_ratio20 ** 2, 20)     # msum(pow(mavg(ratio,20),2),20)
        den = (19 * 18 * (sq_sum ** 1.5)).replace(0, np.nan)
        val = (num / den).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
