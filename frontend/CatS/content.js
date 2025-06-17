function sanitize(input) {
  const div = document.createElement('div');
  div.innerText = input;
  return div.innerHTML;
}

chrome.runtime.sendMessage({ type: "getFilteredURLs" }, (response) => {
  if (response?.urls) {
    const currentUrl = new URL(window.location.href);
    console.log("URLs cargadas en content.js:", response.urls);

    for (const entry of response.urls) {
      let entryUrl;
      try {
        entryUrl = new URL(entry.url);
      } catch (err) {
        console.warn("URL malformada:", entry.url);
        continue;
      }

      if (currentUrl.hostname === entryUrl.hostname) {
        if (!entryUrl.pathname || currentUrl.pathname.startsWith(entryUrl.pathname)) {
          console.log("Match encontrado:", entry.url);

          const action = entry.action;
          const safeJustification = sanitize(entry.justification);
          const safeCommunityName = sanitize(entry.community_name);
          const safeTagName = sanitize(entry.tag_name);
          const contextSuffix = `Comunidad: ${safeCommunityName} (ID: ${entry.community_id}, Tag: ${safeTagName}): `;

          if (action === "alert") {
              alert(safeJustification + "\n\n" + contextSuffix);
          }
          if (action === "notify") {
            chrome.runtime.sendMessage({
              type: "notify",
              message: safeJustification + "\n\n" + contextSuffix
            });
          }
          if (action === "block") {
            //chrome.runtime.sendMessage({
              //type: "block",
              //url: entry.url,
              //justification: safeJustification + "\n\n" + contextSuffix
              document.head.innerHTML = ''; // Vacía el head (quitar CSS original)
              document.body.innerHTML = `
                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100vh;background:black;color:white;text-align:center;font-family:sans-serif;">
                  <h1 style="font-size:3em;margin-bottom:0.5em;">🚫 Sitio Bloqueado</h1>
                  <p style="max-width:80%;font-size:1.2em;">${safeJustification}</p>
                  <p style="margin-top:2em;font-size:0.9em;opacity:0.6;">${contextSuffix}</p>
                </div>
              `;
              document.title = "Sitio bloqueado por CatS";
            //});
          }
        }
      }
    }
  } else {
    console.error("No se pudieron obtener las URLs desde background.js");
  }
});