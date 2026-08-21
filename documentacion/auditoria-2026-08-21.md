# Auditoría del proyecto — 2026-08-21 (segunda vuelta)

Continuación de [`auditoria-2026-08-20.md`](auditoria-2026-08-20.md). Commit de
partida: `d690539`, árbol limpio.

**Lo primero fue comprobar, no leer.** La auditoría de ayer dejó su informe
escrito, pero un informe no demuestra nada. Antes de tocar nada se verificó que
lo que decía es cierto:

| Comprobación | Resultado |
|---|---|
| `python scripts/pruebas.py` | 35 comprobaciones, todas pasan |
| `python scripts/validar_meta.py` | OK: 5 modos, 615 armas, 66 con accesorios |
| `esprima` sobre el `<script>` de `index.html` | parsea, 22 149 caracteres |
| `py_compile` de los tres scripts | compilan |
| commits sin subir | 10 (`a26b20d`…`d690539`) |

Conclusión: la primera vuelta **está realmente aplicada y funcionando**. No se
repite ni se deshace nada de aquello. Lo de hoy es lo que aquella no vio.

---

## Lo que encontré esta vez

Los hallazgos de hoy salen de dos sitios: leer el código con otros ojos, y —
sobre todo — **mirar los datos generados**, que es donde apareció lo gordo. Un
`meta.json` que pasa el validador puede seguir estando medio vacío.

### A — Correcciones

#### A12 · La tarjeta de arma reserva 72 px de hueco para una imagen que no existe

**Dónde:** `docs/index.html:475` (`.artbox`) y `scripts/scrape.py:198`.
**Qué pasa:** de las 615 entradas de arma del `meta.json`, **solo 27 traen
imagen**. Y no es aleatorio: al contar por tier salen exactamente las del **tier
S** de cada modo (10, 14, 7, 5, 10). El resto llega vacío.
**Por qué:** wzstats renderiza en el servidor solo el primer bloque de la tier
list; las demás imágenes las carga el navegador después. El HTML que recibe el
scraper tiene **12 URLs de imagen en total** para 248 armas — verificado hoy
contra la web en vivo. No es un fallo del selector: la información no está ahí.
**Por qué importa:** `.artbox` tiene altura fija (a propósito, para que las
tarjetas no bailen mientras cargan), así que cada arma sin imagen enseña un
rectángulo vacío de 72 px. Se nota sobre todo en «A por la siguiente», que casi
siempre son armas de tier A.
**Qué hago:** dos cosas, una por hallazgo. Aquí, la barata: si no hay imagen, no
se pinta la caja. La otra va en B9.

#### A13 · Compartir el enlace por WhatsApp no funciona

**Dónde:** `docs/index.html:11`, `<meta property="og:image" content="icons/icon-512.png">`.
**Por qué importa:** la mejora B8 de ayer añadió las etiquetas `og:` justamente
para poder pasar el enlace por WhatsApp. Pero **Open Graph exige URL absolutas**:
un `content` relativo no lo resuelve ningún cliente. Es decir, la etiqueta está
puesta y la funcionalidad no existe. Falta además `og:url`.
**Qué hago:** URL absolutas a la web publicada, `og:url`, y `twitter:image`.

#### A14 · El service worker no subió de versión cuando cambió la web

**Dónde:** `docs/sw.js:14`, `VERSION = "armeria-v1"`.
**Por qué importa:** el propio `CLAUDE.md` lo deja escrito: «al tocar cualquier
archivo de `docs/` hay que subir `VERSION`». El historial dice que `sw.js` se
escribió en `ef55288` y que `index.html` volvió a cambiar después, en `600e477`,
sin tocar la versión. La caché es *network-first*, así que quien tenga cobertura
no se queda pegado, pero la regla existe para el caso en que sí.
**Qué hago:** subir a `armeria-v2` en el mismo commit que cambia la web, que es
como debe hacerse siempre.

#### A15 · El regex que quita los acentos lleva los acentos dentro

**Dónde:** `docs/index.html:559`, `normaliza()`.
**Qué pasa:** el rango de marcas diacríticas está escrito con los caracteres
combinantes literales (`/[◌̀-◌ͯ]/`) en vez de con sus códigos. Hoy funciona
—buscar «jager» encuentra `JÄGER 45`, comprobado— pero son caracteres invisibles
que cualquier editor, copia-pega o normalización del archivo puede romper, y el
fallo sería mudo: el buscador dejaría de encontrar las armas con acento y nadie
sabría por qué.
**Qué hago:** `/[̀-ͯ]/g`, que es lo mismo y se ve.

#### A16 · Un fallo de wzranked.com degrada la temporada a «Temporada actual»

