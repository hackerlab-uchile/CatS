document.body.style.border = "5px solid red";

// Cargar la lista de URLs sensibles
fetch(chrome.runtime.getURL("sensitive_urls.json"))
    .then(response => response.json())
    .then(sensitiveUrls => {
        const currentUrl = window.location.href;

        if (sensitiveUrls.includes(currentUrl)) {
            // Muestra una advertencia en el sitio
            alert("Página de contenido sensible. Proceda con precaución.");
        }
    });
