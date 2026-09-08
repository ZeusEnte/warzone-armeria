# Plan por fases (escrito el 2026-09-08, para ejecutar desde la siguiente ventana)

Sale del informe [`informe-2026-09-08-nivel-desbloqueos-ventajas-zodiac.md`](informe-2026-09-08-nivel-desbloqueos-ventajas-zodiac.md).
El usuario aprobó el planteamiento el 2026-09-08 y pidió que la siguiente ventana lo ejecute
**por fases**, decidiendo **modelo y potencia** antes de cada una.

## Protocolo de cada fase (no se salta)

1. **Primera línea de la ventana, antes de tocar nada:** `Modelo: … · Potencia: …`, comparado
   con lo que recomienda la fase. Si coincide, se sigue. Si no, **se para ahí** y se dan las
   líneas exactas que el usuario debe escribir (`/model X`, `/effort Y`) y después `sigue`.
   Si el usuario contesta «sigue con este», se hace con el que hay y no se vuelve a sacar.
2. Se ejecuta la fase **entera**, con sus pruebas: `python scripts/pruebas.py`,
   `python scripts/validar_meta.py`, el chequeo de sintaxis del JS con esprima (está en
   `CLAUDE.md`) y `scripts\comprobar.ps1`.
3. Si se toca cualquier archivo de `docs/`, se sube `VERSION` en `docs/sw.js`.
4. Commit con mensaje descriptivo, `git pull --rebase origin main`, `git push`. Un push que
   toque `docs/` republica la web (no vuelve a raspar).
5. **Verificación desde Gamer.** El usuario usa el panel desde el Windows Gamer (arranca en
   `E:`), no desde este. La ventana no puede arrancarlo: cuando la fase esté publicada, **pita**
   (`F:\COMPARTIDO\Claude\Aviso\avisar.ps1`) y pide al usuario que abra el panel desde Gamer en
   la URL publicada y confirme dos cosas: la versión de interfaz que se ve en el pie (la añade la
   fase A) y la función nueva. **La fase no se da por cerrada sin ese OK.** Comprobado el
   2026-09-08: el service worker carga «red primero» y hace `skipWaiting`, así que con conexión
   Gamer ve lo publicado en el momento de abrir; lo publicado era byte a byte lo del repositorio.
6. `resumen.md` y la ficha `_CONTRATOS\Warezone.md` al día con fechas absolutas; commit hasta
   que `git status --short` salga vacío en los dos repositorios.

## Fase A — interfaz y avisos, sin datos nuevos

**Modelo: sonnet · Potencia: high.** Todo está decidido y localizado aquí; es aplicar. Si al
hacerla aparece lógica que este plan no cubre, se para y se propone subir de modelo.

Archivos: `docs/index.html`, `docs/sw.js`, `scripts/scrape.py`, `scripts/validar_meta.py`,
`scripts/pruebas.py`, `CLAUDE.md`, `resumen.md`.

- **A1. Etiquetas mal traducidas.** `reqLabel()` en `index.html` toma como «nombre de otra arma»
  todo lo que no reconoce. Hoy hay 5 entradas `Week N Challenge` que salen como «subir Week 2
  Challenge». Añadir: `Week N Challenge` → «Desafío semana N»; `Apex` → «Apex» (es la etiqueta
  que wzstats ya usa en las fichas de Modern Warfare 4 para el accesorio que se gana al subir el
  arma al máximo; hoy no aparece en Warzone, en noviembre sí).
- **A2. «¿Cómo se desbloquea?»** Un diccionario `UNLOCK_HELP` con un texto por tipo de requisito
  (nivel, Armería, Prestigio, desafío semanal, otra arma, Apex, vacío), redactado para alguien
  que empieza. Los textos están en el informe, punto 2; copiarlos, no reinventarlos. Se enseñan
  al pulsar la etiqueta del accesorio (`.req`), desplegando un `div` bajo el accesorio. En móvil
  el área pulsable tiene que ser de 44 px como el resto de botones.
