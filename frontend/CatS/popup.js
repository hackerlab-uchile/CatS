const API_BASE = "http://localhost:8000";
const communitySelect = document.getElementById("communitySelect");
const communityDescription = document.getElementById("communityDescription");
const tagSelect = document.getElementById("tagSelect");
const tagDescription = document.getElementById("tagDescription");
const statusMessage = document.getElementById("statusMessage");

let communities = []; // Save to access the name
const subscriptionsList = document.getElementById("subscriptionsList");
let subsVisible = false;

// Load communities and populate select
async function loadCommunities() {
    const response = await fetch(`${API_BASE}/communities/`);
    communities = await response.json();

    communitySelect.innerHTML = "";
    for (const community of communities) {
        const option = document.createElement("option");
        option.value = community.id;
        option.textContent = `${community.name}`;
        communitySelect.appendChild(option);
    }

    // Trigger tag loading
    if (communities.length > 0) {
        updateCommunityDescription(communitySelect.value);
        loadTags(communitySelect.value);
    }
}

// Update community description
function updateCommunityDescription(selectedId) {
    const selected = communities.find(c => c.id == selectedId);
    communityDescription.textContent = selected ? selected.description : "";
}

// Update tag descrption
function updateTagDescription(selectedTagId, tags) {
    const selected = tags.find(t => t.id == selectedTagId);
    if (selected) {
        if (selected.action == 'alert') {action_name= 'Alertar'}
        else if (selected.action == 'block') {action_name= 'Bloquear'}
        else if (selected.action == 'notify') {action_name= 'Notificar'}
        const actionText = ` (acción: ${action_name})`;
        tagDescription.textContent = `${selected.description}${actionText}`;
    } else {
        tagDescription.textContent = "";
    }
}


// Load tags and populate select
async function loadTags(communityId) {
    const response = await fetch(`${API_BASE}/communities/${communityId}/tags`);
    const tags = await response.json();

    tagSelect.innerHTML = "";

    for (const tag of tags) {
        const option = document.createElement("option");
        option.value = tag.id;
        option.textContent = tag.name;
        tagSelect.appendChild(option);
    }
    if (tags.length > 0) {
        updateTagDescription(tagSelect.value, tags);
    }

    // add an disabled option for visual difference between tag options and "Todos sus tag" option
    const separatorOption = document.createElement("option");
    separatorOption.disabled = true;
    separatorOption.textContent = "────────────";
    tagSelect.appendChild(separatorOption);

    // Add option "Todos"
    const allOption = document.createElement("option");
    allOption.value = "ALL_TAGS";
    allOption.textContent = "🌐 Todos sus Tags";
    tagSelect.appendChild(allOption);

    // Update description when changing tag selection
    tagSelect.addEventListener("change", () => {
        if (tagSelect.value === "ALL_TAGS") {
            tagDescription.textContent = "Suscribirse a todos los tags de esta comunidad.";
        } else {
            updateTagDescription(tagSelect.value, tags);
        }
    });
    // Saves tags in memory for use in loadBtn
    tagSelect.dataset.allTags = JSON.stringify(tags); // Guardar como string
}


// Change in community -> load associated tags
communitySelect.addEventListener("change", () => {
    updateCommunityDescription(communitySelect.value);
    loadTags(communitySelect.value);
});


// Button to load and save the list
document.getElementById("loadBtn").addEventListener("click", async () => {
    const communityId = communitySelect.value;
    const tagId = tagSelect.value;
    const communityName = communitySelect.options[communitySelect.selectedIndex]?.text;
    const tagName = tagSelect.options[tagSelect.selectedIndex]?.text;

    if (!communityId || !tagId) {
        statusMessage.style.color = "red";
        statusMessage.textContent = "Debes seleccionar una comunidad y un tag.";
        return;
    }

    if (tagId === "ALL_TAGS") {
        const allTags = JSON.parse(tagSelect.dataset.allTags || "[]");

        if (allTags.length === 0) {
            statusMessage.style.color = "red";
            statusMessage.textContent = "❌ No se encontraron tags para esta comunidad.";
            return;
        }

        for (const tag of allTags) {
            chrome.runtime.sendMessage({
                type: "fetchAndStoreURLs",
                communityId: parseInt(communityId),
                tagId: tag.id,
                communityName,
                tagName: tag.name
            });
        }

        statusMessage.style.color = "green";
        statusMessage.textContent = `✅ Todos los tags de "${communityName}" fueron suscritos.`;
    } else {
        // Send message to background.js
        chrome.runtime.sendMessage({
            type: "fetchAndStoreURLs",
            communityId: parseInt(communityId),
            tagId: parseInt(tagId),
            communityName,
            tagName
        }, (response) => {
            if (response?.status === "success") {
                statusMessage.style.color = "green";
                statusMessage.textContent = `✅ URLs de "${tagName}" en "${communityName}" guardadas exitosamente.`;
            } else {
                statusMessage.style.color = "red";
                statusMessage.textContent = "❌ Error al guardar las URLs.";
            }
        });
    }

    setTimeout(() => {
        statusMessage.textContent = "";
    }, 5000);
});


