import time
import math
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

URL = "http://localhost:5000/stats"
NB_REQUESTS = 20000
CONCURRENCY = 100
TIMEOUT_S = 1.0  # request timeout (connect+read)

# Thread-local Session 
_tls = threading.local()

def get_session() -> requests.Session:
    if not hasattr(_tls, "session"):
        _tls.session = requests.Session()
    return _tls.session

def percentile(values, p: float):
    """Linear interpolation percentile (like numpy default). p in [0,100]."""
    if not values:
        return None
    v = sorted(values)
    k = (len(v) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return v[int(k)]
    return v[f] * (c - k) + v[c] * (k - f)

def send_request(i: int):
    sess = get_session()
    t0 = time.perf_counter()
    try:
        r = sess.get(URL, timeout=TIMEOUT_S)
        dt = time.perf_counter() - t0

        ok = 200 <= r.status_code < 300
        return {
            "ok": ok,
            "status_code": r.status_code,
            "latency_s": dt,
            "timeout": False,
            "error": None if ok else f"http_{r.status_code}",
        }

    except requests.exceptions.Timeout:
        dt = time.perf_counter() - t0
        return {
            "ok": False,
            "status_code": None,
            "latency_s": dt,
            "timeout": True,
            "error": "timeout",
        }
    except Exception as e:
        dt = time.perf_counter() - t0
        return {
            "ok": False,
            "status_code": None,
            "latency_s": dt,
            "timeout": False,
            "error": type(e).__name__,
        }

print(f"Sending {NB_REQUESTS} requests to {URL} (concurrency={CONCURRENCY}, timeout={TIMEOUT_S}s)...")

start_wall = time.perf_counter()

results = []
done = 0

with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
    futures = [ex.submit(send_request, i) for i in range(NB_REQUESTS)]
    for fut in as_completed(futures):
        res = fut.result()
        results.append(res)
        done += 1
        # light progress without flooding stdout
        if done % 100 == 0:
            print(".", end="", flush=True)

end_wall = time.perf_counter()
wall_s = end_wall - start_wall

#  Metrics
total = len(results)
success = sum(1 for r in results if r["ok"])
timeouts = sum(1 for r in results if r["timeout"])
http_errors = sum(1 for r in results if (r["status_code"] is not None and not r["ok"]))
other_errors = total - success - http_errors  # includes timeouts + other exceptions

error_rate = (total - success) / total if total else 0.0
timeout_rate = timeouts / total if total else 0.0

lat_ok = [r["latency_s"] for r in results if r["ok"]]
lat_all = [r["latency_s"] for r in results]  # includes failures 

def fmt_ms(x):
    return "n/a" if x is None else f"{x*1000:.2f} ms"

p50_ok = percentile(lat_ok, 50)
p95_ok = percentile(lat_ok, 95)
p99_ok = percentile(lat_ok, 99)

mean_ok = (sum(lat_ok) / len(lat_ok)) if lat_ok else None
max_ok = max(lat_ok) if lat_ok else None

throughput_rps = total / wall_s if wall_s > 0 else float("nan")

print("\n\n--- Benchmark report ---")
print(f"Total requests:        {total}")
print(f"Success (2xx):         {success}")
print(f"HTTP errors (non-2xx): {http_errors}")
print(f"Timeouts:              {timeouts}")
print(f"Other errors:          {other_errors - timeouts}")  # excludes timeouts

print(f"\nWall time:             {wall_s:.2f} s")
print(f"Throughput:            {throughput_rps:.2f} req/s")
print(f"Error rate:            {error_rate*100:.2f}%")
print(f"Timeout rate:          {timeout_rate*100:.2f}%")

print("\nLatency (successful requests only):")
print(f"Mean:                  {fmt_ms(mean_ok)}")
print(f"p50:                   {fmt_ms(p50_ok)}")
print(f"p95:                   {fmt_ms(p95_ok)}")
print(f"p99:                   {fmt_ms(p99_ok)}")
print(f"Max:                   {fmt_ms(max_ok)}")

# status code breakdown 
codes = {}
for r in results:
    code = r["status_code"]
    if code is not None:
        codes[code] = codes.get(code, 0) + 1
if codes:
    print("\nStatus code breakdown:")
    for k in sorted(codes):
        print(f"  {k}: {codes[k]}")