- **A3. Nivel de esta arma.** En `detailHtml()`, un campo numérico «Nivel de esta arma»
  (0…`max_level`, y sin tope si `max_level` es 0). Se guarda en `profile.levels[slug]`
  (`DEFAULTS` gana `levels:{}` y `load()` lo sanea como hace con `missing`). Con el nivel
  puesto: cada accesorio `Level N` con N mayor que el nivel se marca como pendiente y la
  cabecera de la build dice «te faltan 3 accesorios (17 niveles hasta el último)»; el texto de
  A2 para «nivel» añade «estás en 20: te faltan 17». Sin nivel puesto, nada cambia. `missing`
  sigue significando lo mismo que hoy; no se mezcla.
- **A4. Versión de interfaz visible.** Una constante `UI_VERSION` en `index.html` con la fecha
  del cambio (`"2026-09-xx"`) enseñada en el pie junto al sello de datos (`renderStamp()`). Es
  lo que el usuario mira desde Gamer para saber si tiene la interfaz nueva. Subir `VERSION` en
  `sw.js` a la vez.
- **A5. Juego base en la cabecera y detector del cambio a MW4.** En `scrape.py`, una constante
  `BASE_GAME = "Black Ops 7"` que se escribe en el JSON como `"base_game"`. `renderStamp()`
  enseña «Warzone · Black Ops 7 · Season 5 Reloaded» en vez de la temporada a secas. Y en
  `scrape.py`, tras raspar los modos de Warzone: si algún slug de un modo Warzone termina en
  `-mw4` mientras `BASE_GAME` no es Modern Warfare 4, se añade a `payload["warnings"]` el aviso
  «wzstats ya sirve armas de Modern Warfare 4 en Warzone: toca la fase C del plan del
  2026-09-08». Ese aviso sale en la cabecera de la web, hace que el job `avisar` mande correo, y
  hace fallar `comprobar.ps1` (paso 3, warnings vacíos) en el repaso de las 09:00. **Es el
  recordatorio de noviembre, y se apaga haciendo la fase C** (cambiar `BASE_GAME`). Prueba en
  `pruebas.py` con dos listas de slugs, una con `-mw4` y otra sin. `validar_meta.py` exige que
  `base_game` exista y no esté vacío.
- **A6. Documentación.** `CLAUDE.md`: el campo `base_game` en el formato del JSON, la nota de
  `reqLabel()`, y quitar de «Pendiente» lo que quede hecho. `resumen.md`: estado y fecha.

Cierre de la fase: protocolo completo, incluida la verificación desde Gamer.

## Fase B — ventajas (perks) raspadas de wzstats

**Modelo: opus · Potencia: high.** Toca el scraper, que corre solo cada mañana; un fallo ahí se
ve tarde. Tiene que aplicar la regla de la casa «nada que falle borra un dato bueno».

- **B1. Parser.** `parse_perks(html)` en `scrape.py` para las dos páginas que importan:
  Warzone `https://wzstats.gg/warzone-2/loadouts/best-perks-tier-list` y Black Ops 7
  `https://wzstats.gg/bo7/loadouts/best-perks-tier-list`. Estructura vista el 2026-09-08:
  bloques `.tier-list` con clase de tier (`tier-meta`, `tier-a`, `tier-b`, `tier-c`, `tier-d`),
  dentro tarjetas `.tierlist-card` con el nombre en `.content-name` y la ranura como texto
  («Perk 1», «Perk 2», «Perk 3»; en BO7 también «Speciality»). La página tiene pestañas
  (Perks, Lethal, Tactical, y en BO7 Wildcards, Field Upgrades, Scorestreaks): comprobar con
  `--simular` si todas vienen en el mismo HTML o hay que pedirlas aparte, y anotarlo en
  `CLAUDE.md`. No usar los bloques «Best X Perks» de las fichas de arma: son de Black Ops
  Royale y del multijugador, no de Battle Royale.
- **B2. JSON.** `payload["perks"] = {"warzone": {...}, "bo7": {...}}`, cada uno con `url`,
  `label` y `items: [{name, slot, tier, kind}]` (`kind`: perk, lethal, tactical, wildcard,
  field_upgrade, scorestreak). Si una página falla, se copia el bloque del JSON anterior con
  `stale` y `stale_since` y se anota un warning, como hace `recuperar_modo()`.
