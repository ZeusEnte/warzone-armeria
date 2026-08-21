"""Pruebas del scraper y del validador. Sin red y sin dependencias extra.

    python scripts/pruebas.py

Usa asserts y trozos de HTML recortados de wzstats.gg. No pretenden cubrirlo
todo: cubren lo que ya se rompio alguna vez (los dos vocabularios de categoria,
los dos disenos de ficha, el codigo de canje colgando fuera de la lista) y la
logica nueva de recuperacion, que es la que no se puede probar a mano sin
esperar a que wzstats se caiga.
"""
from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys

AQUI = pathlib.Path(__file__).resolve().parent


def cargar(nombre: str):
    spec = importlib.util.spec_from_file_location(nombre, AQUI / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc = cargar("scrape")
va = cargar("validar_meta")

fallos: list = []


def comprobar(titulo: str, condicion, detalle: str = "") -> None:
    if condicion:
        print(f"  ok  {titulo}")
    else:
        print(f"  FALLO  {titulo}  {detalle}")
        fallos.append(titulo)


# --------------------------------------------------------------------------
# Pagina de meta: los dos vocabularios de categoria y la fusion de duplicados.
# --------------------------------------------------------------------------

META_HTML = """
<div class="tier-list">
  <div class="loadout-container">
    <div class="loadout-content-name"><div>FG42</div></div>
    <div class="loadout-tags">
      <div class="loadout-tag"><span class="rank">#1</span>Long Range</div>
      <div class="loadout-tag">LMG</div>
    </div>
    <div class="weapon-image-rank-container"><img src="https://img.wzstats.gg/fg42.png"></div>
    <a href="/best-loadouts/fg42">ver</a>
  </div>
  <div class="loadout-container">
    <div class="loadout-content-name"><div>FG42</div></div>
    <div class="loadout-tags">
      <div class="loadout-tag"><span class="rank">#3</span>Close Range</div>
    </div>
    <a href="/best-loadouts/fg42">ver</a>
  </div>
  <div class="tier-header">A Tier</div>
  <div class="loadout-container">
    <div class="loadout-content-name"><div>M15 MOD 0</div></div>
    <div class="loadout-tags">
      <div class="loadout-tag"><span class="rank">#2</span>Assault Rifle</div>
    </div>
    <a href="/best-loadouts/m15-mod-0">ver</a>
  </div>
</div>
"""

armas = sc.parse_meta_page(META_HTML)
por_slug = {w["slug"]: w for w in armas}

print("parse_meta_page")
comprobar("fusiona las dos apariciones de la misma arma", len(armas) == 2, f"salieron {len(armas)}")
comprobar("el primer bloque sin cabecera es tier S", por_slug["fg42"]["tier"] == "S")
comprobar("la cabecera 'A Tier' cambia el tier", por_slug["m15-mod-0"]["tier"] == "A")
comprobar("conserva los dos puestos al fusionar", len(por_slug["fg42"]["positions"]) == 2)
comprobar("'Long Range' se normaliza a largo",
          por_slug["fg42"]["positions"][0]["role"] == "largo")
comprobar("'Assault Rifle' de BO7 tambien es largo",
          por_slug["m15-mod-0"]["positions"][0]["role"] == "largo")
comprobar("sin etiqueta suelta, el tipo sale de la categoria",
          por_slug["m15-mod-0"]["weapon_type"] == "Assault Rifle")
comprobar("la imagen no se pierde en la fusion",
          por_slug["fg42"]["image"].endswith("fg42.png"))
comprobar("una pagina sin tier-list devuelve lista vacia",
          sc.parse_meta_page("<div>nada</div>") == [])

# --------------------------------------------------------------------------
# Ficha de arma: diseno nuevo (playstyle-card) y diseno viejo (sin tarjeta).
# --------------------------------------------------------------------------

FICHA_NUEVA = """
<div class="one-build-full-title">Best FG42 Loadout for Warzone Resurgence in Season 5</div>
<div class="playstyle-card">
  <div class="playstyle-text">Recommended</div>
  <div class="build-wrap">
    <ul class="weapon-visual-no-image-container">
      <li class="attachment-slot-no-image">
        <div class="slot-name-no-image">Optic</div>
        <div class="attachment-name-no-image">FANG HOVERPOINT ELO</div>
        <div class="level-tag">Armory</div>
      </li>
      <li class="attachment-slot-no-image prestige-slot">
        <div class="slot-name-no-image">Barrel</div>
        <div class="attachment-name-no-image">CORVUS LONG</div>
        <div class="level-tag">Level 37</div>
      </li>
    </ul>
    <div class="weapon-build-code">A16-34FIQ-XHAUL-11</div>
  </div>
</div>
<div class="one-build-full-title">Best FG42 Loadout for Zombies in Season 5</div>
<div class="playstyle-card">
  <div class="playstyle-text">Recommended</div>
  <ul class="weapon-visual-no-image-container">
    <li class="attachment-slot-no-image">
      <div class="slot-name-no-image">Optic</div>
      <div class="attachment-name-no-image">OTRA COSA</div>
    </li>
  </ul>
</div>
"""

FICHA_VIEJA = """
<div class="one-build-full-title">Best KAR98K Loadout for Warzone Battle Royale in Season 5</div>
<ul class="weapon-visual-no-image-container">
  <li class="attachment-slot-no-image">
    <div class="slot-name-no-image">Stock</div>
    <div class="attachment-name-no-image">SVT-40 STOCK</div>
  </li>
</ul>
"""

nuevas = sc.parse_builds(FICHA_NUEVA)
viejas = sc.parse_builds(FICHA_VIEJA)

print("\nparse_builds")
comprobar("descarta los modos que no seguimos (Zombies)", len(nuevas) == 1, f"salieron {len(nuevas)}")
comprobar("saca el contexto del titulo", nuevas[0]["context"] == "Warzone Resurgence")
comprobar("saca el nombre de la variante", nuevas[0]["label"] == "Recommended")
comprobar("encuentra el codigo, que cuelga fuera de la lista",
          nuevas[0]["code"] == "A16-34FIQ-XHAUL-11")
comprobar("lee los dos accesorios, incluido el de prestigio",
          len(nuevas[0]["attachments"]) == 2)
comprobar("lee el requisito de desbloqueo",
          nuevas[0]["attachments"][1]["unlock"] == "Level 37")
comprobar("el diseno viejo sin playstyle-card tambien se lee", len(viejas) == 1)
comprobar("sin tarjeta, la variante se llama Recommended", viejas[0]["label"] == "Recommended")
comprobar("sin codigo, el campo queda vacio", viejas[0]["code"] == "")
comprobar("parse_max_level lee el nivel",
          sc.parse_max_level('<div class="level-value">41</div>') == 41)
comprobar("parse_max_level devuelve 0 si no hay nada", sc.parse_max_level("<div></div>") == 0)

# --------------------------------------------------------------------------
# Cosecha de imagenes. La lista de tier solo trae las del tier S; el resto hay
# que sacarlas de las fichas de arma, que ya se descargan para los accesorios.
# Los trozos de HTML son recortes reales de wzstats.
# --------------------------------------------------------------------------

FICHA_HTML = """
<img src="https://img.wzstats.gg/kar98k-wzstats-d22486/gunFullDisplay">
<img src="https://img.wzstats.gg/kar98k/gunFullDisplay">
<img src="https://img.wzstats.gg/paranoia-warzone-bor/perksV2">
<div class="weapon-alternative-image"><img src="https://img.wzstats.gg/fg42/gunDisplayLoadouts"></div>
<div class="weapon-alternative-image"><img src="https://img.wzstats.gg/mors/gunDisplayLoadouts"></div>
"""

indice = sc.cosechar_imagenes(FICHA_HTML)
comprobar("saca la imagen del arma de la ficha",
          indice.get("kar98k") == "https://img.wzstats.gg/kar98k/gunFullDisplay")
comprobar("aprovecha las imagenes de las armas alternativas",
          indice.get("fg42") == "https://img.wzstats.gg/fg42/gunDisplayLoadouts" and "mors" in indice)
comprobar("descarta los adornos (skins) del arma",
          not any("-wzstats-" in k for k in indice))
comprobar("no confunde los iconos de ventajas con armas", "paranoia-warzone-bor" not in indice)

comprobar("quita el sufijo _versionN, que no es deducible del slug",
          sc.cosechar_imagenes(
              '<img src="https://img.wzstats.gg/m15-mod-0_version7/gunDisplayLoadouts">'
          ) == {"m15-mod-0": "https://img.wzstats.gg/m15-mod-0_version7/gunDisplayLoadouts"})

# La pequena es la que usa la web en las tarjetas: gana a la grande aunque llegue
# despues, y el orden en que aparezcan en el HTML no debe cambiar el resultado.
GRANDE = '<img src="https://img.wzstats.gg/vst/gunFullDisplay">'
PEQUENA = '<img src="https://img.wzstats.gg/vst/gunDisplayLoadouts">'
comprobar("prefiere la imagen pequena de listado",
          sc.cosechar_imagenes(GRANDE + PEQUENA)["vst"].endswith("gunDisplayLoadouts"))
comprobar("y tambien si llegan en el otro orden",
          sc.cosechar_imagenes(PEQUENA + GRANDE)["vst"].endswith("gunDisplayLoadouts"))

modos_sin_fotos = {
    "m0": {"weapons": [
        {"name": "FG42", "slug": "fg42", "image": ""},
        {"name": "JAGER 45", "slug": "j%C3%A4ger-45", "image": ""},
        {"name": "Ya tiene", "slug": "vst", "image": "https://img.wzstats.gg/vst/ya"},
        {"name": "Sin ficha", "slug": "", "image": ""},
    ]},
    "viejo": {"stale": True, "weapons": [{"name": "FG42", "slug": "fg42", "image": ""}]},
}
puestas = sc.rellenar_imagenes(modos_sin_fotos, {
    "fg42": "https://img.wzstats.gg/fg42/gunDisplayLoadouts",
    "jäger-45": "https://img.wzstats.gg/jäger-45_version5/gunDisplayLoadouts",
})
armas = modos_sin_fotos["m0"]["weapons"]
comprobar("rellena las armas que no traen imagen", puestas == 2 and armas[0]["image"].endswith("gunDisplayLoadouts"))
comprobar("casa el slug aunque venga codificado en el href", armas[1]["image"] != "")
comprobar("no pisa la imagen que ya tenia", armas[2]["image"].endswith("/ya"))
comprobar("no toca un modo conservado del dia anterior",
          modos_sin_fotos["viejo"]["weapons"][0]["image"] == "")

# --------------------------------------------------------------------------
# Recuperacion cuando un modo falla, y acumulacion de cambios el mismo dia.
# --------------------------------------------------------------------------

PREVIO = {
    "generated_at": "2026-08-19T06:10:00+00:00",
    "previous_generated_at": "2026-08-18T06:10:00+00:00",
    "changes": [{"mode": "resurgence", "weapon": "FG42", "kind": "sube", "from": "A", "to": "S"}],
    "modes": {
        "resurgence": {
            "label": "Resurgence", "url": "u", "context": "Warzone Resurgence",
            "weapons": [{"name": "FG42", "slug": "fg42", "tier": "S", "positions": [],
                         "weapon_type": "LMG", "tags": [], "image": ""}],
        }
    },
    "builds": {},
}

recuperado = sc.recuperar_modo(PREVIO, {"id": "resurgence"})
print("\nrecuperacion de un modo caido")
comprobar("copia las armas del dia anterior", len(recuperado["weapons"]) == 1)
comprobar("lo marca como no fresco", recuperado["stale"] is True)
comprobar("guarda desde cuando esta viejo",
          recuperado["stale_since"] == "2026-08-19T06:10:00+00:00")
comprobar("si no hay dato anterior, no inventa nada",
          sc.recuperar_modo({}, {"id": "resurgence"}) == {})

# Un modo recuperado no debe generar diferencias contra si mismo.
comprobar("un modo conservado no ensucia el diff de cambios",
          sc.diff_modes(PREVIO, {"resurgence": recuperado}) == [])

nuevo_modo = {
    "resurgence": {
        "label": "Resurgence", "url": "u", "context": "Warzone Resurgence",
        "weapons": [{"name": "FG42", "slug": "fg42", "tier": "A", "positions": [],
                     "weapon_type": "LMG", "tags": [], "image": ""}],
    }
}
bajada = sc.diff_modes(PREVIO, nuevo_modo)
comprobar("detecta que un arma baja de tier",
          bajada == [{"mode": "resurgence", "weapon": "FG42", "kind": "baja", "from": "S", "to": "A"}],
          str(bajada))

print("\nacumulacion de cambios dentro del mismo dia")
fusion = sc.fusionar_cambios(PREVIO["changes"], bajada)
comprobar("suma los cambios de las dos pasadas", len(fusion) == 2)
comprobar("no repite el mismo cambio dos veces",
          len(sc.fusionar_cambios(PREVIO["changes"], PREVIO["changes"])) == 1)

# --------------------------------------------------------------------------
# Validador.
# --------------------------------------------------------------------------

BUENO = {
    "generated_at": "2026-08-20T06:10:00+00:00",
    "season": "Season 5", "source": "wzstats.gg", "changes": [],
    "modes": {
        f"m{i}": {
            "label": f"Modo {i}", "url": "u", "context": f"ctx{i}",
            "weapons": [
                {"name": "A", "slug": "a", "tier": "S",
                 "positions": [{"range": "Long Range", "rank": 1, "role": "largo"}],
                 "weapon_type": "AR", "tags": [], "image": ""},
                {"name": "B", "slug": "b", "tier": "A",
                 "positions": [{"range": "Close Range", "rank": 1, "role": "corto"}],
                 "weapon_type": "SMG", "tags": [], "image": ""},
                {"name": "C", "slug": "c", "tier": "B",
                 "positions": [{"range": "Sniper", "rank": 1, "role": "sniper"}],
                 "weapon_type": "Sniper", "tags": [], "image": ""},
            ],
        } for i in range(3)
    },
    "builds": {
        f"arma{i}": {"name": f"Arma {i}", "max_level": 30, "builds": [
            {"context": "ctx0", "label": "Recommended", "code": "",
             "attachments": [{"slot": "Optic", "name": "X", "unlock": ""}]}
        ]} for i in range(20)
    },
}

print("\nvalidar_meta")
errores, _ = va.validar(BUENO)
comprobar("un meta.json correcto pasa", errores == [], str(errores))

malo = copy.deepcopy(BUENO)
malo["modes"]["m0"]["weapons"][0]["tier"] = "Z"
comprobar("caza un tier imposible", any("tier invalido" in e for e in va.validar(malo)[0]))

malo = copy.deepcopy(BUENO)
malo["modes"]["m0"]["weapons"] = []
comprobar("caza un modo vacio", any("solo 0 armas" in e for e in va.validar(malo)[0]))

malo = copy.deepcopy(BUENO)
for w in malo["modes"]["m0"]["weapons"]:
    for p in w["positions"]:
        p["role"] = "otro"
comprobar("caza un modo sin ningun papel util",
          any("ningun arma tiene papel" in e for e in va.validar(malo)[0]))

malo = copy.deepcopy(BUENO)
malo["builds"]["arma0"]["builds"][0]["attachments"] = []
comprobar("caza una build sin accesorios", any("sin accesorios" in e for e in va.validar(malo)[0]))

malo = copy.deepcopy(BUENO)
del malo["modes"]
comprobar("caza que falte una clave de la raiz", any("faltan claves" in e for e in va.validar(malo)[0]))

malo = copy.deepcopy(BUENO)
malo["modes"]["m0"]["stale"] = True
malo["modes"]["m0"]["stale_since"] = "2026-08-19T06:10:00+00:00"
errores, notas = va.validar(malo)
comprobar("un modo conservado avisa pero no bloquea",
          errores == [] and any("conservado" in n for n in notas))

print()
if fallos:
    print(f"{len(fallos)} prueba(s) fallida(s):")
    for f in fallos:
        print(f"  - {f}")
    sys.exit(1)
print("Todas las pruebas pasan.")
