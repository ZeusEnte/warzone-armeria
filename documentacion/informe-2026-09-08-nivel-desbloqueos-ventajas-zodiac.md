# Informe del 2026-09-08: nivel y desbloqueos, explicaciones para novatos, ventajas por estilo y la «zona nueva»

**Estado: solo análisis. No se ha tocado código.** Lo pidió el usuario así: primero saber qué
es posible, después decidir.

Preguntas que se hicieron:

1. ¿Puede el panel detectar solo qué nivel tengo y qué armas y accesorios tengo desbloqueados?
2. ¿Puede explicar, para alguien que empieza, qué hay que hacer para desbloquear cada arma y cada
   accesorio que recomienda?
3. ¿Puede decirme qué ventajas (perks) llevar según mi estilo de juego?
4. Ha salido una zona nueva de Warzone. ¿Cuál es, y cómo evitar que el panel me lleve a error
   sobre qué Warzone es?

---

## Resumen en cinco líneas

1. **Detectar automáticamente tu nivel y tus desbloqueos: no se puede.** Activision no da ese dato
   a nadie. No hay API oficial; la no oficial está abandonada desde octubre de 2024 y nunca tuvo
   nada de desbloqueos. Ningún tracker del mundo lo hace: todos te lo hacen apuntar a mano.
2. **Lo que sí se puede, y es barato:** que tú escribas tu nivel de jugador (un número) y el nivel
   de cada arma que te interese (otro número). Con eso la web sabe exactamente qué accesorios te
   faltan y cuántos niveles te quedan. Se guarda en tu navegador, como ya se guarda «No la tengo».
3. **Explicar cómo se desbloquea cada accesorio: sí, y el dato ya está en el JSON.** Falta solo el
   texto. De paso hay dos etiquetas que hoy salen mal y conviene arreglar.
4. **Ventajas según tu estilo:** wzstats publica listas de ventajas que se raspan igual que las
   armas. La parte «según tu estilo» no la publica nadie: sería una tabla pequeña hecha a mano.
5. **La zona nueva es Zodiac, y es el aviso de algo más gordo:** Modern Warfare 4 sale el
   **23-10-2026** y en **noviembre Warzone cambia de juego base**. Cambian las armas, los niveles y
   la forma de desbloquear. Cualquier tabla hecha a mano sobre Black Ops 7 caduca en unas ocho
   semanas. La recomendación es hacer ahora lo que no caduca y esperar a noviembre para el resto.

---

## 1. ¿Puede la web saber sola qué nivel tengo y qué tengo desbloqueado?

**No.** Y no es por falta de ganas ni de técnica: es que el dato no sale del juego.

Explicado para alguien que empieza:

- Para que una web lea algo de tu cuenta, Activision tiene que ofrecer una «ventanilla» (una API).
  **Activision no tiene API pública.** Lo que usan los trackers de estadísticas es una puerta
  trasera de `my.callofduty.com` que Activision cierra cuando quiere. La librería más usada para
  entrar por ahí dejó de mantenerse el **13-10-2024**, y su documentación llega hasta Modern
  Warfare III (2023). Lo que ofrece esa puerta es: estadísticas de carrera, últimas partidas,
  tienda, puntos COD, cuentas vinculadas. **Nada de armas desbloqueadas, nada de accesorios, nada
  de nivel de arma.** Nunca lo hubo.
- Además, esa puerta exige tu sesión iniciada (una cookie de tu cuenta). Nuestra web es una página
  estática publicada en GitHub, sin servidor. Desde ahí el navegador bloquea ese tipo de llamadas,
  y aunque no las bloqueara, no vamos a pedirle a nadie que pegue su cookie de Activision en una
  web pública.
- La prueba de que nadie puede: el rastreador de camuflajes de wzstats y los de la App Store son
  **casillas que marcas tú**. Uno de ellos lo dice en su descripción: es imposible leer el progreso
  automáticamente. Hasta un rastreador de Black Ops 7 Ranked hecho en Google Sheets lo resuelve
  con **capturas de pantalla leídas por una IA**, «porque no hay API».
- Dónde ves tus datos dentro del juego: **Carrera > Estadísticas > Historial de combate** (tu
  nivel) y el **Armero** (el nivel de cada arma, y qué accesorios tienen candado).

**Alternativa semiautomática, descartada:** hacer una foto de la pantalla del Armero y que una IA
la lea. Requiere una clave de API y un servidor, o pagar por cada foto. Contradice el diseño de
este proyecto (sin servidor, sin secretos, gratis) y la regla de la casa de que un secreto no
sale del disco.

### Lo óptimo: pedir el mínimo y deducir el resto

