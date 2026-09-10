# Resumen de estado — Armería Warzone

**Última actualización: 2026-09-10** (fases A y B cerradas; fallo del despliegue detectado).

El contexto técnico detallado vive en **[CLAUDE.md](CLAUDE.md)**: arquitectura,
formato de los datos, trampas del scraping y cómo probarlo. Este fichero es la
bitácora: en qué punto está, qué se decidió y qué viene después.

---

## 2026-09-10 — Verificación desde Gamer: fases A y B cerradas, y dos cosas rotas

Primera sesión desde el **Windows Gamer**, que es justo lo que faltaba para cerrar
las fases.

### ✅ Las fases A y B quedan cerradas

Abierta la web publicada en el navegador de Gamer y leído el DOM:

| Qué había que confirmar | Resultado |
|---|---|
| Versión de interfaz en el pie | `interfaz 2026-09-08c`, coincide con `UI_VERSION` |
| Nivel del arma en las tarjetas del día | presente en las tres («NIVEL DE ESTA ARMA (0–34)») |
| Sección «Ventajas meta por ranura» (fase B) | presente, Perk 1/2/3 con META y A |
| Cabecera con el juego base (fase A) | «Warzone · Black Ops 7 · Season 5 Reloaded, 2026» |
| Textos de desbloqueo (fase A) | «subir Dravec 45», «Armería», «Nv. 12» |

**No hay PWA instalada en Gamer**, así que no hay caché vieja que pueda engañar.

### 🔧 En Gamer no hay Python (y eso rompía el panel)

Ni instalación, ni registro, ni `py`: lo que responde a `python` es el señuelo de
0 bytes de la Microsoft Store. Por eso el acceso directo **«Panel de Warezone»**
—que lanzaba `python -m http.server 8765` sobre `docs/`— escribía su mensaje y
moría. **Arreglado con autorización del usuario**: ahora abre directamente la web
publicada, sin Python ni servidor. Probado, abre el panel en Brave.

El servidor local sigue siendo útil, pero **solo en Worker** y solo para probar
cambios antes de publicarlos. Nunca fue la forma de mirar el panel.

**Queda abierto:** `scripts\comprobar.ps1` da **falsa alarma triple en Gamer**,
porque sus tres pasos llaman a `python -B`. Salen los tres en rojo con el proyecto
perfectamente sano. El propio script ya evita ese mal con la falta de red («no
concluyente», no cuenta como fallo); le falta hacer lo mismo con la falta de Python.

### 🔴 El despliegue de hoy expiró, y no avisó nadie

