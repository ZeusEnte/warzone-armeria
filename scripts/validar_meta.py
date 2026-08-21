"""Comprueba que docs/data/meta.json tiene sentido antes de publicarlo.

El scraper ya se protege del caso extremo (cero armas), pero si wzstats rediseña
la web el parser puede devolver basura *no vacia*: nombres sueltos, tiers
imposibles, armas sin accesorios. Eso se commitea y se publica sin que nadie se
entere hasta que el usuario abre la web y no entiende nada.

Uso:

    python scripts/validar_meta.py                 # valida docs/data/meta.json
    python scripts/validar_meta.py otro.json       # valida el archivo que le digas
    python scripts/validar_meta.py --avisos-fallan # los avisos tambien tumban la validacion

Sale con 0 si todo bien, 1 si hay algun error de estructura.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
POR_DEFECTO = ROOT / "docs" / "data" / "meta.json"

# Minimos por debajo de los cuales algo se ha roto seguro. Son holgados a
# proposito: no queremos que un dia flojo de wzstats tumbe la publicacion.
MODOS_MINIMOS = 3
ARMAS_MINIMAS_POR_MODO = 3
BUILDS_MINIMAS = 20
TIERS_VALIDOS = {"S", "A", "B", "C", "D", "E", "F"}
ROLES_VALIDOS = {"largo", "corto", "sniper", "otro"}
CLAVES_RAIZ = {"generated_at", "season", "source", "changes", "modes", "builds"}


def validar(datos: dict) -> tuple[list, list]:
    """Devuelve (errores, observaciones). Errores = no publicar."""
    errores: list = []
    notas: list = []

    faltan = CLAVES_RAIZ - set(datos)
    if faltan:
        errores.append(f"faltan claves en la raiz: {', '.join(sorted(faltan))}")
        return errores, notas

    try:
        generado = datetime.fromisoformat(datos["generated_at"])
        if generado.tzinfo is None:
            generado = generado.replace(tzinfo=timezone.utc)
        horas = (datetime.now(timezone.utc) - generado).total_seconds() / 3600
        if horas < -1:
            errores.append(f"generated_at esta en el futuro ({datos['generated_at']})")
        elif horas > 48:
            notas.append(f"los datos tienen {horas / 24:.1f} dias")
    except Exception:
        errores.append(f"generated_at no es una fecha valida: {datos['generated_at']!r}")

    modos = datos.get("modes") or {}
    if len(modos) < MODOS_MINIMOS:
        errores.append(f"solo hay {len(modos)} modos, se esperaban al menos {MODOS_MINIMOS}")

    contextos = set()
    for mid, modo in modos.items():
        for campo in ("label", "url", "context", "weapons"):
            if campo not in modo:
                errores.append(f"modo {mid}: le falta '{campo}'")
        contextos.add(modo.get("context", ""))

        armas = modo.get("weapons") or []
        if len(armas) < ARMAS_MINIMAS_POR_MODO:
            errores.append(f"modo {mid}: solo {len(armas)} armas")
        if modo.get("stale"):
            notas.append(f"modo {mid}: dato conservado del {str(modo.get('stale_since'))[:10]}")

        for w in armas:
            quien = f"modo {mid}, arma {w.get('name', '?')!r}"
            if not w.get("name"):
                errores.append(f"{quien}: sin nombre")
            if w.get("tier") not in TIERS_VALIDOS:
                errores.append(f"{quien}: tier invalido {w.get('tier')!r}")
            # "desde" es opcional (no se inventa cuando no hay historia), pero si
            # esta tiene que ser una fecha creible: una en el futuro haria que la
            # web dijese tonterias del tipo "entra hoy" para siempre.
            desde = w.get("desde")
            if desde is not None:
                try:
                    dia = datetime.strptime(str(desde), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if (dia - datetime.now(timezone.utc)).days > 0:
                        errores.append(f"{quien}: 'desde' esta en el futuro ({desde})")
                except ValueError:
                    errores.append(f"{quien}: 'desde' no es una fecha AAAA-MM-DD ({desde!r})")
            for p in w.get("positions") or []:
                if p.get("role") not in ROLES_VALIDOS:
                    errores.append(f"{quien}: papel invalido {p.get('role')!r}")
                if not isinstance(p.get("rank"), int):
                    errores.append(f"{quien}: puesto no numerico {p.get('rank')!r}")

        # Si ningun arma del modo tiene papel util, la web no puede recomendar
        # nada: se quedarian las tres tarjetas de equipamiento vacias.
        papeles = {p.get("role") for w in armas for p in (w.get("positions") or [])}
        if not papeles & {"largo", "corto", "sniper"}:
            errores.append(f"modo {mid}: ningun arma tiene papel (largo/corto/sniper)")

    builds = datos.get("builds") or {}
    if len(builds) < BUILDS_MINIMAS:
        errores.append(f"solo {len(builds)} armas con accesorios, se esperaban {BUILDS_MINIMAS}+")

    huerfanos = set()
    for slug, entrada in builds.items():
        lista = entrada.get("builds") or []
        if not lista:
            errores.append(f"build {slug}: sin ninguna configuracion")
        for b in lista:
            if not b.get("attachments"):
                errores.append(f"build {slug} ({b.get('label')}): sin accesorios")
            ctx = b.get("context")
            if ctx and ctx not in contextos:
                huerfanos.add(ctx)
    if huerfanos:
        # No es un error: wzstats publica builds de modos que no seguimos y el
        # scraper solo las guarda cuando no hay ninguna de las nuestras.
        notas.append(f"builds de contextos que no seguimos: {', '.join(sorted(huerfanos))}")

    for a in datos.get("warnings") or []:
        notas.append(f"aviso del scraper: {a}")

    return errores, notas


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Valida la estructura del meta.json generado.")
    p.add_argument("archivo", nargs="?", type=pathlib.Path, default=POR_DEFECTO)
    p.add_argument("--avisos-fallan", action="store_true",
                   help="salir con error tambien si hay observaciones (util en CI)")
    args = p.parse_args(argv)

    if not args.archivo.exists():
        print(f"ERROR: no existe {args.archivo}", file=sys.stderr)
        return 1
    try:
        datos = json.loads(args.archivo.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: {args.archivo} no es JSON valido: {exc}", file=sys.stderr)
        return 1

    errores, notas = validar(datos)

    for n in notas:
        print(f"nota: {n}")
    for e in errores:
        print(f"ERROR: {e}", file=sys.stderr)

    if errores:
        print(f"\n{len(errores)} problema(s): NO publicar este meta.json.", file=sys.stderr)
        return 1
    modos = len(datos.get("modes") or {})
    armas = sum(len(m.get("weapons") or []) for m in (datos.get("modes") or {}).values())
    print(f"OK: {modos} modos, {armas} armas, {len(datos.get('builds') or {})} armas con accesorios.")
    return 1 if (notas and args.avisos_fallan) else 0


if __name__ == "__main__":
    raise SystemExit(main())
