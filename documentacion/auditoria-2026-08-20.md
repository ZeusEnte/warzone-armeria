# Auditoría del proyecto — 2026-08-20

Commit de partida: `be5f1fd` (`meta: actualizacion 2026-08-20`), árbol limpio.

El proyecto ya venía de una limpieza previa (existe `_CUARENTENA/` con su
justificación), así que aquí hay poca basura que barrer y el peso de la auditoría
cae en **fragilidad, casos borde y funcionalidad que falta**.

---

## Resumen del estado encontrado

Web estática que raspa la tier list de wzstats.gg una vez al día con un cron de
GitHub Actions y recomienda armas de Warzone con sus accesorios exactos. Está
bien escrita y bien documentada; el `CLAUDE.md` es honesto y describe trampas
reales del scraping. Los problemas no son de suciedad, son de **robustez**: hay
tres caminos por los que la web se queda en blanco o miente al usuario, y el
workflow tiene un fallo de diseño que borra el panel de "Movimientos del meta"
cada vez que se toca el código.

---

## A — Limpieza y correcciones

### A1 · La estructura choca con el estándar canónico (`docs/`)

**Dónde:** `docs/` (raíz de la web publicada) vs. `docs/` (documentación) del estándar.
**Por qué importa:** el estándar reserva `docs/` para guías e informes, pero aquí
`docs/` es lo que GitHub Pages publica (`.github/workflows/update-meta.yml:63`,
`path: docs`). Meter informes ahí los publicaría en internet.
**Qué hago:** intenté renombrar `docs/` → `web/` para dejar `docs/` libre para la
documentación; **la capa de seguridad del entorno bloqueó el renombrado del
directorio y no he insistido**. Solución adoptada: `docs/` se queda como raíz web
(es además la convención de GitHub Pages) y la documentación del proyecto vive en
`documentacion/`. Queda anotado en `CLAUDE.md` para que no se vuelva a dudar.

### A2 · Datos personales publicados en un repo público

**Dónde:** `docs/index.html:164` y `docs/index.html:250` — el gamertag
`<GAMERTAG-DEL-USUARIO>` está escrito a fuego en el HTML y en `DEFAULTS`.
**Por qué importa:** el repo es público y la web también. Además cualquier
visitante ve el gamertag ajeno como si fuera el suyo.
**Qué hago:** el valor por defecto pasa a ser genérico (`Jugador`). El botón
«cambiar gamertag» sigue existiendo y guarda el valor en `localStorage`, que es
por dispositivo: no se pierde ninguna capacidad. **Sigue en el historial de git**
(ver sección "Secretos" del informe final).

### A3 · La web se queda en blanco si el modo guardado desaparece

**Dónde:** `docs/index.html:558` (`const mode = DATA.modes[profile.mode];` y acto
seguido `mode.weapons`).
**Por qué importa:** no es hipotético. `scripts/scrape.py:349-366` **se salta los
modos que fallan y sigue**, así que un `meta.json` sin `multiplayer_ranked` es un
resultado normal del scraper. Quien tuviera ese modo guardado en `localStorage`
se encuentra la página en blanco, sin mensaje, y sin forma de recuperarse salvo
borrando datos del navegador. `renderFilters()` sí corrige el modo inválido, pero
se llama *después* de leer `mode.weapons`.
**Qué hago:** validar y recolocar el modo antes de usarlo, y envolver el render en
un `try/catch` que enseñe el cartel de error en vez de morir en silencio.

### A4 · El botón «copiar» dice "copiado" aunque no haya copiado nada

**Dónde:** `docs/index.html:594`.
**Por qué importa:** si `navigator.clipboard` no existe (contexto no seguro,
navegadores antiguos, WebView), el código llama igualmente a `ok()` y el botón
anuncia "copiado". El usuario se va al juego a pegar un código que no tiene.
**Qué hago:** respaldo real con `textarea` + `execCommand("copy")`, y si tampoco
funciona, decirlo ("no se pudo").

### A5 · Barra de encaje con `width:NaN%`

