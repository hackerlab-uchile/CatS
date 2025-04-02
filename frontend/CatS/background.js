const DB_NAME = "FilteredURLsDB";
const DB_VERSION = 1;
const STORE_NAME = "urls";

// Abrir (o crear) la base de datos "urlDatabase" con un objectStore "urlList"
function openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        if (!db.objectStoreNames.contains(STORE_NAME)) {
        // Crea el objectStore con la clave 'url' y añade índices para 'tag', 'comunidad' y 'accion'
        const objectStore = db.createObjectStore(STORE_NAME, { keyPath: "url" });
        objectStore.createIndex("tag", "tag", { unique: false });
        objectStore.createIndex("community", "community", { unique: false });
        objectStore.createIndex("action", "action", { unique: false });
        }
      };
      request.onsuccess = (event) => resolve(event.target.result);
      request.onerror = (event) => reject(event.target.error);
    });
}
  
// Ejemplo de función para obtener todas las URL que deben notificar
async function getUrlsByAction(actionType) {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(STORE_NAME, "readonly");
        const store = transaction.objectStore(STORE_NAME);
        const index = store.index("action");
        const request = index.getAll(actionType);
        
        request.onsuccess = (event) => resolve(event.target.result);
        request.onerror = (event) => reject(event.target.error);
    });
}

async function addURL(url, tag, community, action) {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(STORE_NAME, "readwrite");
        const store = transaction.objectStore(STORE_NAME);
        const request = store.put({ url, tag, community, action });
        request.onsuccess = () => {
            console.log(`Agregado: ${url}`);
            resolve();
        };
        request.onerror = () => reject(request.error);
    });
}


// Obtener todas las URLs de IndexedDB
async function getAllURLs() {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(STORE_NAME, "readonly");
        const store = transaction.objectStore(STORE_NAME);
        const request = store.getAll();

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}
  
// Permitir que content.js consulte la base de datos
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "getFilteredURLs") {
        getAllURLs()
            .then(data => sendResponse({ urls: data }))
            .catch(error => sendResponse({ error }));
        return true; // Indica respuesta asincrónica
    }
});

self.addURL = addURL;
