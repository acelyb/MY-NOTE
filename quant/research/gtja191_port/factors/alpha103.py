"""
GTJA191 Alpha103 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: ((20-(19-TSMIN(LOW,20)))/20)*100
DolphinDB:
  def gtjaAlpha103(low){
      return (20 - (19 - mimin(low, 20))) \ 20 * 100
  }

翻译要点:
- mimin(low,20)=过去20日最低价出现的位置(距今天数，0=今天,19=最早)。
- (19 - mimin) = 最低价距20日窗口起点的天数（0=最早出现最低,19=今天就是最低）。
- 20 - (19-mimin) = 1 + mimin ∈[1,20]。
- /20*100 ∈[5,100]：最低价越早出现(已远离最低)→值越大；今天就是最低→值最小(5)。
- mimin 等价 Alpha101 的 ts_argmin。

语义: 20日最低价的"时效"——最低价越早出现因子越大(已脱离底部)，今天创新低因子最小。
  超卖/底部时效维度：值小=刚创20日新低(超卖)，值大=20日最低在早期(已反弹)。
  与 reversal(跌幅) 不同：alpha103 看最低价的"时间位置"非"跌幅"，是超卖时效维度。
  无横截面算子，单标的可忠实还原。方向 IC 定夺。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha103Factor(FactorBase):
    name = "gtja_alpha103"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # argmin(20)
            return None
        low = df["low"]
        # ts_argmin: 过去20日最小值的位置(距今天数)
        argmin = low.rolling(20).apply(lambda x: pd.Series(x).argmin(), raw=False)
        val = ((20 - (19 - argmin)) / 20 * 100).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