// reset button with confirmation
document.getElementById("resetBtn").addEventListener("click", () => {
    const confirmed = confirm("¿Estás segurx que deseas eliminar todas tus subscripciones y tags subscritos?");
    if (!confirmed) return;

    chrome.runtime.sendMessage({ type: "resetEverything" }, (response) => {
        if (response.status === "success") {
            statusMessage.style.color = "green";
            statusMessage.textContent = "🧹 Se eliminaron URLs y reglas.";
            subscriptionsList.innerHTML = "";
            subsVisible = false;
        } else {
            statusMessage.style.color = "red";
            statusMessage.textContent = "❌ Error al resetear.";
        }
        setTimeout(() => {
            statusMessage.textContent = "";
        }, 5000);
    });
});


// view subscriptions communities
document.getElementById("subscriptionsBtn").addEventListener("click", () => {
    if (subsVisible) {
        // Ocultar si ya está visible
        subscriptionsList.innerHTML = "";
        subsVisible = false;
        return;
    }

    chrome.runtime.sendMessage({ type: "getSubscriptions" }, (response) => {
        subscriptionsList.innerHTML = "";

        if (!response || !Array.isArray(response.urls) || response.urls.length === 0) {
            subscriptionsList.style.color = "gray";
            subscriptionsList.textContent = "No hay suscripciones activas.";
        } else {
            const uniqueSubs = new Map();
            for (const entry of response.urls) {
                const key = `${entry.community_id}-${entry.tag_id}`;
                if (!uniqueSubs.has(key)) {
                    uniqueSubs.set(key, {
                        community_id: entry.community_id,
                        community_name: entry.community_name,
                        tag_id: entry.tag_id,
                        tag_name: entry.tag_name
                    });
                }
            }

            for (const [key, data] of uniqueSubs.entries()) {
                const container = document.createElement("div");
                container.style.marginTop = "8px";

                const label = document.createElement("span");
                label.textContent = `• ${data.community_name} → ${data.tag_name}`;
                label.style.marginRight = "6px";

                // View URLs button
                const viewBtn = document.createElement("button");
                viewBtn.textContent = "Ver URLs";
                viewBtn.style.fontSize = "11px";
                viewBtn.style.padding = "2px 6px";
                viewBtn.style.marginRight = "4px";
                viewBtn.style.backgroundColor = "#3C3B6E";
                viewBtn.style.color = "white";
                viewBtn.addEventListener("click", () => {
                    chrome.runtime.sendMessage({
                        type: "getSubscriptions"
                    }, (response) => {
                        if (!response || !response.urls) return;
                        const filtered = response.urls.filter(
                            u => u.community_id == data.community_id && u.tag_id == data.tag_id
                        );

                        // Temporarily save data in chrome.storage.local
                        chrome.storage.local.set({
                            urlsToShow: {
                                community: data.community_name,
                                tag: data.tag_name,
                                urls: filtered.map(u => u.url)
                            }
                        }, () => {
                            // Open new popup window
                            chrome.windows.create({
                                url: chrome.runtime.getURL("urls_popup.html"),
                                type: "popup",
                                width: 500,
                                height: 300
                            });
                        });
                    });
                });

                // Unsubscribe button
                const btn = document.createElement("button");
                btn.textContent = "Desubscribir";
                btn.style.fontSize = "11px";
                btn.style.padding = "2px 6px";
                btn.style.backgroundColor = "#6D3B47"
                btn.style.color = "white"
                btn.addEventListener("click", () => {
                    const confirmed = confirm(`¿Estás segurx de que deseas desuscribirte de "${data.tag_name}" en "${data.community_name}"?`);
                    if (!confirmed) return;

                    chrome.runtime.sendMessage({
                        type: "unsubscribe",
                        community_id: data.community_id,
                        tag_id: data.tag_id
                    }, (res) => {
                        if (res.status === "success") {
                            label.textContent = "🧹 Desuscrito";
                            btn.remove();
                            viewBtn.remove();
                        } else {
                            alert("Error al desubscribir.");
                        }
                    });
                });

                container.appendChild(label);

                // Crear un contenedor para los botones
                const btnGroup = document.createElement("div");
                btnGroup.style.display = "flex";
                btnGroup.style.gap = "8px"; // Espacio entre botones
                btnGroup.style.marginTop = "4px";

                // Botón Ver URLs (asegúrate de haberlo creado antes)
                viewBtn.style.flex = "1";
                viewBtn.style.fontSize = "11px";
                viewBtn.style.padding = "2px 6px";
                viewBtn.style.backgroundColor = "#4A6FA5";
                viewBtn.style.color = "white";

                // Botón Desubscribir (ya creado como `btn`)
                btn.style.flex = "1";

                // Añadir ambos botones al contenedor
                btnGroup.appendChild(viewBtn);
                btnGroup.appendChild(btn);

                // Añadir al contenedor principal
                container.appendChild(btnGroup);
                subscriptionsList.appendChild(container);

            }
        }

        subsVisible = true;
    });
});


// Initialize on popup opening
loadCommunities();