**Dónde:** `scripts/scrape.py:325-334`.
**Qué pasa:** `detect_season()` devuelve el literal `"Temporada actual"` si no
puede leer wzranked. Ese valor se escribe en el JSON y **pisa** el bueno
(`Season 5 Reloaded, 2026`), que se pierde para siempre. Un servidor ajeno con
un mal minuto y la cabecera de la web empeora sola.
**Qué hago:** si no se puede leer, conservar la temporada del `meta.json`
anterior. El literal genérico solo se usa si tampoco hay dato previo. Es la misma
política que ya se aplica a los modos y a los accesorios.

#### A17 · La guarda que impide publicar datos a medias se salta con una ruta relativa

**Dónde:** `scripts/scrape.py:429`, `args.salida == OUT`.
**Qué pasa:** `OUT` es absoluta y el `--salida` que teclea una persona no lo es,
así que `python scripts/scrape.py --sin-builds --salida docs/data/meta.json`
**no** dispara la protección y sobrescribe el JSON bueno con una pasada parcial.
La guarda funciona para el camino descuidado (olvidarse de `--salida`) y falla
justo para el que la nombra.
**Qué hago:** comparar rutas resueltas.

#### A18 · Los jobs del workflow no tienen límite de tiempo

**Dónde:** `.github/workflows/update-meta.yml`.
**Por qué importa:** el scraper hace ~70 peticiones con `timeout=45` cada una. Si
wzstats se queda a medias respondiendo, el job puede tirarse hasta el máximo de
GitHub (6 h) consumiendo minutos de la cuenta y bloqueando el grupo de
concurrencia `pages`, con lo que la ejecución del día siguiente tampoco entra.
**Qué hago:** `timeout-minutes` en los tres jobs, holgado (20/10/5).

### B — Mejoras de criterio

#### B9 · Recuperar las imágenes que faltan sin gastar ni una petición más

**Qué gana:** las armas dejan de ser una línea de texto. Hoy solo 27 tienen foto;
con esto la tienen todas las que la web enseña en tarjeta.
**Cómo:** la ficha de cada arma —que **ya descargamos** para sacar los
accesorios— sí trae imágenes servidas desde el servidor. Verificado hoy sobre
tres fichas reales:
- la del arma de la ficha, como `img.wzstats.gg/<slug>[_versionN]/gunFullDisplay`;
- y, de regalo, un bloque `.weapon-alternative-image` con la imagen de **otras**
  armas (`<slug>/gunDisplayLoadouts`), que sirve para rellenar armas cuya ficha
  ni siquiera abrimos.

Se recolectan las dos en un índice `slug → url` y se rellenan al final los huecos.
Coste: **cero peticiones nuevas**. Las cuatro formas de URL se comprobaron con una
petición real cada una: las cuatro responden 200 `image/avif`.
**Lo que no hago:** inventar la URL a partir del slug. El sufijo `_versionN` va de
la 1 a la 7 y no es deducible (`fg42_version1`, `m15-mod-0_version7`, `kar98k` sin
sufijo). Solo se guardan URL que wzstats haya escrito.

#### B10 · Desde cuándo lleva cada arma en su tier

**Qué gana:** es la pregunta que el usuario no puede responder hoy y que decide
en qué arma merece la pena gastar horas de subida de nivel. «S» no dice lo mismo
si lleva tres semanas que si entró ayer y mañana la parchean.
**Cómo:** cada arma guarda `desde` (fecha en que llegó a su tier actual). No hace
falta un archivo nuevo ni una segunda descarga: el dato se arrastra del
`meta.json` de ayer, que ya se lee para calcular los cambios. Si el tier no ha
variado se conserva la fecha; si ha variado, la fecha es hoy.
**Honestidad del dato:** la primera vez no hay historia, así que **no se inventa
una fecha**. Para un arma que ya estaba en ese tier ayer se anota la fecha del
JSON anterior, que es lo único que se puede demostrar («al menos desde»). Un modo
recién aparecido se queda sin `desde` y la web sencillamente no enseña nada.
**En la web:** «lleva 3 semanas en S» en las tarjetas de equipamiento y en la
ficha desplegada.

#### B11 · Comparar dos armas lado a lado

Estaba anotado como próximo paso en `resumen.md` y los datos ya están todos en
`meta.json`: es solo interfaz. Se implementa si el presupuesto de la sesión da
para hacerlo bien; si no, se deja documentado. **Decidido al final: ver el
informe.**

### C — Requiere decisión del usuario

#### C3 · Los 10 commits siguen sin subir a GitHub

Es lo que la regla 9 llama irreversible y fuera de la carpeta: publicar en
internet. No lo hago yo. Va en el informe final con el comando exacto.

