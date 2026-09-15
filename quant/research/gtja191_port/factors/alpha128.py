"""
GTJA191 Alpha128 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  100-(100/(1+SUM(((HIGH+LOW+CLOSE)/3>DELAY((HIGH+LOW+CLOSE)/3,1)?(HIGH+LOW+CLOSE)/3*VOLUME:0),14)
       /SUM(((HIGH+LOW+CLOSE)/3<DELAY((HIGH+LOW+CLOSE)/3,1)?(HIGH+LOW+CLOSE)/3*VOLUME:0),14)))
DolphinDB:
  def gtjaAlpha128(close, high, low, vol){
      return 100 - (100 \ (1 + msum(iif((high + low + close) \ 3 > mfirst((high + low + close) \ 3, 2),
                            (high + low + close) \ 3 * vol, 0), 14)
                         \ msum(iif((high + low + close) \ 3 < mfirst((high + low + close) \ 3, 2),
                            (high + low + close) \ 3 * vol, 0), 14)))
  }

翻译要点:
- typical=(high+low+close)/3 典型价；mfirst(typical,2)=delay(typical,1)=前一日典型价。
- up_flow = iif(typical>delay1, typical*vol, 0) 上涨日典型成交额。
- down_flow = iif(typical<delay1, typical*vol, 0) 下跌日典型成交额。
- 14日上涨资金流和 / 14日下跌资金流和 = 资金流比率 MFR。
- 100 - 100/(1+MFR) = MFI(货币流量指标) 的 0-100 标准化。
- 除零：down_flow 14日和为 0 时 MFR→inf，结果趋近 100，用 np.where 置 NaN 守卫。
- mfirst(t,2)=delay(t,1)，需 1 行延迟；msum(14) 共 15 行起算。

语义: 14日货币流量指标(MFI)。资金流入强→MFI 高→因子大→预期未来收益高（动量/资金流）。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase, ts_sum


class Alpha128Factor(FactorBase):
    name = "gtja_alpha128"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 15:  # delay(1) + msum(14) = 15
            return None
        close, high, low, vol = df["close"], df["high"], df["low"], df["volume"]
        typ = (high + low + close) / 3
        prev_typ = typ.shift(1)
        up_flow = pd.Series(np.where(typ > prev_typ, typ * vol, 0.0), index=df.index)
        dn_flow = pd.Series(np.where(typ < prev_typ, typ * vol, 0.0), index=df.index)
        sum_up = ts_sum(up_flow, 14)
        sum_dn = ts_sum(dn_flow, 14)
        mfr = sum_up / sum_dn.replace(0, np.nan)
        mfi = 100 - 100 / (1 + mfr)
        val = mfi.iloc[-1]
        if pd.isna(val):
            return None
        return float(val)
