const API_BASE = "http://localhost:8000";
const communitySelect = document.getElementById("communitySelect");
const communityDescription = document.getElementById("communityDescription");
const tagSelect = document.getElementById("tagSelect");
const tagDescription = document.getElementById("tagDescription");
const statusMessage = document.getElementById("statusMessage");

let communities = []; // Save to access the name

// Load communities and populate select
async function loadCommunities() {
    const response = await fetch(`${API_BASE}/communities/`);
    communities = await response.json();

    communitySelect.innerHTML = "";
    for (const community of communities) {
        const option = document.createElement("option");
        option.value = community.id;
        option.textContent = `${community.name} (ID: ${community.id})`;
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
    tagDescription.textContent = selected ? selected.description : "";
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

    // Update description when changing tag selection
    tagSelect.addEventListener("change", () => {
        updateTagDescription(tagSelect.value, tags);
    });
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
        setTimeout(() => {
            statusMessage.textContent = "";
        }, 5000);
    });
});


// Initialize on popup opening
loadCommunities();