# Estado — Armería Warzone

Última actualización: 2026-08-20

## Qué está hecho

Proyecto completo y commiteado en `main` (commit `e05db60`). Funciona de punta a punta en local.

- `scripts/scrape.py` — raspa wzstats.gg. 5 modos: Resurgence, Multijugador (BO7),
  Resurgence Ranked, MP Ranked y Battle Royale. Saca tier, puesto por categoría,
  imagen y los accesorios de las 26 mejores armas separados por modo.
- `docs/index.html` — la app. Sin dependencias, sin build. Perfil (modo, estilo,
  mando/teclado, exclusiones) en localStorage.
- `docs/data/meta.json` — datos generados (~520 KB).
- `.github/workflows/update-meta.yml` — cron diario 06:10 UTC → scraper → commit → Pages.

## Decisiones tomadas

- Hosting: **GitHub Actions + Pages** (no hace falta que el PC esté encendido).
- **Sin stats personales**: la API de Activision no es pública y las no oficiales
  piden una cookie `ACT_SSO_COOKIE` que caduca cada ~14 días. Se descartó para que
  esto no necesite mantenimiento. El gamertag es solo etiqueta visual.
- Modos prioritarios del usuario: **Resurgence** y **Multijugador**.

## Detalles del scraping que costaron

- Warzone categoriza por alcance (`Long Range`), BO7 por tipo (`Assault Rifle`).
  El scraper normaliza ambos a `largo` / `corto` / `sniper` en el campo `role`.
- Hay **dos diseños** de ficha de arma: con `.playstyle-card` (FG42) y sin ella
  (KAR98K). El parser ancla en `ul.weapon-visual-no-image-container`, común a ambos.
- Hay que forzar `r.encoding = "utf-8"` o los nombres con acento se rompen (JÄGER 45).
- El primer bloque de la tier list no lleva cabecera: es el S tier.

## Pendiente

1. El usuario debe dar su **usuario de GitHub** (o instalar `gh`) para crear el repo.
2. Tras subirlo: Settings → Pages → Source = **GitHub Actions**, y
   Settings → Actions → Workflow permissions = **Read and write**.
3. Lanzar el workflow a mano una vez desde Actions.

## Entorno

`git` OK (hizo falta `git config --global --add safe.directory F:/COMPARTIDO/Claude/Warezone`
porque la unidad F: pertenece a otro usuario). Python 3.13 OK. **Node no instalado**,
**`gh` no instalado** — ninguno de los dos hace falta, el workflow corre en la nube.
