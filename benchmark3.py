import requests
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────
#URL = "http://localhost:5000/stats"
URL = "http://localhost:5000/houses?locality=New York"
NB_REQUESTS = 5000
CONCURRENCY = 300
TIMEOUT     = 10  # secondes avant de considérer une requête comme échouée

# ─────────────────────────────────────────────
#  Collecte des résultats
# ─────────────────────────────────────────────
latencies = []   # temps de réponse en secondes (requêtes réussies)
errors    = []   # messages d'erreur

def send_request(i):
    try:
        t0 = time.perf_counter()
        r  = requests.get(URL, timeout=TIMEOUT)
        t1 = time.perf_counter()

        latency_ms = (t1 - t0) * 1000  # convertir en millisecondes

        if r.status_code == 200:
            latencies.append(latency_ms)
            print(".", end="", flush=True)
        else:
            errors.append(f"HTTP {r.status_code}")
            print("E", end="", flush=True)

    except requests.exceptions.Timeout:
        errors.append("timeout")
        print("T", end="", flush=True)
    except Exception as e:
        errors.append(str(e))
        print("X", end="", flush=True)


# ─────────────────────────────────────────────
#  Lancement du test
# ─────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  Benchmark — {URL}")
print(f"  {NB_REQUESTS} requêtes  |  {CONCURRENCY} utilisateurs simultanés")
print(f"{'='*55}")
print("Légende : (.) succès  (E) erreur HTTP  (T) timeout  (X) exception\n")

start = time.perf_counter()

with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
    list(executor.map(send_request, range(NB_REQUESTS)))

total_time = time.perf_counter() - start

# ─────────────────────────────────────────────
#  Calcul des métriques
# ─────────────────────────────────────────────
nb_success   = len(latencies)
nb_errors    = len(errors)
error_rate   = (nb_errors / NB_REQUESTS) * 100
throughput   = nb_success / total_time  # req/s

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
#  Affichage du rapport
# ─────────────────────────────────────────────
print(f"\n\n{'='*55}")
print(f"  RÉSULTATS")
print(f"{'='*55}")
print(f"  URL testée          : {URL}")
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

# Résumé en une ligne facile à copier dans un rapport
print(f"  Résumé CSV (à copier dans votre rapport) :")
print(f"  config,req/s,p50_ms,p95_ms,p99_ms,errors_%")
print(f"  VOTRE_CONFIG,{throughput:.1f},{p50:.1f},{p95:.1f},{p99:.1f},{error_rate:.1f}")
print()