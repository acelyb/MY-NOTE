# 期货 CTA / A股 双线 — 开源方案（v4，决策已定）

> 状态：**方案定稿，待执行**。
> 基线：`futures_new_factor` @ 2026-11-03
> 仓库规模：226 个 .py / 43,326 行；32 个 factors 文件；12 个 CTA 策略；19 个期货脚本；27 个测试文件
> 前序版本：v1（只开源期货线）、v2（全开源+配置分层）、v3（框架/alpha 分层）已废弃

---

## 一、已定决策

| # | 决策 | 结果 |
|---|---|---|
| 1 | 仓库结构 | **双仓库**：公开框架 + 私有 alpha |
| 2 | 私有库托管 | **GitHub 私有库**，通过 **submodule** 挂载到 `private/` |
| 3 | 许可证 | **AGPL-3.0** |
| 4 | `docs/` 归属 | 实验结果与流程（结论、台账、quant_system）→ **私有库** |
| 5 | 配置归属 | 因子权重、风控参数、`nav` → **私有库**；token → **环境变量** |
| 6 | 缓存路径 | 相对路径（现有实现已支持），进私有库 |
| 7 | AGPL 网络条款 | 仅本地运行，不提供服务 → 不触发传染；若未来卖 API 需先咨询律师 |

---

## 二、切分原则

**判据**：别人拿到这些代码，能直接复现你的收益吗？

| 层 | 内容 | 归属 |
|---|---|---|
| 接口 / 引擎 | `StrategyBase.on_bar`、`FactorBase.calc_cross_section`、两层合成 | 🟢 公开 |
| 数据 | 换月拼接、复权、缓存、fail-loud | 🟢 公开 |
| 风控骨架 | `FuturesRiskManager.apply()` 的四步顺序 | 🟢 公开 |
| 风控参数 | `dd_tol=0.15` / `dd_floor=0.25` / `sigma_target=0.12` | 🔴 私有 |
| 因子实现 | 32 个 factors 文件 | 🔴 私有 |
| 因子权重 | 11 个生产因子的 w 值 | 🔴 私有 |
| 策略实现 | `strategies/cta/` 12 个策略 | 🔴 私有 |
| 示例 | 2 个玩具因子 + 双均线 | 🟢 公开 |

### 关键事实：策略本体只有 75 行

```
strategies/cta/tsmom.py        75 行   ← 生产信号全部来源
scripts/plot_swing_levels.py  1520 行   ← 画图，是策略本体的 20 倍
```

**alpha 不在策略代码里，在配置权重 + 合成方式 + 风控数值里。**

---

## 三、仓库结构

```
GitHub 公开：acelyb/junior-quant-framework   (AGPL-3.0)
│
├── jq_framework/
│   ├── data/
│   │   ├── fetchers/
│   │   │   ├── fetcher.py            股票日线
│   │   │   ├── fetcher_futures.py    期货（换月拼接，核心价值）
│   │   │   ├── _ratelimit.py  _source.py  snapshot.py
│   │   ├── cache.py
│   ├── strategies/
│   │   ├── base.py                   StrategyBase + Signal
│   │   ├── adapter.py                backtrader 适配
│   │   └── examples/
│   │       ├── dual_ma.py            示例策略
│   │       └── donchian.py           示例策略
│   ├── factors/
│   │   ├── base.py                   FactorBase + 截面工具
│   │   ├── composite.py              两层合成引擎
│   │   ├── composite_ml.py
│   │   ├── ic.py  ic_report.py  corr.py
│   │   └── examples/
│   │       └── demo_factors.py       20日动量 + 20日反转
│   ├── backtest/
│   │   ├── direction.py              ← 新增：DirectionPolicy 接口
│   │   ├── runner.py
│   │   ├── portfolio_runner.py
│   │   ├── walk_forward.py
│   │   ├── futures_walk_forward.py
│   │   ├── limits.py  intraday_filter.py
│   ├── risk/
│   │   ├── manager.py  futures_risk.py
│   │   ├── vol_target.py  cppi.py  timing.py
│   ├── portfolio/futures_sizing.py
│   ├── signals/daily_runner.py
│   ├── config/loader.py              ← 新增：统一配置加载
│   └── examples/run_demo.py          端到端示例（保证能跑）
│
├── private/                          ← submodule → junior-quant-alpha
├── configs/example.yaml              指向 jq_framework.examples
├── tests/framework/                  17 个，公开可跑
├── docs/                             设计 + 使用（脱敏）
├── pyproject.toml
├── LICENSE (AGPL-3.0)
├── .gitmodules
└── README.md


GitHub 私有：acelyb/junior-quant-alpha
│
├── jq_alpha/
│   ├── factors/                      32 个真实因子
│   │   ├── momentum.py  reversal.py  low_vol.py  ivol.py
│   │   ├── size.py  value_ep.py  quality_roe.py  growth_rev.py
│   │   ├── gtja191_extras.py  gtja191_h10.py
│   │   ├── alpha158.py  wq101_*.py
│   │   └── vol_dryup.py  quiet_breakout.py  pullback_rebound.py
│   ├── strategies/cta/               12 个策略
│   └── direction/                    私有 DirectionPolicy 实现
│
├── configs/
│   ├── futures.yaml                  期货：真实品种/参数/风控数值
│   └── stock.yaml                    A股：11 个因子权重
│
├── docs/
│   ├── 期货CTA_结论.md               完整版（含具体读数）
│   ├── 期货CTA_调研测试台账.md       完整版
│   └── quant_system/                 内部实验记录
│
├── tests/integration/                10 个依赖私有实现的测试
└── pyproject.toml
```