Solo hacen falta **dos números**, y la web deduce todo lo demás:

| Qué escribes | Dónde | Qué deduce la web |
|---|---|---|
| Tu **nivel de jugador** (1-55, y si tienes prestigio) | una vez, junto al gamertag | qué armas de lanzamiento te faltan todavía (cada una se abre a un nivel fijo) |
| El **nivel de esta arma** | en la ficha del arma, solo cuando te interese | exactamente qué accesorios de la build te faltan («Nv. 37» con el arma a 20: te faltan 17 niveles) y cuántos hay que subir |
| «Ya lo tengo» por accesorio | opcional, para los de Armería / Prestigio / semanal | tacharlo de la lista de tareas |

Todo se guarda en el `localStorage` del navegador, en el mismo perfil donde hoy vive `missing`.
**No hace falta tocar el scraper ni el JSON**: el requisito de cada accesorio ya viene
(`unlock: "Level 37"`) y el nivel máximo de cada arma también (`max_level`).

Lo que no se puede deducir con números y hay que preguntar: si un accesorio de **Armería**,
**Prestigio** o **desafío semanal** lo tienes ya. Por eso el «ya lo tengo» por accesorio.

---

## 2. Explicar cómo se desbloquea cada cosa, para novatos

### Lo que ya sabe el JSON

De las 3.471 entradas de accesorio (66 armas de tier S y A, 796 builds), el requisito viene así:

| `unlock` | Entradas | Qué significa |
|---|---|---|
| `Level N` | 2.534 (73 %) | subir **esa arma** al nivel N |
| `Armory` | 522 | recuperarlo en la Armería |
| `Prestige` | 162 | accesorio de prestigio del arma |
| nombre de otra arma (`Coda 9`, `Dravec 45`…) | 89 | se desbloquea subiendo **otra** arma; wzstats no dice a qué nivel |
| `Week 2/3/4 Challenge` | 5 | desafío semanal de la temporada |
| vacío | 159 | wzstats no lo publica (fichas de diseño antiguo, como la KAR98K) |

Hoy la web lo traduce a una etiqueta corta («Nv. 37», «Armería», «Prestigio», «subir Coda 9»).
Lo que falta es el **«¿y eso cómo se hace?»**. Texto propuesto por tipo, al pulsar la etiqueta:

- **Nivel N.** «Este accesorio se abre cuando **esta arma** llega al nivel N. El nivel del arma
  sube jugando con ella (matar, asistir, completar contratos). El arma llega hasta el nivel
  `max_level`.» Y si has escrito tu nivel: «Estás en 20: te faltan 17 niveles.»
- **Armería.** «Es contenido de una temporada pasada que ya no se puede conseguir por su vía
  original. En el juego: **Carrera > Desafíos > Armería**. Activas el objeto y completas su
  desafío de experiencia; las guías hablan de 250.000 a 750.000 XP por objeto. Es lento: si
  el objeto aún está en su evento o pase de batalla, consíguelo por ahí antes.»
- **Prestigio.** «Accesorio exclusivo del arma. Hay que subir el arma al máximo y hacerle
  **prestigio** (se reinician sus niveles y sus accesorios, salvo las miras). Después queda
  desbloqueado para siempre.»
- **Desafío semanal.** «Se consigue completando el desafío semanal de esa semana de la temporada.
  Si la semana ya pasó, va a parar a la Armería.» **Hoy esto sale mal:** la web enseña «subir
  Week 2 Challenge», porque toma todo lo que no reconoce como nombre de arma. Son 5 entradas.
- **Otra arma.** «Este accesorio se desbloquea subiendo de nivel la Coda 9, no esta arma. wzstats
  no dice a qué nivel.»
- **Vacío.** «wzstats no publica el requisito de este accesorio.» Mejor decirlo que callar.

### El arma en sí: eso wzstats no lo dice

Las fichas de wzstats traen el requisito de cada **accesorio**, pero no cómo se consigue **el
arma**. Sí está en fuentes públicas, y es sencillo de contar:

- Las **30 armas de lanzamiento** de Black Ops 7 se abren por **nivel de jugador**: seis desde el
  nivel 1 (M15 MOD 0, Ryden 45K, MK.78, Jäger 45, AAROW 109, cuchillo), y el resto escalonadas
  del AK-27 (nivel 4) al MPC-25 (nivel 55).
- Las **armas de temporada** (26 hasta la temporada 4, y en la 5 el FG42, las Gremlin, la Mammoth
  y la Mace) se consiguen por **pase de batalla** (gratis, en una página concreta), por **evento**
  de temporada, o por **desafío semanal**. Si se te pasó, **Armería**.
