import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI()

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>K6 Benchmark Runner</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', sans-serif;
      background: #0d1117;
      color: #c9d1d9;
      padding: 40px 20px;
      min-height: 100vh;
    }
    h1 { color: #58a6ff; margin-bottom: 8px; font-size: 1.6rem; }
    .subtitle { color: #8b949e; margin-bottom: 30px; font-size: 0.9rem; }
    .controls {
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
      align-items: flex-end;
      margin-bottom: 24px;
      background: #161b22;
      padding: 20px;
      border-radius: 8px;
      border: 1px solid #30363d;
    }
    .field { display: flex; flex-direction: column; gap: 6px; }
    label { font-size: 0.82rem; color: #8b949e; text-transform: uppercase; letter-spacing: 0.05em; }
    input[type=number] {
      background: #0d1117;
      color: #c9d1d9;
      border: 1px solid #30363d;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 1rem;
      width: 160px;
    }
    input[type=number]:focus { outline: none; border-color: #58a6ff; }
    button {
      background: #238636;
      color: #fff;
      border: none;
      padding: 10px 24px;
      border-radius: 6px;
      font-size: 1rem;
      cursor: pointer;
      transition: background 0.2s;
      align-self: flex-end;
    }
    button:hover:not(:disabled) { background: #2ea043; }
    button:disabled { background: #21262d; color: #484f58; cursor: not-allowed; }
    .status-bar {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
      font-size: 0.85rem;
      color: #8b949e;
      min-height: 22px;
    }
    .dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: #484f58;
      transition: background 0.3s;
    }
    .dot.running { background: #f0883e; animation: pulse 1s infinite; }
    .dot.done    { background: #3fb950; animation: none; }
    .dot.error   { background: #f85149; animation: none; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
    #output {
      background: #010409;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 16px;
      font-family: 'Courier New', monospace;
      font-size: 0.82rem;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-all;
      min-height: 400px;
      max-height: 70vh;
      overflow-y: auto;
      color: #e6edf3;
    }
  </style>
</head>
<body>
  <h1>K6 Benchmark Runner</h1>
  <p class="subtitle">Lance un benchmark k6 sur le cluster web et affiche les résultats en direct.</p>

  <div class="controls">
    <div class="field">
      <label>Utilisateurs simultanés (VUs)</label>
      <input type="number" id="vus" value="50" min="1" max="1000">
    </div>
    <div class="field">
      <label>Nombre total de requêtes</label>
      <input type="number" id="requests" value="5000" min="1" max="10000000">
    </div>
    <button id="btn" onclick="runBenchmark()">▶ Lancer</button>
  </div>

  <div class="status-bar">
    <div class="dot" id="dot"></div>
    <span id="status">Prêt</span>
  </div>
  <div id="output">En attente du lancement...</div>

  <script>
    let evtSource = null;

    function runBenchmark() {
      const vus      = document.getElementById('vus').value;
      const requests = document.getElementById('requests').value;
      const btn      = document.getElementById('btn');
      const output   = document.getElementById('output');
      const dot      = document.getElementById('dot');
      const status   = document.getElementById('status');

      if (evtSource) evtSource.close();

      btn.disabled     = true;
      output.textContent = '';
      dot.className    = 'dot running';
      status.textContent = `Exécution en cours — ${vus} VUs × ${requests} requêtes...`;

      evtSource = new EventSource(`/run?vus=${vus}&requests=${requests}`);

      evtSource.onmessage = (e) => {
        if (e.data === '__DONE__') {
          evtSource.close();
          btn.disabled      = false;
          dot.className     = 'dot done';
          status.textContent = 'Terminé.';
          return;
        }
        output.textContent += e.data + '\\n';
        output.scrollTop    = output.scrollHeight;
      };

      evtSource.onerror = () => {
        evtSource.close();
        btn.disabled      = false;
        dot.className     = 'dot error';
        status.textContent = 'Erreur de connexion.';
      };
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML


@app.get("/run")
async def run_benchmark(vus: int = 10, requests: int = 1000):
    async def stream():
        proc = await asyncio.create_subprocess_exec(
            "k6", "run",
            "--vus",        str(vus),
            "--iterations", str(requests),
            "--no-color",
            "--no-usage-report",
            "-e", "BASE_URL=http://nginx/houses",
            "/scripts/benchmark_k6.js",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        async for line in proc.stdout:
            text = line.decode("utf-8", errors="replace").rstrip()
            if text:
                yield f"data: {text}\n\n"
        await proc.wait()
        yield "data: __DONE__\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
