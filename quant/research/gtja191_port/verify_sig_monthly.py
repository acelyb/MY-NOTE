"""批次F 月频 IC 复跑 —— 通用脚本,改 SIG 集合即可跑任意子集。
6进程, 月频(freq=21, n~76), 同口径加载器(load_batch_daily_with_vwap_index)。
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

# 批次F 剩余34个(44总 - 4强显著 - 6边界,均已月频测过)
SIG = {8,13,17,26,36,39,41,44,45,61,64,73,77,87,90,92,101,108,114,119,120,121,124,125,131,138,156,163,170,179,75,149,181,182}
FACTORS = []
for name in F.__all__:
    m = re.fullmatch(r"Alpha(\d+)Factor", name)
    if not m: continue
    n = int(m.group(1))
    if n not in SIG: continue
    FACTORS.append((f"gtja_alpha{n}", getattr(F, name)()))
print(f"月频复跑 {len(FACTORS)} 个显著因子", flush=True)

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
    print(f"csi1000: {len(syms)} 只, 读缓存+合并VWAP+指数(1× I/O)...", flush=True)
    pdfs = load_batch_daily_with_vwap_index(syms)
    print(f"缓存命中: {len(pdfs)}/{len(syms)}", flush=True)
    _SYM_DATA = {s: df.set_index("date") for s,df in pdfs.items() if not df.empty}
    _ALL_DATES = sorted(set().union(*[set(d.index) for d in _SYM_DATA.values()]))
    n_dates = len(range(0, len(_ALL_DATES)-_HORIZON, _FREQ))
    print(f"\n月频 IC (horizon=21, ~{n_dates}点) — 6 进程...", flush=True)
    print("-"*72, flush=True)
    print(f"{'因子':<20}{'IC均值':>9}{'ICIR':>8}{'胜率':>7}{'t值':>7}{'n':>5}  判断", flush=True)
    print("-"*72, flush=True)
    with Pool(6) as pool:
        results = pool.map(_ic_one, FACTORS, chunksize=1)
    results.sort(key=lambda x: (x[1]['ic_mean'] if not pd.isna(x[1]['ic_mean']) else 0))
    for label, s in results:
        print(f"{label:<20}{s['ic_mean']:>+9.4f}{s['icir']:>+8.3f}{s['win_rate']:>7.1%}{s['t_stat']:>+7.2f}{s['n']:>5}  {interpret(s)}")
    print("-"*72)
if __name__=="__main__": main()