Los puntos C1 (gamertag en el historial) y C2 (contraseña pegada en el chat) de
ayer siguen igual y con la misma recomendación; no se repiten aquí.

---

## Lo aplicado hoy, y cómo se comprobó

| Commit | Qué |
|---|---|
| `d690539` | punto de partida (árbol limpio, no hizo falta commit previo) |
| `960b7ae` | este plan |
| `8e236d2` | A13–A18: og absolutas, temporada, guarda de `--salida`, caja vacía, regex, sw v2, timeouts |
| `0ee62f7` | **mejora** B9: imágenes de todas las armas del top |
| `512762c` | **mejora** B10: antigüedad en el tier |
| `9deed6e` | **mejora** B11: comparador con veredicto |
| `710df16` | README y CLAUDE.md |

Los tres bloques de mejora llevan su propio commit con el mensaje empezando por
`mejora:`, como pide el guion. (La primera vuelta no lo hizo y lo dejó anotado
como desviación; esta sí.)

### Comprobado de verdad

- `python scripts/pruebas.py` → **57 comprobaciones**, todas pasan (eran 35).
  Las 22 nuevas cubren la cosecha de imágenes y, sobre todo, que la antigüedad
  **no invente fechas** cuando no hay historia.
- `python scripts/validar_meta.py` sobre el `meta.json` publicado → OK: 5 modos,
  615 armas, 66 con accesorios.
- **Pasada completa en vivo** contra wzstats escribiendo fuera del proyecto:
  248/59/55/5/248 armas, 66 fichas, código 0, sin avisos. De ahí salió el
  `meta.json` que se publica, ya validado.
- **Imágenes:** 46 → 257 entradas con foto, y **100 % de los tiers S y A** de los
  cinco modos, que es de donde salen todas las tarjetas. Las cuatro formas de URL
  se comprobaron con una petición real: las cuatro responden 200 `image/avif`.
- **Antigüedad:** aplicada al JSON de hoy comparándolo con el de ayer (sacado de
  git): 18 armas se movieron de tier, 597 constan desde el día 20. Ninguna fecha
  inventada.
- **Web en el navegador** (servida en `127.0.0.1:8765`): cero errores de consola,
  cero cajas de imagen vacías, cero barras `NaN`, buscador con acentos («jager» →
  JÄGER 45) y armas fuera del top 20 (KAR98K), rachas correctas en tarjetas y en
  ficha desplegada.
- **Comparador:** ejercidas las cinco ramas del veredicto (diferencia de tier,
  puesto oficial, estilo agresivo contra un francotirador, estilo táctico y arma
  secundaria), más los casos borde: misma arma dos veces, botón de limpiar y
  cambio de modo con un arma elegida que no existe en el nuevo.
- **Móvil a 360 px** con el andamio de iframes: sin desbordes, tarjetas del
  comparador apiladas a ancho completo, ningún elemento pulsable por debajo de
  44 px. El andamio se retiró a `_CUARENTENA/` (en `docs/` se publicaría).
- **Sin conexión:** con el servidor local **apagado**, recarga completa y la app
  siguió mostrando armas, accesorios, códigos, rachas y el comparador con sus 249
  opciones. Después se desregistró el service worker y se vació la caché para no
  dejar el navegador del usuario apuntando a `127.0.0.1`.
- **Secretos:** `git grep` de contraseñas, tokens, claves, IP y correos sobre los
  archivos versionados. Cero. Detalle en el informe final.
- **Enlaces:** los 5 enlaces relativos de los `.md` y las 9 rutas citadas en
  README y CLAUDE.md existen.
- YAML del workflow validado con `yaml.safe_load`; `index.html` y `sw.js` con
  `esprima`; los tres scripts con `py_compile`.

### No comprobado

- **El workflow de GitHub Actions sigue sin ejecutarse nunca.** Es el mismo punto
  que dejó abierto la primera vuelta y no se puede cerrar desde aquí: los tres
  jobs encadenados solo se ven funcionando en GitHub, y los commits siguen sin
  subir. Los `timeout-minutes` añadidos hoy tampoco se han ejercido.
- **La copia al portapapeles con una pulsación real.** Igual que ayer: en la
  prueba sintética no hay activación de usuario, así que solo se ejerce la rama
  de fallo.
- **El service worker en un móvil de verdad.** Verificado en Chrome de
  escritorio, incluido el modo sin conexión. iOS se comporta distinto.
- **La vista previa del enlace en WhatsApp.** Las etiquetas `og:` ya son
  absolutas y apuntan a la URL publicada, que es lo que faltaba, pero no se puede
  comprobar hasta que la web esté publicada con este cambio.
