# Qlib Alpha158 因子库调研

> 调研于 2026-09-03。用户原话提到"vwapAlpha158"并给 DolphinDB 教程链接。经核实：Alpha158 因子库**源自微软 Qlib 自研**（DolphinDB 只是实现了它），不是 GTJA191 的 #158 号因子。本文厘清来源、因子构成、所需数据、Qlib 官方基准回测表现，并评估对本系统的移植价值与路线。

## 一、来源与定位（一手核实）

| 维度 | 结论 |
|---|---|
| 原始出处 | **微软 Qlib**（microsoft/qlib，48k★），论文 arxiv:2009.11189 |
| 性质 | Qlib 内置两套标准量价因子库之一（另一套 Alpha360） |
| 常见误解 | ❌ 不是 WorldQuant Alpha101 的一部分；❌ 不是 GTJA191 的 #158；❌ 不是 DolphinDB 自研 |
| DolphinDB 角色 | 仅用 DolphinDB 脚本实现了全部 158 个因子函数（`alpha158.dos` 模块），非设计者 |

> 勘误：本地 `gtja191_port/factors/alpha158.py` 是 **GTJA191 的 #158 号因子**（日内振幅率 (H-L)/C，已测 IC=-0.0842），与 Qlib Alpha158 因子库**毫无关系**，仅编号撞车。本文调研的是后者。

## 二、因子总数与构成（源码级，来自 qlib/contrib/data/loader.py）

**总计 158 个** = 9（kbar）+ 4（price 默认）+ 145（rolling 全量）。

### 1. kbar 类（9个）—— K线形态
KMID/KLEN/KMID2/KUP/KUP2/KLOW/KLOW2/KSFT/KSFT2，全部刻画当日 K 线各部分相对开盘价或振幅的比例。**本质就是上下影线/实体形态**——本系统已结案的"上下影线日线"路线在此有完整对照。

### 2. price 类（默认4个）
OPEN0/HIGH0/LOW0/VWAP0 = 当日开/高/低/VWAP 除以收盘价。**唯一用到 VWAP 的就是 VWAP0 这一个因子**。

### 3. rolling 类（145个 = 29算子 × 5窗口[5/10/20/30/60日]）
| 算子族 | 算子 | 数量 |
|---|---|---|
| 价格趋势 | ROC/MA/STD/BETA/RSQR/RESI/MAX/MIN/QTLU/QTLD/RANK/RSV | 60 |
| 极值位置 | IMAX/IMIN/IMXD | 15 |
| 价量相关 | CORR/CORD | 10 |
| 涨跌统计 | CNTP/CNTN/CNTD/SUMP/SUMN/SUMD（类 RSI） | 30 |
| 纯量 | VMA/VSTD/WVMA/VSUMP/VSUMN/VSUMD | 30 |

**结构特点**：固定 5 个窗口的滚动统计，规整统一。与 WQ101（复杂横截面公式）、GTJA191（技术指标混合）风格不同——Alpha158 偏"传统量价技术指标的系统化整合"。

## 三、所需输入数据

| 字段 | 用到该字段的因子 |
|---|---|
| open, close, high, low | kbar 全部 + rolling 多数 |
| volume | rolling 价量/纯量类（CORR/CORD/VMA/VSTD 等） |
| **vwap** | **仅 VWAP0 一个**（price 类） |

**关键**：158 个里只有 1 个真依赖 VWAP。其余 157 个纯 OHLCV 可跑。本系统日线缓存无原生 VWAP，但有成交额可反推（见 `gtja191_port/fetch_amount.py`），补 VWAP0 成本极低。

## 四、Qlib 官方基准回测（A股，关键决策依据）

来源：Qlib examples/benchmarks/README.md。均为 20 次随机种子均值。

### CSI300 / Alpha158（主要模型）
| 模型 | IC | ICIR | 年化收益 | 信息比率 | 最大回撤 |
|---|---|---|---|---|---|
| Linear | 0.0397 | 0.300 | 6.92% | 0.921 | -15.09% |
| LightGBM | 0.0448 | 0.366 | 9.01% | 1.016 | -10.38% |
| XGBoost | 0.0498 | 0.378 | 7.80% | 0.907 | -11.68% |
| **DoubleEnsemble** | **0.0521** | **0.422** | **11.58%** | **1.343** | **-9.20%** |
| MLP | 0.0376 | 0.285 | 8.95% | 1.141 | -11.03% |
| LSTM/GRU/ALSTM | 0.03~0.04 | 0.24~0.28 | 3.4~4.7% | 0.5~0.7 | -10~12% |
| TRA | 0.0440 | 0.354 | 7.18% | 1.084 | -7.60% |

### CSI500 / Alpha158
| 模型 | IC | ICIR | 年化收益 | 信息比率 | 最大回撤 |
|---|---|---|---|---|---|
| **LightGBM** | **0.0399** | **0.407** | **12.84%** | **1.565** | **-6.35%** |
| Linear | 0.0332 | 0.304 | 3.82% | 0.172 | -48.76% |
| CatBoost | 0.0345 | 0.286 | 4.96% | 0.598 | -14.96% |

