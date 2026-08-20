# CLAUDE.md — Armería Warzone

> **Este fichero basta como contexto.** No hace falta releer el proyecto entero.
> Lee `scripts/scrape.py` solo si vas a tocar el scraping, y `docs/index.html`
> solo si vas a tocar la interfaz. `docs/data/meta.json` **nunca se lee entero**
> (33 000 líneas): su formato está descrito más abajo.

## Qué es

Web estática que raspa la tier list de [wzstats.gg](https://wzstats.gg/) una vez
al día y recomienda con qué armas jugar en Warzone según el modo y el estilo que
marque el usuario, con **los accesorios exactos** que hay que montar, el
requisito de desbloqueo de cada uno y el código de canje para pegar en el juego.

No hay servidor ni base de datos: un cron de GitHub Actions raspa, commitea el
JSON y republica la página. Funciona con el PC del usuario apagado.

- **Web:** https://zeusente.github.io/warzone-armeria/
- **Repo:** https://github.com/ZeusEnte/warzone-armeria (público, cuenta `ZeusEnte`)
- Pages → Source = *GitHub Actions* ✅ · Actions → *Read and write* ✅ (ya configurado)

## Ficheros

```
CLAUDE.md                          este fichero (contexto para retomar)
README.md                     73L  documentación pública del repo
resumen.md                         stub que apunta aquí (lo pide la config global del usuario)
_CUARENTENA/                       basura apartada para que el usuario la borre; en .gitignore
scripts/scrape.py            415L  el scraper (única lógica de servidor)
scripts/requirements.txt           requests + beautifulsoup4
docs/index.html                    la app entera: HTML + CSS + JS, sin build ni dependencias
docs/data/meta.json          680K  datos generados. NO EDITAR A MANO, NO LEER ENTERO
docs/manifest.webmanifest          para "añadir a pantalla de inicio" en el móvil
docs/icons/                        iconos generados con PIL (ver historial de git)
.github/workflows/update-meta.yml  cron 06:10 UTC + push + manual
```

## Formato de `docs/data/meta.json`

```jsonc
{
  "generated_at": "2026-08-20T14:42:59+00:00",
  "season": "Season 5 Reloaded, 2026",          // sacado de wzranked.com
  "source": "wzstats.gg",
  "previous_generated_at": "...",
  "changes": [ {"mode","weapon","kind","from","to"} ],  // kind: sube|baja|entra|sale
  "modes": {
    "resurgence": {                              // + multiplayer, resurgence_ranked,
      "label": "Resurgence",                     //   multiplayer_ranked, battle_royale
      "url": "...",
      "context": "Warzone Resurgence",           // clave para casar con builds[].context
      "weapons": [{
        "name": "CBRS-3", "slug": "cbrs-3", "tier": "S",
        "positions": [{"range":"Close Range","rank":1,"role":"corto"}],
        "weapon_type": "SMG", "tags": [], "image": "https://img.wzstats.gg/..."
      }]
    }
  },
  "builds": {                                    // solo las ~66 armas de tier S y A
    "fg42": {
      "name": "FG42", "max_level": 41,
      "builds": [{
        "context": "Warzone Resurgence",         // = modes[x].context
        "label": "Recommended",                  // o LOW RECOIL, PRESTIGE, CONVERSION KIT...
        "code": "A16-34FIQ-XHAUL-11",            // código de canje, "" en armas de diseño viejo
        "attachments": [{"slot":"Optic","name":"FANG HOVERPOINT ELO","unlock":"Armory"}]
      }]
    }
  }
}
```

`unlock` es `"Level 37"`, `"Armory"`, `"Prestige"`, el nombre de otra arma que
hay que subir, o `""`. El frontend lo traduce en `reqLabel()`.

**No toda arma tiene build de todos los modos.** El VS RECON, por ejemplo, no
tiene una de `Black Ops 7 Ranked`. `buildsForMode()` cae entonces a las que haya
y `buildTitle()` lo avisa en la etiqueta («build de Warzone Battle Royale»), para
que no parezca que esos accesorios son los del modo activo.

## Cómo ejecutarlo y probarlo

```bash
pip install -r scripts/requirements.txt
python scripts/scrape.py          # ~4 min, ~70 peticiones. Regenera meta.json
cd docs && python -m http.server 8765   # http://127.0.0.1:8765
```

Abrir `docs/index.html` con doble clic **no** funciona: el navegador bloquea el
`fetch` del JSON en `file://`.

**Validar el JS sin navegador** (no hay Node instalado):

```bash
pip install esprima
python -c "import re,esprima;esprima.parseScript(re.search(r'<script>(.*?)</script>',open('docs/index.html',encoding='utf-8').read(),re.S).group(1));print('OK')"
```

**Probar una función del scraper aislada**, sin raspar los 5 modos:

```python
import importlib.util, requests
spec = importlib.util.spec_from_file_location("sc", "scripts/scrape.py")
sc = importlib.util.module_from_spec(spec); spec.loader.exec_module(sc)
sc.parse_builds(sc.get("https://wzstats.gg/best-loadouts/fg42", requests.Session()))
```

**Verificar la interfaz:** las capturas de pantalla de la extensión de Chrome
fallaron repetidamente en este proyecto (timeouts de `Page.captureScreenshot`,
con la página en 625 nodos — es cosa de la extensión, no del sitio). Inspeccionar
el DOM con `javascript_tool` resultó mucho más fiable para comprobar estado,
despliegues y `localStorage`.

## Trampas del scraping (esto costó descubrirlo)

- **Dos vocabularios de categoría.** Warzone ordena por alcance (`Long Range`),
  Black Ops 7 por tipo de arma (`Assault Rifle`). `ROLE_BY_CATEGORY` los
  normaliza a `largo` / `corto` / `sniper` en el campo `role`. Sin esto el modo
  Multijugador se queda sin recomendaciones.
- **Dos diseños de ficha de arma.** Las nuevas envuelven cada build en
  `.playstyle-card`; las viejas (KAR98K) no. Lo común a ambas es
  `ul.weapon-visual-no-image-container`: hay que anclar ahí y buscar el nombre
  hacia arriba. Las viejas tampoco traen `unlock` ni `code`.
- **El código de canje** (`.weapon-build-code`) es *hermano* de la lista de
  accesorios, no descendiente: hay que subir hasta 4 niveles buscándolo.
- **`.prestige-slot` lleva también `.attachment-slot-no-image`**, un selector basta.
- **Forzar `r.encoding = "utf-8"`** o los nombres con acento se rompen (`JÄGER 45`).
- **El primer bloque de la tier list no lleva cabecera**: ése es el S tier.
- **Cada ficha repite sus builds para modos que no seguimos** (Iron Gauntlet,
  Zombies, Black Ops Royale). `TRACKED_CONTEXTS` las filtra o el JSON se dispara.
- **La misma arma aparece una vez por cada categoría** en la que entra; se
  fusionan por slug al final de `parse_meta_page`.
- Si no se puede raspar **ningún** modo, `main()` sale con 1 y **no toca**
  `meta.json`: la web sigue sirviendo el último dato bueno y el workflow avisa.

## Lógica de recomendación (`score()` en index.html)

`tier` (S=100…D=18) + bonus por puesto oficial `max(0, 28 - rank*3)` + ajustes de
estilo (agresivo premia corto y castiga sniper; táctico premia largo y sniper) +
6 puntos por dispositivo (mando→corto, teclado→largo/sniper) **− 45 si es
secundaria** (`Pistol`, `Melee`, `Launcher`, `Special`).

Esa penalización es necesaria: wzstats rankea las pistolas en su propia
categoría, así que un `#1 Pistol` sumaba tanto como un `#1 Assault Rifle` y las
pistolas salían por delante del FG42.

## Posesión de armas

wzstats da el requisito de cada **accesorio**, pero **qué armas posee un jugador
no existe en ninguna fuente pública** (depende de pase de batalla, eventos y
paquetes comprados). Se resuelve con un botón «No la tengo» por arma, guardado en
`profile.missing` (localStorage `armeria-perfil`). **No es un descarte
definitivo, es un «todavía no»**: el equipamiento del día solo usa las
disponibles y el panel «A por la siguiente» ordena las que faltan por lo que
aportarían. Fue una petición explícita del usuario, no lo conviertas en filtro.

## Trabajo con git

- **El bot commitea sobre `main`** (`meta: actualizacion AAAA-MM-DD`), así que
  **siempre `git pull --rebase origin main` antes de pushear**.
- Si hay conflicto en `meta.json`, no lo resuelvas a mano: quédate con una
  versión y deja que el workflow lo regenere. En rebase, tu versión local es
  `--theirs`.
- Los push de solo `.md` no disparan el scraping (`paths-ignore` en el workflow).

## Entorno del usuario

- Windows 11, proyecto en `F:\COMPARTIDO\Claude\Warezone`.
- Hizo falta `git config --global --add safe.directory F:/COMPARTIDO/Claude/Warezone`
  porque la unidad F: pertenece a otro usuario de red.
- **Node NO está instalado. `gh` NO está instalado.** Ninguno hace falta.
- Python 3.13 y git 2.55 sí.
- El usuario escribe en español; responderle en español.

## Móvil

Verificado a 390 y 360 px: sin desbordes horizontales, tarjetas apiladas, la
columna «puesto oficial» se oculta y la ficha desplegada cabe. Los botones tenían
21-27 px de alto (intocables con el dedo) y ahora son de 44 px en móvil.

**Cómo auditar la vista móvil** (`resize_window` de la extensión no afecta al
viewport): crea una página temporal en `docs/` que cargue `index.html` en un
`<iframe width="360">` — las media queries responden al ancho del iframe — y
inspecciona `iframe.contentDocument` con `javascript_tool`. Hay una copia en
`_CUARENTENA/test-movil-andamio.html`. **No dejar ese fichero en `docs/`**, se
publicaría.

Se instala como app desde el navegador del móvil: *Añadir a pantalla de inicio*.
No hay nada que desplegar en los dispositivos, es una web.

## Pendiente

- El usuario pegó su contraseña de GitHub en texto plano en el chat el
  2026-08-20 y se le recomendó cambiarla. Sin confirmar que lo hiciera.