---

## 四、配置机制

### 4.1 配置文件进私有库（多机一致）

```
private/configs/futures.yaml  ← 进版本控制，含真实权重
private/configs/stock.yaml    ← 进版本控制，含 11 个因子权重
```

**只有 token 走环境变量**，其余全部入库：

```bash
export TUSHARE_TOKEN='xxx'    # 唯一需要手动设的
```

### 4.2 配置发现链

```python
# jq_framework/config/loader.py
SEARCH = [
    Path("private/configs") / f"{market}.yaml",   # 私有库，优先
    Path("configs") / f"{market}.yaml",           # 公开示例
]
```

没有 submodule 的外部用户自动落到 `configs/example.yaml`，开箱可跑。

### 4.3 多机同步（重要）

submodule 的父仓库记录的是**具体 commit**，所以：

```bash
# A 机器：改了 private/configs/futures.yaml → 在 private/ 里 commit + push
# B 机器：git pull 公开仓库 → private/ 还是旧的！
```

**B 机器需要额外一步：**

```bash
git submodule update --remote private     # 或 cd private && git pull
```

这条必须写进 README。

### 4.4 缓存路径

现有实现已是相对路径，无需改动：

```python
# data/fetchers/fetcher.py:68
root = Path(__file__).resolve().parent.parent.parent
return root / cache_dir / f"{key}.parquet"

# data/fetchers/snapshot.py:66
p = Path(d)
return p if p.is_absolute() else REPO_ROOT / p
```

⚠️ **重构时必须改**：`parent.parent.parent` 靠层级数推导根目录，代码移入 `jq_framework/` 后会多一层，指错位置。改用显式包根。

---

## 五、API 契约

### 5.1 StrategyBase

```python
class StrategyBase:
    default_params: dict = {}

    def __init__(self, params: dict | None = None):
        self.params = {**self.default_params, **(params or {})}

    @abstractmethod
    def on_bar(self, bars: pd.DataFrame) -> Signal:
        """bars: 到当前 bar 为止的历史 [date,open,high,low,close,volume]"""
```

**契约**：
- 无状态禁止：策略不得保存跨 bar 状态（分窗引擎逐段重建实例）
- `direction ∈ {"long","short","flat","hold"}`
- `target_pos ∈ [0, 1]`

### 5.2 FactorBase

```python
class FactorBase:
    name: str = "base"
    family: str = ""
    process_method: str = "rank"           # ← 参数化，公开默认值
    winsorize_quantile: tuple = (0.01, 0.99)  # ← 参数化
    industry_neutral: bool = False

    @abstractmethod
    def calc(self, df: pd.DataFrame) -> float | None: ...

    def calc_series(self, df: pd.DataFrame) -> pd.Series | None: ...
```

