#!/usr/bin/env bash
# Preparacion automatica del Codespace: instala las dependencias exactas para Linux.
# No usa ni necesita credenciales de Azure.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Python: $(python --version)"
for intento in 1 2 3; do
  if python -m pip install --no-cache-dir -r requirements-codespaces.lock.txt; then
    break
  fi
  if [ "$intento" -eq 3 ]; then
    echo "ERROR: no se pudieron instalar las dependencias tras 3 intentos (revisa la red)." >&2
    exit 1
  fi
  echo "Reintentando instalacion ($intento/3)..."
  sleep 5
done

python -m pip check
python scripts/verificar_entorno.py || echo "AVISO: la verificacion del entorno ha fallado; revisa el mensaje anterior."
echo "== Codespace listo. Abre notebooks/entrepinares_01_fundamentos_offline.ipynb"