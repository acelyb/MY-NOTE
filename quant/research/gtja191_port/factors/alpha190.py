"""
GTJA191 Alpha190 —— 移植自 DolphinDB gtja191Alpha.dos。

研报公式:
  LOG((COUNT(CLOSE/DELAY(CLOSE)-1 > (CLOSE/DELAY(CLOSE,19))^(1/20)-1, 20) - 1)
      * SUMIF((CLOSE/DELAY(CLOSE)-1 - (CLOSE/DELAY(CLOSE,19))^(1/20)-1)^2, 20,
              CLOSE/DELAY(CLOSE)-1 < (CLOSE/DELAY(CLOSE,19))^(1/20)-1)
      / (COUNT(CLOSE/DELAY(CLOSE)-1 < (CLOSE/DELAY(CLOSE,19))^(1/20)-1, 20)
         * SUMIF((CLOSE/DELAY(CLOSE)-1 - (CLOSE/DELAY(CLOSE,19))^(1/20)-1)^2, 20,
                 CLOSE/DELAY(CLOSE)-1 > (CLOSE/DELAY(CLOSE,19))^(1/20)-1)))
DolphinDB:
  def gtjaAlpha190(close){
      A = close\move(close,1)
      B = pow((close\move(close,19)),1\20)
      C = (A-1)>(B-1)
      D = (A-1)<(B-1)
      E = mcount(C,20)
      F = mcount(D,20)
      F0 = pow(A-1-B-1,2)
      F1 = msum(F0 * D, 20)
      F2 = msum(F0 * C, 20)
      return log(((E-1) * F1) \ (D * F2))
  }

翻译要点:
- A=close/delay(close,1) 日比率；B=(close/delay(close,19))^(1/20) 19日比的1/20次方(几何均值)。
- C = 日收益(A-1) > 几何收益(B-1) (上行偏离)；D = 日收益 < 几何收益 (下行偏离)。
- E=mcount(C,20)=20日上行偏离天数；F=mcount(D,20)=20日下行偏离天数。
- F0 = 偏离平方。⚠️ DolphinDB 写 `A-1-B-1`(字面=A-B-2)，研报意图为 (A-1)-(B-1)=A-B；
  按研报意图取 ((A-1)-(B-1))^2 = (A-B)^2，差异注明。
- F1=msum(F0*D,20)=下行偏离平方和(仅D日)；F2=msum(F0*C,20)=上行偏离平方和(仅C日)。
- ⚠️ DolphinDB return 分母写 `D * F2`(D为布尔序列→逐元素，D=false处置零→inf)，
  研报公式分母为 COUNT(down,20)*SUMIF(sq,20,up) = F * F2(标量计数×上行平方和)。
  按研报意图用 F * F2 (标量)，避免逐元素除零产生 inf。差异注明。
- 最终 = log((E-1)*F1 / (F*F2)) = log(上行偏离平方和(计数加权) / 下行偏离计数×下行偏离... )
  实为上行/下行偏离平方的"计数加权对数比率"(类对数似然比)。
- log 输入 ≤0 产生 NaN；除零 F=0 或 F2=0 置 NaN。
- pow(close/delay(close,19), 1/20) 底数为正(价格>0)，1/20 次方安全。
- 最长链：delay(19)+mcount/msum(20) = 39 行起算。

语义: 日收益相对19日几何均值的上下行偏离平方的计数加权对数比率。
      上行偏离强度大→因子大→预期未来收益高(动量延续)，方向以 IC 实测定。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from base import FactorBase


class Alpha190Factor(FactorBase):
    name = "gtja_alpha190"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 39:  # delay(19) + mcount/msum(20)
            return None
        close = df["close"]
        A = close / close.shift(1)                       # 日比率
        B = (close / close.shift(19)) ** (1 / 20)        # 19日比的1/20次方
        ret = A - 1                                      # 日收益
        geo = B - 1                                      # 几何收益
        C = ret > geo                                    # 上行偏离
        D = ret < geo                                    # 下行偏离
        E = C.rolling(20).sum()                          # mcount(C,20) 上行天数
        F = D.rolling(20).sum()                          # mcount(D,20) 下行天数
        dev = (ret - geo) ** 2                           # 偏离平方 (研报意图 (A-1)-(B-1))
        F1 = (dev * D).rolling(20).sum()                 # 下行偏离平方和
        F2 = (dev * C).rolling(20).sum()                 # 上行偏离平方和
        num = (E - 1) * F1
        den = (F * F2).replace(0, np.nan)                # 研报意图 F*F2 (标量)
        ratio = num / den
        val = np.log(ratio.replace(0, np.nan)).iloc[-1]  # log(≤0)→NaN 守卫
        if pd.isna(val):
            return None
        return float(val)
