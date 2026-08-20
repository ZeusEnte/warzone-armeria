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

## Publicado y funcionando

- Repo: https://github.com/ZeusEnte/warzone-armeria (público)
- Web: https://zeusente.github.io/warzone-armeria/
- Pages → Source = GitHub Actions ✅ · Actions → Read and write ✅
- Run #1 en verde: el bot ya hizo su primer commit automático (`bbbdb07`),
  o sea que el ciclo raspar → commit → desplegar funciona solo.

El push necesitó que el usuario aprobara la ventana del Git Credential Manager
("Connect to GitHub" → Browser). La credencial queda guardada, los siguientes
push ya no preguntan. Ojo: el bot commitea sobre `main`, así que **antes de
pushear en local hay que hacer `git pull --rebase`**.

## Pendiente / sin verificar

- **La vista móvil no está comprobada.** El `@media (max-width:640px)` de
  `docs/index.html` está escrito pero nunca se vio renderizado: `resize_window`
  no llegó a aplicarse al viewport en las pruebas.
- El usuario debería cambiar su contraseña de GitHub: la pegó en texto plano
  en el chat el 2026-08-20.

## Entorno

`git` OK (hizo falta `git config --global --add safe.directory F:/COMPARTIDO/Claude/Warezone`
porque la unidad F: pertenece a otro usuario). Python 3.13 OK. **Node no instalado**,
**`gh` no instalado** — ninguno de los dos hace falta, el workflow corre en la nube.
