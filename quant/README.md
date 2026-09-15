# Quant

个人量化系统（quant_system）的研究与笔记。分三块：`research/` 因子库与系统调研、`futures/` 期货CTA线、`plan/` 落地计划，以及根部的 `basic.md` 学习笔记。

> 调研文档于 2026-09-15 从 `~/Documents/code/survey/` 迁入，统一纳入 git 版本控制。旧目录保留空骨架作未来调研落点。

## 导航

### 学习笔记
- [BASIC](basic.md) — 面板/截面/时间序列数据概念
- [TODO](todo.md) — alpha/beta/SML/CML 待做清单

### research/ — 因子库调研与系统诊断
- [主流量价因子库调研](research/主流量价因子库调研.md) — WorldQuant Alpha101 / 国泰君安191 / Qlib Alpha158 三库合一事实来源
- [Alpha101与国泰君安191因子调研](research/Alpha101与国泰君安191因子调研.md) — 一手核验 + 常见错误勘误
- [QlibAlpha158因子库调研](research/QlibAlpha158因子库调研.md) — 厘清来源（Qlib 自研，非 GTJA191 #158）
- [三因子库ML重测候选](research/三因子库ML重测候选.md) — 线性 ICIR 淘汰 vs ML 复活重测
- [QuantaAlpha结合调研](research/QuantaAlpha结合调研.md) — LLM 轨迹进化因子挖掘评估
- [量化工程调研](research/量化工程调研.md) — 系统短板诊断（幸存者偏差/样本外可信度/CPPI 风控）
- [gtja191_dolphindb](research/gtja191_dolphindb/) — DolphinDB 实现（.dos 脚本）
- [gtja191_port](research/gtja191_port/) — Python 移植实证（~200 因子 + 验证脚本）

### futures/ — 期货CTA线
- [期货量化调研](futures/期货量化调研.md) — 业界流程/因子/风控/系统构建
- [期货因子_业界通行提法_旁证](futures/期货因子_业界通行提法_旁证.md) — 因子桶的旁证清单（线索源）

### plan/ — 落地计划
- [全市场选股域迁移计划](plan/全市场选股域迁移计划.md) — csi_all 全频谱选股工程
