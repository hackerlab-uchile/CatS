chrome.runtime.sendMessage({ type: "getFilteredURLs" }, response => {
    if (response && response.urls) {
        const currentHostname = window.location.hostname;
        response.urls.forEach(({ url, action }) => {
            let storedHostname = new URL(url).hostname;
            if (currentHostname.endsWith(storedHostname)) {
                if (action === "alertar") {
                    alert("Página de contenido sensible. Proceda con precaución.");
                } else if (action === "notificar") {
                    chrome.runtime.sendMessage({ type: "notify", message: `Advertencia: Estás visitando ${currentHostname}` });
                } else if (action === "bloquear") {
                    window.location.href = "about:blank";
                }
            }
        });
    }
});

