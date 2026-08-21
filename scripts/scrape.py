"""Raspa la tier list de wzstats.gg y genera docs/data/meta.json.

Se ejecuta a diario desde GitHub Actions. Una sola peticion por pagina de meta
y otra por arma del top (con pausa entre ellas) para no castigar la web origen.

Para trabajar en el parser sin lanzar los cinco modos y ochenta fichas:

    python scripts/scrape.py --modo resurgence --sin-builds --simular

Ver todas las opciones con ``--help``.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "data" / "meta.json"

BASE = "https://wzstats.gg"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Modos que seguimos. El orden es el de las pestanas en la web.
# "context" es como titula wzstats la build de ese modo dentro de la ficha del
# arma ("Best FG42 Loadout for Warzone Resurgence in Season 5").
MODES = [
    {"id": "resurgence", "label": "Resurgence", "url": BASE + "/warzone/meta/resurgence",
     "context": "Warzone Resurgence"},
    {"id": "multiplayer", "label": "Multijugador (BO7)", "url": BASE + "/bo7/meta",
     "context": "Black Ops 7 Multiplayer"},
    {"id": "resurgence_ranked", "label": "Resurgence Ranked", "url": BASE + "/warzone/meta/ranked/resurgence",
     "context": "Warzone Resurgence Ranked"},
    {"id": "multiplayer_ranked", "label": "MP Ranked (BO7)", "url": BASE + "/bo7/ranked/meta",
     "context": "Black Ops 7 Ranked"},
    {"id": "battle_royale", "label": "Battle Royale", "url": BASE + "/",
     "context": "Warzone Battle Royale"},
]

# Cuantas fichas de arma abrimos para sacar los accesorios completos. Cubrimos
# todas las S y A porque la web deja pinchar cualquier arma de la tabla y hay
# que tener su build lista.
BUILD_BUDGET = 80
REQUEST_PAUSE = 1.5

TIER_ORDER = ["S", "A", "B", "C", "D", "E", "F"]

# Warzone ordena sus rankings por alcance ("Long Range") y Black Ops 7 por tipo
# de arma ("Assault Rifle"). Normalizamos ambos vocabularios a tres papeles para
# que la web pueda tratar todos los modos igual.
ROLE_BY_CATEGORY = {
    "long range": "largo",
    "assault rifle": "largo",
    "lmg": "largo",
    "br": "largo",
    "battle rifle": "largo",
    "close range": "corto",
    "sniper support": "corto",
    "smg": "corto",
    "shotgun": "corto",
    "pistol": "corto",
    "sniper": "sniper",
    "marksman": "sniper",
}

WEAPON_CLASSES = {
    "assault rifle", "smg", "lmg", "sniper", "marksman", "shotgun",
    "pistol", "br", "battle rifle", "special", "launcher", "melee",
}


class ErrorDeDescarga(RuntimeError):
    """No se pudo traer una pagina despues de los reintentos."""


def aviso(mensaje: str) -> None:
    """Mensaje a stderr. Los avisos tambien acaban dentro del meta.json."""
    print(f"   {mensaje}", file=sys.stderr)


def tier_rank(tier: str) -> int:
    """Menor es mejor. Los tiers desconocidos van al final."""
    return TIER_ORDER.index(tier) if tier in TIER_ORDER else len(TIER_ORDER)


def get(url: str, session: requests.Session, tries: int = 3) -> str:
    last = None
    for attempt in range(tries):
        try:
            r = session.get(url, headers=HEADERS, timeout=45)
            # Un 404 o un 403 no se arreglan esperando: reintentarlos solo gasta
            # tiempo y peticiones. El 429 si, que es "vas demasiado rapido".
            if 400 <= r.status_code < 500 and r.status_code != 429:
                raise ErrorDeDescarga(f"{url}: HTTP {r.status_code}")
            r.raise_for_status()
            # La cabecera no siempre trae charset y los nombres llevan acentos
            # (JAGER 45, etc.), asi que forzamos utf-8.
            r.encoding = "utf-8"
            return r.text
        except ErrorDeDescarga:
            raise
        except Exception as exc:  # red inestable en el runner
            last = exc
            if attempt < tries - 1:
                time.sleep(2 + attempt * 3)
    raise ErrorDeDescarga(f"no se pudo descargar {url}: {last}")


def txt(node) -> str:
    if node is None:
        return ""
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def slug_from(card) -> str:
    link = card.select_one("a[href*='/best-loadouts/']")
    if not link:
        return ""
    return link["href"].rsplit("/", 1)[-1]


def parse_meta_page(html: str) -> list:
    """Devuelve las armas de una pagina de meta, con su tier y su ranking."""
    soup = BeautifulSoup(html, "html.parser")
    tier_list = soup.select_one(".tier-list")
    if tier_list is None:
        return []

    weapons = []
    # El primer bloque no lleva cabecera "X Tier": es el top 10, o sea el S.
    current = "S"
    seen_header = False

    for el in tier_list.descendants:
        if not hasattr(el, "get"):
            continue
        classes = el.get("class") or []

        if "tier-header" in classes:
            label = txt(el)
            m = re.match(r"([SABCDEF])\s*tier", label, re.I)
            if m:
                current = m.group(1).upper()
                seen_header = True
            elif seen_header:
                current = "?"
            continue

        if "loadout-container" not in classes:
            continue

        name = txt(el.select_one(".loadout-content-name > div"))
        if not name:
            continue

        positions, tags = [], []
        for tag in el.select(".loadout-tags .loadout-tag"):
            rank_el = tag.select_one(".rank")
            label = txt(tag)
            if rank_el:
                rank_txt = txt(rank_el)
                label = label.replace(rank_txt, "").strip()
                try:
                    rank = int(rank_txt.lstrip("#"))
                except ValueError:
                    rank = 99
                positions.append(
                    {
                        "range": label,
                        "rank": rank,
                        "role": ROLE_BY_CATEGORY.get(label.lower(), "otro"),
                    }
                )
            else:
                tags.append(label)

        # En BO7 la categoria del ranking ya es el tipo de arma y no hay etiqueta
        # suelta, asi que la reutilizamos para no dejar el tipo vacio.
        weapon_type = tags[0] if tags else ""
        if not weapon_type:
            weapon_type = next(
                (p["range"] for p in positions if p["range"].lower() in WEAPON_CLASSES), ""
            )

        img = el.select_one(".weapon-image-rank-container img")
        weapons.append(
            {
                "name": name,
                "slug": slug_from(el),
                "tier": current,
                "positions": positions,
                "weapon_type": weapon_type,
                "tags": tags,
                "image": img["src"] if img is not None and img.has_attr("src") else "",
            }
        )

    # La misma arma aparece una vez por cada categoria de rango en la que entra.
    merged = {}
    for w in weapons:
        key = w["slug"] or w["name"].lower()
        prev = merged.get(key)
        if prev is None:
            merged[key] = w
            continue
        have = {(p["range"], p["rank"]) for p in prev["positions"]}
        prev["positions"] += [p for p in w["positions"] if (p["range"], p["rank"]) not in have]
        if tier_rank(w["tier"]) < tier_rank(prev["tier"]):
            prev["tier"] = w["tier"]
        # La primera aparicion puede venir sin tipo, sin imagen o sin slug (segun
        # la categoria en la que salga); completamos con lo que traigan las otras.
        for campo in ("weapon_type", "image", "slug"):
            if not prev[campo] and w[campo]:
                prev[campo] = w[campo]
        for t in w["tags"]:
            if t not in prev["tags"]:
                prev["tags"].append(t)
    return list(merged.values())


CONTEXT_RE = re.compile(r"Loadout for (.+?) in Season", re.I)
TRACKED_CONTEXTS = {m["context"] for m in MODES}


def parse_builds(html: str) -> list:
    """Saca las configuraciones (accesorios) de la ficha de un arma.

    La ficha repite las mismas builds para cada modo, precedidas de un titulo
    ".one-build-full-title". Recorremos en orden de documento para saber a que
    modo pertenece cada configuracion.

    Hay dos disenos en la web: las armas nuevas envuelven cada build en un
    ".playstyle-card" con nombre ("Recommended", "SNIPER SUPPORT"...) y las
    antiguas (KAR98K y companyia) sueltan la lista de accesorios sin tarjeta.
    Lo que tienen en comun es el "ul.weapon-visual-no-image-container", asi que
    anclamos ahi y buscamos el nombre hacia arriba si existe.
    """
    soup = BeautifulSoup(html, "html.parser")
    builds = []
    seen = set()
    context = ""

    for el in soup.descendants:
        if not hasattr(el, "get"):
            continue
        classes = el.get("class") or []

        if "one-build-full-title" in classes:
            m = CONTEXT_RE.search(txt(el))
            context = m.group(1).strip() if m else ""
            continue

        if el.name != "ul" or "weapon-visual-no-image-container" not in classes:
            continue

        card = el.find_parent(class_="playstyle-card")
        label = (txt(card.select_one(".playstyle-text")) if card else "") or "Recommended"
        attachments = []
        # .prestige-slot lleva tambien .attachment-slot-no-image, un selector basta.
        for slot in el.select(".attachment-slot-no-image"):
            att_name = txt(slot.select_one(".attachment-name-no-image"))
            if not att_name:
                continue
            attachments.append(
                {
                    "slot": txt(slot.select_one(".slot-name-no-image")),
                    "name": att_name,
                    # "Level 37", "Armory", "Prestige" o el arma que hay que
                    # subir para desbloquearlo ("Peacekeeper MK1").
                    "unlock": txt(slot.select_one(".level-tag")),
                }
            )
        if not attachments:
            continue

        # El codigo de canje vive junto a la lista, no dentro de ella.
        code = ""
        node = el
        for _ in range(4):
            node = node.parent
            if node is None:
                break
            found = node.select_one(".weapon-build-code")
            if found:
                code = txt(found)
                break

        key = (context, label, tuple(a["name"] for a in attachments))
        if key in seen:
            continue
        seen.add(key)
        builds.append(
            {"context": context, "label": label, "code": code, "attachments": attachments}
        )

    # Solo guardamos las builds de los modos que seguimos: la ficha trae ademas
    # Iron Gauntlet, Zombies y Black Ops Royale, que no usamos y ocupan sitio.
    tracked = [b for b in builds if b["context"] in TRACKED_CONTEXTS]
    return tracked or builds


# Las dos variantes de imagen de arma que sirve wzstats: la pequena que usa en
# los listados y la grande de la ficha. El sufijo "_versionN" (de la 1 a la 7, y
# a veces ausente) NO es deducible del slug, asi que no se construyen URL: solo
# se recogen las que wzstats haya escrito.
IMG_RE = re.compile(
    r"https://img\.wzstats\.gg/([^/\"'\s]+)/(gunDisplayLoadouts|gunFullDisplay)")
VERSION_RE = re.compile(r"_version\d+$")


def cosechar_imagenes(html: str) -> dict:
    """Indice slug -> URL de imagen con lo que traiga una pagina cualquiera.

    La lista de tier solo trae imagen del primer bloque (el tier S): las demas
    las carga el navegador despues, asi que no estan en el HTML que recibimos y
    el 96% de las armas se quedaba sin foto.

    La ficha de arma, que ya descargamos para los accesorios, si trae varias:
    la del arma en cuestion y un bloque de "armas alternativas" con las de
    otras, que sirven para rellenar armas cuya ficha ni siquiera abrimos.

    Los adornos de la ficha (skins) van como "<slug>-wzstats-<hash>", que no
    casa con ningun slug conocido: al indexar por el segmento limpio se
    descartan solos.
    """
    encontrado: dict = {}
    for segmento, variante in IMG_RE.findall(html):
        slug = VERSION_RE.sub("", segmento)
        # Los adornos ("kar98k-wzstats-d22486") no casan con ningun slug, pero se
        # descartan aqui para no llenar el indice de entradas que no sirven.
        if not slug or "-wzstats-" in slug:
            continue
        # La pequena es la que usa la web en las tarjetas; la grande solo se
        # guarda si no hay otra cosa.
        if variante == "gunDisplayLoadouts" or slug not in encontrado:
            anterior = encontrado.get(slug, "")
            if anterior and "gunDisplayLoadouts" in anterior and variante != "gunDisplayLoadouts":
                continue
            encontrado[slug] = f"https://img.wzstats.gg/{segmento}/{variante}"
    return encontrado


def rellenar_imagenes(modes: dict, indice: dict) -> int:
    """Pone imagen a las armas que no la traigan. Devuelve cuantas se rellenaron."""
    puestas = 0
    for modo in modes.values():
        if modo.get("stale"):
            continue
        for w in modo["weapons"]:
            if w.get("image") or not w.get("slug"):
                continue
            # El href viene codificado ("j%C3%A4ger-45") y la URL de imagen no.
            url = indice.get(unquote(w["slug"])) or indice.get(w["slug"])
            if url:
                w["image"] = url
                puestas += 1
    return puestas


def parse_max_level(html: str) -> int:
    """Nivel maximo del arma, para saber hasta donde hay que subirla."""
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.select(".level-value"):
        raw = txt(el)
        if raw.isdigit():
            return int(raw)
    return 0


def detect_season(session: requests.Session, previa: str = "") -> str:
    """La temporada sale de wzranked.com, que es un servidor ajeno mas.

    Si hoy no contesta, se conserva la que ya teniamos: el literal generico
    empeoraria la cabecera de la web ("Temporada actual" donde ponia "Season 5
    Reloaded, 2026") y ese dato bueno se perderia para siempre. Misma politica
    que con los modos y los accesorios.
    """
    try:
        html = get("https://wzranked.com/games/call-of-duty-warzone/meta", session)
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        m = re.search(r"Season\s+\d+(?:\s+Reloaded)?,?\s*20\d\d", text)
        if m:
            return m.group(0)
        aviso("aviso: wzranked no traia el numero de temporada")
    except Exception as exc:
        aviso(f"aviso: no se pudo leer la temporada ({exc})")
    return previa or "Temporada actual"


def pick_for_builds(modes: dict, budget: int = BUILD_BUDGET) -> list:
    """Elige que armas merecen una peticion extra: las mejores de cada modo."""
    scored = {}
    for mode in modes.values():
        for w in mode["weapons"]:
            if not w["slug"] or w["tier"] not in ("S", "A"):
                continue
            best_rank = min((p["rank"] for p in w["positions"]), default=50)
            weight = (0 if w["tier"] == "S" else 100) + best_rank
            prev = scored.get(w["slug"])
            if prev is None or weight < prev[0]:
                scored[w["slug"]] = (weight, w["name"])
    ordered = sorted(scored.items(), key=lambda kv: kv[1][0])
    return [(slug, value[1]) for slug, value in ordered[:budget]]


def diff_modes(old: dict, new: dict) -> list:
    """Compara la meta anterior con la nueva para poder avisar de los cambios."""
    changes = []
    for mode_id, mode in new.items():
        # Un modo que no se pudo raspar viene copiado del dia anterior: comparar
        # su copia consigo misma no dice nada, y encima taparia el diff bueno.
        if mode.get("stale"):
            continue
        prev_mode = (old.get("modes") or {}).get(mode_id)
        if not prev_mode:
            continue
        prev = {w["name"]: w for w in prev_mode["weapons"]}
        for w in mode["weapons"]:
            before = prev.pop(w["name"], None)
            if before is None:
                changes.append({"mode": mode_id, "weapon": w["name"], "kind": "entra", "to": w["tier"]})
            elif before["tier"] != w["tier"]:
                kind = "sube" if tier_rank(w["tier"]) < tier_rank(before["tier"]) else "baja"
                changes.append({
                    "mode": mode_id, "weapon": w["name"], "kind": kind,
                    "from": before["tier"], "to": w["tier"],
                })
        for name in prev:
            changes.append({"mode": mode_id, "weapon": name, "kind": "sale"})
    return changes


def marcar_antiguedad(modes: dict, previo: dict, hoy: str) -> int:
    """Anota en cada arma desde que dia lleva en el tier que tiene ahora.

    Es la pregunta que decide en que arma merece la pena gastar horas de subida
    de nivel: una S que lleva tres semanas no dice lo mismo que una que entro
    ayer y manana parchean.

    No hace falta un archivo aparte ni una descarga mas: el dato se arrastra del
    meta.json anterior, que ya se lee para calcular los cambios.

    Importa mucho **no inventar la fecha**. La primera vez que esto corre no hay
    historia, y poner "hoy" en todas seria decirle al usuario que la meta entera
    acaba de cambiar. Asi que:

    - Modo sin dato anterior: no se anota nada y la web no ensena nada.
    - El arma ya estaba ayer en este tier y traia fecha: se conserva.
    - Ya estaba ayer en este tier pero sin fecha: se anota la fecha del JSON
      anterior, que es lo unico demostrable ("al menos desde"). Se queda fija
      mientras el tier no cambie, que es justo lo que se quiere.
    - Cambio de tier, o arma nueva: hoy, que ahi si consta.

    Devuelve cuantas armas quedaron con fecha.
    """
    antes = previo.get("modes") or {}
    demostrable = (previo.get("generated_at") or "")[:10]
    marcadas = 0
    for mode_id, modo in modes.items():
        # Un modo conservado viene copiado entero del dia anterior: sus fechas ya
        # son las buenas y recalcularlas contra si mismo no aportaria nada.
        if modo.get("stale"):
            marcadas += sum(1 for w in modo["weapons"] if w.get("desde"))
            continue
        ayer = {w["name"]: w for w in (antes.get(mode_id) or {}).get("weapons") or []}
        if not ayer:
            continue
        for w in modo["weapons"]:
            anterior = ayer.get(w["name"])
            if anterior is None or anterior.get("tier") != w["tier"]:
                w["desde"] = hoy
            else:
                fecha = anterior.get("desde") or demostrable
                if not fecha:
                    continue
                w["desde"] = fecha
            marcadas += 1
    return marcadas


def fusionar_cambios(previos: list, nuevos: list) -> list:
    """Une dos listas de cambios sin repetir, conservando el orden."""
    salida, vistos = [], set()
    for c in list(previos) + list(nuevos):
        clave = (c.get("mode"), c.get("weapon"), c.get("kind"), c.get("from"), c.get("to"))
        if clave in vistos:
            continue
        vistos.add(clave)
        salida.append(c)
    return salida


def cargar_previo(ruta: pathlib.Path) -> dict:
    if not ruta.exists():
        return {}
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception as exc:
        aviso(f"aviso: no se pudo leer el meta.json anterior ({exc})")
        return {}


def parsear_argumentos(argv=None) -> argparse.Namespace:
    ids = [m["id"] for m in MODES]
    p = argparse.ArgumentParser(
        description="Raspa wzstats.gg y genera el meta.json que lee la web.",
        epilog="Ejemplo rapido para probar el parser: "
               "python scripts/scrape.py --modo resurgence --sin-builds --simular",
    )
    p.add_argument("--modo", action="append", choices=ids, metavar="ID",
                   help=f"raspar solo este modo (repetible). Validos: {', '.join(ids)}")
    p.add_argument("--sin-builds", action="store_true",
                   help="no abrir las fichas de arma: sin accesorios ni codigos, pero en segundos")
    p.add_argument("--limite-builds", type=int, default=BUILD_BUDGET, metavar="N",
                   help=f"cuantas fichas de arma abrir como maximo (por defecto {BUILD_BUDGET})")
    p.add_argument("--pausa", type=float, default=REQUEST_PAUSE, metavar="SEG",
                   help=f"pausa entre peticiones en segundos (por defecto {REQUEST_PAUSE})")
    p.add_argument("--salida", type=pathlib.Path, default=OUT, metavar="RUTA",
                   help="donde escribir el JSON (por defecto docs/data/meta.json)")
    p.add_argument("--simular", action="store_true",
                   help="hacerlo todo pero no escribir nada en disco")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parsear_argumentos(argv)
    parcial = bool(args.modo) or args.sin_builds or args.limite_builds != BUILD_BUDGET
    # Se comparan rutas resueltas: OUT es absoluta y lo que teclea una persona no
    # lo es, asi que "--salida docs/data/meta.json" se colaba por delante de la
    # guarda justo cuando la nombraba.
    salida_es_el_bueno = args.salida.resolve() == OUT.resolve()
    # Se comprueba antes de gastar peticiones: una pasada parcial no puede pisar
    # el JSON bueno o el bot commitearia datos a medias como si fueran del dia.
    if parcial and not args.simular and salida_es_el_bueno:
        print("ERROR: una ejecucion parcial (--modo/--sin-builds/--limite-builds) no sobrescribe "
              "docs/data/meta.json. Anade --simular para probar, o --salida para otro archivo.",
              file=sys.stderr)
        return 2
    modos_pedidos = [m for m in MODES if not args.modo or m["id"] in args.modo]

    session = requests.Session()
    previo = cargar_previo(args.salida)
    modes: dict = {}
    avisos: list = []
    # slug -> URL de imagen, con lo que vaya apareciendo en cualquier pagina.
    imagenes: dict = {}

    for mode in modos_pedidos:
        print(f"-> {mode['label']}: {mode['url']}")
        weapons = []
        try:
            html = get(mode["url"], session)
            weapons = parse_meta_page(html)
            imagenes.update(cosechar_imagenes(html))
        except Exception as exc:
            aviso(f"FALLO: {exc}")
        if not weapons:
            # Sin armas casi siempre significa que wzstats cambio el HTML.
            recuperado = recuperar_modo(previo, mode)
            if recuperado:
                modes[mode["id"]] = recuperado
                desde = recuperado.get("stale_since", "")[:10]
                avisos.append(f"{mode['label']}: no se pudo leer, se conserva el dato del {desde}")
                aviso(f"sin armas: se conserva el dato guardado del {desde}")
            else:
                avisos.append(f"{mode['label']}: no se pudo leer y no habia dato anterior")
                aviso("sin armas y sin dato anterior que conservar")
            continue

        print(f"   {len(weapons)} armas")
        modes[mode["id"]] = {
            "label": mode["label"],
            "url": mode["url"],
            "context": mode["context"],
            "weapons": weapons,
        }
        time.sleep(args.pausa)

    # Si solo se pidieron algunos modos, los demas se traen del JSON anterior
    # para no publicar una web a la que le faltan pestanas.
    for mode in MODES:
        if mode["id"] not in modes:
            heredado = recuperar_modo(previo, mode)
            if heredado:
                modes[mode["id"]] = heredado

    if not any(not m.get("stale") for m in modes.values()):
        print("ERROR: ningun modo se pudo raspar, no se sobrescribe el JSON", file=sys.stderr)
        return 1

    builds = dict(previo.get("builds") or {}) if args.sin_builds else {}
    if args.sin_builds:
        print("-> accesorios: omitidos (--sin-builds), se conservan los del JSON anterior")
    else:
        frescos = {k: v for k, v in modes.items() if not v.get("stale")}
        targets = pick_for_builds(frescos or modes, args.limite_builds)
        # Partimos de los accesorios que ya teniamos para estas mismas armas: si
        # hoy falla la ficha de una, se queda la de ayer en vez de desaparecer.
        # Solo las de la lista de hoy, para que el JSON no crezca sin control con
        # armas que ya no estan en la meta.
        anteriores = previo.get("builds") or {}
        for slug, _ in targets:
            if slug in anteriores:
                builds[slug] = anteriores[slug]

        print(f"-> accesorios de {len(targets)} armas")
        fallos = 0
        for slug, name in targets:
            try:
                page = get(f"{BASE}/best-loadouts/{slug}", session)
                found = parse_builds(page)
                # La ficha es la unica fuente de imagenes que no se cargan por
                # javascript, y ya la tenemos descargada: no cuesta una peticion.
                imagenes.update(cosechar_imagenes(page))
            except Exception as exc:
                fallos += 1
                aviso(f"{slug}: {exc}")
                continue
            if found:
                builds[slug] = {
                    "name": name,
                    "max_level": parse_max_level(page),
                    "builds": found,
                }
                print(f"   {name}: {len(found)} builds")
            else:
                fallos += 1
                aviso(f"{slug}: la ficha no traia ninguna build")
            time.sleep(args.pausa)

        heredados = sum(1 for slug, _ in targets
                        if slug in anteriores and builds.get(slug) is anteriores[slug])
        if heredados:
            print(f"   {heredados} armas conservan los accesorios de la actualizacion anterior")
        # Un fallo suelto es ruido de red; que falle un tercio significa que
        # wzstats cambio el HTML de las fichas y hay que mirarlo.
        if targets and fallos >= max(3, len(targets) // 3):
            avisos.append(f"no se pudieron leer los accesorios de {fallos} de {len(targets)} armas")

    # Las imagenes que ya conociamos ayer siguen valiendo hoy: sembrando el
    # indice con ellas, el catalogo crece dia a dia en vez de depender de que
    # hoy toque abrir la ficha de esa arma.
    for modo_previo in (previo.get("modes") or {}).values():
        for w in modo_previo.get("weapons") or []:
            if w.get("image") and w.get("slug"):
                imagenes.setdefault(unquote(w["slug"]), w["image"])
    puestas = rellenar_imagenes(modes, imagenes)
    if puestas:
        print(f"-> {puestas} armas reciben imagen del catalogo ({len(imagenes)} conocidas)")

    ahora = datetime.now(timezone.utc)
    marcadas = marcar_antiguedad(modes, previo, ahora.isoformat()[:10])
    if marcadas:
        print(f"-> {marcadas} armas con fecha de entrada en su tier")
    cambios = diff_modes(previo, modes)
    anterior_ts = previo.get("generated_at", "")
    # El workflow tambien se dispara al empujar codigo. Si hoy hay dos pasadas,
    # la segunda no debe borrar los movimientos que detecto la primera: dentro
    # del mismo dia UTC los cambios se acumulan en vez de reemplazarse.
    if anterior_ts[:10] == ahora.isoformat()[:10]:
        cambios = fusionar_cambios(previo.get("changes") or [], cambios)
        anterior_ts = previo.get("previous_generated_at", "")

    payload = {
        "generated_at": ahora.isoformat(timespec="seconds"),
        "season": detect_season(session, previo.get("season", "")),
        "source": "wzstats.gg",
        "previous_generated_at": anterior_ts,
        "warnings": avisos,
        "changes": cambios,
        "modes": modes,
        "builds": builds,
    }

    if args.simular:
        print(f"[simulacion] no se escribe nada. {len(modes)} modos, {len(builds)} armas con build, "
              f"{len(cambios)} cambios, {len(avisos)} avisos")
        return 0

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"escrito {args.salida} ({args.salida.stat().st_size // 1024} KB)")
    for a in avisos:
        print(f"AVISO: {a}", file=sys.stderr)
    return 0


def recuperar_modo(previo: dict, mode: dict) -> dict:
    """Copia el bloque de un modo del JSON anterior y lo marca como no fresco.

    Sin esto, un modo que falla desaparece de la web sin avisar y quien lo
    tuviera seleccionado se encontraba la pagina en blanco.
    """
    anterior = (previo.get("modes") or {}).get(mode["id"])
    if not anterior or not anterior.get("weapons"):
        return {}
    copia = dict(anterior)
    copia["stale"] = True
    copia["stale_since"] = anterior.get("stale_since") or previo.get("generated_at", "")
    return copia


if __name__ == "__main__":
    raise SystemExit(main())
