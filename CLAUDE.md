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
README.md                          documentación pública del repo
resumen.md                         bitácora: estado, decisiones y próximos pasos
documentacion/                     informes y documentación técnica (auditorías 08-20 y 08-21)
_CUARENTENA/                       basura apartada para que el usuario la borre; en .gitignore
scripts/scrape.py                  el scraper (única lógica de servidor). Tiene CLI, ver --help
scripts/validar_meta.py            invariantes del JSON generado; corre en el workflow
scripts/pruebas.py                 pruebas del parser y del validador. Sin red, un segundo
scripts/requirements.txt           requests + beautifulsoup4
scripts/comprobar.ps1              comprobacion declarada. Solo lee. 0 si va bien
scripts/servidor-pruebas.ps1       sirve docs\ en local para ver un cambio sin publicarlo
docs/index.html                    la app entera: HTML + CSS + JS, sin build ni dependencias
docs/sw.js                         service worker (funciona sin cobertura). Subir VERSION al tocar la web
docs/data/meta.json          680K  datos generados. NO EDITAR A MANO, NO LEER ENTERO
docs/manifest.webmanifest          para "añadir a pantalla de inicio" en el móvil
docs/icons/                        iconos generados con PIL (ver historial de git)
.github/workflows/update-meta.yml  cron 06:10 UTC + push (solo despliega) + manual
```

**`docs/` es la raíz web que publica GitHub Pages, no la documentación.** El
estándar de proyectos del usuario reserva `docs/` para guías e informes, pero
aquí está ocupado: la documentación vive en `documentacion/`. No renombrar `docs/`
sin cambiar a la vez `path: docs` en el workflow.

## Formato de `docs/data/meta.json`

```jsonc
{
  "generated_at": "2026-08-20T14:42:59+00:00",
  "season": "Season 5 Reloaded, 2026",          // sacado de wzranked.com
  "base_game": "Black Ops 7",                   // ver "Juego base y el aviso de MW4" abajo
  "source": "wzstats.gg",
  "previous_generated_at": "...",
  "warnings": [ "Resurgence: no se pudo leer, se conserva el dato del 2026-08-19" ],
  "changes": [ {"mode","weapon","kind","from","to"} ],  // kind: sube|baja|entra|sale
  "modes": {
    "resurgence": {                              // + multiplayer, resurgence_ranked,
      "label": "Resurgence",                     //   multiplayer_ranked, battle_royale
      "url": "...",
      "context": "Warzone Resurgence",           // clave para casar con builds[].context
      "stale": true, "stale_since": "...",       // solo si ese modo no se pudo releer
      "weapons": [{
        "name": "CBRS-3", "slug": "cbrs-3", "tier": "S",
        "positions": [{"range":"Close Range","rank":1,"role":"corto"}],
        "weapon_type": "SMG", "tags": [], "image": "https://img.wzstats.gg/...",
        "desde": "2026-07-30"                    // en este tier desde ese dia
      }]
    }
  },
  "perks": {                                     // una tier list por modo, NO una global
    "resurgence": {
      "label": "Resurgence", "url": "...",
      "stale": true, "stale_since": "...",       // solo si hoy no se pudo leer
      "items": [{"name":"Sprinter","slot":"Perk 2","tier":"META","kind":"perk"}]
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

`unlock` es `"Level 37"`, `"Armory"`, `"Prestige"`, `"Apex"` (accesorio de
Modern Warfare 4, aún no aparece en Warzone), `"Week N Challenge"`, el nombre
de otra arma que hay que subir, o `""` (wzstats no publica el requisito). El
frontend lo clasifica en `parseUnlock()`, lo traduce en `reqLabel()` y da el
texto de "¿cómo se desbloquea?" en `unlockHelp()` / `UNLOCK_HELP` (se despliega
al pulsar el chip `.req`). El nivel que el usuario pone para cada arma vive en
`profile.levels[slug]` y marca los accesorios de `Level N` ya alcanzados
(`done`) y cuántos quedan (`nivelResumen()`).

**El campo del nivel (`levelFieldHtml`) va en las tarjetas de «Tu equipamiento
de hoy» y en la ficha desplegada del ranking, no solo en la ficha.** El
2026-09-08 estuvo un rato solo en la ficha y el usuario no lo encontró: hay que
pedirlo donde se están leyendo los «Nv. 37» de los accesorios. En «A por la
siguiente» no se pone, que son armas que aún no tiene.

**No toda arma tiene build de todos los modos.** El VS RECON, por ejemplo, no
tiene una de `Black Ops 7 Ranked`. `buildsForMode()` cae entonces a las que haya
y `buildTitle()` lo avisa en la etiqueta («build de Warzone Battle Royale»), para
que no parezca que esos accesorios son los del modo activo.

## Cómo ejecutarlo y probarlo

```bash
pip install -r scripts/requirements.txt

python scripts/pruebas.py         # pruebas del parser y del validador. Sin red, 1 s
python scripts/scrape.py          # ~4 min, ~70 peticiones. Regenera meta.json
python scripts/validar_meta.py    # invariantes del JSON

cd docs && python -m http.server 8765   # http://127.0.0.1:8765
```

**Para tocar el parser, no lances los cinco modos.** El scraper tiene CLI:

```bash
python scripts/scrape.py --modo resurgence --sin-builds --simular   # segundos, 2 peticiones
python scripts/scrape.py --limite-builds 3 --salida prueba.json
python scripts/scrape.py --help
```

Una ejecucion parcial (`--modo`, `--sin-builds`, `--limite-builds`) **se niega a
sobrescribir** `docs/data/meta.json` y sale con codigo 2: usa `--simular` o
`--salida`. Es a proposito, para que el bot no commitee datos a medias.

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
- **La lista de tier solo trae imagen del tier S.** Las demás las carga el
  navegador después, así que no están en el HTML: 12 URL para 248 armas. Las que
  faltan salen de las fichas de arma, que ya se descargan para los accesorios
  (`cosechar_imagenes` + `rellenar_imagenes`, ver la auditoría del 2026-08-21).
  **El sufijo `_versionN` de la URL no es deducible del slug**, así que no se
  construyen URL: solo se guardan las que wzstats haya escrito.

## Qué pasa cuando falla algo (añadido en la auditoría del 2026-08-20)

Antes, un modo que fallaba desaparecía del JSON en silencio, el workflow quedaba
en verde y quien tuviera ese modo guardado se encontraba la web **en blanco**.
Ahora:

1. `recuperar_modo()` copia el bloque de ese modo del `meta.json` anterior y lo
   marca `stale` + `stale_since`.
2. El aviso se guarda en `payload["warnings"]` y la web lo enseña en cabecera
   («se muestra el dato guardado del…»).
3. `diff_modes()` **ignora** los modos `stale`: compararlos consigo mismos no
   dice nada y taparía el diff bueno.
4. El job `avisar` del workflow corre **después** de `deploy` y falla si hay
   warnings: la web se publica igual, pero GitHub manda el correo. Lleva
   **`if: always()`**, y eso no es decorativo — ver abajo.
5. `modoValido()` en el frontend recoloca al modo por defecto si el guardado ya
   no existe, en vez de reventar.
6. Las armas cuya **ficha** falle hoy conservan los accesorios de la
   actualizacion anterior (solo las que siguen en la lista del dia, para que el
   JSON no crezca sin control). Si falla un tercio o mas, se anota un warning.
7. Si **wzranked.com** no contesta, se conserva la temporada del JSON anterior
   en vez de degradarla al literal `"Temporada actual"`.
8. Las **imagenes** conocidas se arrastran del JSON anterior, asi que el
   catalogo crece dia a dia aunque hoy no toque abrir la ficha de esa arma.

Si dos ejecuciones caen el **mismo día UTC**, los `changes` se acumulan en vez de
reemplazarse (`fusionar_cambios`). Sin eso, tocar `index.html` dejaba el panel
«Movimientos del meta» vacío hasta el día siguiente.

### Cuando lo que falla es el *publicado*, no el raspado (2026-09-10)

Todo lo de arriba protege del raspado que falla. El **2026-09-10** falló la otra
mitad y no estaba cubierta: `build` raspó y commiteó bien, pero `deploy-pages@v4`
tardó más que el `timeout-minutes: 10` del job `deploy` y GitHub lo mató. Los datos
de ese día quedaron **en `main` pero sin publicar**, y la web siguió sirviendo los
de la víspera.

**Lo grave fue el silencio, y son dos cosas encadenadas:**

- Un job que agota su `timeout-minutes` deja el run en **`cancelled`**, no en
  `failure`. **GitHub solo manda correo de los `failure`.**
- Y `avisar` —el que debía chillar— **se saltaba**, porque un job con
  `needs: [build, deploy]` no corre si alguno de los dos no acaba en success.
  Es decir: se saltaba justo el día en que había algo que contar.

Arreglado poniéndole a `avisar` **`if: always()`** y un primer paso que falla si
`needs.deploy.result != 'success'`. Ahora un despliegue cortado deja el run en rojo
y sale el correo. **No quitar ese `if: always()`**: sin él, este job solo avisa
cuando todo ha ido bien, que es cuando no hace falta.

Efecto secundario aceptado: si se cancela un run **a mano**, también llega correo.
Se prefiere eso al silencio.

Cuando pase, se arregla **relanzando el workflow a mano** (*Actions → Run
workflow*): al ser `workflow_dispatch` no vuelve a raspar, solo valida y publica lo
que ya hay en `main`.

**Ojo con la antigüedad como red de seguridad:** `comprobar.ps1` tolera 3 días, así
que un fallo de publicado no se ve hasta el tercero. Es a propósito, pero significa
que **el correo es la única alerta rápida**.

## Ventajas (perks), añadidas en la fase B el 2026-09-08

`parse_perks()` raspa las tier lists de ventajas. **Hay una por modo y no son la
misma lista**: comprobado el 2026-09-08, Battle Royale y Resurgence llevan las
mismas 15 ventajas pero intercambian cuatro entre META y A, y las dos Ranked van
por su cuenta. Por eso cada entrada de `MODES` tiene su `perks_url` y el JSON
guarda `perks[<id de modo>]`, en vez de una lista «de Warzone» y otra «de BO7».

Trampas de estas páginas, que no son las de armas:

- **Los tiers empiezan en META**, no en S: `META`, `A`, `B`, `C`, `D`
  (`PERK_TIERS`). Un `S` ahí es un error y el validador lo caza.
- **La clase de tier va junto a `tier-header` y el orden cambia** de un bloque a
  otro: `tier-header tier-meta` pero `tier-a tier-header`. Hay que buscar cuál de
  las clases es de tier, no mirar una posición fija.
- **`.tier-content` es hermano del bloque de la cabecera**, no descendiente: se
  sube buscándolo, igual que con el código de canje en `parse_builds`.
- El nombre está en `.content-name` y la ranura en `.content-tag` (`Perk 1/2/3`,
  y `Speciality` solo en Black Ops 7).
- **Las pestañas de esas páginas NO vienen en el mismo HTML**: cada una es una
  URL propia. Hoy solo se raspan las de ventajas. Si algún día hacen falta:
  `/warzone-2/loadouts/best-lethals-tier-list`, `.../best-tacticals-tier-list`, y
  en BO7 además `/bo7/loadouts/best-wildcards-tier-list` y
  `.../best-field-upgrades-tier-list`. Por eso `kind` existe en el JSON aunque
  hoy valga siempre `"perk"`.
- **No usar los bloques «Best X Perks» de las fichas de arma**: son de Black Ops
  Royale y del multijugador, no de Battle Royale ni Resurgence.

Si una página falla, `recuperar_perks()` conserva la del día anterior con
`stale`/`stale_since` y se anota un warning, igual que con los modos. **Que
falten ventajas es una nota del validador, no un error**: un fallo ahí no puede
impedir publicar las armas, que son lo principal de la web.

Son 5 peticiones más al día (una por modo), sobre las ~70 que ya se hacían.

## Juego base y el aviso del cambio a Modern Warfare 4 (añadido en la fase A, 2026-09-08)

`BASE_GAME` en `scrape.py` (hoy `"Black Ops 7"`) se escribe en el JSON como
`base_game` y la web lo enseña junto a la temporada («Warzone · Black Ops 7 ·
Season 5 Reloaded, 2026»), para que un «Season 1» de Modern Warfare 4 en
noviembre no se lea igual que el «Season 1» de Black Ops 7 de hace un año.
`validar_meta.py` exige que no esté vacío.

`detectar_mw4()` mira, tras cada raspado, si algún arma de los modos de
Warzone (`WARZONE_MODE_IDS`: `resurgence`, `resurgence_ranked`,
`battle_royale` — no los de Black Ops 7) trae ya el sufijo `-mw4` en su slug.
Si lo ve y `BASE_GAME` todavía no es `"Modern Warfare 4"`, añade un aviso a
`payload["warnings"]`: sale en la cabecera de la web (`renderAvisos()` en
`index.html` ahora sí lee `DATA.warnings`, además de las dos comprobaciones de
frescura que ya hacía), hace fallar el job `avisar` del workflow (manda
correo) y el repaso de las 09:00. **Es el recordatorio de la fase C** del plan
`documentacion/plan-2026-09-08-fases.md`; se apaga haciendo esa fase (cambiar
`BASE_GAME` a `"Modern Warfare 4"`).

## Lógica de recomendación (`score()` en index.html)

`tier` (S=100…D=18) + bonus por puesto oficial `max(0, 28 - rank*3)` + ajustes de
estilo (agresivo premia corto y castiga sniper; táctico premia largo y sniper) +
6 puntos por dispositivo (mando→corto, teclado→largo/sniper) **− 45 si es
secundaria** (`Pistol`, `Melee`, `Launcher`, `Special`).

Esa penalización es necesaria: wzstats rankea las pistolas en su propia
categoría, así que un `#1 Pistol` sumaba tanto como un `#1 Assault Rifle` y las
pistolas salían por delante del FG42.

## Antigüedad en el tier y comparador (auditoría del 2026-08-21)

Cada arma lleva `desde`: el día en que llegó al tier que tiene ahora. Lo calcula
`marcar_antiguedad()` arrastrando el dato del `meta.json` anterior, sin archivo
nuevo ni descarga extra. **La regla es no inventar fechas**: si no hay historia
el campo no se escribe y `rachaTexto()` no enseña nada; si el arma ya estaba ayer
en ese tier pero sin fecha, se anota la del JSON anterior, que es lo único
demostrable. `validar_meta.py` rechaza fechas mal formadas o futuras.

El comparador (`renderComparador`) es solo interfaz sobre datos que ya estaban.
Lo que aporta es `veredicto()`: explica **por qué** gana una, y en particular
cuando el motivo está en el perfil y no en el arma («la otra es de francotirador
y tú juegas agresivo»), que es el caso en que la ganadora rankea peor y el
resultado parecería arbitrario. Su estado no se guarda en el perfil a propósito:
es una consulta de un rato, no una preferencia.

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
  Un push que toque `.github/workflows/` **sí** dispara el workflow (y republica).

## La comprobación declarada: `scripts\comprobar.ps1`

Tres pasos. Los dos primeros lanzan `pruebas.py` y `validar_meta.py` con Python; el
tercero mira **el `meta.json` ya publicado**, que es el único que ve el producto de
verdad. Sale 0 si todo va bien.

**Dos situaciones se declaran «no concluyente» y NO cuentan como fallo**, porque una
alarma que salta cuando no pasa nada enseña a no mirar la alarma:

- **Sin red**, el paso 3 no se puede hacer.
- **Sin Python**, los pasos 1 y 2 no se pueden hacer. Desde el 2026-09-10 las dos
  máquinas lo tienen, así que hoy no debería saltar; se queda porque la detección
  es lo que evita el mensaje críptico de la Microsoft Store, y porque una máquina
  nueva empieza sin Python.

**El paso 3 está en PowerShell y no en Python a propósito** (desde el 2026-09-10):
así se comprueba igual en la máquina que no tiene Python, que además es desde donde
se usa la web. De paso se fue la sonda de Python embebida en un heredoc y su fichero
temporal.

> **Trampa de fechas, que costó una prueba descubrir y se reintroduce sola.**
> `ConvertFrom-Json` **no** deja `generated_at` como texto: reconoce el ISO-8601 y lo
> convierte a `[datetime]`. Si después se llama a `[datetimeoffset]::Parse($marca)`,
> ese `DateTime` se vuelve a texto con la cultura de la máquina (**es-ES**,
> `dd/MM/yyyy`) y se re-parsea con la invariante (`MM/dd/yyyy`): **`02/09` se lee como
> 9 de febrero**. Un JSON de hace 8 días daba «213 días». No se veía a simple vista
> porque ese día la fecha era `09/09`, simétrica. Y el caso peligroso es el contrario:
> una marca vieja leída como reciente, con el cron parado y nadie avisando. Se
> resuelve usando `[datetimeoffset]::new($marca)` cuando ya es `[datetime]`, y
> `Parse` con `InvariantCulture` + `RoundtripKind` solo cuando es texto.
>
> **Al tocar ese cálculo, probarlo con una fecha cuyo día sea ≤ 12**, o el error pasa
> desapercibido.

## Entorno del usuario

- Windows 11, proyecto en `F:\COMPARTIDO\Claude\Warezone`.
- Hizo falta `git config --global --add safe.directory F:/COMPARTIDO/Claude/Warezone`
  porque la unidad F: pertenece a otro usuario de red.
- **Node NO está instalado. `gh` NO está instalado.** Ninguno hace falta.
- Python 3.13 y git 2.55 sí.

**Son dos Windows, y este proyecto se gestiona entero desde cualquiera de los
dos** (decidido por el usuario el 2026-09-10). `Worker` tiene Python 3.13;
`DESPACHO_GAMER` —desde donde se juega y se mira el panel— tiene **Python 3.12
desde el 2026-09-10**, la misma versión que usa el CI, instalada con
`winget install --id Python.Python.3.12 --scope user`.

Que se pueda es porque **este proyecto es estanco**: no depende de ningún otro,
nadie depende de él y su cron vive en los servidores de GitHub, no en un PC.
Python no se comparte por el disco `F:` —es una instalación local de cada
Windows—, así que tenerlo en los dos no le quita nada a ninguno. **Lo que sigue
siendo solo de Worker son las tareas programadas de la casa** (el repaso de las
09:00 y el respaldo de las 03:00), que sirven a todos los proyectos; en Gamer no
hay ninguna.

> **La trampa del `python.exe` de 0 bytes, que reaparece cada vez.** Aunque no
> haya Python, el PATH trae igualmente
> `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`: un fichero de **cero bytes**
> que solo abre la Microsoft Store. `Get-Command python` lo encuentra y dice que
> sí. Para saber si hay Python de verdad hay que **mirar el tamaño o ejecutarlo**
> (lo hacen `comprobar.ps1` y `servidor-pruebas.ps1`).
>
> Y tras instalarlo, **el PATH no se recarga en las ventanas ya abiertas**: hay
> que abrir una nueva, o el señuelo sigue ganando. Costó un rato el 2026-09-10.

**Dos accesos directos, con dos oficios distintos**, en
`F:\COMPARTIDO\Claude\...Accesos directos\` (fuera de este proyecto; se tocan
solo con permiso del usuario):

| Acceso directo | Qué hace |
|---|---|
| **Panel de Warezone** | abre la web publicada. Es el uso diario y no necesita nada instalado |
| **Warezone - servidor de pruebas** | lanza `scripts\servidor-pruebas.ps1`: sirve tu `docs\` local para ver un cambio **antes** de publicarlo |

La lógica del segundo vive en `scripts\servidor-pruebas.ps1` y no dentro del
`.lnk` a propósito: así está versionada y se puede arreglar. Si no encuentra
Python, lo dice a la cara en vez de morir con el mensaje críptico de la Store.

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

**Desde la auditoría del 2026-08-20 hay service worker** (`docs/sw.js`): la app
instalada sigue funcionando sin cobertura con la última meta descargada.
Verificado apagando el servidor local y recargando: armas, accesorios y códigos
seguían saliendo. **Al tocar cualquier archivo de `docs/` hay que subir `VERSION`
en `sw.js`**, o un usuario puede quedarse con la interfaz vieja cacheada. Y a la
vez `UI_VERSION` en `index.html`, que es lo que el usuario lee en el pie para
saber desde el Gamer si ya tiene lo nuevo: **si hay dos publicaciones el mismo
día se le añade letra** (`2026-09-08b`), o las dos se leerían igual.

Al probar en local, acuérdate de desregistrar el service worker
(`navigator.serviceWorker.getRegistrations()` → `unregister()`) o seguirás viendo
la versión cacheada de `127.0.0.1`.

## Datos personales

El gamertag ya **no** está escrito en el código: `DEFAULTS.tag` es `"Jugador"` y
cada usuario pone el suyo con «cambiar gamertag», que se guarda solo en el
`localStorage` de su dispositivo. El repo y la web son públicos; no metas ahí
nada personal. El gamertag anterior sigue en el historial de git (commits previos
a `ef55288`) y se decidió no reescribir la historia por ello.

## Pendiente

- **Plan por fases aprobado el 2026-09-08:** `documentacion/plan-2026-09-08-fases.md`.
  **Fase A (sonnet · high): hecha el 2026-09-08** — textos de desbloqueo,
  etiquetas, nivel del arma, versión visible, juego base y detector del cambio
  a MW4. Pendiente que el usuario la confirme **desde el Windows Gamer**
  (versión de interfaz en el pie y la función nueva) antes de darla por
  cerrada. **Fase B (opus · high): hecha el 2026-09-08** — ventajas raspadas de
  wzstats, una tier list por modo, y la sección «Ventajas meta por ranura».
  Pendiente la misma confirmación desde Gamer.
  **Fase C** (fable · high), noviembre de 2026: Modern Warfare 4 sale el
  23-10-2026 y en su temporada 1 Warzone cambia de juego base; la avisa sola
  el detector de la fase A (`detectar_mw4()`). Cada fase empieza diciendo
  modelo y potencia. El informe que lo justifica:
  `documentacion/informe-2026-09-08-nivel-desbloqueos-ventajas-zodiac.md`.
- El usuario pegó su contraseña de GitHub en texto plano en el chat el
  2026-08-20 y se le recomendó cambiarla. Sin confirmar que lo hiciera.
  **No está en ningún archivo del repositorio** (verificado con `git grep` en la
  auditoría del 2026-08-20).
- `multiplayer_ranked` solo trae **5 armas**. Verificado el 2026-08-20 contra la
  web en vivo: es lo que publica wzstats en esa página, no es un fallo del
  parser. `validar_meta.py` tiene el mínimo en 3 por eso.
