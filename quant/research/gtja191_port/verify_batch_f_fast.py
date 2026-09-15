"""批次F 44因子IC验证(快版) —— fork+COW共享缓存, 6进程并行(留核给其他agent)。

与 verify_all_new.py 同口径, 差异:
1. 加载器 load_batch_daily_with_vwap_index(OHLCV+vwap+指数开收);
2. 采样 freq=63(季频)减算量——因子多为长窗口(20/60日), 季频26点仍支撑t检验,
   月频77点与季频结论一致但耗时8×;选季频兼顾速度与统计有效性;
3. 6进程(非8)留核给同机其他agent, 契合"慢慢来不影响他人"。

批次F: VWAP(40)+指数(4), #30 Fama-French 无缓存跳过。
"""
import sys, re
from pathlib import Path
from multiprocessing import Pool
PORT = Path("/home/cambricon/Documents/code/survey/gtja191_port")
sys.path.insert(0, str(PORT))
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from cache_reader import load_constituents, load_batch_daily_with_vwap_index
from ic import ic_summary, interpret, _future_return
import factors as F

BATCH_F = {7,8,12,13,16,17,26,36,39,41,44,45,61,64,70,73,74,77,87,90,92,95,101,
           108,114,119,120,121,124,125,130,131,132,138,144,154,156,163,170,179,
           75,149,181,182}
FACTORS = []
for name in F.__all__:
    m = re.fullmatch(r"Alpha(\d+)Factor", name)
    if not m: continue
    n = int(m.group(1))
    if n not in BATCH_F: continue
    cls = getattr(F, name)
    FACTORS.append((f"gtja_alpha{n}", cls()))
print(f"收集到 {len(FACTORS)} 个批次F因子(40 VWAP + 4 指数)", flush=True)

_SYM_DATA=None; _ALL_DATES=None; _HORIZON=21; _FREQ=63
def _ic_one(args):
    label, fac = args
    sym_data, all_dates = _SYM_DATA, _ALL_DATES
    records = []
    for i in range(0, len(all_dates)-_HORIZON, _FREQ):
        date = all_dates[i]; fv, fr = {}, {}
        for s, d in sym_data.items():
            pos = int(np.searchsorted(d.index.values, np.datetime64(date)))
            if pos >= len(d) or d.index[pos] != date: continue
            v = fac.calc_value(d.iloc[:pos+1])
            if v is None or (isinstance(v,float) and np.isnan(v)): continue
            r = _future_return(d["close"], pos, _HORIZON)
            if r is None: continue
            fv[s]=v; fr[s]=r
        if len(fv) < 10: continue
        common = pd.Index(fv.keys()).intersection(pd.Index(fr.keys()))
        if len(common) < 10: continue
        ic,_ = spearmanr(pd.Series(fv).loc[common], pd.Series(fr).loc[common])
        if not np.isnan(ic): records.append(ic)
    s = ic_summary(pd.Series(records)) if records else ic_summary(pd.Series(dtype=float))
    return (label, s)
def main():
    global _SYM_DATA, _ALL_DATES
    syms = load_constituents("csi1000")
    print(f"csi1000: {len(syms)} 只, 读缓存+合并VWAP+指数(1× I/O)...", flush=True)
    pdfs = load_batch_daily_with_vwap_index(syms)
    print(f"缓存命中: {len(pdfs)}/{len(syms)}", flush=True)
    _SYM_DATA = {s: df.set_index("date") for s,df in pdfs.items() if not df.empty}
    _ALL_DATES = sorted(set().union(*[set(d.index) for d in _SYM_DATA.values()]))
    n_dates = len(range(0, len(_ALL_DATES)-_HORIZON, _FREQ))
    print(f"\n跑 {len(FACTORS)} 因子 IC (horizon=21, 季频采样~{n_dates}点, csi1000, 2020-2026) — 6 进程并行...", flush=True)
    print("-"*80, flush=True)
    print(f"{'因子':<20}{'IC均值':>9}{'ICIR':>8}{'胜率':>7}{'t值':>7}{'n':>5}  判断", flush=True)
    print("-"*80, flush=True)
    with Pool(6) as pool:
        results = pool.map(_ic_one, FACTORS, chunksize=1)
    results.sort(key=lambda x: (x[1]['ic_mean'] if not pd.isna(x[1]['ic_mean']) else 0))
    for label, s in results:
        print(f"{label:<20}{s['ic_mean']:>+9.4f}{s['icir']:>+8.3f}{s['win_rate']:>7.1%}{s['t_stat']:>+7.2f}{s['n']:>5}  {interpret(s)}")
    print("-"*80)
    print("判定: |IC|>0.03弱/>0.05中/>0.1强; |ICIR|>0.5稳定; |t|>2显著")
    sig = [(l,s) for l,s in results if not pd.isna(s["t_stat"]) and abs(s["t_stat"])>2]
    if sig:
        print(f"\n=== 显著因子(|t|>2)共 {len(sig)} 个 ===")
        for l,s in sig: print(f"  {l}: IC={s['ic_mean']:+.4f} t={s['t_stat']:+.2f} ICIR={s['icir']:+.3f} n={s['n']} {'正向' if s['ic_mean']>0 else '反向'}")
    else:
        print("\n=== 无显著因子(|t|>2)===")
if __name__=="__main__": main()