- Las armas **heredadas** (de MW2, MW3 y BO6) se usan en Warzone desde la pestaña **Legacy**: las
  tienes si las ganaste en su juego; si no, se recuperan con XP en la Armería. **No admiten
  accesorios de Black Ops 7 ni códigos de canje**, y la web ya lo refleja: esas builds vienen sin
  código.

Meter esto en la web supone una **tabla hecha a mano** de unas 60 armas de Black Ops 7 más una
regla general para las heredadas. Es una tarde de trabajo, pero **caduca en noviembre** (véase
el punto 4). Por eso no la haría todavía.

### Qué cuesta la parte que no caduca

Solo texto y dos campos en `docs/index.html`, y subir `VERSION` en `sw.js`. Sin dependencias, sin
tocar el scraper. Una tarde, con pruebas.

---

## 3. Ventajas (perks) según el estilo de juego

### Lo que publica wzstats, comprobado hoy

| Página | Qué trae | Actualizada |
|---|---|---|
| `/warzone-2/loadouts/best-perks-tier-list` | ventajas de **Warzone** (Battle Royale y Resurgence) por ranura (Perk 1, 2, 3), en tiers META / A / B, más letales y tácticos | 07-09-2026 |
| `/warzone/meta/black-ops-royale/perks` | ventajas de **Black Ops Royale** (modo que no seguimos) | 07-09-2026 |
| `/bo7/loadouts/best-perks-tier-list` | ventajas de **Black Ops 7 multijugador** por ranura más especialidad, comodines, mejoras de campo y rachas | 08-09-2026 |

Las tres tienen la **misma estructura** que las tier lists de armas (tarjetas con nombre y ranura
dentro de bloques por tier), así que se raspan con el mismo tipo de parser: dos o tres peticiones
más al día, nada comparado con las 70 de hoy.

Meta de Warzone ahora mismo, tal cual lo publica wzstats: Sprinter (ranura 2), Ghost (3), Hunter
(3), Momentum (2), Drill Instructor (1), Tempered (3), Scavenger (1) y Quick Fix.

**Trampa descubierta:** las fichas de cada arma tienen bloques «Best X Perks», pero son las de
**Black Ops Royale** y las de **BO7 multijugador**, no las de Battle Royale ni Resurgence (lo delata
la ruta de sus imágenes, `-warzone-bor` y `-bo7`, y que las de Warzone son las mismas tres para
todas las armas). No hay que rasparlas de ahí.

### Lo que no publica nadie

**La parte «según tu estilo».** wzstats da una tier list única, no una por estilo. Para que la
web diga «tú juegas agresivo: lleva Quick Fix y Sprinter» hace falta una **tabla a mano** que
etiquete cada ventaja (unas 20 en Warzone, unas 30 en BO7) con el estilo al que favorece. Es
pequeña y el perfil ya guarda el estilo (agresivo / táctico) y el dispositivo, así que encaja con
lo que hay. Pero vuelve a ser **contenido de Black Ops 7 que cambia en noviembre**.

### Propuesta

1. Raspar las dos listas que nos importan (Warzone y BO7 multijugador) y guardarlas en el JSON
   como `perks`, con nombre, ranura y tier.
2. Enseñar «Ventajas meta por ranura» en la web, junto al equipamiento del día.
3. La tabla de estilo, a mano, **cuando la lista sea la de Modern Warfare 4**, no antes.

---

## 4. La «zona nueva», y qué es Warzone hoy para que nada lleve a error

### Zodiac

- Es un **mapa nuevo de Resurgence**: una fábrica de drones («DRC Advanced Systems»), con naves
  industriales, oficinas, túneles, una vía de tren central y costa. Compacto y con mucha altura.
- Solo se ha podido jugar en la **beta abierta de Modern Warfare 4**, del **28-08 al 01-09-2026**
  (segundo fin de semana). **Hoy no está disponible.** Se espera de vuelta con el lanzamiento de
  MW4, el **23-10-2026**, sin fecha confirmada.
- Fuente oficial: el blog de Call of Duty de la beta (fin de semana dos).

### Qué es Warzone ahora mismo (temporada 5 Recargada de Black Ops 7, desde el 20-08-2026)

| Modo | Mapas |
|---|---|
| Battle Royale | **Verdansk** y **Avalon**, rotando |
| Resurgence | **Rebirth Island** y **Haven's Hollow** |
| Black Ops Royale (estilo Blackout, desde el 12-03-2026) | Avalon |

