import requests
import time
import random
import statistics
from concurrent.futures import ThreadPoolExecutor

# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────
BASE_URL    = "http://localhost:5000/houses"
NB_REQUESTS = 5000
CONCURRENCY = 100
TIMEOUT     = 10

# Localities réelles du dataset NY Housing
LOCALITIES = [
    "Bronx County",
    "Brooklyn",
    "Flatbush",
    "Kings County",
    "New York",
    "New York County",
    "Queens",
    "Queens County",
    "Richmond County",
    "The Bronx",
    "United States",
]

# ─────────────────────────────────────────────
#  Collecte des résultats
# ─────────────────────────────────────────────
latencies = []
errors    = []

def send_request(i):
    locality = random.choice(LOCALITIES)
    url = f"{BASE_URL}?locality={requests.utils.quote(locality)}&limit=20"
    try:
        t0 = time.perf_counter()
        r  = requests.get(url, timeout=TIMEOUT)
        t1 = time.perf_counter()

        latency_ms = (t1 - t0) * 1000

        if r.status_code == 200:
            latencies.append(latency_ms)
            if len(latencies) % 1000 == 0:
                print(".", end="", flush=True)
        else:
            errors.append(f"HTTP {r.status_code}")
            print("E", end="", flush=True)

    except requests.exceptions.Timeout:
        errors.append("timeout")
        print("T", end="", flush=True)
    except Exception as e:
        errors.append(str(e))
        print(f"\nX [{type(e).__name__}]: {e}", flush=True)


# ─────────────────────────────────────────────
#  Lancement du test
# ─────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  Benchmark — {BASE_URL} (localities aléatoires)")
print(f"  {NB_REQUESTS} requêtes  |  {CONCURRENCY} utilisateurs simultanés")
print(f"  {len(LOCALITIES)} localities possibles")
print(f"{'='*55}")
print("Légende : (.) succès  (E) erreur HTTP  (T) timeout  (X) exception\n")

start = time.perf_counter()

with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
    list(executor.map(send_request, range(NB_REQUESTS)))

total_time = time.perf_counter() - start

# ─────────────────────────────────────────────
#  Calcul des métriques
# ─────────────────────────────────────────────
nb_success = len(latencies)
nb_errors  = len(errors)
error_rate = (nb_errors / NB_REQUESTS) * 100
throughput = nb_success / total_time

if latencies:
    latencies_sorted = sorted(latencies)
    p50 = statistics.median(latencies)
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
    p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]
    avg = statistics.mean(latencies)
    min_l = min(latencies)
    max_l = max(latencies)
else:
    p50 = p95 = p99 = avg = min_l = max_l = 0

# ─────────────────────────────────────────────
#  Affichage
# ─────────────────────────────────────────────
print(f"\n\n{'='*55}")
print(f"  RÉSULTATS")
print(f"{'='*55}")
print(f"  URL testée          : {BASE_URL}?locality=<random>")
print(f"  Requêtes totales    : {NB_REQUESTS}")
print(f"  Concurrence         : {CONCURRENCY} workers")
print(f"{'─'*55}")
print(f"  Durée totale        : {total_time:.2f} s")
print(f"  Succès              : {nb_success}  ({100 - error_rate:.1f}%)")
print(f"  Erreurs / timeouts  : {nb_errors}   ({error_rate:.1f}%)")
print(f"{'─'*55}")
print(f"  Débit (throughput)  : {throughput:.1f} req/s")
print(f"{'─'*55}")
print(f"  Latence moyenne     : {avg:.1f} ms")
print(f"  Latence min         : {min_l:.1f} ms")
print(f"  Latence max         : {max_l:.1f} ms")
print(f"  p50 (médiane)       : {p50:.1f} ms")
print(f"  p95                 : {p95:.1f} ms  ← 95% des requêtes sont sous cette valeur")
print(f"  p99                 : {p99:.1f} ms  ← queue de distribution (pires cas)")
print(f"{'='*55}\n")