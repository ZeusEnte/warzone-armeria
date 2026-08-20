"""Raspa la tier list de wzstats.gg y genera docs/data/meta.json.

Se ejecuta a diario desde GitHub Actions. Una sola peticion por pagina de meta
y otra por arma del top (con pausa entre ellas) para no castigar la web origen.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import time
from datetime import datetime, timezone

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

# Cuantas fichas de arma abrimos para sacar los accesorios completos.
BUILD_BUDGET = 26
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


def tier_rank(tier: str) -> int:
    """Menor es mejor. Los tiers desconocidos van al final."""
    return TIER_ORDER.index(tier) if tier in TIER_ORDER else len(TIER_ORDER)


def get(url: str, session: requests.Session, tries: int = 3) -> str:
    last = None
    for attempt in range(tries):
        try:
            r = session.get(url, headers=HEADERS, timeout=45)
            r.raise_for_status()
            # La cabecera no siempre trae charset y los nombres llevan acentos
            # (JAGER 45, etc.), asi que forzamos utf-8.
            r.encoding = "utf-8"
            return r.text
        except Exception as exc:  # red inestable en el runner
            last = exc
            time.sleep(2 + attempt * 3)
    raise RuntimeError("no se pudo descargar " + url + ": " + str(last))


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
    return list(merged.values())


CONTEXT_RE = re.compile(r"Loadout for (.+?) in Season", re.I)


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
        for slot in el.select(".attachment-slot-no-image"):
            att_name = txt(slot.select_one(".attachment-name-no-image"))
            slot_name = txt(slot.select_one(".slot-name-no-image"))
            if att_name:
                attachments.append({"slot": slot_name, "name": att_name})
        if not attachments:
            continue

        key = (context, label, tuple(a["name"] for a in attachments))
        if key in seen:
            continue
        seen.add(key)
        builds.append({"context": context, "label": label, "attachments": attachments})

    return builds


def detect_season(session: requests.Session) -> str:
    try:
        html = get("https://wzranked.com/games/call-of-duty-warzone/meta", session)
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        m = re.search(r"Season\s+\d+(?:\s+Reloaded)?,?\s*20\d\d", text)
        if m:
            return m.group(0)
    except Exception as exc:
        print("  aviso: no se pudo leer la temporada (" + str(exc) + ")", file=sys.stderr)
    return "Temporada actual"


def pick_for_builds(modes: dict) -> list:
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
    return [(slug, value[1]) for slug, value in ordered[:BUILD_BUDGET]]


def diff_modes(old: dict, new: dict) -> list:
    """Compara la meta anterior con la nueva para poder avisar de los cambios."""
    changes = []
    for mode_id, mode in new.items():
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


def main() -> int:
    session = requests.Session()
    modes = {}

    for mode in MODES:
        print("-> " + mode["label"] + ": " + mode["url"])
        try:
            weapons = parse_meta_page(get(mode["url"], session))
        except Exception as exc:
            print("   FALLO: " + str(exc), file=sys.stderr)
            continue
        if not weapons:
            print("   sin armas (la estructura de la web pudo cambiar)", file=sys.stderr)
            continue
        print("   " + str(len(weapons)) + " armas")
        modes[mode["id"]] = {
            "label": mode["label"],
            "url": mode["url"],
            "context": mode["context"],
            "weapons": weapons,
        }
        time.sleep(REQUEST_PAUSE)

    if not modes:
        print("ERROR: ningun modo se pudo raspar, no se sobrescribe meta.json", file=sys.stderr)
        return 1

    builds = {}
    targets = pick_for_builds(modes)
    print("-> accesorios de " + str(len(targets)) + " armas")
    for slug, name in targets:
        try:
            found = parse_builds(get(BASE + "/best-loadouts/" + slug, session))
        except Exception as exc:
            print("   " + slug + ": " + str(exc), file=sys.stderr)
            continue
        if found:
            builds[slug] = {"name": name, "builds": found}
            print("   " + name + ": " + str(len(found)) + " builds")
        time.sleep(REQUEST_PAUSE)

    previous = {}
    if OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            previous = {}

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "season": detect_season(session),
        "source": "wzstats.gg",
        "previous_generated_at": previous.get("generated_at", ""),
        "changes": diff_modes(previous, modes),
        "modes": modes,
        "builds": builds,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print("escrito " + str(OUT) + " (" + str(OUT.stat().st_size // 1024) + " KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
