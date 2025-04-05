chrome.runtime.sendMessage({ type: "getFilteredURLs" }, response => {
    if (response && response.urls) {
        const currentHostname = window.location.hostname;
        response.urls.forEach(({ url, action }) => {
            let storedHostname = new URL(url).hostname;
            if (currentHostname.endsWith(storedHostname)) {
                if (action === "alert") {
                    alert("Página de contenido sensible. Proceda con precaución.");
                } else if (action === "notify") {
                    chrome.runtime.sendMessage({ type: "notify", message: `Estás visitando ${currentHostname}` });
                } else if (action === "block") {                   
                    chrome.runtime.sendMessage({ type: "block", url})               
                } else if(action === "blockAndNotify"){
                    chrome.runtime.sendMessage({
                        type: "blockAndNotify",
                        url: url,
                        host: window.location.hostname
                    });
                    
                }
            }
        });
    }
});

