"""
GTJA191 Alpha143 —— 自递归因子（研报最特殊的一个），移植自 DolphinDB gtja191Alpha.dos。

研报公式: CLOSE>DELAY(CLOSE,1) ? (CLOSE-DELAY(CLOSE,1))/DELAY(CLOSE,1) * SELF : SELF
  其中 SELF = t-1 日的 Alpha143 因子值（自递归）

DolphinDB:
  def gtjaAlpha143(close){
      return accumulate(def(x,y){return iif(y>1,(y-1)*x,x)},
                        (close\\move(close,1)).transpose(),
                        take(1,cols(close))).transpose()
  }

递推语义拆解:
- r_t = close_t / close_{t-1}（日收益率比，>1 表示涨）
- 初始 Y_0 = 1（take(1,...)）
- accumulate: x=上一日因子 Y_{t-1}，y=当日 r_t
  Y_t = iif(r_t > 1, (r_t - 1) * Y_{t-1}, Y_{t-1})
      = 当日涨(r_t>1) → Y_t = 当日涨幅(r_t-1) * 昨日因子；当日跌/平 → Y_t = 昨日因子（不变）
- 即：只在上涨日，因子 = 当日涨幅 × 上一日因子；下跌日因子沿用昨日。

这本质是一个"上涨日才累积、下跌日冻结"的递归累积器——
  从初始1开始，每次上涨乘以当日涨幅，相当于"连续上涨的复利累积"。
  一旦下跌，因子冻结在下跌前的值，直到下次上涨才继续累积。

方向: 因子越大=近期连续上涨的复利累积越强→动量/强势逻辑。IC 定夺。
  注意自递归因子初值敏感（研报用1），长序列后初值影响衰减。

单标的实现：用 pandas 逐行递推（向量化困难，因递归依赖）。
"""
from __future__ import annotations

import pandas as pd

from base import FactorBase


class Alpha143Factor(FactorBase):
    name = "gtja_alpha143"

    def calc(self, df: pd.DataFrame) -> float | None:
        if len(df) < 2:
            return None
        close = df["close"]
        r = close / close.shift(1)  # r_t = close_t/close_{t-1}
        # 逐行递推：Y_0=1；Y_t = r_t>1 ? (r_t-1)*Y_{t-1} : Y_{t-1}
        y = 1.0
        rvals = r.iloc[1:].values  # 跳过第一日（r_0 为 nan）
        for rv in rvals:
            if pd.isna(rv):
                continue
            if rv > 1:
                y = (rv - 1) * y
            # else: y 不变（冻结）
        # 递归因子可能数值极小（连续乘涨幅），或冻结后长期不变；返回标量
        if pd.isna(y):
            return None
        return float(y)
