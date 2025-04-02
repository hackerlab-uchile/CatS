//
//chrome.runtime.sendMessage({ type: "notify", message: "Página de contenido sensible detectada." });
// Cargar la lista de URLs sensibles
fetch(chrome.runtime.getURL("sensitive_urls.json"))
    .then(response => response.json())
    .then(sensitiveUrls => {
        const currentHostname = window.location.hostname;
        const sensitiveDomains = sensitiveUrls.map(url => {
          // Extrae el dominio base, por ejemplo: "ilovepdf.com"
          const parser = document.createElement('a');
          parser.href = url;
          return parser.hostname;
        });
        
        if (sensitiveDomains.some(domain => currentHostname.endsWith(domain))) {
          alert("Página de contenido sensible. Proceda con precaución.");
        }
    });
