"""回撤控制叠加回测器 —— 验证"仓位层全局乘数"能否压回撤、代价多大。

为什么做这个(回答用户"风控很重要,回撤控制不满意,业界主流做法"):
  诊断结论:quant_system 现有三层风控——个股止损止盈、个股波动率目标、RSRS 大盘择时(已禁用)——
  都挡不住系统性回撤。个股级机制对相关性视而不见(崩盘时相关性≈1,组合真实波动爆表而个股 vol 目标
  系统性低估);组合级那把扳手(RSRS)关着。缺口正是"组合级回撤控制"。
  业界主流对此有:组合级 vol-target、CPPI 地板、regime 减仓、风险预算、Kelly、尾部对冲。
  本脚本验证最通用且最对口的两个——组合级 vol-target 与 CPPI 地板——叠加在仓位层的效果。

机制(两把都是"对整本书施加的标量仓位乘数 mult_t",复用 MarketTimer 的接入哲学,不碰选股/因子):
  应用口径(防未来函数):信号在 t 日收盘后可知 → 决定 t+1 开盘仓位 mult_{t+1} → 承担 t+1 收益。
    NAV_{t+1} = NAV_t · (1 + mult_{t+1} · r_{t+1}) · (1 - cost_{t+1})
    cost_{t+1} = cost_rate · |mult_{t+1} - mult_t|   (t+1 开盘从 mult_t 调到 mult_{t+1} 的换手成本)
  (A) 组合级 vol-target:mult_t = σ_target / σ_{t-1},σ 用过去 W 日实现波动率×√252,clip[min,max]。
      控"风险水平轴":组合波动↑(崩盘/相关性飙升)→ 自动降杠杆。修个股 vol 忽略相关性的洞。
  (B) CPPI 地板:cushion_t = (NAV_t - floor_t)/NAV_t,floor = (1-max_dd_tol)·HWM;mult = min(m·cushion, max)。
      控"损失预算轴":回撤加深→cushion 缩→减仓,接近地板→接近清仓。把回撤上限变成被控变量。
      与 vol-target 互补:vol-target 在 V 型反弹(波动高但无回撤)可能误杀,CPPI 只看回撤深度。

代理净值(关键诚实标注):
  用官方真实中证1000指数(index_real_csi1000,市值加权、含调入调出、2015-2026 全期)日收益作"策略代理"。
  不是系统的等权成分股基准(get_index_daily),两者口径不同——代理是真实可交易 beta,系统基准是等权偏小盘合成。
  **叠加器是线性仓位乘数 r'_t=mult_t·r_t,对任意策略净值作用机制一致**,故用代理验证"机制能否压回撤、
  压多少、收益代价方向"的结论是稳的,只有绝对数字因代理无 alpha 而异(主策略有 alpha,叠加会砍掉部分 alpha,
  权衡不同——本脚本量化的是机制本身,非主策略的最终数字)。

约束:只读 quant_system 缓存(index_real_csi1000.parquet),写在 survey 独立目录,绝不改源码。单进程秒级。
成本口径对齐 walk_forward:净仓位变动×双边均值(0.0015)= (cost_buy+cost_sell)/2,加减仓同价。
去抖动(debounce):连续乘数天生高换手,加阈值再平衡(偏离>阈值才调),复刻系统 turnover_buffer。
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PORT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PORT_DIR))

from cache_reader import load_index_daily  # noqa: E402

UNIVERSE = "csi1000"
COST_BUY = 0.00125   # 佣金0.025%+滑点0.1%(单边买,对齐 config cost)
COST_SELL = 0.00175  # 佣金0.025%+滑点0.1%+印花税0.05%(单边卖)
COST_TURNOVER = (COST_BUY + COST_SELL) / 2  # =0.0015,系统 rebal 口径:净仓位变动×双边均值
RISK_FREE = 0.02    # 夏普扣减(对齐 _stats)


def _stats(nav: pd.Series, mult: pd.Series, name: str) -> dict:
    """复刻 walk_forward._stats 口径 + 暴露/换手统计。"""
    nav = nav.dropna()
    if len(nav) < 2:
        return {"name": name, "n_days": 0}
    daily_ret = nav.pct_change().dropna()
    n_years = len(nav) / 252
    total_ret = nav.iloc[-1] / nav.iloc[1] - 1  # 从首个有效点起
    ann_ret = (1 + total_ret) ** (1 / n_years) - 1 if n_years > 0 else 0
    peak = nav.cummax()
    max_dd = (nav / peak - 1).min()
    vol = daily_ret.std() * np.sqrt(252)
    sharpe = (daily_ret.mean() * 252 - RISK_FREE) / vol if vol > 0 else 0
    calmar = ann_ret / abs(max_dd) if max_dd < 0 else np.nan
    avg_mult = mult.reindex(nav.index).mean()
    turnover = mult.diff().abs().mean()  # 日均仓位变动
    return {
        "name": name, "n_days": len(nav), "ann_return": ann_ret, "max_dd": max_dd,
        "vol": vol, "sharpe": sharpe, "calmar": calmar,
        "avg_exposure": avg_mult, "avg_turnover": turnover,
    }


def _apply(r: pd.Series, mult: pd.Series, cost_rate: float, debounce: float = 0.0) -> tuple[pd.Series, pd.Series]:
    """叠加仓位乘数 + 换手成本,返回 (nav, 实际mult)。

    防未来函数:mult.iloc[t] 只用 ≤t-1 信息,承担 r.iloc[t] 收益。
    成本口径对齐 walk_forward:净仓位变动×双边均值(0.0015),加减仓同价。
    debounce>0:去抖动——只当目标mult偏离实际mult超过阈值才调,复刻系统 turnover_buffer 思路。
      这是 CPPI/vol-target 落地的关键:连续乘数不抖动则换手失控,业界都带阈值再平衡。
    """
    aligned = mult.reindex(r.index).ffill().fillna(1.0)
    if debounce > 0:
        actual = pd.Series(index=r.index, dtype=float)
        cur = 1.0
        for i in range(len(aligned)):
            target = aligned.iloc[i]
            # 用 t-1 实际仓位 cur 决定是否再平衡(避免未来函数:再平衡决策只用历史)
            if i == 0 or abs(target - cur) > debounce or pd.isna(cur):
                cur = target
            actual.iloc[i] = cur
        aligned = actual
    cost = cost_rate * aligned.diff().abs().fillna(0.0)
    net = aligned * r - cost
    nav = (1 + net).cumprod()
    nav.iloc[:1] = 1.0  # 起点
    return nav, aligned


def _vol_target_mult(r: pd.Series, sigma_target: float, window: int,
                     min_exp: float, max_lev: float) -> pd.Series:
    """组合级 vol-target 仓位乘数。σ_{t-1} 决定 t 日仓位。"""
    realized = r.rolling(window, min_periods=window // 2).std() * np.sqrt(252)
    mult = sigma_target / realized.replace(0, np.nan)
    mult = mult.clip(min_exp, max_lev)
    return mult.shift(1)  # 用 t-1 的 σ 决定 t 仓位


def _cppi_mult(nav_proxy: pd.Series, max_dd_tol: float, m_mult: float,
               max_lev: float, min_exp: float) -> pd.Series:
    """CPPI 地板仓位乘数。floor=(1-max_dd_tol)·HWM;t 日收盘 NAV 决定 t+1 仓位。
    nav_proxy: 无叠加的代理净值(用于算 HWM/cushion,与叠加后 NAV 解耦避免反馈振荡)。
    """
    hwm = nav_proxy.cummax()
    floor = (1 - max_dd_tol) * hwm
    cushion = (nav_proxy - floor) / nav_proxy
    cushion = cushion.clip(0, None)  # 跌破地板→cushion=0→清仓
    mult = (m_mult * cushion).clip(min_exp, max_lev)
    return mult.shift(1)  # t 收盘 cushion 决定 t+1 仓位


def _combine(*mults: pd.Series) -> pd.Series:
    """多把扳手组合:取乘积(都收敛于"减仓"语义时取乘积最保守)。"""
    out = None
    for m in mults:
        out = m if out is None else out * m
    return out


def main():
    idx = load_index_daily(UNIVERSE)
    if idx is None or idx.empty:
        print(f"无 {UNIVERSE} 指数缓存,退出。")
        return
    idx = idx.set_index("date")
    r = idx["close"].pct_change()
    start = pd.Timestamp("2020-01-01")
    r = r[r.index >= start].dropna()
    print(f"代理: 官方真实中证1000指数, {r.index[0].date()}~{r.index[-1].date()} ({len(r)} 日)")
    print(f"成本: 净仓位变动×双边均值 {COST_TURNOVER:.2%} | 无风险 {RISK_FREE:.0%}\n")

    # 无叠加基准(代理 beta 本身)
    base_nav = (1 + r).cumprod()
    base_nav.iloc[:1] = 1.0
    base_mult = pd.Series(1.0, index=r.index)

    # 配置网格(对比机制,非全参数扫描)
    # 去抖动 debounce=0.10:目标仓位偏离实际>10%才再平衡(复刻系统 turnover_buffer,控换手)
    configs = [
        ("baseline 无叠加", base_mult, 0.0),
        ("vol-target σ=15% W=60", _vol_target_mult(r, 0.15, 60, 0.2, 1.5), 0.0),
        ("vol-target σ=15% W=60 去抖0.10", _vol_target_mult(r, 0.15, 60, 0.2, 1.5), 0.10),
        ("vol-target σ=10% W=60", _vol_target_mult(r, 0.10, 60, 0.2, 1.5), 0.0),
        ("CPPI 地板-15% m=4", _cppi_mult(base_nav, 0.15, 4.0, 1.5, 0.0), 0.0),
        ("CPPI 地板-15% m=4 去抖0.10", _cppi_mult(base_nav, 0.15, 4.0, 1.5, 0.0), 0.10),
        ("CPPI 地板-20% m=5 去抖0.10", _cppi_mult(base_nav, 0.20, 5.0, 1.5, 0.0), 0.10),
        ("组合 vol15%W60+CPPI-15% 去抖0.10",
         _combine(_vol_target_mult(r, 0.15, 60, 0.2, 1.5),
                  _cppi_mult(base_nav, 0.15, 4.0, 1.5, 0.0)), 0.10),
    ]

    rows, navs = [], {}
    for name, mult, debounce in configs:
        nav, actual_mult = _apply(r, mult, COST_TURNOVER, debounce)
        navs[name] = nav
        rows.append(_stats(nav, actual_mult, name))

    df = pd.DataFrame(rows)
    cols = ["name", "ann_return", "max_dd", "calmar", "sharpe", "vol", "avg_exposure", "avg_turnover", "n_days"]
    df["ann_return"] = df["ann_return"].map(lambda x: f"{x:+.2%}")
    df["max_dd"] = df["max_dd"].map(lambda x: f"{x:.2%}")
    df["vol"] = df["vol"].map(lambda x: f"{x:.2%}")
    df["calmar"] = df["calmar"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    df["sharpe"] = df["sharpe"].map(lambda x: f"{x:.2f}")
    df["avg_exposure"] = df["avg_exposure"].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    df["avg_turnover"] = df["avg_turnover"].map(lambda x: f"{x:.2%}")
    print(df[cols].to_string(index=False))

    # 逐日净值存盘供画图
    out = pd.DataFrame(navs)
    out.index.name = "date"
    out_path = PORT_DIR / "data_gbdt" / "drawdown_overlay_nav.parquet"
    out_path.parent.mkdir(exist_ok=True)
    out.to_parquet(out_path)
    print(f"\n逐日净值已存: {out_path}")

    print("\n读法:")
    print("· 代理是官方真实中证1000 beta(无 alpha)。主策略有 alpha,叠加会砍部分 alpha,最终数字不同。")
    print("· 关注方向:叠加后 maxDD 是否下降、Calmar 是否提升、代价(年化/夏普)方向。")
    print("· vol-target 控风险水平轴(波动↑→降杠杆);CPPI 控损失预算轴(回撤深→减仓)。互补。")
    print("· 成本已扣(0.15%/单边换手)。avg_turnover 高的配置成本吃重。")


if __name__ == "__main__":
    main()
