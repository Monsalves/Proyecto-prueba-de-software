## Reporte de Rendimiento (Benchmark Concurrente)

| Clientes | Operaciones Totales | Tiempo (s) | Mínimo (µs) | Promedio (µs) | Percentil 95 (µs) | Máximo (µs) | Throughput |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1000 | 0.045 s | 33.6 µs | 42.71 µs | 57.82 µs | 1161.22 µs | 22416.3 ops/s |
| 5 | 5000 | 0.228 s | 34.71 µs | 220.79 µs | 390.67 µs | 4212.55 µs | 21909.5 ops/s |
| 10 | 10000 | 0.516 s | 34.4 µs | 504.21 µs | 1157.07 µs | 4262.99 µs | 19396.0 ops/s |

### Análisis de Degradación bajo Carga Concurrente

- **5 clientes vs 1 cliente:** La latencia promedio se incrementó por un factor de **5.17x** (degradación súper-lineal).
- **10 clientes vs 1 cliente:** La latencia promedio se incrementó por un factor de **11.81x** (degradación súper-lineal).

### Análisis de Concurrencia (Variabilidad)

- **1 cliente(s):** Desviación estándar = **46.9µs**, Ratio P95/Avg = **1.35x**
- **5 cliente(s):** Desviación estándar = **177.8µs**, Ratio P95/Avg = **1.77x**
- **10 cliente(s):** Desviación estándar = **351.2µs**, Ratio P95/Avg = **2.29x**

> **Estabilidad:** Todos los escenarios de concurrencia completaron de manera exitosa sin provocar la caída (*crash*) del servidor.
