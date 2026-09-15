"""全部新移植因子(B/C/D/E 共88个)统一 IC 验证 —— fork+COW 共享缓存, 8进程并行。1× I/O。
动态从 factors 包 __all__ 收集所有 Alpha{N}Factor 类, 跳过批次A已单独跑的20个。
批次A编号:14,15,18,19,20,21,22,23,24,25,27,29,31,32,34,35,37,38,43,46
本脚本跑批次B/C/D/E: 51,53,54,55,56,57,58,59,60,63,65,66,67,68,71,72,76,78,79,80,81,82,
                    86,88,89,93,94,96,97,98,100,102,106,109,110,111,113,115,116,117,118,122,123,126,
                    127,128,129,133,134,136,137,139,140,142,145,146,147,148,151,152,153,155,157,159,160,161,
                    162,164,165,166,168,169,171,172,173,174,175,177,178,180,183,184,185,186,187,188,189,190
"""
import sys, re
from pathlib import Path
from multiprocessing import Pool
PORT = Path("/home/cambricon/Documents/code/survey/gtja191_port")
sys.path.insert(0, str(PORT))
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from cache_reader import load_constituents, load_batch_daily
from ic import ic_summary, interpret, _future_return
import factors as F

# 动态收集所有 Alpha{N}Factor 类
BATCH_A = {14,15,18,19,20,21,22,23,24,25,27,29,31,32,34,35,37,38,43,46}
FACTORS = []
for name in F.__all__:
    m = re.fullmatch(r"Alpha(\d+)Factor", name)
    if not m: continue
    n = int(m.group(1))
    if n in BATCH_A: continue  # 批次A已单独跑过
    cls = getattr(F, name)
    FACTORS.append((f"gtja_alpha{n}", cls()))

print(f"收集到 {len(FACTORS)} 个新因子(批次B/C/D/E,排除批次A)", flush=True)

_SYM_DATA=None; _ALL_DATES=None; _HORIZON=21; _FREQ=21
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
    print(f"csi1000: {len(syms)} 只, 读缓存(1× I/O)...", flush=True)
    pdfs = load_batch_daily(syms)
    print(f"缓存命中: {len(pdfs)}/{len(syms)}", flush=True)
    _SYM_DATA = {s: df.set_index("date") for s,df in pdfs.items() if not df.empty}
    _ALL_DATES = sorted(set().union(*[set(d.index) for d in _SYM_DATA.values()]))
    print(f"\n跑 {len(FACTORS)} 因子 IC (horizon=21, 月频, csi1000, 2020-2026) — 8 进程并行...", flush=True)
    print("-"*80, flush=True)
    print(f"{'因子':<20}{'IC均值':>9}{'ICIR':>8}{'胜率':>7}{'t值':>7}{'n':>5}  判断", flush=True)
    print("-"*80, flush=True)
    with Pool(8) as pool:
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