**Dónde:** `docs/index.html:506` y `:518`.
**Por qué importa:** si la mejor arma puntúa 0 (posible: `score()` recorta a 0 y
las secundarias restan 45), `w._s/max` es `0/0` = `NaN` y el atributo sale roto.
**Qué hago:** `|| 1` en el divisor.

### A6 · `esc()` no escapa la comilla simple

**Dónde:** `docs/index.html:359`.
**Por qué importa:** hoy no explota porque todos los atributos generados usan
comillas dobles, pero es una mina para el siguiente que escriba `href='...'`.
**Qué hago:** escapar también `'`.

### A7 · Código muerto

**Dónde:** `docs/index.html:572`, `const btn` declarado y nunca usado.
**Qué hago:** quitarlo.

### A8 · El scraper reintenta errores que nunca se van a arreglar

**Dónde:** `scripts/scrape.py:83-96`.
**Por qué importa:** un 404 (arma retirada de wzstats) se reintenta 3 veces con
esperas de 2 s y 5 s. Con 80 armas eso es tiempo tirado y peticiones de más a la
web origen. Además duerme también **después** del último intento fallido.
**Qué hago:** no reintentar 4xx (salvo 429), y no dormir tras el último intento.

### A9 · La fusión de duplicados pierde datos

**Dónde:** `scripts/scrape.py:188-200`.
**Por qué importa:** la misma arma aparece una vez por categoría. Al fusionar solo
se combinan `positions` y `tier`; si la primera aparición vino sin `weapon_type`
o sin `image` y la segunda sí los trae, se descartan.
**Qué hago:** completar los campos vacíos al fusionar.

### A10 · Estilo mezclado en los mensajes del scraper

**Dónde:** todo `scripts/scrape.py`, concatenación con `+` para construir textos.
**Qué hago:** unificar a f-strings (Python 3.12+ garantizado por el workflow).
Cambio puramente cosmético, sin efecto en el comportamiento.

### A11 · Documentación desajustada

- `_CUARENTENA/LEEME.md` debería llamarse `INDICE.md` con el formato del estándar
  (archivo · ruta original · motivo · fecha).
- `.gitignore` (3 líneas) no cubre entornos virtuales ni basura de editor/SO.
- `resumen.md` es un puntero a `CLAUDE.md`, no una bitácora.
- El `README.md` no menciona nada de lo que se añade hoy.

---

## B — Mejoras de criterio (decididas y aplicadas)

### B1 · El workflow raspa wzstats en cada push, y eso borra el panel de movimientos

**Dónde:** `.github/workflows/update-meta.yml:8-12`.
**Qué pasa:** cualquier push que no sea `.md` dispara el scraping completo (~70
peticiones). Peor: `changes` se recalcula contra la ejecución anterior, así que si
hoy tocas `index.html`, el diff se hace contra el `meta.json` de hace diez minutos
y **"Movimientos del meta" se queda vacío hasta mañana**. Se ve en el propio
`meta.json` actual: dos ejecuciones con 14 minutos de diferencia y `changes: 2`.
**Qué gana:** el panel de movimientos deja de autodestruirse y wzstats recibe la
mitad de tráfico.
**Qué hago:** en `push` solo se despliega, no se raspa (`if: github.event_name !=
'push'`). Y como cinturón, si dos ejecuciones caen el mismo día UTC y el diff sale
vacío, el scraper **arrastra** los `changes` del día anterior en vez de borrarlos.

### B2 · Si un modo falla, hoy desaparece de la web sin avisar

**Dónde:** `scripts/scrape.py:349-370`.
**Qué pasa:** el scraper se salta el modo roto, escribe el JSON sin él y **sale con
código 0**: el workflow queda en verde y nadie se entera de que la web perdió un
modo (y de paso provoca A3).
**Qué gana:** la web no pierde nada y el fallo se ve.
**Qué hago:** si un modo falla, se reutiliza su bloque del `meta.json` anterior y
se marca `"stale": true` con la fecha del dato. La web enseña un aviso en ese modo.
Los avisos se guardan en `meta.json` (`warnings`) y un tercer job del workflow,
que corre **después** de desplegar, falla si hay avisos — así el sitio se publica
igual y GitHub manda el correo de aviso.

