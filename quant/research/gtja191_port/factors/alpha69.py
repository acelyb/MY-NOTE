"""
GTJA191 Alpha69 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  DTM = (OPEN<=DELAY(OPEN,1) ? 0 : MAX((HIGH-OPEN),(OPEN-DELAY(OPEN,1))))
  DBM = (OPEN>=DELAY(OPEN,1) ? 0 : MAX((OPEN-LOW),(OPEN-DELAY(OPEN,1))))
  IF(SUM(DTM,20)>SUM(DBM,20), (SUM(DTM,20)-SUM(DBM,20))/SUM(DTM,20),
     IF(SUM(DTM,20)==SUM(DBM,20), 0, (SUM(DTM,20)-SUM(DBM,20))/SUM(DBM,20)))
DolphinDB:
  def gtjaAlpha69(open, high, low){
      DTM = iif(open <= mfirst(open, 2), 0, max(high - open, open - mfirst(open, 2)))
      DBM = iif(open >= mfirst(open, 2), 0, max(open - low, open - mfirst(open, 2)))
      return iif(msum(DTM,20) > msum(DBM,20), (msum(DTM,20)-msum(DBM,20))\msum(DTM,20),
              iif(msum(DTM,20) == msum(DBM,20), 0, (msum(DTM,20)-msum(DBM,20))\msum(DBM,20)))
  }

翻译要点:
- mfirst(open,2)=昨开 O_{t-1}。
- DTM（多头开窗力）: 今日高开(O>O1)时取 MAX(HIGH-OPEN, OPEN-O1)——开盘向上跳空后
  继续冲高(冲高幅度)与跳空缺口(OPEN-O1)的较大者；低开或平开则记0。
- DBM（空头开窗力）: 今日低开(O<O1)时取 MAX(OPEN-LOW, OPEN-O1)——开盘向下跳空后
  继续下探(下探幅度)与跳空缺口(O1-OPEN)的较大者；高开或平开则记0。
- 比较 20日内 DTM/DBM 总和：多头力大→用差/多头力归一化；空头力大→用差/空头力归一化；
  相等→0。结果∈[-1,1]，+1=纯多头开盘强势，-1=纯空头开盘弱势。
- 分母=0时替换 nan。无横截面算子，单标的可忠实还原。

语义: 开盘缺口方向的多空力量比（20日）——捕捉"开盘情绪"。
  与 overnight_reversal(隔夜收益反转) 相关但不同：overnight 用收-开(隔夜段)，
  alpha69 用开盘跳空方向 + 当日冲高/下探幅度，是"开盘动能+日内延续"维度。
  方向 IC 定夺。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha69Factor(FactorBase):
    name = "gtja_alpha69"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 21:  # mfirst(2) + msum(20)
            return None
        op, high, low = df["open"], df["high"], df["low"]
        o1 = op.shift(1)
        dtm = pd.Series(
            np.where((op <= o1).values, 0.0, np.maximum((high - op).values, (op - o1).values)),
            index=op.index,
        )
        dbm = pd.Series(
            np.where((op >= o1).values, 0.0, np.maximum((op - low).values, (o1 - op).values)),
            index=op.index,
        )
        sdtm = dtm.rolling(20).sum()
        sdbm = dbm.rolling(20).sum()
        diff = sdtm - sdbm
        # 多头大→除以多头和；空头大→除以空头和；相等→0
        denom = pd.Series(
            np.where((sdtm > sdbm).values, sdtm.values,
                     np.where((sdtm == sdbm).values, 1.0, sdbm.values)),
            index=op.index,
        )
        denom = denom.replace(0, np.nan)
        val = (diff / denom).iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
