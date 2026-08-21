# Resumen de estado — Armería Warzone

**Última actualización: 2026-08-21.**

El contexto técnico detallado vive en **[CLAUDE.md](CLAUDE.md)**: arquitectura,
formato de los datos, trampas del scraping y cómo probarlo. Este fichero es la
bitácora: en qué punto está, qué se decidió y qué viene después.

---

## ⚠️ Lo único pendiente: subir la auditoría a GitHub

La auditoría del 2026-08-20 está **terminada y commiteada en el PC**, pero
**no subida**. En GitHub sigue la versión de antes.

Hay **9 commits sin subir**, desde `a26b20d` hasta `5ad0329`. Suben en línea
recta (comprobado el 2026-08-21: GitHub sigue en `be5f1fd`, no hay conflicto).

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
- deja marcar las que no tienes («todavía no», no un descarte) y ordena las que
  faltan por lo que aportarían;
- **funciona sin cobertura** una vez instalada en el móvil;
- avisa cuando los datos son viejos o cuando un modo viene del día anterior.

## Qué se hizo en la auditoría del 2026-08-20

Informe completo en
[`documentacion/auditoria-2026-08-20.md`](documentacion/auditoria-2026-08-20.md).
En corto, se arreglaron tres formas de mentir o morir de la web (página en blanco
si el modo guardado desaparecía, botón «copiar» que decía "copiado" sin copiar,
modo caído que desaparecía en silencio) y se añadieron: modo sin conexión,
buscador de armas, modo de prueba en el scraper, validador del JSON y 35 pruebas
automáticas.

## Decisiones tomadas (y por qué)

- **`docs/` no se renombró.** El estándar de proyectos reserva `docs/` para
  documentación, pero aquí es la raíz que publica GitHub Pages. La documentación
  vive en `documentacion/`. Renombrarla obligaría a tocar el workflow.
- **El gamertag salió del código.** El repo y la web son públicos; el valor por
  defecto es genérico y el de cada uno se guarda en su navegador. El anterior
  sigue en el historial de git: se decidió no reescribir la historia por eso.
- **Un push ya no vuelve a raspar wzstats**, solo republica. Además de ahorrar
  ~70 peticiones, evitaba que el panel «Movimientos del meta» se vaciara cada vez
  que se tocaba el código.
- **Un modo que falla ya no desaparece**: se conserva el dato del día anterior,
  la web lo avisa y el workflow queda en rojo aunque la página se publique.
- **Sin dependencias nuevas.** Las pruebas usan `assert` y no `pytest`;
  `requirements.txt` sigue siendo `requests` + `beautifulsoup4`.

## Próximos pasos sugeridos

1. **Subir los 9 commits** (ver arriba) y vigilar la primera ejecución del cron.
2. **Historial de la meta**: hoy solo se guarda el diff contra la actualización
   anterior. Un `docs/data/historico.json` con el tier de cada arma por día
   permitiría enseñar la tendencia («lleva tres semanas en S»). Empezar por
   añadir un volcado diario en `scrape.py`.
3. **Comparador de dos armas** lado a lado, con sus builds. Es solo frontend:
   los datos ya están en `meta.json`.

## Fuera del proyecto, sin confirmar

- La contraseña de GitHub que se pegó en texto plano en el chat el 2026-08-20.
  **No está en ningún archivo del repositorio** (verificado), pero conviene
  cambiarla si no se hizo ya.

## Cuarentena

`_CUARENTENA/` tiene cuatro cosas para borrar cuando quieras, listadas en
[`_CUARENTENA/INDICE.md`](_CUARENTENA/INDICE.md). Ninguna hace falta. La carpeta
está en `.gitignore`: no se sube ni se publica.

---

## Cómo retomar esto en una ventana nueva

Abrir Claude Code en `F:\COMPARTIDO\Claude\Warezone` y pegar:

> Lee `CLAUDE.md` y `resumen.md` de esta carpeta y dime en qué punto está el
> proyecto y qué queda pendiente.
