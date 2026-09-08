# Resumen de estado — Armería Warzone

**Última actualización: 2026-09-08** (informe de viabilidad, sin tocar código).

El contexto técnico detallado vive en **[CLAUDE.md](CLAUDE.md)**: arquitectura,
formato de los datos, trampas del scraping y cómo probarlo. Este fichero es la
bitácora: en qué punto está, qué se decidió y qué viene después.

---

## 2026-09-08 — Informe pendiente de decisión del usuario

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

Abrir Claude Code en `F:\COMPARTIDO\Claude\Warezone`. Primero el modelo y la potencia de la
fase que toque (para la fase A):

```
/model sonnet
/effort high
```

Y después pegar:

> Lee CLAUDE.md, resumen.md y documentacion/plan-2026-09-08-fases.md de esta carpeta y
> ejecuta la fase A del plan. Primera línea: modelo y potencia que tocan para esta fase; si no
> son los que hay, para y pídemelos antes de tocar nada.

Para solo mirar en qué punto está, sin ejecutar nada:

> Lee `CLAUDE.md` y `resumen.md` de esta carpeta y dime en qué punto está el
> proyecto y qué queda pendiente.
