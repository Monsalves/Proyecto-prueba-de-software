import json
import os
import subprocess
import sys

def extract_test_ids(tests_dir="tests"):
    """
    Escanea la carpeta de pruebas y retorna un diccionario
    mapeando el nombre de la prueba con su ID extraído de los comentarios.
    """
    mapping = {}
    for root, _, files in os.walk(tests_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                last_id = None
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        stripped = line.strip()
                        if stripped.startswith('# ID:'):
                            last_id = stripped.replace('# ID:', '').strip()
                        elif stripped.startswith('def test_'):
                            # test_name(self) -> test_name
                            test_name = stripped.split('def ')[1].split('(')[0]
                            if last_id:
                                mapping[test_name] = last_id
                                last_id = None
    return mapping

def generate_markdown(report_file, mapping):
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
        
        test_id = mapping.get(base_name, "Sin ID")
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
    print("Escaneando IDs de pruebas en tests/...")
    mapping = extract_test_ids()
    print(f"Se encontraron {len(mapping)} pruebas con IDs comentados.")
    
    print("Generando Markdown...")
    markdown = generate_markdown("report.json", mapping)
    
    # En entorno local sin GITHUB_TOKEN esto fallará, 
    # pero está pensado para correr en GitHub Actions.
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        publish_issue(markdown)
    else:
        print("Ejecución local detectada. Mostrando el reporte generado en consola:\n")
        print(markdown)
