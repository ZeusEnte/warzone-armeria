# Armería — qué armas usar en Warzone

Web estática que lee la tier list de [wzstats.gg](https://wzstats.gg/) una vez al día
y te dice con qué armas jugar según el modo y el estilo que marques, **con los
accesorios exactos**, el requisito de desbloqueo de cada uno y el código de canje
para pegar en el juego.

No necesita servidor propio, ni base de datos, ni que tu PC esté encendido:
un cron de GitHub Actions raspa, hace commit del JSON y republica la página.

**En marcha:** https://zeusente.github.io/warzone-armeria/

> Si vas a trabajar en este repo con Claude Code, empieza por
> [CLAUDE.md](CLAUDE.md): resume la arquitectura, cómo probarlo y las
> trampas del scraping.

## Cómo funciona

```
.github/workflows/update-meta.yml   cron diario 06:10 UTC → scraper → commit → deploy a Pages
scripts/scrape.py                   raspa wzstats.gg y escribe docs/data/meta.json
scripts/validar_meta.py             comprueba que el JSON generado tiene sentido
scripts/pruebas.py                  pruebas del parser y del validador, sin red
docs/index.html                     la app (HTML+JS plano, sin build ni dependencias)
docs/sw.js                          service worker: la app funciona sin cobertura
docs/data/meta.json                 los datos: 5 modos, tiers, puestos y accesorios
documentacion/                      informes y documentación técnica del proyecto
```

`meta.json` guarda, por cada modo:

- las armas con su **tier** (S/A/B/C/D) y su **puesto oficial** por categoría
  (`#1 Long Range`, `#2 Close Range`, `#1 Sniper`…),
- los **accesorios** de las ~66 armas de tier S y A, separados por modo (la build
  de Resurgence no es la de Battle Royale) y por variante (Recommended, LOW
  RECOIL, PRESTIGE…),
- el **requisito de desbloqueo de cada accesorio**: `Level 37`, `Armory`,
  `Prestige`, o el arma que hay que subir para conseguirlo,
- el **código de canje** de cada build, para pegarlo en el juego,
- el **nivel máximo** de cada arma,
- **desde cuándo lleva cada arma en su tier**, para saber si esa S es sólida o
  acaba de llegar,
- un bloque `changes` con lo que **subió, bajó, entró o salió** respecto a la
  actualización anterior. De ahí sale el panel "Movimientos del meta".

## Qué puedes hacer con ella

- **Tu equipamiento de hoy**: tres armas (corta, larga y francotirador) elegidas
  por modo, estilo de juego y si juegas con mando o con teclado.
- **Buscar cualquier arma** por nombre o por tipo, no solo las 20 mejores, y ver
  su build completa con los códigos de canje.
- **Marcar las que no tienes**: no es un descarte, es un «todavía no». El
  equipamiento del día solo usa las disponibles y el panel «A por la siguiente»
  ordena las que faltan por lo que te aportarían.
- **Comparar dos armas** lado a lado, con sus accesorios y un veredicto que te
  dice cuál encaja mejor con tu perfil **y por qué**.
- **Ver cuánto lleva un arma en su tier** («3 semanas en S»), que es lo que
  decide si merece la pena gastar horas subiéndola de nivel.
- **Instalarla en el móvil** (*Añadir a pantalla de inicio*) y consultarla
  **aunque no tengas cobertura**: guarda la última meta descargada.

## Puesta en marcha

1. Crear un repo en GitHub y subir esta carpeta.
2. En **Settings → Pages**, poner *Source* en **GitHub Actions**.
3. En **Settings → Actions → General → Workflow permissions**, marcar
   **Read and write permissions** (el bot necesita hacer commit del JSON).
4. Lanzar el workflow a mano una vez desde la pestaña **Actions**.

A partir de ahí se actualiza solo cada mañana.

## Uso en local

```bash
pip install -r scripts/requirements.txt

python scripts/pruebas.py         # pruebas del parser, sin red, en un segundo
python scripts/scrape.py          # ~4 min, ~70 peticiones. Regenera docs/data/meta.json
python scripts/validar_meta.py    # revisa que el JSON generado no sea basura

cd docs && python -m http.server  # http://localhost:8000
```

Abrir `docs/index.html` con doble clic **no** funciona: el navegador bloquea el
`fetch` del JSON en `file://`. Hay que servirlo.

Para tocar el parser sin lanzar los cinco modos y las ochenta fichas de arma:

```bash
python scripts/scrape.py --modo resurgence --sin-builds --simular
python scripts/scrape.py --help   # todas las opciones
```

Una ejecución parcial **nunca sobrescribe** `docs/data/meta.json`: para escribir
en otro sitio, `--salida prueba.json`.

## Qué armas tienes

wzstats publica el requisito de cada **accesorio**, pero en ninguna parte consta
qué **armas** posee un jugador concreto: depende de su pase de batalla, eventos y
paquetes comprados. Se resuelve a mano y sin fricción, con el botón «No la tengo»
de cada arma. Se guarda en el navegador de cada dispositivo, no sale de ahí.

## Cuando algo falla

- Si **un modo** no se puede leer, se conserva el dato del día anterior, la web
  lo avisa («se muestra el dato guardado del…») y la ejecución del workflow queda
  en rojo para que llegue el correo. La página se publica igual.
- Si **ningún** modo se puede leer, no se toca `meta.json` y la web sigue
  sirviendo el último dato bueno.
- Si el JSON generado no pasa `validar_meta.py`, no se commitea.
- Si el cron lleva más de 48 h sin actualizar, la web lo dice en cabecera.
- Si **wzranked.com** (de donde sale el nombre de la temporada) no contesta, se
  conserva el nombre anterior en vez de degradarlo a un texto genérico.
- Si una **ficha de arma** falla, se conservan sus accesorios del día anterior.

## Límites que conviene tener claros

- Las recomendaciones salen de la **meta pública** y del perfil que marcas a mano
  (modo, estilo, mando o teclado), **no de tus partidas**. Activision no tiene API
  pública; las no oficiales exigen una cookie de sesión que caduca cada ~14 días,
  así que se dejaron fuera para que esto no necesite mantenimiento.
- El scraper depende del HTML de wzstats.gg. Si rediseñan la web, el parser puede
  dejar de encontrar armas.
- Las **imágenes** de las armas las sirve wzstats y solo vienen en el HTML del
  tier S; las demás se recogen de las fichas que ya se descargan, así que el
  catálogo se completa solo con los días. Un arma recién salida puede tardar en
  tener foto.
- Una petición por página y 1,5 s de pausa entre ellas: unas 70 peticiones al día.
  Un push de código ya **no** vuelve a raspar, solo republica.