**契约**：
- 方向约定：值越大 → 预期未来收益越高（负向因子子类取负号）
- 必须因果：`calc` 只能用 `df` 截至最后一行的数据
- `calc_series` 与 `calc` 口径逐字一致（测试守护）

### 5.3 DirectionPolicy（新增）

现在硬编码在 `walk_forward.py:102`，抽出：

```python
class DirectionPolicy(ABC):
    @abstractmethod
    def fit(self, factor, train_dfs, horizon, freq) -> tuple[float, float, str]:
        """返回 (weight, sign, reason)"""

# 公开实现
class StaticDirection(DirectionPolicy):    # 配置静态权重 + 训练段 IC 符号
class ICRatioDirection(DirectionPolicy):   # ICIR 幅度加权
```

### 5.4 动态加载（保持现状）

```python
module = importlib.import_module(spec["module"])
cls = getattr(module, spec["class"])
factor = cls(params=spec.get("params", {}))
```

`spec["module"]` 是任意字符串 → 私有包只要可 import 就能被加载。

---

## 六、执行计划

### 阶段 0：清障（1–2 小时）

| # | 事项 | 位置 | 动作 |
|---|---|---|---|
| 1 | 删除坏脚本 | `.ab_alpha_sub.py`、`.rollwin_sub.py` | 删除（`sys.path.insert` 指向不存在的 `code/junior_quant`，本地也是坏的） |
| 2 | 修硬编码路径 | 9 个文件（`factors/gtja191_extras.py:2`、`wq101_prod.py:99`、`scripts/run_daily_ml.sh:13`、`scripts/futures_level_validity_probe.py:48`、`verifications/` 等） | 改 `Path(__file__).resolve().parents[N]` |
| 3 | LICENSE | 根目录 | 加 AGPL-3.0 |
| 4 | 移除坏路径残留 | `docs/env.md`（1091 行个人环境笔记） | 移出公开版 |

### 阶段 1：接口抽取（1–2 天）—— **最核心**

| 文件 | 改动 | 验证 |
|---|---|---|
| `factors/base.py` | `winsorize` 分位、`process_method`、`industry_neutral` 参数化 | 默认值 = 现值（0.01/0.99/rank）→ 逐位零回归 |
| `backtest/walk_forward.py` | `_train_factor_directions` 抽成 `DirectionPolicy` | 同配置下结果逐位一致 |
| `backtest/futures_walk_forward.py` | 同上 | 同上 |
| `risk/futures_risk.py` | 确认所有数值从 config 读（已基本完成） | 检查无硬编码 |
| 新建 `config/loader.py` | 统一替换 62 处 `yaml.safe_load` | 行为不变 |

**关键：本阶段必须在拆仓库之前完成。** 拆完再改，行为变化难以定位。

### 阶段 2：拆分仓库（1 天）

| 步骤 | 动作 |
|---|---|
| 1 | 新建 `jq_framework/` 命名空间，公开代码移入，改所有 import |
| 2 | 新建 GitHub 私有库 `junior-quant-alpha`，alpha 代码移入 |
| 3 | 公开仓库 `git submodule add git@github.com:acelyb/junior-quant-alpha.git private` |
| 4 | 写 `examples/`（2 个玩具因子 + 双均线 + `run_demo.py`） |
| 5 | 测试分层：`tests/framework/`（17 个）与 `tests/integration/`（10 个） |

### 阶段 3：补测试与文档（1–2 天）

| 项 | 现状 | 目标 |
|---|---|---|
| A股测试 | **0 例** | 补 15–20 例核心因子 |
| 框架测试 | 17 个可独立跑 | 保持 |
| `pyproject.toml` | 无 | 两个仓库各一份 |
| README | 需重写 | 诚实写清绝对表现 + 迁移流程 |
| `docs/EXTENDING.md` | 无 | 如何写因子 / 策略 / DirectionPolicy |

### 阶段 4：验收（半天）

| 检查 | 方法 |
|---|---|
| 公开框架独立跑 | 干净环境 clone → `pip install -e .` → `python -m jq_framework.examples.run_demo` 有输出 |
| 公开测试全绿 | 17 个框架测试通过 |
| 私有包挂上 | `git submodule update --init` → `pip install -e private/` → 配置指向私有模块 → 跑通 |
| **零回归** | 私有包安装前后回测结果逐位一致 |
| AGPL 合规 | LICENSE + README 声明 + `pyproject.toml` 的 `license` 字段 |

