"""
GTJA191 Alpha144 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式: SUM(IF(CLOSE<DELAY(CLOSE,1), ABS(CLOSE/DELAY(CLOSE,1)-1)/(VOL*VWAP), 0),20) / COUNT(CLOSE<DELAY(CLOSE,1),20)
DolphinDB:
  def gtjaAlpha144(close, vol, vwap){
      return msum(iif(close < mfirst(close,2), abs(close\mfirst(close,2) - 1) \(vol*vwap), 0), 20) \ mcount(iif(close < mfirst(close,2), 1, NULL), 20)
  }

翻译要点:
- mfirst(close,2)=delay(close,1)=前日收盘。
- 下跌日（close<前日）：跌幅绝对值 / (vol*vwap=成交额代理)；非下跌日取0。
- msum(...,20)=20日累加（下跌日的"单位成交额跌幅"之和）。
- 分母：mcount(下跌日, 20)=20日内下跌日数（iif 的 NULL 分支不计入 mcount）。
- 分子 / 分母=过去20日下跌日的平均"单位成交额跌幅"。
- 分母可能0（20日全涨），需防护。

语义: 20日下跌日的平均单位成交额跌幅（下跌时的成交额加权跌幅强度）。
  无横截面 rank，单标的可忠实还原。方向以 IC 实测定。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase, mfirst, ts_sum, mcount


class Alpha144Factor(FactorBase):
    name = "gtja_alpha144"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:
            return None
        close, vol, vwap = df["close"], df["volume"], df["vwap"]
        prev = mfirst(close, 2)
        down = close < prev
        amt = vol * vwap
        # 下跌日单位成交额跌幅；非下跌日 NaN（供 mcount 计数用），iif 取0用于 msum
        drop = (close / prev - 1).abs() / amt
        contrib = drop.where(down, 0.0)  # msum 用：非下跌日0
        num = ts_sum(contrib, 20)
        # mcount：下跌日计数（用 down 序列，True=1 计入）
        den = mcount(down.astype("float64").where(down, float("nan")), 20)
        val = (num / den).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
