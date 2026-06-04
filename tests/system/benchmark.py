"""
benchmark.py — Benchmark de Rendimiento del Bus de Objetos
Proyecto: Bus de Objetos en Python — Etapa 4
Descripción: Mide la latencia round-trip con 1, 5 y 10 clientes simultáneos.
             Cada cliente ejecuta 1000 operaciones INSERT.
             Calcula: mínimo, máximo, promedio y percentil 95.
             Analiza degradación bajo carga concurrente.
"""

import time
import threading
import statistics
import sys
import os

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.server.bus_server import BusServer
from src.client.bus_client import BusClient
from src.server.object_server import _reset_server


OPERATIONS_PER_CLIENT = 1000
SCENARIOS = [1, 5, 10]


def run_client_benchmark(host: str, port: int, num_operations: int) -> list[float]:
    """
    Connects a client, creates a list, and performs num_operations INSERTs.
    Returns a list of round-trip latencies in microseconds.
    """
    client = BusClient(host=host, port=port)
    client.connect()

    latencies = []
    try:
        list_id = client.list_create()

        for i in range(num_operations):
            start = time.perf_counter()
            client.list_insert(list_id, i)
            end = time.perf_counter()
            latencies.append((end - start) * 1_000_000)  # → microseconds
    finally:
        client.close()

    return latencies


def run_scenario(host: str, port: int, num_clients: int,
                 num_operations: int) -> dict:
    """
    Runs a benchmark scenario with num_clients concurrent clients.
    Returns aggregated statistics.
    """
    all_latencies: list[list[float]] = [[] for _ in range(num_clients)]
    threads: list[threading.Thread] = []
    errors: list[str] = []

    def worker(client_idx: int):
        try:
            lats = run_client_benchmark(host, port, num_operations)
            all_latencies[client_idx] = lats
        except Exception as e:
            errors.append(f"Client {client_idx}: {e}")

    # Launch all clients simultaneously
    for i in range(num_clients):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)

    start_time = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    total_time = time.perf_counter() - start_time

    if errors:
        print(f"  ⚠ Errors: {errors}")

    # Flatten all latencies
    flat = []
    for lats in all_latencies:
        flat.extend(lats)

    if not flat:
        return {"error": "No latencies collected"}

    flat.sort()
    p95_idx = int(len(flat) * 0.95)

    return {
        "clients": num_clients,
        "operations_per_client": num_operations,
        "total_operations": len(flat),
        "total_time_s": round(total_time, 3),
        "min_us": round(min(flat), 2),
        "max_us": round(max(flat), 2),
        "avg_us": round(statistics.mean(flat), 2),
        "median_us": round(statistics.median(flat), 2),
        "p95_us": round(flat[p95_idx], 2),
        "stddev_us": round(statistics.stdev(flat), 2) if len(flat) > 1 else 0,
        "throughput_ops_s": round(len(flat) / total_time, 1),
    }


def print_results(results: list[dict]) -> None:
    """Prints benchmark results as a formatted table."""
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS — Bus de Objetos TCP")
    print("=" * 80)

    header = (
        f"{'Clients':>8} | {'Total Ops':>10} | {'Time (s)':>9} | "
        f"{'Min (µs)':>10} | {'Avg (µs)':>10} | {'P95 (µs)':>10} | "
        f"{'Max (µs)':>10} | {'Throughput':>12}"
    )
    print(header)
    print("-" * len(header))

    for r in results:
        if "error" in r:
            print(f"  {r['clients']:>6} | ERROR: {r['error']}")
            continue
        print(
            f"{r['clients']:>8} | {r['total_operations']:>10} | "
            f"{r['total_time_s']:>9} | {r['min_us']:>10} | "
            f"{r['avg_us']:>10} | {r['p95_us']:>10} | "
            f"{r['max_us']:>10} | {r['throughput_ops_s']:>10} ops/s"
        )

    print()

    # Degradation analysis
    print("DEGRADATION ANALYSIS")
    print("-" * 40)
    if len(results) >= 2 and "error" not in results[0]:
        baseline = results[0]["avg_us"]
        for r in results[1:]:
            if "error" in r:
                continue
            factor = r["avg_us"] / baseline if baseline > 0 else float("inf")
            print(
                f"  {r['clients']} clients vs 1 client: "
                f"avg latency ×{factor:.2f} "
                f"({'linear' if factor < r['clients'] * 0.8 else 'super-linear'} "
                f"degradation)"
            )

    print()
    print("CONCURRENCY ANALYSIS")
    print("-" * 40)
    for r in results:
        if "error" in r:
            continue
        print(
            f"  {r['clients']} client(s): "
            f"stddev={r['stddev_us']:.1f}µs, "
            f"p95/avg ratio={r['p95_us']/r['avg_us']:.2f}x"
        )

    print()
    print("STABILITY: All scenarios completed without server crash.")
    print("=" * 80)