- **B3. Validador y pruebas.** Invariantes en `validar_meta.py` (ranuras y tiers válidos, un
  mínimo de elementos por lista). Pruebas del parser en `pruebas.py` con un fragmento de HTML
  guardado en el propio fichero de pruebas, como las que ya existen.
- **B4. Web.** Sección «Ventajas meta por ranura» junto al equipamiento del día: para los modos
  de Warzone enseña `perks.warzone`, para los de BO7 `perks.bo7`. META y A por ranura, con el
  tier. **Sin lógica de estilo todavía** (va en la fase C, con la lista de MW4).
- **B5. Documentación y versión.** `CLAUDE.md` (formato, trampas nuevas del parser),
  `resumen.md`, `VERSION` del `sw.js`. Cierre con el protocolo.

## Fase C — cuando wzstats pase Warzone a Modern Warfare 4 (noviembre de 2026)

**Modelo: fable · Potencia: high.** Es diagnóstico sobre un cambio que no está escrito en ningún
sitio: hay que mirar qué hace wzstats ese día y decidir.

**Disparador:** el aviso de A5 (correo del workflow, cabecera de la web, repaso de las 09:00).
Si el 15-11-2026 no ha saltado, mirar a mano `https://wzstats.gg/` y las fichas de Warzone.

- **C1.** Confirmar en wzstats qué sirven las páginas de Warzone (armas MW4, sufijo `-mw4` en
  algunos slugs), qué pasa con `/bo7/meta` y `/bo7/ranked/meta`, y si existen `/mw4/meta` y
  un ranked de MW4. Leer `CONTEXT_RE` y `TRACKED_CONTEXTS` en `scrape.py` y comprobar con
  `--modo … --sin-builds --simular` los textos de contexto nuevos en las fichas.
- **C2.** Cambiar `MODES` (multijugador y ranked a MW4), `BASE_GAME`, y revisar los mínimos del
  validador (`multiplayer_ranked` tiene el mínimo en 3 por Black Ops 7).
- **C3.** Desbloqueos en MW4: los accesorios se desbloquean una vez por clase y aparecen los
  Apex; los niveles de arma pasan de 42 a 61 o más. Revisar `reqLabel()`, los textos de A2 y el
  campo de nivel de A3 con las fichas reales.
- **C4.** Tabla de armas por **nivel de jugador** (la de MW4, no la de Black Ops 7) y el campo
  «Mi nivel» en el perfil: «A por la siguiente» pasa a decir qué armas te faltan por nivel.
- **C5.** Tabla de ventajas **por estilo** (agresivo / táctico, mando / teclado) sobre la lista
  de MW4 de la fase B, y la recomendación en la web.
- **C6.** Armas heredadas de Black Ops 7 dentro de Warzone: cómo las enseña wzstats, si traen
  código y accesorios, y cómo etiquetarlas.
- **C7.** Documentación, versión, verificación desde Gamer.

## Recordatorio de noviembre: dónde vive

- Automático y real: el aviso de A5 (se dispara con el cambio de wzstats, no con una fecha).
- `CLAUDE.md`, sección «Pendiente», con fecha: se lee en cada arranque de esta carpeta.
- `resumen.md` y la ficha `_CONTRATOS\Warezone.md`.
- La memoria persistente de la ventana (`mw4-cambia-warzone-en-noviembre-2026`).

No se ha creado ningún evento en el calendario de Google: es una cuenta compartida de la casa y
eso lo decide el usuario.

## Qué escribir para empezar la fase A

Antes del primer mensaje, en la ventana nueva:

```
/model sonnet
/effort high
```

Y después, tal cual:

```
Lee CLAUDE.md, resumen.md y documentacion/plan-2026-09-08-fases.md de esta carpeta y ejecuta la fase A del plan. Primera línea: modelo y potencia que tocan para esta fase; si no son los que hay, para y pídemelos antes de tocar nada.
```

Para las fases B y C, lo mismo cambiando la letra de la fase y el modelo:
B → `/model opus` y `/effort high`; C → `/model fable` y `/effort high`.
