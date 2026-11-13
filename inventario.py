
import csv
from collections import Counter
from pathlib import Path

RUTA_INVENTARIO = (
    Path(__file__).resolve().parent
    / "datos"
    / "inventario_demo.csv"
)

CAMPOS_OBLIGATORIOS = {
    "asset_id",
    "nombre",
    "centro",
    "tipo",
    "fabricante",
    "producto",
    "version",
    "criticidad",
    "responsable",
    "configuracion",
}


def leer_inventario(ruta=RUTA_INVENTARIO):
    """Lee y valida el inventario CSV de activos IT/OT."""

    ruta = Path(ruta)

    if not ruta.is_file():
        raise FileNotFoundError(
            f"No se encuentra el inventario: {ruta}"
        )

    with ruta.open(
        "r", encoding="utf-8-sig", newline=""
    ) as archivo:
        lector = csv.DictReader(archivo)

        campos = set(lector.fieldnames or [])
        faltantes = CAMPOS_OBLIGATORIOS - campos

        if faltantes:
            raise ValueError(
                f"Faltan columnas: {sorted(faltantes)}"
            )

        activos = []
        identificadores = set()

        for numero, fila in enumerate(lector, start=2):
            if None in fila:
                raise ValueError(
                    f"Fila {numero}: columnas adicionales"
                )

            activo = {
                clave: (valor or "").strip()
                for clave, valor in fila.items()
            }

            for campo in CAMPOS_OBLIGATORIOS:
                if not activo[campo]:
                    raise ValueError(
                        f"Fila {numero}: campo vacío '{campo}'"
                    )

            asset_id = activo["asset_id"]

            if asset_id in identificadores:
                raise ValueError(
                    f"Identificador duplicado: {asset_id}"
                )

            if activo["tipo"] not in {"IT", "OT"}:
                raise ValueError(
                    f"Tipo inválido en {asset_id}"
                )

            if activo["criticidad"] not in {
                "alta", "media", "baja"
            }:
                raise ValueError(
                    f"Criticidad inválida en {asset_id}"
                )

            identificadores.add(asset_id)
            activos.append(activo)

    if not activos:
        raise ValueError("El inventario está vacío")

    return activos


if __name__ == "__main__":
    activos = leer_inventario()

    tipos = Counter(a["tipo"] for a in activos)
    criticidades = Counter(
        a["criticidad"] for a in activos
    )

    print("INVENTARIO VALIDADO CORRECTAMENTE")
    print(f"Total de activos: {len(activos)}")
    print(f"Activos IT: {tipos['IT']}")
    print(f"Activos OT: {tipos['OT']}")
    print(f"Criticidad alta: {criticidades['alta']}")
    print(f"Criticidad media: {criticidades['media']}")
    print(f"Criticidad baja: {criticidades['baja']}")

    print("\nActivos cargados:")

    for activo in activos:
        print(
            f"- {activo['asset_id']} | "
            f"{activo['producto']} | "
            f"{activo['version']}"
        )
