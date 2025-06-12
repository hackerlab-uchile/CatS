const API_BASE = "http://localhost:8000";
const DB_NAME = "CatS_local_DB";
const DB_VERSION = 1;
const STORE_NAME = "urls_storage";

// Clean up dynamic rules on install or update
chrome.runtime.onInstalled.addListener(() => {
  chrome.declarativeNetRequest.getDynamicRules((rules) => {
    const ids = rules.map(rule => rule.id);
    if (ids.length > 0) {
      chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: ids }, () => {
        console.log("Dynamic rules cleaned on install/update:", ids);
      });
    }
  });
});

// Open (or create) database 
function openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;

        if (!db.objectStoreNames.contains(STORE_NAME)) {
        // Create the objectStore with the key 'url' and add index for 'tag_id', 'community_id', 'action' and 'justification'
        const objectStore = db.createObjectStore(STORE_NAME, { keyPath: "url_tag" });
        objectStore.createIndex("url", "url", { unique: false });
        objectStore.createIndex("tag_id", "tag_id", { unique: false });
        objectStore.createIndex("community_id", "community_id", { unique: false });
        objectStore.createIndex("action", "action", { unique: false });
        objectStore.createIndex("justification", "justification", { unique: false });
        objectStore.createIndex("community_name", "community_name", { unique: false });
        objectStore.createIndex("tag_name", "tag_name", { unique: false });

        }
      };
      request.onsuccess = (event) => resolve(event.target.result);
      request.onerror = (event) => reject(event.target.error);
    });
}

// Add url to indexedDB
async function addURL(url, tag_id, community_id, action, justification, community_name, tag_name) {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(STORE_NAME, "readwrite");
        const store = transaction.objectStore(STORE_NAME);
        const url_tag = `${url}|${tag_id}`;
        const request = store.put({
            url_tag,
            url,
            tag_id,
            community_id,
            action,
            justification,
            community_name,
            tag_name
        });
        request.onsuccess = () => {
            console.log(`Agregado: ${url}`);
            resolve();
        };
        request.onerror = () => reject(request.error);
    });
}

// Store all url list to indexedDB
async function fetchAndStoreURLs(communityId, tagId, communityName, tagName) {
    try {
        const response = await fetch(`${API_BASE}/communities/${communityId}/${tagId}/urls`);
        if (!response.ok) throw new Error("No se pudieron obtener las URLs");

        const urls = await response.json();

        for (const urlObj of urls) {
            await addURL(
                urlObj.url,
                tagId,
                communityId,
                urlObj.action,
                urlObj.justification,
                communityName,
                tagName
            );
        }

        console.log(`Se guardaron ${urls.length} URLs de la comunidad: ${communityName}, con tag: ${tagName}`);
    } catch (error) {
        console.error("Error al obtener y guardar URLs:", error);
    }
}

// ---------------------------------------- To execute actions -----------------------------------

// Get all URLs from IndexedDB
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

// Create an determinist id for the dinamic rules based on the url
function generateRuleIdFromUrl(url) {
    let hash = 0;
    for (let i = 0; i < url.length; i++) {
        hash = (hash << 5) - hash + url.charCodeAt(i);
        hash |= 0; // Converts to 32-bit int
    }
    return Math.abs(hash);
}


// Allow content.js to query the database
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "getFilteredURLs") {
        getAllURLs()
            .then(data => sendResponse({ urls: data }))
            .catch(error => sendResponse({ error }));
        return true; // indicate async response
    }
    if (message.type === "notify") {
        chrome.notifications.create({
            type: "basic",
            iconUrl: "icons/border-48.png", // CHANGE --------------------------------------!!!!!
            title: "CatS",
            message: message.message
        });
    }
    if (message.type === "block") {
        const urlToBlock = message.url;
        const justification = message.justification;
    
        chrome.notifications.create({
            type: "basic",
            iconUrl: "icons/border-48.png",
            title: "Sitio Bloqueado",
            message: `${justification}`
        });

        // delay before locking
        setTimeout(() => {
            chrome.declarativeNetRequest.updateDynamicRules({
                addRules: [{
                    id: generateRuleIdFromUrl(urlToBlock),
                    priority: 1,
                    action: { type: "block" },
                    condition: {
                        urlFilter: urlToBlock,
                        resourceTypes: ["main_frame"]
                    }
                }],
            });
        }, 200); // 200ms, ajustable
    
        return true;
    }    
    if (message.type === "fetchAndStoreURLs") {
        const { communityId, tagId, communityName, tagName } = message;
        fetchAndStoreURLs(communityId, tagId, communityName, tagName)
            .then(() => sendResponse({ status: "success" }))
            .catch((error) => {
                console.error("Error en fetchAndStoreURLs desde popup:", error);
                sendResponse({ status: "error", error: error.message });
            });
        return true;
    }

});

// Clear indexedDB 
async function clearIndexedDB() {
    const db = await openDatabase();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(STORE_NAME, "readwrite");
        const store = transaction.objectStore(STORE_NAME);
        const clearRequest = store.clear();

        clearRequest.onsuccess = () => resolve();
        clearRequest.onerror = () => reject(clearRequest.error);
    });
}

// Clear dinamic rules
async function removeAllDynamicRules() {
    return new Promise((resolve) => {
        chrome.declarativeNetRequest.getDynamicRules((rules) => {
            const ids = rules.map(rule => rule.id);
            if (ids.length > 0) {
                chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: ids }, resolve);
            } else {
                resolve();
            }
        });
    });
}


// Listen to new commands from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "resetEverything") {
        Promise.all([clearIndexedDB(), removeAllDynamicRules()])
            .then(() => sendResponse({ status: "success" }))
            .catch((err) => {
                console.error("Error al resetear:", err);
                sendResponse({ status: "error" });
            });
        return true;
    }

    if (message.type === "getSubscriptions") {
        getAllURLs()
            .then(urls => sendResponse({ status: "success", urls }))
            .catch(() => sendResponse({ status: "error" }));
        return true;
    }

    if (message.type === "unsubscribe") {
        const { community_id, tag_id } = message;

        openDatabase().then(db => {
            const transaction = db.transaction(STORE_NAME, "readwrite");
            const store = transaction.objectStore(STORE_NAME);
            const request = store.getAll();

            request.onsuccess = () => {
                const allItems = request.result;
                const toDelete = allItems.filter(item =>
                    item.community_id == community_id && item.tag_id == tag_id
                );

                const ruleIdsToRemove = toDelete.map(item => generateRuleIdFromUrl(item.url));

                for (const item of toDelete) {
                    store.delete(item.url_tag);
                }

                chrome.declarativeNetRequest.updateDynamicRules({
                    removeRuleIds: ruleIdsToRemove
                }, () => {
                    console.log("Reglas eliminadas:", ruleIdsToRemove);
                    sendResponse({ status: "success" });
                });
            };

            request.onerror = () => {
                sendResponse({ status: "error" });
            };
        });
        return true; // Keep message channel open
    }
});
