# Resumen de estado — Armería Warzone

**Última actualización: 2026-08-20** (auditoría completa del proyecto).

El contexto técnico detallado vive en **[CLAUDE.md](CLAUDE.md)**: arquitectura,
formato de los datos, trampas del scraping y cómo probarlo. Este fichero es la
bitácora: en qué punto está, qué se decidió y qué viene después.

## Estado actual

Publicado y funcionando en https://zeusente.github.io/warzone-armeria/
Se actualiza solo cada mañana a las 06:10 UTC. No hay nada pendiente de desplegar.

Qué hace hoy la web:

- recomienda tres armas (corta, larga, francotirador) por modo, estilo y mando o
  teclado, con los accesorios exactos, el requisito de desbloqueo y el código de
  canje;
- deja **buscar cualquier arma** del modo, no solo las 20 mejores;
- deja marcar las que no tienes («todavía no», no un descarte) y ordena las que
  faltan por lo que aportarían;
- **funciona sin cobertura** una vez instalada en el móvil;
- avisa cuando los datos son viejos o cuando un modo viene del día anterior.

## Decisiones tomadas (y por qué)

- **`docs/` no se renombró.** El estándar de proyectos reserva `docs/` para
  documentación, pero aquí es la raíz que publica GitHub Pages. La documentación
  vive en `documentacion/`. Renombrarla obligaría a tocar el workflow y no
  compensa el riesgo.
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

1. **Vigilar la primera ejecución del cron** tras estos cambios (mañana 06:10
   UTC): es la primera vez que corre el workflow con los jobs nuevos.
2. **Historial de la meta**: hoy solo se guarda el diff contra la actualización
   anterior. Un `docs/data/historico.json` con el tier de cada arma por día
   permitiría enseñar la tendencia («lleva tres semanas en S»).
3. **Comparador de dos armas** lado a lado, con sus builds. Los datos ya están.

## Cuarentena

`_CUARENTENA/` tiene cuatro cosas para borrar cuando quieras, listadas en
[`_CUARENTENA/INDICE.md`](_CUARENTENA/INDICE.md). Ninguna hace falta.

## Informes

- [`documentacion/auditoria-2026-08-20.md`](documentacion/auditoria-2026-08-20.md)
  — hallazgos, decisiones y qué se aplicó.
