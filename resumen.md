# Resumen de estado — Armería Warzone

**Última actualización: 2026-08-21** (segunda vuelta de auditoría, terminada).

El contexto técnico detallado vive en **[CLAUDE.md](CLAUDE.md)**: arquitectura,
formato de los datos, trampas del scraping y cómo probarlo. Este fichero es la
bitácora: en qué punto está, qué se decidió y qué viene después.

---

## ⚠️ Lo único pendiente: subir el trabajo a GitHub

Está **todo terminado y commiteado en el PC**, pero **no subido**. En GitHub
sigue la versión del 20 de agosto por la mañana.

Sin subir está **todo lo de las dos auditorías**, desde `a26b20d` en adelante.
Sube en línea recta: no hay conflicto.

Para subirlo, en la carpeta del proyecto:

```
git pull --rebase origin main && git push origin main
```

Eso republica la web con todo lo nuevo. Después conviene mirar la pestaña
**Actions** de GitHub: es la primera vez que corre el workflow con los tres
trabajos encadenados (`build` → `deploy` → `avisar`).

Si no se sube, no pasa nada malo: la web sigue funcionando con la versión
anterior y el robot sigue actualizando los datos cada mañana.

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

1. **Subir el trabajo** (ver arriba) y vigilar la primera ejecución del cron.
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

Abrir Claude Code en `F:\COMPARTIDO\Claude\Warezone` y pegar:

> Lee `CLAUDE.md` y `resumen.md` de esta carpeta y dime en qué punto está el
> proyecto y qué queda pendiente.
