"""Crea mkdocs.yml, GitHub Actions workflow, .gitignore y README para docs-centralized"""
import os
from pathlib import Path

BASE = Path(r"C:\Users\julio\Documents\Proyectos\docs-centralized")

files = {}

files["mkdocs.yml"] = """site_name: Centro de Documentacion - Julio Cadenas
site_description: Documentacion centralizada de infraestructura AI, proyectos y clientes
site_url: https://juliocadenas.github.io/docs-centralized
repo_url: https://github.com/juliocadenas/docs-centralized
repo_name: juliocadenas/docs-centralized
edit_uri: edit/main/docs/

theme:
  name: material
  language: es
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
  palette:
    - scheme: default
      primary: deep purple
      accent: indigo
      toggle:
        icon: material/weather-night
        name: Modo oscuro
    - scheme: slate
      primary: deep purple
      accent: indigo
      toggle:
        icon: material/weather-sunny
        name: Modo claro

nav:
  - Inicio: index.md
  - Infraestructura:
    - Mapa: global/servers/infrastructure-map.md
    - NAB9: global/servers/server-gpu-map.md
  - Proyectos:
    - AI Hub: projects/ai-hub-madrid/model-catalog.md
    - Registry: projects/project-registry.md
  - Reglas:
    - Globales: rules/global-rules.md
    - NAB9: rules/nab9-rules.md
    - XEON: rules/xeon-rules.md
    - Contabo: rules/contabo-rules.md

markdown_extensions:
  - admonition
  - codehilite
  - footnotes
  - meta
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - tables

plugins:
  - search:
      lang: [es, en]
"""

files[".gitignore"] = """site/
__pycache__/
*.pyc
.env
.vscode/
"""

files["README.md"] = """# docs-centralized

Repositorio central de documentacion de toda la infraestructura de Julio Cadenas.

## Estructura

- `docs/global/` - Infraestructura global (servidores, red)
- `docs/projects/` - Proyectos personales
- `docs/clients/` - Clientes (restringido)
- `docs/audits/` - Reportes y auditorias
- `docs/rules/` - Reglas para agentes de IA

## Sitio web

El sitio MkDocs se publica automaticamente en GitHub Pages al hacer push:
https://juliocadenas.github.io/docs-centralized

## Reglas para IA

Los agentes de IA (Cline, Cursor) DEBEN leer `docs/rules/global-rules.md` antes
de cualquier tarea y mantener esta documentacion actualizada.
"""

# GitHub Actions workflow para auto-deploy a Pages
actions_dir = BASE / ".github" / "workflows"
actions_dir.mkdir(parents=True, exist_ok=True)

files[str(actions_dir / "ci.yml")] = """name: Build and Deploy MkDocs

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install mkdocs-material pymdown-extensions
      - run: mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
"""

for relpath, content in files.items():
    fpath = BASE / relpath if not os.path.isabs(relpath) else Path(relpath)
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")
    print(f"OK: {fpath.name}")

print(f"\nTotal: {len(files)} archivos creados")