**总计 4–5 天。**

---

## 七、迁移到新机器（完整流程）

```bash
# 1. clone（带 submodule）
git clone --recurse-submodules git@github.com:acelyb/junior-quant-framework.git
cd junior-quant-framework

# 2. 如果忘了 --recurse-submodules
git submodule update --init --recursive

# 3. 安装
pip install -e .
pip install -e private/

# 4. 唯一手动的：token
export TUSHARE_TOKEN='xxx'

# 5. 直接能跑（配置随 submodule 一起下来了）
python -m jq_framework.examples.run_demo
python -m scripts.futures_combination_signal
```

### 日常同步（两台机器）

```bash
# 改了私有库（因子/配置）
cd private && git add . && git commit -m "..." && git push && cd ..
git add private && git commit -m "bump alpha submodule"

# 另一台机器拉取
git pull
git submodule update --remote private    # ← 关键：这步不能漏
```

---

## 八、外部用户体验

```bash
git clone https://github.com/acelyb/junior-quant-framework.git
cd junior-quant-framework
pip install -e .
python -m jq_framework.examples.run_demo
```

- `private/` 是空目录（无权限拉取）
- `git status` 显示 "modified: private (untracked content)" —— README 需说明
- 自动落到 `configs/example.yaml`，用 `examples/` 的玩具因子
- 17 个框架测试可跑

README 需明确写：

> 本仓库的 `private/` 是作者的私有 alpha 模块（submodule）。
> 你不需它即可体验框架：`python -m jq_framework.examples.run_demo`。
> 若要接入自己的实现，见 `docs/EXTENDING.md`。

---

## 九、风险清单

| # | 风险 | 缓解 |
|---|---|---|
| 1 | 外部用户首次 clone 困惑于空 `private/` | README 顶部说明 |
| 2 | submodule 同步遗漏导致配置不一致 | README 写清两步同步流程 |
| 3 | `parent.parent.parent` 重构后路径错误 | 阶段 1 改为显式包根 |
| 4 | 62 处 `yaml.safe_load` 改造引入回归 | 阶段 1 单独提交 + 逐位对比 |
| 5 | 依赖腐化（akshare/backtrader） | 加 `requirements-lock.txt` |
| 6 | 数据源 ToS（akshare 抓取） | README 加"遵守各源 ToS"；不发布数据 |
| 7 | AGPL 网络条款若未来卖 API | 先咨询律师 |
| 8 | 结论被断章取义 | README 诚实说明绝对表现（TSMOM 夏普 0.26） |

---

## 十、已定项（2026-11-03 用户拍板）

| # | 问题 | 决定 |
|---|---|---|
| 1 | 脱敏版台账是否放公开库 | **要**（方案 C）——保留"试过什么/结论是什么"，删掉精确读数（ΔIR/夏普/权重），其余标注"见私有库" |
| 2 | `examples/` 的 demo 组合 | **双均线 + 20日动量**（期货 + A股各一个端到端演示） |
| 3 | 命名空间 | **`jq_framework`（公开）/ `jq_alpha`（私有）** |
| 4 | 私有库认证 | **SSH key**（`git@github.com:acelyb/junior-quant-alpha.git`）；`.gitmodules` 中 URL 对外可见属预期行为 |

---

## 十一、诚实的价值评估

**这套方案的价值不在 star 数（用户明确表示不在乎），在于：**

1. **可验证的工程能力**：换月拼接的正确实现、L1O 治理管线、62 份实验纪律文档
2. **知识产权边界意识**：submodule 让外部看到"这里接了私有模块"，是专业性的体现
3. **迁移可复现**：clone + install + token 三步上手

**但要清楚它不展示什么：**
- 系统实际表现是负的（期货 TSMOM built 口径 −0.44%/夏普 −0.18）
- 开源的是一个"如何正确建系统"的框架，不是"如何赚钱"的策略

**真正的最优展示可能是三篇技术博客**（换月拼接的坑、L1O 治理、八规则为何全否），但这是另一条路，不在本方案范围内。