### B3 · No hay forma de consultar un arma concreta

**Dónde:** `docs/index.html:505`, `pool.slice(0, 20)` fijo.
**Qué pasa:** `meta.json` trae 248 armas por modo y accesorios de 66, pero la
interfaz solo deja ver 20 y no hay buscador. Si quieres saber qué se le monta al
KAR98K y no está en el top 20 de tu perfil, no puedes.
**Qué gana:** la utilidad se multiplica con un campo de texto. Es la mejora más
barata de todas.
**Qué hago:** buscador por nombre/tipo sobre todas las armas del modo + botón «ver
todas».

### B4 · Es una PWA que no funciona sin cobertura

**Dónde:** `docs/manifest.webmanifest` declara `display: standalone` pero no hay
service worker.
**Qué pasa:** el usuario la instala en el móvil como si fuera una app y en cuanto
falla la red le sale el error de `fetch`. Justo el momento en que la quiere: en el
sofá, con el juego cargando y el wifi flojo.
**Qué gana:** deja de ser una web con icono y pasa a ser una app consultable
siempre.
**Qué hago:** service worker con caché versionada, *network-first* para el HTML y
para `meta.json` (con respaldo a caché) y *cache-first* para iconos. Con
`skipWaiting` + `clients.claim` para que una versión nueva no se quede pegada.

### B5 · El scraper no tiene modo de prueba

**Qué pasa:** para tocar una línea del parser hay que ejecutar los 5 modos y 80
fichas: ~4 minutos y 70 peticiones a wzstats.
**Qué gana:** iterar sobre el parser pasa a costar segundos.
**Qué hago:** `argparse` con `--modo`, `--sin-builds`, `--limite-builds`,
`--salida` y `--simular` (no escribe nada).

### B6 · Nada comprueba que el JSON generado tenga sentido

**Qué pasa:** si wzstats rediseña y el parser devuelve basura *no vacía*, se
commitea y se publica tal cual. La única red de seguridad actual es "cero armas".
**Qué gana:** una regresión silenciosa del parser se detecta el mismo día.
**Qué hago:** `scripts/validar_meta.py` con invariantes (modos mínimos, armas
mínimas por modo, tiers válidos, builds con accesorios, contextos casando con los
modos, fechas coherentes). Se ejecuta en el workflow antes de commitear y también
sirve a mano sobre el JSON que ya hay.

### B7 · La web no avisa si los datos están viejos

**Qué gana:** si el cron lleva días caído, el usuario lo ve en vez de creerse la
meta de la semana pasada.
**Qué hago:** aviso visible si `generated_at` tiene más de 48 h.

### B8 · Detalles de uso

- `fetch` con `?v=Date.now()` se traga los 680 KB **en cada carga**. Pasa a
  `cache: "no-cache"`: revalidación condicional, respuesta 304 vacía si no cambió.
- Etiquetas en español en «Armas que no quieres ver» (hoy `Sniper`, `Shotgun`…
  en inglés dentro de una interfaz en español).
- Las filas de la tabla se abren con el ratón pero no con el teclado.
- Sin `og:` no se puede compartir el enlace decentemente por WhatsApp.

---

## C — Requiere decisión del usuario

### C1 · El gamertag sigue en el historial de git

Quitarlo del historial exige reescribirlo (`filter-repo`) y un `push --force`, que
la regla 3 prohíbe y que además rompería los clones. **Mi recomendación: no hacer
nada.** Un gamertag no es una credencial, es un nombre público dentro del juego, y
el repo es del propio interesado. Queda dicho para que la decisión sea suya.

### C2 · La contraseña de GitHub pegada en el chat el 2026-08-20

Viene anotado en `CLAUDE.md` como pendiente sin confirmar. **No está en ningún
archivo del repositorio** (verificado, ver informe). Sigue siendo recomendable
cambiarla; es una acción fuera de esta carpeta, así que no la toco.
