# Armería — qué armas usar en Warzone

Web estática que lee la tier list de [wzstats.gg](https://wzstats.gg/) una vez al día
y te dice con qué armas jugar según el modo y el estilo que marques.

No necesita servidor propio, ni base de datos, ni que tu PC esté encendido:
un cron de GitHub Actions raspa, hace commit del JSON y republica la página.

## Cómo funciona

```
.github/workflows/update-meta.yml   cron diario 06:10 UTC → scraper → commit → deploy a Pages
scripts/scrape.py                   raspa wzstats.gg y escribe docs/data/meta.json
docs/index.html                     la app (HTML+JS plano, sin build ni dependencias)
docs/data/meta.json                 los datos: 5 modos, tiers, puestos y accesorios
```

`meta.json` guarda, por cada modo:

- las armas con su **tier** (S/A/B/C/D) y su **puesto oficial** por categoría
  (`#1 Long Range`, `#2 Close Range`, `#1 Sniper`…),
- los **accesorios** de la build recomendada de las ~26 mejores armas, separados
  por modo (la build de Resurgence no es la de Battle Royale),
- un bloque `changes` con lo que **subió, bajó, entró o salió** respecto a la
  actualización anterior. De ahí sale el panel "Movimientos del meta".

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
python scripts/scrape.py          # regenera docs/data/meta.json
cd docs && python -m http.server  # http://localhost:8000
```

Abrir `docs/index.html` con doble clic **no** funciona: el navegador bloquea el
`fetch` del JSON en `file://`. Hay que servirlo.

## Límites que conviene tener claros

- Las recomendaciones salen de la **meta pública** y del perfil que marcas a mano
  (modo, estilo, mando o teclado), **no de tus partidas**. Activision no tiene API
  pública; las no oficiales exigen una cookie de sesión que caduca cada ~14 días,
  así que se dejaron fuera para que esto no necesite mantenimiento.
- El scraper depende del HTML de wzstats.gg. Si rediseñan la web, el parser puede
  dejar de encontrar armas; en ese caso **no sobrescribe** `meta.json` y la página
  sigue mostrando el último dato válido, pero el workflow falla y avisa.
- Una petición por página y 1,5 s de pausa entre ellas: unas 30 peticiones al día.
