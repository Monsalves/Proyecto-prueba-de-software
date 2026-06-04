## Reporte de Rendimiento (Benchmark Concurrente)

| Clientes | Operaciones Totales | Tiempo (s) | Mínimo (µs) | Promedio (µs) | Percentil 95 (µs) | Máximo (µs) | Throughput |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1000 | 0.064 s | 39.25 µs | 60.62 µs | 89.19 µs | 1540.87 µs | 15602.6 ops/s |
| 5 | 5000 | 0.309 s | 42.4 µs | 301.78 µs | 516.21 µs | 6442.64 µs | 16191.8 ops/s |
| 10 | 10000 | 0.712 s | 43.86 µs | 684.61 µs | 1403.49 µs | 9659.19 µs | 14036.3 ops/s |

### Análisis de Degradación bajo Carga Concurrente

- **5 clientes vs 1 cliente:** La latencia promedio se incrementó por un factor de **4.98x** (degradación súper-lineal).
- **10 clientes vs 1 cliente:** La latencia promedio se incrementó por un factor de **11.29x** (degradación súper-lineal).

### Análisis de Concurrencia (Variabilidad)

- **1 cliente(s):** Desviación estándar = **81.2µs**, Ratio P95/Avg = **1.47x**
- **5 cliente(s):** Desviación estándar = **238.9µs**, Ratio P95/Avg = **1.71x**
- **10 cliente(s):** Desviación estándar = **556.3µs**, Ratio P95/Avg = **2.05x**

> **Estabilidad:** Todos los escenarios de concurrencia completaron de manera exitosa sin provocar la caída (*crash*) del servidor.