El panel sigue Battle Royale, Resurgence, Resurgence Ranked, y el multijugador y ranked de Black
Ops 7. **No sigue** Black Ops Royale ni Iron Gauntlet, aunque wzstats tenga página de ambos.

### El calendario que lo cambia todo

| Fecha | Qué pasa |
|---|---|
| **17-09-2026** (no confirmado, sale del contador del pase de batalla) | temporada 6 de Black Ops 7, «The Haunting». La última. |
| **23-10-2026** (oficial) | sale **Modern Warfare 4**. Ese mismo día **Warzone deja de funcionar en PS4 y Xbox One**. |
| **noviembre de 2026** (sin fecha; las temporadas 1 suelen llegar 3-4 semanas después del juego) | **temporada 1 de MW4**: Warzone pasa a estar basado en MW4. Arsenal, operadores y pase de batalla de MW4 son el nuevo estándar. |

### Qué cambia con MW4 y por qué importa para este proyecto

- **Los accesorios se desbloquean una vez y valen para todas las armas compatibles de su clase.**
  Hoy se desbloquean arma por arma. Cambia el significado de «Level N».
- **Accesorios Apex**: uno por arma, se gana subiendo el arma al máximo. wzstats ya los enseña en
  las fichas de MW4 con una etiqueta `Apex`, y los niveles de arma llegan al menos a 61 (en Black
  Ops 7 el tope es 42). **Nuestra web hoy traduciría «Apex» como «subir Apex»**, igual que le pasa
  con los desafíos semanales.
- **Las armas se abren por nivel de jugador**, como ahora, pero con otra tabla.
- **Las armas de Black Ops 7** pasarán previsiblemente a «heredadas» dentro de Warzone (así ha
  ocurrido en cada cambio de juego). **No está confirmado oficialmente**; hay filtraciones que
  hablan de más de cien armas heredadas sin prestigio, sin códigos y sin camuflajes nuevos.
- **wzstats ya tiene** `/mw4/meta` (148 armas, actualizado hoy) y fichas de armas MW4. Sus páginas
  de Warzone siguen siendo de Black Ops 7 hasta noviembre. Nuestros modos «Multijugador (BO7)» y
  «MP Ranked (BO7)» apuntan a `/bo7/...` y se quedarán viejos.
- **Curiosidad que no es fallo nuestro:** wzstats pone «Season 2» en las cabeceras de todas sus
  páginas (Warzone, BO7, Black Ops Royale). Nuestra temporada sale de wzranked («Season 5
  Reloaded, 2026»), que es la correcta.

### Para que el panel no lleve a error

Una sola cosa, y barata: que la cabecera diga **el juego base junto a la temporada**. Hoy dice
«Season 5 Reloaded, 2026». Cuando en noviembre wzranked diga «Season 1», tiene que leerse
**«Warzone · Modern Warfare 4 · Temporada 1»**, no «Temporada 1» a secas, que es lo mismo que decía
en diciembre de 2025 con Black Ops 7. El dato del juego base hoy no lo raspamos: habrá que sacarlo
de la propia tier list (las armas MW4 llevan sufijo `-mw4` en wzstats) o de wzranked.

---

## 5. Recomendación, en orden

**A. Ahora, porque no caduca** (una tarde, solo `index.html` y `sw.js`):

1. El texto de «¿cómo se desbloquea?» por tipo de requisito (punto 2).
2. Arreglar las dos etiquetas: «Week N Challenge» y, para noviembre, «Apex».
3. «Mi nivel» y «nivel de esta arma» en el perfil, con la cuenta de lo que falta por accesorio.
   MW4 mantiene niveles de arma y de jugador: cambian los números, no la idea.
4. La cabecera con el juego base.

**B. Ahora, pero solo el raspado** (una o dos tardes, `scrape.py` + validador + pruebas):

5. Las listas de ventajas de wzstats al JSON, y «Ventajas meta por ranura» en la web. Las páginas
   de MW4 tendrán la misma estructura, así que el trabajo no se pierde.

**C. Después de noviembre, cuando wzstats cambie Warzone a MW4:**

6. La tabla de armas por nivel de jugador (la de MW4, no la de Black Ops 7).
7. La tabla de ventajas por estilo.
8. Revisar los modos de multijugador (`/bo7/...` → `/mw4/...`) y lo que pase con las armas heredadas.

**D. Nunca:** la detección automática. No depende de nosotros.

**Lo que no he comprobado:** el texto exacto del aviso «Not Unlocked?» de wzstats (se carga por
JavaScript al pulsar; no está en el HTML ni en su bundle), y si Activision ha dicho algo oficial
sobre las armas de Black Ops 7 en el Warzone de MW4. Lo segundo se sabrá con las notas de la
temporada 1.

