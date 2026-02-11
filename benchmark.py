import requests
import time
from concurrent.futures import ThreadPoolExecutor

URL="http://localhost:5000/stats"
NB_REQUESTS=3000
CONCURRENCY = 10

def send_request(i):
    try:
        response = requests.get(URL)
        print(".", end="", flush=True)
    except Exception as e:
        print(f"\nError during request {i+1}: {e}")


print(f"Sending {NB_REQUESTS} requests to {URL}...")

start_time = time.perf_counter()

with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
    results = list(executor.map(send_request, range(NB_REQUESTS)))

end_time = time.perf_counter()
total_time = end_time - start_time
average_time = total_time / NB_REQUESTS
print(f"\nTotal time for {NB_REQUESTS} requests: {total_time:.2f} seconds")
print(f"Average time per request: {average_time:.2f} seconds")