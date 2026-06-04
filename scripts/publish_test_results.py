import json
import os
import subprocess
import sys

def generate_markdown(report_file):
    """
    Lee el JSON de pytest y genera el Markdown con los resultados.
    """
    if not os.path.exists(report_file):
        print(f"Error: No se encontró el archivo de reporte {report_file}")
        sys.exit(1)
        
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)

        
    commit_sha = os.environ.get('GITHUB_SHA', 'local-run')
    short_sha = commit_sha[:7] if commit_sha != 'local-run' else 'Local'
    
    # Try to get the commit message if available
    commit_msg = "Resultados de integración continua"
    try:
        result = subprocess.run(["git", "log", "-1", "--pretty=%B"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            commit_msg = result.stdout.strip().split('\n')[0]
    except Exception:
        pass
        
    lines = [
        f"## Reporte de Pruebas Automáticas",
        f"**Commit:** `{short_sha}` - {commit_msg}",
        "",
        "| ID | Función de Prueba | Estado |",
        "|---|---|---|"
    ]
    
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for test in report.get('tests', []):
        nodeid = test.get('nodeid', '')
        # extract test name from nodeid (e.g. tests/foo.py::TestClass::test_name)
        test_name = nodeid.split('::')[-1]
        base_name = test_name.split('[')[0]  # Por si hay pruebas parametrizadas
        
        test_id = test.get('metadata', {}).get('test_id', 'Sin ID')
        outcome = test.get('outcome', 'unknown')
        
        if outcome == 'passed':
            icon = "✅ Pasó"
            passed_count += 1
        elif outcome == 'failed':
            icon = "❌ Falló"
            failed_count += 1
        else:
            icon = "⚠️ Omitido"
            skipped_count += 1
            
        lines.append(f"| `{test_id}` | `{test_name}` | {icon} |")
        
    summary = report.get('summary', {})
    total = summary.get('total', passed_count + failed_count + skipped_count)
    
    header_summary = [
        f"**Resumen:** {total} pruebas en total. {passed_count} ✅, {failed_count} ❌, {skipped_count} ⚠️.",
        ""
    ]
    
    return "\n".join(header_summary + lines)

def publish_issue(markdown_body):
    """
    Usa GitHub CLI (gh) para crear el issue.
    """
    commit_sha = os.environ.get('GITHUB_SHA', 'local-run')
    short_sha = commit_sha[:7] if commit_sha != 'local-run' else 'Local'
    
    title = f"Resultados de Pruebas: Commit {short_sha}"
    
    body_file = "issue_body.md"
    with open(body_file, "w", encoding="utf-8") as f:
        f.write(markdown_body)
        
    print(f"Creando GitHub Issue: '{title}'...")
    try:
        # Asegurarnos de que el label exista o GitHub no fallará si lo omitimos si no podemos garantizarlo.
        # Es más seguro crearlo sin label o con un comando que asegure su creación,
        # pero omitiré los labels por ahora para evitar fallos si el repositorio restringe labels.
        result = subprocess.run([
            "gh", "issue", "create",
            "--title", title,
            "--body-file", body_file
        ], check=True, capture_output=True, text=True)
        print("Issue creado con éxito:", result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print("Error al crear el Issue:", e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    print("Generando Markdown...")
    markdown = generate_markdown("report.json")
    
    # Intentar leer y anexar el reporte del benchmark si existe
    benchmark_file = "benchmark_report.md"
    if os.path.exists(benchmark_file):
        print(f"Anexando reporte de rendimiento desde {benchmark_file}...")
        with open(benchmark_file, "r", encoding="utf-8") as f:
            bench_content = f.read()
        markdown += "\n\n---\n\n" + bench_content
        
    # En entorno local sin GITHUB_TOKEN esto fallará, 
    # pero está pensado para correr en GitHub Actions.
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        publish_issue(markdown)
    else:
        print("Ejecución local detectada. Mostrando el reporte generado en consola:\n")
        print(markdown)