---

## Fuentes

Oficiales:
- [Modern Warfare 4 Open Beta: Weekend Two Intel](https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-open-beta-weekend-two) (Zodiac, fechas de la beta)
- [Modern Warfare 4 Open Beta: Everything You Need to Know](https://www.callofduty.com/blog/2026/08/call-of-duty-modern-warfare-4-open-beta-everything-you-need-to-know)
- [Announcing Call of Duty: Modern Warfare 4](https://www.callofduty.com/blog/2026/05/call-of-duty-modern-warfare-4-announcement) (23-10-2026, temporada 1 después)
- [MW4 Open Beta: Weapons Guide](https://www.callofduty.com/guides/mw4/open-beta-weapons) (accesorios por clase, Apex, armas por nivel)
- [Black Ops Royale: A Tactical Tour of Avalon](https://www.callofduty.com/blog/2026/03/black-ops-7-black-ops-royale-tour-of-avalon)
- [Black Ops 7: Full Progression and Prestige Intel](https://www.callofduty.com/blog/2025/11/call-of-duty-black-ops-7-ready-for-launch-progression-prestige)

Prensa y guías:
- [GameSpot: primer vistazo a Zodiac](https://www.gamespot.com/articles/heres-a-first-look-at-cod-warzones-new-zodiac-map-for-mw4/)
- [timesaver.gg: Zodiac en la beta](https://timesaver.gg/blog/modern-warfare-4-beta-warzone-zodiac)
- [Dot Esports: Avalon entra en la rotación de Battle Royale](https://dotesports.com/call-of-duty/news/warzone-avalon-battle-royale-map-rotation)
- [esports.gg: cuándo es la temporada 6](https://esports.gg/guides/call-of-duty/when-is-season-6-in-black-ops-7-warzone-release-date-explained/)
- [Dexerto: Warzone termina en PS4 y Xbox One con MW4](https://www.dexerto.com/call-of-duty/warzone-will-end-on-ps4-xbox-one-with-modern-warfare-4-launch-3369227/)
- [timesaver.gg: integración MW4 y Warzone](https://timesaver.gg/blog/modern-warfare-4-warzone-integration-explained) y [¿se conservan las armas?](https://timesaver.gg/blog/modern-warfare-4-do-warzone-weapons-carry-over) (filtraciones, no oficial)
- [neonsect: progresión y accesorios Apex en MW4](https://neonsect.com/call-of-duty-modern-warfare-4/mw4-apex-attachments-progression/)
- [timesaver.gg: la Armería de Black Ops 7](https://timesaver.gg/blog/bo7-armory-unlocks-guide)
- [Game Rant: Armería y armas heredadas en Warzone](https://gamerant.com/cod-black-ops-7-bo7-warzone-wz-armory-unlocks-legacy-content-how-to-get/)
- [Steam: todos los accesorios de prestigio de BO7](https://steamcommunity.com/sharedfiles/filedetails/?id=3612330006)
- [mitchcactus: las 56 armas de BO7 y cómo se desbloquean](https://mitchcactus.co/blog/call-of-duty/black-ops-7-full-list-of-weapons-how-to-unlock-them/)
- [Dot Esports: ver tus estadísticas en BO7](https://dotesports.com/call-of-duty/news/check-stats-black-ops-7)

Sobre la API:
- [docs.codapi.dev](https://docs.codapi.dev/llms.txt) (documentación de la API no oficial: sin desbloqueos)
- [Node-CallOfDuty](https://raw.githubusercontent.com/Lierrmm/Node-CallOfDuty/master/README.md) («no longer maintained» desde el 13-10-2024)
- [warzone-stats-tracker, issue 6](https://github.com/grovecj/warzone-stats-tracker/issues/6) («no hay API oficial»)
- [BO7 Ranked Tracker en Google Sheets](https://gist.github.com/quindogl33t/ca7957a8d0dd069b7317d0d40009769f) (capturas leídas por IA «porque no hay API»)
- [BO6 Camo Tracker, App Store](https://apps.apple.com/us/app/id6733240293) («imposible leer el progreso automáticamente»)
- [wzstats camo tracker](https://wzstats.gg/warzone/camo-tracker) (manual)

wzstats, comprobado en vivo hoy:
- [tier list de ventajas de Warzone](https://wzstats.gg/warzone-2/loadouts/best-perks-tier-list) · [de Black Ops Royale](https://wzstats.gg/warzone/meta/black-ops-royale/perks) · [de BO7](https://wzstats.gg/bo7/loadouts/best-perks-tier-list) · [meta de MW4](https://wzstats.gg/mw4/meta)