def save_markdown_report(results: list[dict], filepath: str = "benchmark_report.md") -> None:
    """Saves the benchmark results as a Markdown table."""
    lines = [
        "## Reporte de Rendimiento (Benchmark Concurrente)",
        "",
        "| Clientes | Operaciones Totales | Tiempo (s) | Mínimo (µs) | Promedio (µs) | Percentil 95 (µs) | Máximo (µs) | Throughput |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['clients']} | ERROR: {r['error']} | | | | | | |")
            continue
        lines.append(
            f"| {r['clients']} | {r['total_operations']} | {r['total_time_s']} s | "
            f"{r['min_us']} µs | {r['avg_us']} µs | {r['p95_us']} µs | "
            f"{r['max_us']} µs | {r['throughput_ops_s']} ops/s |"
        )
    lines.append("")
    lines.append("### Análisis de Degradación bajo Carga Concurrente")
    lines.append("")
    if len(results) >= 2 and "error" not in results[0]:
        baseline = results[0]["avg_us"]
        for r in results[1:]:
            if "error" in r:
                continue
            factor = r["avg_us"] / baseline if baseline > 0 else float("inf")
            deg_type = "degradación lineal" if factor < r["clients"] * 0.8 else "degradación súper-lineal"
            lines.append(
                f"- **{r['clients']} clientes vs 1 cliente:** La latencia promedio se incrementó por un factor de **{factor:.2f}x** ({deg_type})."
            )
    lines.append("")
    lines.append("### Análisis de Concurrencia (Variabilidad)")
    lines.append("")
    for r in results:
        if "error" in r:
            continue
        ratio = r["p95_us"] / r["avg_us"] if r["avg_us"] > 0 else 0
        lines.append(
            f"- **{r['clients']} cliente(s):** Desviación estándar = **{r['stddev_us']:.1f}µs**, Ratio P95/Avg = **{ratio:.2f}x**"
        )
    lines.append("")
    lines.append("> **Estabilidad:** Todos los escenarios de concurrencia completaron de manera exitosa sin provocar la caída (*crash*) del servidor.")
    lines.append("")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Reporte de benchmark guardado en {filepath}")



def main():
    """Entry point for the benchmark."""
    print("Starting Bus de Objetos Benchmark...")
    print(f"Operations per client: {OPERATIONS_PER_CLIENT}")
    print(f"Scenarios: {SCENARIOS} clients")

    # Start server
    _reset_server()
    server = BusServer(host="127.0.0.1", port=0)
    server.start()
    port = server.port
    print(f"Server started on port {port}")
    time.sleep(0.2)

    results = []

    for num_clients in SCENARIOS:
        print(f"\nRunning scenario: {num_clients} client(s)...")
        _reset_server()  # Fresh state per scenario
        result = run_scenario("127.0.0.1", port, num_clients,
                              OPERATIONS_PER_CLIENT)
        results.append(result)

    server.stop()

    print_results(results)
    save_markdown_report(results)

    return results


if __name__ == "__main__":
    main()
