# fundflow_offline — 主力资金流离线数据层

A股**主力资金流**(东财口径)离线数据。本目录自包含,数据源不可达与离线回测分离:

- 拉取脚本在**能连东财 `push2his.eastmoney.com` 的网络**上跑;
- 数据落地后,读取端在本机**只读本地 parquet、不联网**即可回测。

## 文件

| 文件 | 作用 | 在哪跑 |
|---|---|---|
| `fetch_fundflow_standalone.py` | 全量拉取主力资金流历史(自包含) | 能连东财的网络 |
| `csi1000_symbols.txt` | csi1000 成分股清单(1000 只) | 脚本自动读 |
| `fundflow_reader.py` | 读取端:`load_fundflow(sym)` / `load_panel(syms)` | 本机回测 |
| `data_fundflow/` | 输出目录:`ff_{symbol}.parquet` | 拉取脚本生成,拷回本机 |

## 为什么单独放一个目录(背景)

本机访问东财资金流历史端点 `push2his/stock/fflow/daykline` 稳定 **HTTP 000 断连**(网络级阻塞,非限流)。
用户决定改在**别的网络**拉取,拉完把数据给回本机。因此拉取端与读取端完全解耦,本目录只负责资金流这一路。

## 用法

```bash
# ① 在能连东财的网络,冒烟拉前 5 只验证通 + 格式对
python fetch_fundflow_standalone.py --limit 5

# ② 全量 csi1000(断点续传,中断重跑接着拉)
python fetch_fundflow_standalone.py

# ③ 拉完把整个 data_fundflow/ 拷回本机 fundflow_offline/ 下

# ④ 本机回测
python fundflow_reader.py                                  # 自检/看覆盖范围
# 或
from fundflow_reader import load_fundflow, load_panel
df  = load_fundflow('000012')       # 单票 DataFrame{date, main_pct, ...}
pan = load_panel(symbols)           # {symbol: df}
```

## 存储格式(数据交接契约)

单票一个 parquet,文件名 `ff_{symbol}.parquet`(symbol 为 6 位不带前缀,如 `000012`),
`date` 升序唯一主键:

| 列 | 类型 | 含义 |
|---|---|---|
| date | datetime64[ns] | 交易日(升序,主键) |
| close | float64 | 收盘价(元) |
| pct_chg | float64 | 涨跌幅(%) |
| main_amt / main_pct | float64 | **主力**净流入-净额(元) / 净占比(%) |
| xlarge_amt / xlarge_pct | float64 | 超大单净流入-净额 / 净占比(%) |
| large_amt / large_pct | float64 | 大单净流入-净额 / 净占比(%) |
| mid_amt / mid_pct | float64 | 中单净流入-净额 / 净占比(%) |
| small_amt / small_pct | float64 | 小单净流入-净额 / 净占比(%) |

> 说明:主力 = 超大单 + 大单;四个单子各净额+净占比两列。口径与东财个股资金流一致(akshare `stock_individual_fund_flow`,已核实 1.18.94 源码)。

## 下一步(接到因子流程)

数据到位后,用 `main_pct`/`main_amt` 及其时序(如 5/10 日累计主力占比)构造截面因子,
走量化系统因子 gate:
**门1 IC → 门2 相关性 → 门3 正交残差 → 门4 组合 A/B**
(见 `new-factor-process-checklist` / csi1000 做厚主线 #29)。

## 防封 / 断点续传(拉取脚本内建)

- 单线程串行 + 0.3s/票 + BAN_MARKERS 识别封禁 + BAN_PAUSE=60s 整体暂停;
- 已有缓存自动跳过,可中断重跑续传;
- 原子写(tempfile + `os.replace`),崩溃不损坏已存文件。