### Alpha360 vs Alpha158（CSI300, LightGBM）
| 数据集 | IC | 年化 | IR | 最大回撤 |
|---|---|---|---|---|
| Alpha158 | 0.0448 | 9.01% | 1.016 | -10.38% |
| Alpha360 | 0.0400 | 5.58% | 0.763 | -6.59% |

**读数要点**：
- Alpha158 单因子 IC 普遍 0.03~0.05，**与本系统 GTJA191 实测区间接近**（191 真增量 IC 也在 0.02~0.05）。无明显优于现有因子库的信号。
- **表格模型（LightGBM/XGBoost/DoubleEnsemble）显著优于时序模型（LSTM/GRU/Transformer）**——Alpha158 是表格特征，时序模型在 20 特征子集上跑反而更差。
- DoubleEnsemble（CSI300）和 LightGBM（CSI500）是各自最优，IR 1.3~1.6，回撤可控。
- 这是 **T+1买T+2卖的超短 horizon**（标签 = Ref($close,-2)/Ref($close,-1)-1，即次日相对次后日收益），与本系统月频 horizon=21 口径**完全不同**，IC 不可直接对比。

## 五、与本系统的关系评估

### 5.1 重叠度（核心问题）
Alpha158 的 158 个里，大量因子本系统**已有等价物**：
- MA/STD/MAX/MIN/RANK/ROC → 本系统 momentum/reversal/low_vol 已覆盖趋势与波动
- RSV/CNTP/SUMP（类 RSI）→ 与 reversal(60) 重叠
- CORR/CORD（价量相关）→ 与 GTJA191 alpha99（量价协方差，已测弃用）同维度
- kbar 上下影线 → 本系统已结案（上下影线日线失效）
- VMA/VSTD（量波动）→ 与流动性代理重叠（已验证流动性是伪装高发区）

**独立新维度候选**（本系统缺失的）：
- **BETA/RSQR/RESI**：价格对时间的线性回归斜率/R²/残差——本系统无"趋势线性度"因子
- **IMAX/IMIN/IMXD**：距区间最高/最低价的天数位置——本系统无"极值时序位置"因子
- **WVMA**：加权量价波动——比纯 VSTD 多一层价量交互

### 5.2 移植 ROI 判断
| 维度 | 评估 |
|---|---|
| 数据成本 | 低（157/158 纯 OHLCV，1 个补 VWAP） |
| 实现成本 | 中（29 个 rolling 算子要逐个写，但结构规整可批量） |
| 增量预期 | **中低**——大量因子与现有重叠，真增量可能就 BETA/RSQR/RESI/IMAX/IMIN/WVMA 这几个 |
| 风险 | Alpha158 是为**短 horizon + ML 表格模型**设计的；本系统是**月频 + 线性 ICIR**，因子有效性可能随 horizon 漂移 |

## 六、建议路线（供决策，未改系统源码）

### 路线A（推荐）：只移植"独立新维度"子集，走标准 5 道门
不移植全 158 个，只挑本系统缺失的 6~8 个（BETA/RSQR/RESI/IMAX/IMIN/IMXD/WVMA），逐个走 [[new-factor-process-checklist]]：
- 门1 IC 检验（月频 horizon=21，注意 Qlib 基准是短 horizon，方向可能反转）
- 门2 vs 当前 11 因子相关性（用 verify_candidates_gate23.py，对照基准=当前 11 因子非旧快照）
- 门3 正交残差
- 门4 walk-forward A/B（baseline=当前 20 只因子集）

**省时点**：门1-3 不跑组合，几秒一个。筛完真增量的再进组合 A/B。

### 路线B：全量移植 + ML 表格化（重）
照搬 158 个 + 上 LightGBM/DoubleEnsemble 合成。但：
- 本系统 ML 分支已实测跑输线性（[[ml-ab-negative-excess-diagnosis]]），且因子数 11→158 易过拟合
- Alpha158 设计 horizon 与本系统不同，需先验短 horizon 有效性再迁月频
- ROI 不明，不推荐作首选

### 路线C：暂不移植，优先验证现有 CPPI/仓位层
当前 CPPI 真 A/B 在跑（仓位层回撤攻坚），因子层已 11 个够用。**因子扩展的边际收益（路线A）可能低于仓位层 CPPI 的边际收益**（CPPI 仿真把回撤 -68%→-31%）。建议等 CPPI 真 A/B 出结果再定因子层是否需要扩。

## 七、与既有调研的关系

- 本系统已完整调研并实测：WorldQuant Alpha101（文献级，未全量实测）、GTJA191（190/191 全量实测，见 [[alpha101-gtja191-survey]]）
- **Alpha158 是第三个主流量价因子库**，定位"Qlib 自研的表格化量价特征"，与 101/191 三足鼎立但来源独立
- 三者共性：A 股上单因子 IC 都在 0.03~0.05 区间，无明显"银弹"；差异在结构（101 横截面公式 / 191 技术指标混合 / 158 规整滚动统计）

## 附录：参考来源
1. DolphinDB 教程（实现层）：https://docs.dolphindb.com/zh/tutorials/alpha_158.html
2. Qlib 源码 loader.py（因子定义）：https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/loader.py
3. Qlib 基准回测：https://github.com/microsoft/qlib/blob/main/examples/benchmarks/README.md
4. Qlib 论文：arxiv:2009.11189
