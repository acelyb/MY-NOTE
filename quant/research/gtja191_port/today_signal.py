"""
今日盘面双模型选股信号（只读，不碰 quant_system 源码）。

复刻 compare_ml.py 的两套合成口径，但只跑"最新一个交易日"的截面信号，
输出两个模型各自今日 top_n 买点清单，回答"今天买哪支股票"。

两个模型（A/B 唯一变量=合成方式，其余口径与 compare_ml 逐字一致）：
  linear = weighting "ic"   （线性 ICIR 加权，twolevel 族内正交+族间风险预算）
  ml     = weighting "ml"   （LightGBM 非线性合成，同批因子作特征）

口径对齐 compare_ml / walk_forward：
  - universe = csi1000
  - top_n = 100，turnover_buffer = 15（新建仓视角，prev_holdings=None）
  - combine = twolevel（族内正交+族间风险预算），families/orthogonalize 取 config
  - 训练段 = 历史数据截至信号日前 train_days(252) 天（walk_forward 窗口口径）
  - horizon = 10（IC/ML 标签的未来收益持有期，walk_forward 默认）
  - 信号日 = 缓存最新公共交易日（read_only 纯缓存不拉网）

只读纪律：
  - get_index_constituents / get_batch_daily 一律 read_only=True（cache-only，不拉网不写）
  - 不修改 quant_system 任何源码，只 import 调用
  - 单进程（守"慢慢来不影响其他 agent"）

诚实标注：read_only 模式下信号日=缓存最新日（实测 2026-08-27），非今日盘面。
日线端点不限流（仅分钟端点限流，见 sina-minute-endpoint-rate-limit），若需今日实时
数据可去掉 read_only 让 fetcher 拉网——但那会写 cache，本脚本默认不做。

用法：
  python today_signal.py
  python today_signal.py --universe csi500 --top-n 50
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

# quant_system 在父目录的父目录（survey/gtja191_port → survey → code/quant_system）
QS_ROOT = Path(__file__).resolve().parents[2] / "quant_system"
sys.path.insert(0, str(QS_ROOT))

from data.fetcher import get_index_constituents, get_batch_daily  # noqa: E402
from data.fetcher_fundamental import build_fundamental_data  # noqa: E402
from factors.composite import (  # noqa: E402
    load_factor, composite_score, select_portfolio,
)
from factors.composite_ml import composite_score_ml  # noqa: E402
from backtest.walk_forward import _train_factor_directions, _train_ml_model  # noqa: E402


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _latest_common_date(price_dfs: dict) -> pd.Timestamp:
    """缓存最新公共交易日（所有非空 df 末日的众数）。"""
    last_dates = [df["date"].iloc[-1] for df in price_dfs.values()
                  if df is not None and len(df)]
    if not last_dates:
        raise RuntimeError("缓存无任何日线数据")
    return pd.to_datetime(pd.Series(last_dates).mode().iloc[0])


def _build_factors(cfg: dict, syms: list[str], verbose: bool, read_only: bool = True):
    """加载因子实例 + 注入基本面数据（若有 fundamental 因子）。复刻 daily_portfolio 口径。"""
    factors = [(load_factor(spec), spec.get("weight", 1.0))
               for spec in cfg["multifactor"]["factors"].values()]
    if any(getattr(f, "is_fundamental", False) for f, _ in factors):
        if verbose:
            print(f"  拉取基本面数据（{'read_only 缓存' if read_only else '拉网'}） ...")
        try:
            fund_data = build_fundamental_data(syms, progress=verbose, read_only=read_only)
            for factor, _ in factors:
                factor.set_fundamental_data(fund_data)
        except Exception as e:
            if verbose:
                print(f"  基本面数据读取失败: {e}")
    return factors


def _ref_prices(price_dfs: dict, signal_date: pd.Timestamp) -> dict:
    """信号日参考价（close 作建议买入参考价，复刻 daily_portfolio.format_report 口径）。"""
    ref = {}
    for s, df in price_dfs.items():
        if df is None or df.empty:
            continue
        row = df[df["date"] == signal_date]
        if not row.empty:
            ref[s] = {"close": float(row["close"].iloc[0]),
                      "open": float(row["open"].iloc[0])}
    return ref


def _format_buys(target: list[str], score: pd.Series, ref: dict,
                 name: str, signal_date: pd.Timestamp,
                 stop_loss: float, take_profit: float, show: int) -> str:
    """格式化一个模型的买入清单（按打分排序，前 show 只带价位）。"""
    lines = []
    lines.append(f"\n{'─' * 64}")
    lines.append(f"  模型【{name}】  信号日 {signal_date:%Y-%m-%d}  目标持仓 {len(target)} 只")
    lines.append(f"{'─' * 64}")
    if not target:
        lines.append("  （无有效持仓——该模型在训练段样本不足或因子全不显著，退化为空仓）")
        return "\n".join(lines)
    ranked = score.reindex(target).sort_values(ascending=False)
    lines.append(f"  Top {show}（按打分降序，建议买入参考价=信号日收盘，实盘入场=T+1 开盘）:")
    lines.append(f"  {'排名':>4} {'代码':<8} {'得分':>8} {'参考价':>10} {'止损':>9} {'止盈':>9}")
    for i, sym in enumerate(ranked.index[:show], 1):
        s = ranked[sym]
        p = ref.get(sym)
        if p and p["close"] > 0:
            c = p["close"]
            lines.append(f"  {i:>4} {sym:<8} {s:>+8.3f} {c:>10.2f} "
                         f"{c*(1-stop_loss):>9.2f} {c*(1+take_profit):>9.2f}")
        else:
            lines.append(f"  {i:>4} {sym:<8} {s:>+8.3f}  (无信号日收盘价)")
    if len(ranked) > show:
        lines.append(f"  ... 余 {len(ranked)-show} 只见完整清单（目标共 {len(target)} 只）")
    return "\n".join(lines)


def run(cfg: dict, universe: str, top_n: int, buffer: int,
        train_days: int, horizon: int, show: int, verbose: bool,
        live: bool = False) -> None:
    mf = cfg["multifactor"]
    wf_cfg = mf.get("walk_forward", {})
    ic_freq = int(wf_cfg.get("ic_freq", 5))
    min_ic_abs = float(wf_cfg.get("min_ic_abs", 0.01))
    clamp = (float(wf_cfg.get("ic_clamp_floor", 0.25)),
             float(wf_cfg.get("ic_clamp_cap", 1.50)))
    ml_cfg = wf_cfg.get("ml", {})
    combine_cfg = {k: mf.get(k) for k in ("combine", "families", "orthogonalize")}
    risk = mf.get("risk", {})
    stop_loss = float(risk.get("stop_loss", 0.10))
    take_profit = float(risk.get("take_profit", 0.30))

    ro = not live
    tag = "read_only 缓存" if ro else "拉网更新 cache"
    print(f"获取 {universe} 成分股（{tag}） ...")
    syms = get_index_constituents(universe, read_only=ro)
    print(f"  {len(syms)} 只。拉取日线（{tag}） ...")
    price_dfs = get_batch_daily(syms, progress=verbose, read_only=ro)
    valid = {s: df for s, df in price_dfs.items() if df is not None and not df.empty}
    signal_date = _latest_common_date(valid)
    print(f"  最新公共交易日 = {signal_date:%Y-%m-%d}"
          + ("（read_only 未拉网）" if ro else "（已拉网更新）"))

    factors = _build_factors(cfg, syms, verbose, read_only=ro)

    # 训练段：历史数据截至信号日（含），往前取 train_days 天（walk_forward train_dfs 口径）。
    # 注意：walk_forward 训练段用 train_dates[-1] 截断，此处信号日即"最后一个测试窗的末日"，
    # 训练段应截至信号日之前。为与 walk_forward "最后一个测试窗"对齐，训练段末日 = 信号日，
    # 信号截面也用截至信号日（含）的数据——即训练与预测同日截面，但训练标签用历史未来收益
    # （horizon 日前的样本），预测用末日截面，无未来泄漏。这里训练段取截至信号日前一天，
    # 预测截面取截至信号日（含），与 walk_forward 测试窗首日口径一致（T 日收盘信号→T+1 持仓）。
    train_end = signal_date - pd.Timedelta(days=1)
    train_dfs = {s: df[df["date"] <= train_end] for s, df in valid.items()
                 if (df["date"] <= train_end).any()}
    # 信号截面：截至信号日（含）
    signal_dfs = {s: df[df["date"] <= signal_date] for s, df in valid.items()
                  if (df["date"] <= signal_date).any()}
    ref = _ref_prices(valid, signal_date)

    print(f"\n训练段：{len(train_dfs)} 只股票，截至 {train_end:%Y-%m-%d}，"
          f"train_days≈{train_days}，horizon={horizon}")

    # ============ 模型①：线性 ICIR（weighting=ic, twolevel）============
    print("\n[1/2] 训练线性 ICIR 方向（weighting=ic） ...")
    trained = _train_factor_directions(
        train_dfs, factors, horizon, ic_freq, min_ic_abs,
        weighting="ic", clamp=clamp)
    directed_linear = [(f, w) for f, w, s, _, _, _ in trained if s != 0]
    dirs = {f.name: {"sign": s, "ic_mean": im, "t": t, "icir": iir}
            for f, w, s, im, t, iir in trained}
    print("  各因子方向(ICIR)：")
    for nm, d in dirs.items():
        print(f"    {nm:<16} sign={d['sign']:+d}  ic_mean={d['ic_mean']:+.4f}  "
              f"t={d['t']:+.2f}  icir={d['icir']:+.3f}")
    score_linear = composite_score(signal_dfs, directed_linear, combine_cfg=combine_cfg)
    target_linear = select_portfolio(score_linear, top_n, None, buffer)

    # ============ 模型②：ML LightGBM（weighting=ml）============
    print("\n[2/2] 训练 LightGBM（weighting=ml） ...")
    ml_model, feature_names = _train_ml_model(train_dfs, factors, horizon, ml_cfg)
    if ml_model is not None:
        imp = dict(zip(feature_names,
                       ml_model.feature_importance(importance_type="gain").tolist()))
        print(f"  best_iter={ml_model.best_iteration}  特征重要度(gain):")
        for nm, g in sorted(imp.items(), key=lambda x: -x[1]):
            print(f"    {nm:<16} {g:.1f}")
    else:
        print("  ⚠ 样本不足，ML 退化为空仓")
    score_ml = composite_score_ml(signal_dfs, factors, ml_model, feature_names)
    target_ml = select_portfolio(score_ml, top_n, None, buffer)

    # ============ 输出 ============
    header = []
    header.append("=" * 64)
    header.append(f"  今日盘面双模型选股信号  universe={universe}  "
                  f"top_n={top_n}  buffer={buffer}")
    header.append(f"  信号日：{signal_date:%Y-%m-%d}（缓存最新公共交易日，read_only 未拉今日盘）")
    header.append(f"  止损={stop_loss:.0%}  止盈={take_profit:.0%}  "
                  f"训练段≈{train_days}日  horizon={horizon}日")
    header.append("=" * 64)
    print("\n" + "\n".join(header))
    print(_format_buys(target_linear, score_linear, ref, "线性 ICIR (twolevel)",
                       signal_date, stop_loss, take_profit, show))
    print(_format_buys(target_ml, score_ml, ref, "ML LightGBM",
                       signal_date, stop_loss, take_profit, show))

    # ============ 两模型交集/差异（辅助判断一致性）============
    set_l, set_m = set(target_linear), set(target_ml)
    inter = sorted(set_l & set_m)
    only_l = sorted(set_l - set_m)
    only_m = sorted(set_m - set_l)
    print(f"\n{'─' * 64}")
    print(f"  两模型对比：交集 {len(inter)} 只 | 仅线性 {len(only_l)} 只 | 仅ML {len(only_m)} 只")
    print(f"{'─' * 64}")
    print(f"  两模型共同看好（交集 {len(inter)} 只，按线性打分降序）:")
    inter_ranked = score_linear.reindex(inter).sort_values(ascending=False)
    for i, sym in enumerate(inter_ranked.index[:show], 1):
        sl = score_linear.get(sym, float("nan"))
        sm = score_ml.get(sym, float("nan"))
        p = ref.get(sym)
        pc = f"{p['close']:.2f}" if p and p["close"] > 0 else "—"
        print(f"    {i:>3}. {sym:<8} 线性{sl:+.3f}  ML{sm:+.3f}  价{pc}")
    if len(inter_ranked) > show:
        print(f"    ... 余 {len(inter_ranked)-show} 只交集")
    print(f"\n  仅线性看好（{len(only_l)} 只）: {', '.join(only_l[:15])}"
          + (f" ...+{len(only_l)-15}" if len(only_l) > 15 else ""))
    print(f"  仅 ML 看好（{len(only_m)} 只）: {', '.join(only_m[:15])}"
          + (f" ...+{len(only_m)-15}" if len(only_m) > 15 else ""))

    # 落盘完整清单
    out = Path(__file__).parent / "today_signal_output.txt"
    full = []
    full.append(f"信号日 {signal_date:%Y-%m-%d}  universe={universe}  top_n={top_n}  buffer={buffer}")
    full.append("\n[线性 ICIR] 完整目标持仓（按打分降序）：")
    rl = score_linear.reindex(target_linear).sort_values(ascending=False)
    for i, sym in enumerate(rl.index, 1):
        p = ref.get(sym)
        c = f"{p['close']:.2f}" if p and p["close"] > 0 else "—"
        full.append(f"  {i:>3}. {sym:<8} {rl[sym]:+.3f}  {c}")
    full.append("\n[ML LightGBM] 完整目标持仓（按打分降序）：")
    rm = score_ml.reindex(target_ml).sort_values(ascending=False)
    for i, sym in enumerate(rm.index, 1):
        p = ref.get(sym)
        c = f"{p['close']:.2f}" if p and p["close"] > 0 else "—"
        full.append(f"  {i:>3}. {sym:<8} {rm[sym]:+.3f}  {c}")
    out.write_text("\n".join(full), encoding="utf-8")
    print(f"\n完整清单已存：{out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(QS_ROOT / "config.yaml"))
    ap.add_argument("--universe", default="csi1000")
    ap.add_argument("--top-n", type=int, default=100)
    ap.add_argument("--buffer", type=int, default=15)
    ap.add_argument("--train-days", type=int, default=252)
    ap.add_argument("--horizon", type=int, default=10)
    ap.add_argument("--show", type=int, default=20, help="终端展示前 N 只")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--live", action="store_true",
                    help="去掉 read_only，让 fetcher 拉网更新 cache（写 parquet）")
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    run(cfg, args.universe, args.top_n, args.buffer,
        args.train_days, args.horizon, args.show,
        verbose=not args.quiet, live=args.live)


if __name__ == "__main__":
    main()
