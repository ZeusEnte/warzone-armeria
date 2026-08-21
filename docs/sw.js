/* Service worker de Armería.
 *
 * Objetivo: que la app instalada en el móvil siga sirviendo la última meta
 * descargada cuando no hay cobertura, sin quedarse nunca pegada a una versión
 * antigua cuando sí la hay.
 *
 * Estrategia:
 *   - HTML, JS y meta.json  -> red primero, caché como respaldo.
 *   - iconos y manifest     -> caché primero (no cambian y ahorran red).
 *
 * Al cambiar cualquier archivo de la web hay que subir VERSION: es lo que borra
 * la caché vieja y evita que un usuario se quede con la interfaz de antes.
 */
const VERSION = "armeria-v2";

// Lo mínimo para que la app arranque sin red. meta.json NO va aquí: se cachea
// solo cuando el usuario ya lo ha descargado una vez, y pesa 680 KB.
const BASICOS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/favicon.ico",
];

// Estos sí valen cacheados sin revalidar: no cambian de un día para otro.
const ES_ESTATICO = /\/(icons\/|manifest\.webmanifest$)/;

self.addEventListener("install", ev => {
  ev.waitUntil(
    caches.open(VERSION)
      // addAll aborta entero si un solo archivo falla; los metemos de uno en uno
      // para que un icono ausente no deje la app sin instalar.
      .then(c => Promise.all(BASICOS.map(u => c.add(u).catch(() => null))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", ev => {
  ev.waitUntil(
    caches.keys()
      .then(claves => Promise.all(claves.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", ev => {
  const req = ev.request;
  // Solo gestionamos lo nuestro: las imágenes de las armas viven en img.wzstats.gg
  // y las deja pasar el navegador como siempre.
  if(req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;

  if(ES_ESTATICO.test(new URL(req.url).pathname)){
    ev.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => guardar(req, res)))
    );
    return;
  }

  // Red primero: si hay conexión, siempre gana el dato fresco.
  ev.respondWith(
    fetch(req)
      .then(res => guardar(req, res))
      .catch(() => caches.match(req).then(hit => hit || caches.match("./index.html")))
  );
});

function guardar(req, res){
  if(res && res.ok && res.type === "basic"){
    const copia = res.clone();
    caches.open(VERSION).then(c => c.put(req, copia)).catch(() => {});
  }
  return res;
}