Lo gordo del día. El cron de las 06:10 UTC corrió (run #34) y:

- `build` → **success**: raspó y commiteó `adbab17` (`meta: actualizacion 2026-09-10`)
- `deploy` → **cancelled**: `deploy-pages@v4` estuvo `in_progress` de 11:15:47 a
  11:25:50 — **exactamente los 10 minutos** de `timeout-minutes: 10` del job
- `avisar` → **skipped**, porque depende de `deploy`
- El despliegue de Pages figura en estado **`error`**

Resultado: **los datos de hoy están en `main` pero no publicados**. La web sirve los
de ayer (1,0 días de antigüedad; el límite son 3, así que no es urgente).

**El agujero de verdad es el silencio.** GitHub manda correo de los runs en
`failure`, no de los `cancelled`; y `avisar`, que es quien debía chillar, se saltó
por `needs: deploy`. Es el modo de fallo que este proyecto tiene escrito como el
peligroso —«la web sigue en pie con datos viejos y nadie se entera»— pero por una
vía no prevista: **no falla el raspado, falla el publicado**. La comprobación de las
09:00 tampoco lo caza hoy: juzga por antigüedad y 1 día está dentro del límite; lo
vería al tercer día.

### ✅ Arreglado ese mismo día, con las tres decisiones del usuario

**1. El workflow ya avisa cuando el despliegue falla.** `avisar` lleva ahora
`if: always()` y un primer paso que falla si `deploy` no acabó en `success`. Sin
`always()`, ese job se saltaba justo el día en que había algo que contar. Efecto
secundario aceptado: cancelar un run a mano también manda correo; se prefiere eso
al silencio.

**2. `comprobar.ps1` ya no da falsa alarma sin Python.** Los pasos 1 y 2 se omiten
diciéndolo, y el **paso 3 —el único que mira el producto de verdad— pasó a
PowerShell**, así que se comprueba igual en las dos máquinas. De paso se fue la
sonda de Python embebida en un heredoc y su fichero temporal: una pieza menos.

**3. Y esa reescritura tenía un bug, que la prueba destapó.** `ConvertFrom-Json` no
deja `generated_at` como texto: lo convierte a `[datetime]`. Al re-parsearlo con
`[datetimeoffset]::Parse()` se pasaba por texto con la cultura de la máquina
(es-ES, `dd/MM`) y se leía con la invariante (`MM/dd`): **`02/09` se interpretaba
como 9 de febrero**, y un JSON de hace 8 días daba «213 días». No se veía a simple
vista porque la fecha de ese día, `09/09`, es simétrica. **El caso peligroso es el
contrario**: una marca vieja leída como reciente, con el cron parado y sin avisar.
Arreglado, y anotado en `CLAUDE.md` porque se reintroduce solo.

**Comprobado que sabe fallar**, que es la mitad que suele faltar: siete JSON falsos
—cron parado, warning, un modo de menos, un modo `stale`, `generated_at` ilegible,
JSON sano y **una fecha reciente pero ambigua (día ≤ 12)**, que es el que caza el
bug de arriba— y los siete se comportan como deben.

**Queda en manos del usuario:** relanzar el workflow para publicar los datos de hoy
(*Actions → Run workflow*; al ser `workflow_dispatch` no vuelve a raspar).

---

## 2026-09-08 — Ajuste después de las fases: el nivel del arma, donde se ve

El usuario abrió su panel y **no encontró dónde poner el nivel del arma**. No era
un fallo: estaba dentro de la ficha desplegada de cada arma, en el ranking, que
es donde tenía sentido técnico pero no donde se busca. Arreglado: el campo sale
ahora **en las tarjetas de «Tu equipamiento de hoy»**, justo debajo de los
accesorios que dicen «Nv. 37», que es donde se está mirando cuando surge la
pregunta. En «A por la siguiente» no, que son armas que todavía no tiene.
`UI_VERSION` a `2026-09-08c`, `sw.js` a `armeria-v7`.

**Decidido en el mismo momento, por el usuario:** el **nivel de jugador** (el
general, distinto del nivel de cada arma) **sigue aplazado a la fase C de
noviembre**, como estaba en el plan. El motivo: para que ese número sirva hace
falta una tabla a mano de qué arma se abre a qué nivel, y esa tabla caduca con
Modern Warfare 4. No está descartado, está esperando a la tabla que sí valdrá.

---

## 2026-09-08 — Fase B ejecutada (opus · high)

La web ya dice **qué ventajas (perks) llevar**, en una sección nueva «Ventajas
meta por ranura» junto al equipamiento del día: META y A por cada ranura
(Perk 1, 2, 3 y la «Speciality» de Black Ops 7).

**El hallazgo que cambió el plan.** El plan pedía dos listas, una «de Warzone» y
otra «de BO7». Al mirar las páginas de verdad resultó que **wzstats publica una
tier list de ventajas por cada modo, y las cinco son distintas entre sí**: entre
Battle Royale y Resurgence —los dos modos que el usuario juega— cambian cuatro
ventajas de sitio (Quick Fix y Berserker son META en Resurgence y bajan a A en
Battle Royale; Scavenger y Field Medic al revés). Con dos listas, tres de los
cinco modos habrían enseñado el dato de otro modo. Así que hay **una lista por
modo**, que además encaja con cómo ya estaban definidos los modos en el scraper:
cada uno tiene su `perks_url` y el JSON guarda `perks[<id de modo>]`. Cuesta 5
peticiones más al día sobre las ~70 de siempre.

Lo hecho, con las 81 pruebas en verde, el validador OK y el JS comprobado con
esprima:

- **B1.** `parse_perks()` en `scrape.py`. Trampas nuevas anotadas en `CLAUDE.md`:
  los tiers empiezan en **META** (no en S), la clase del tier va junto a
  `tier-header` y **en orden variable**, y el `.tier-content` es **hermano** de la
  cabecera, no descendiente.
- **Comprobado lo que el plan mandaba comprobar:** las pestañas (Lethal,
  Tactical, Wildcards, Field Upgrades) **no vienen en el mismo HTML**, cada una
  es una URL propia. Hoy no se raspan; sus rutas quedan anotadas en `CLAUDE.md`
  por si algún día hacen falta, y por eso el campo `kind` existe aunque hoy valga
  siempre `"perk"`.
- **B2.** `payload["perks"]`, con `recuperar_perks()`: si una página falla se
  conserva la del día anterior con `stale`/`stale_since` y se avisa. Misma regla
  de siempre: nada que falle borra un dato bueno.
- **B3.** Invariantes en `validar_meta.py` (tiers META/A/B/C/D, ranura y tipo
  válidos) y pruebas del parser con un recorte real de HTML. **Quedarse sin
  ventajas es una nota, no un error**: un fallo ahí no puede impedir que se
  publiquen las armas, que son lo principal.
- **B4.** La sección en la web, con aviso si el dato viene del día anterior.
- **B5.** `CLAUDE.md` y `resumen.md` al día; `sw.js` a `armeria-v6` y
  `UI_VERSION` a **`2026-09-08b`** — con letra, porque es la segunda publicación
  del mismo día y desde Gamer las dos se leerían igual.

Como en la fase A, hubo que **regenerar `meta.json`** antes de commitear: el
workflow no rasca en un `push` y ahora se exige la clave `perks`. El JSON pasa de
709 a 718 KB (77 ventajas).

**Falta cerrar la fase:** verificación desde el **Windows Gamer**. Que el pie
diga «interfaz 2026-09-08b» y que aparezca la sección «Ventajas meta por ranura».

**Siguiente:** Fase C (fable · high), pero **es de noviembre de 2026**, cuando
wzstats pase Warzone a Modern Warfare 4. La avisa sola el detector de la fase A;
no hay nada que hacer hasta entonces.

---

## 2026-09-08 — Fase A ejecutada (sonnet · high)

Hecho, con `python scripts/pruebas.py` (66 pruebas, todas pasan),
`python scripts/validar_meta.py` (OK, sin avisos) y el chequeo de sintaxis del
JS con esprima, todos en verde:

- **A1.** `Week N Challenge` ya no sale como «subir Week 2 Challenge»: ahora
  «Desafío semana 2». Añadido `Apex` (accesorio de Modern Warfare 4).
- **A2.** Cada accesorio tiene un chip `.req` clicable que despliega el texto
  de «¿cómo se desbloquea?» (`UNLOCK_HELP` en `index.html`), con los textos del
  informe. Comprobado a mano en el navegador (nivel, Armería, desafío semanal,
  vacío).
- **A3.** Campo «Nivel de esta arma» en la ficha desplegada. Con el nivel
  puesto, los accesorios ya alcanzados se marcan `done` (✓) y la build dice
  «te faltan N accesorios (M niveles hasta el último)». Probado en el
  navegador: nivel 10 en la 1911 marcó Nv. 4 y Nv. 10 como hechos y calculó
  bien los que faltan.
- **A4.** `UI_VERSION = "2026-09-08"` visible en el pie, junto al sello de
  datos. `VERSION` de `sw.js` subido a `armeria-v5`.
- **A5.** Cabecera con el juego base («Warzone · Black Ops 7 · Season 5
  Reloaded, 2026»). `BASE_GAME` en `scrape.py` y `detectar_mw4()` comprueban
  si wzstats ya sirve armas de MW4 en los modos de Warzone; si es así, avisan
  en `payload["warnings"]`. **De paso se corrigió que `renderAvisos()` nunca
  leía `DATA.warnings`**: sin eso, este aviso nuevo (y cualquier otro del
  scraper que no fuera la frescura o el modo actual) no habría llegado nunca a
  la cabecera de la web. Comprobado hoy: `detectar_mw4()` no encuentra ningún
  slug `-mw4` todavía, como toca antes de noviembre.
- **A6.** `CLAUDE.md` al día (formato del JSON, `reqLabel`/`unlockHelp`, juego
  base, «Pendiente»).

**Para publicar el cambio de código hacía falta regenerar `meta.json`**: el
workflow, en un `push`, no vuelve a raspar (solo valida y despliega), y el
`meta.json` de ayer no traía `base_game`. Se lanzó `python scripts/scrape.py`
completo (619 armas, 66 con accesorios) antes de commitear, para que el `push`
no rompiera `validar_meta.py`.

**Falta cerrar la fase:** verificación desde el **Windows Gamer** (arranca en
`E:`). Cuando el usuario abra el panel publicado desde ahí, tiene que
confirmar dos cosas: que el pie dice «interfaz 2026-09-08» y que puede
desplegar la ayuda de un accesorio o poner el nivel de un arma. La fase no se
da por cerrada sin ese OK.

**Siguiente:** la fase B, hecha ese mismo día (arriba).

---

## 2026-09-08 — Informe que dio origen al plan por fases

El usuario preguntó si la web puede detectar sola su nivel y sus desbloqueos,
explicar a un novato cómo desbloquear cada cosa, recomendar ventajas por estilo, y
qué es la «zona nueva» de Warzone. La respuesta completa está en
[`documentacion/informe-2026-09-08-nivel-desbloqueos-ventajas-zodiac.md`](documentacion/informe-2026-09-08-nivel-desbloqueos-ventajas-zodiac.md).
En corto:

- **Detección automática: imposible.** Activision no publica desbloqueos por ninguna
  vía; lo viable es pedir dos números (nivel de jugador y nivel del arma) y deducir.
- **Explicar el desbloqueo: sí, el dato ya está en el JSON.** Falta texto. Dos
  etiquetas salen mal hoy («subir Week 2 Challenge») y otra saldrá mal en noviembre («Apex»).
- **Ventajas: raspables de wzstats** (tres tier lists, misma estructura que las de
  armas). La parte «por estilo» sería tabla a mano.
- **La zona nueva es Zodiac** (Resurgence, solo en la beta de MW4 del 28-08 al 01-09).
  **Modern Warfare 4 sale el 23-10-2026 y en noviembre Warzone cambia de juego base:**
  todo lo hecho a mano sobre Black Ops 7 caduca entonces. Recomendación: hacer ahora
  solo lo que no caduca (textos, dos números, cabecera con el juego base) y el resto
  después de noviembre.

**No se ha tocado código.** El usuario aprobó el planteamiento ese mismo día y pidió
ejecutarlo **por fases, decidiendo modelo y potencia antes de cada una**. El plan, con lo que
hace cada fase y con qué modelo, está en
[`documentacion/plan-2026-09-08-fases.md`](documentacion/plan-2026-09-08-fases.md):

- **Fase A** (sonnet · high): textos de desbloqueo, etiquetas, nivel del arma, versión visible,
  juego base en cabecera y el detector del cambio a MW4. Es la siguiente.
- **Fase B** (opus · high): ventajas raspadas de wzstats.
- **Fase C** (fable · high): **noviembre de 2026**, cuando wzstats pase Warzone a Modern
  Warfare 4. La avisa sola el detector de la fase A.

**Verificación desde Gamer:** el usuario usa el panel desde el Windows Gamer (`E:`), no desde
este. Cada fase se cierra cuando él la ve allí. Comprobado hoy: lo publicado es byte a byte lo
del repositorio, y el service worker carga red primero, así que Gamer ve lo publicado al abrir.

---

## ✅ Subido y publicado

**Ya no queda nada pendiente de subir.** Las dos auditorías están en GitHub y la
web publicada las sirve. Verificado el 2026-08-21 desde fuera, sin fiarse del
repositorio local:

| Comprobación | Resultado |
|---|---|
| `git status -sb` | `main...origin/main`, sin commits por delante ni por detrás |
| HEAD remoto | `825e0bf`, el mismo que el local |
| La web en vivo | enseña la sección **«Comparar dos armas»**, que no existía antes |
| `data/meta.json` publicado | `generated_at` **2026-08-21T10:11:31Z**, temporada `Season 5 Reloaded, 2026` conservada, y los campos nuevos `imagen` y `desde` presentes |

El robot hizo su actualización diaria (`c24e394`) mientras la auditoría estaba en
curso y se juntó con ella antes del push: se conservó el `meta.json` local, tres
horas más nuevo y con las imágenes y la antigüedad, y los movimientos del meta de
ambos se unieron (resultaron ser los mismos 20).

**Lo que sigue sin verse:** la ejecución del **cron** con los tres trabajos
encadenados (`build` → `deploy` → `avisar`). El push solo despliega, no raspa, así
que el workflow completo no se estrena hasta las **06:10 UTC**. Conviene mirar la
pestaña *Actions* de GitHub esa mañana. Aquí no se puede comprobar: `gh` no está
instalado.

---

## Estado actual

Publicado y funcionando en https://zeusente.github.io/warzone-armeria/
Se actualiza solo cada mañana a las 06:10 UTC.

Qué hace la web **con los cambios ya commiteados**:

- recomienda tres armas (corta, larga, francotirador) por modo, estilo y mando o
  teclado, con los accesorios exactos, el requisito de desbloqueo y el código de
  canje;
- deja **buscar cualquier arma** del modo, no solo las 20 mejores;
- **compara dos armas** lado a lado y dice cuál te conviene y por qué;
- dice **cuánto lleva cada arma en su tier** («3 semanas en S»);
- enseña **la foto** de todas las armas del top, no solo de las diez primeras;
- deja marcar las que no tienes («todavía no», no un descarte) y ordena las que
  faltan por lo que aportarían;
- **funciona sin cobertura** una vez instalada en el móvil;
- avisa cuando los datos son viejos o cuando un modo viene del día anterior.

## Qué se hizo en las dos auditorías

**Primera vuelta, 2026-08-20** —
[informe](documentacion/auditoria-2026-08-20.md). Se arreglaron tres formas de
mentir o morir de la web (página en blanco si el modo guardado desaparecía, botón
«copiar» que decía "copiado" sin copiar, modo caído que desaparecía en silencio)
y se añadieron: modo sin conexión, buscador de armas, modo de prueba en el
scraper, validador del JSON y 35 pruebas automáticas.

**Segunda vuelta, 2026-08-21** —
[informe](documentacion/auditoria-2026-08-21.md). Empezó comprobando que lo
anterior fuera cierto (lo era) y siguió mirando **los datos generados**, que es
donde estaba lo gordo: de 615 armas solo 27 tenían foto. Se arreglaron siete
cosas más —entre ellas que compartir el enlace por WhatsApp no funcionaba y que
un fallo de wzranked empeoraba la cabecera de la web— y se añadieron las tres
capacidades nuevas: fotos, antigüedad en el tier y comparador. Las pruebas
pasaron de 35 a 57.

## Decisiones tomadas (y por qué)

- **`docs/` no se renombró.** El estándar de proyectos reserva `docs/` para
  documentación, pero aquí es la raíz que publica GitHub Pages. La documentación
  vive en `documentacion/`. Renombrarla obligaría a tocar el workflow.
- **El gamertag salió del código.** El repo y la web son públicos; el valor por
  defecto es genérico y el de cada uno se guarda en su navegador. El anterior
  sigue en el historial de git: se decidió no reescribir la historia por eso.
- **Un push ya no vuelve a raspar wzstats**, solo republica.
- **Nada que falle borra un dato bueno.** Vale para los modos, para los
  accesorios, para las imágenes y —desde hoy— para el nombre de la temporada: si
  la fuente no contesta, se conserva lo de ayer y se avisa.
- **Las fechas no se inventan.** La antigüedad en el tier solo se escribe cuando
  se puede demostrar; si no hay historia, la web no enseña nada en vez de decir
  que toda la meta acaba de cambiar.
- **No se construyen URL de imagen** a partir del nombre del arma: el sufijo de
  versión no es deducible. Solo se guardan las que wzstats publica.
- **Sin dependencias nuevas.** Las pruebas usan `assert` y no `pytest`;
  `requirements.txt` sigue siendo `requests` + `beautifulsoup4`.

## Próximos pasos sugeridos

1. **Vigilar la primera ejecución del cron** (06:10 UTC), que es lo único de las
   dos auditorías que todavía no se ha visto funcionar de verdad.
2. **Historial largo de la meta.** Hoy se sabe desde cuándo lleva un arma en su
   tier, pero no por dónde ha pasado. Un `docs/data/historico.json` con un
   registro por día permitiría enseñar la curva («lleva tres semanas cayendo»).
   Empezar por volcar en `scrape.py` un registro diario de tier por arma.
3. **Plan de desbloqueo.** La web ya sabe el requisito de cada accesorio
   (`Nv. 37`, `Armería`, `subir X`). Juntarlos en una lista de tareas —«para
   montar tu equipamiento de hoy te falta subir el AN-94 a nivel 37»— convertiría
   el dato en algo accionable dentro del juego.

## Fuera del proyecto, sin confirmar

- La contraseña de GitHub que se pegó en texto plano en el chat el 2026-08-20.
  **No está en ningún archivo del repositorio** (verificado otra vez hoy), pero
  conviene cambiarla si no se hizo ya.

## Cuarentena

`_CUARENTENA/` tiene cinco cosas para borrar cuando quieras, listadas en
[`_CUARENTENA/INDICE.md`](_CUARENTENA/INDICE.md). Ninguna hace falta. La carpeta
está en `.gitignore`: no se sube ni se publica.

---

## Cómo retomar esto en una ventana nueva

Abrir Claude Code en `F:\COMPARTIDO\Claude\Warezone`.

**Las fases A y B están hechas. La C es de noviembre de 2026** y la avisa sola el
detector (correo del workflow, cabecera de la web y repaso de las 09:00). Cuando
salte, o si el 15-11-2026 no ha saltado:

```
/model fable
/effort high
```

> Lee CLAUDE.md, resumen.md y documentacion/plan-2026-09-08-fases.md de esta carpeta y
> ejecuta la fase C del plan. Primera línea: modelo y potencia que tocan para esta fase; si no
> son los que hay, para y pídemelos antes de tocar nada.

Para solo mirar en qué punto está, sin ejecutar nada:

> Lee `CLAUDE.md` y `resumen.md` de esta carpeta y dime en qué punto está el
> proyecto y qué queda pendiente.
