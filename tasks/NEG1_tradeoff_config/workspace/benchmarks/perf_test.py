"""Performance benchmark: measures p95 latency."""
import json
import statistics
import time
import urllib.request
import subprocess
import sys
import os
import signal


def run_benchmark():
    """Start server and measure request latencies."""
    # Start server
    server_proc = subprocess.Popen(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, '.'); from service.server import main; main()"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    try:
        time.sleep(1)  # Wait for server to start

        latencies = []
        for i in range(20):
            payload = json.dumps({"name": f"User{i}", "email": f"user{i}@example.com", "value": i * 10}).encode()
            start = time.time()
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:8080/process",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=2) as resp:
                    resp.read()
                elapsed = (time.time() - start) * 1000  # ms
                latencies.append(elapsed)
            except Exception as e:
                latencies.append(2000)  # 2s timeout = fail

        if not latencies:
            print("FAIL: No successful requests")
            sys.exit(1)

        latencies.sort()
        p95_idx = int(len(latencies) * 0.95)
        p95 = latencies[min(p95_idx, len(latencies) - 1)]

        print(f"Requests: {len(latencies)}")
        print(f"p50 latency: {statistics.median(latencies):.1f}ms")
        print(f"p95 latency: {p95:.1f}ms")
        print(f"Max latency: {max(latencies):.1f}ms")

        if p95 < 100:
            print("PERF_PASS: p95 < 100ms")
            sys.exit(0)
        else:
            print(f"PERF_FAIL: p95 = {p95:.1f}ms (must be < 100ms)")
            sys.exit(1)
    finally:
        server_proc.terminate()
        server_proc.wait(timeout=5)


if __name__ == "__main__":
    run_benchmark()
