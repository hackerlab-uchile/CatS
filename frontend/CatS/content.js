// function to sanitize inputs
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
            // temporarily saved in local database
            chrome.storage.local.set({
              block_msg: safeJustification,
              block_suffix: contextSuffix
            }, () => {
              console.log("Justificación guardada en storage:", safeJustification);
              console.log("Contexto guardado en storage:", contextSuffix);
              window.location.replace(chrome.runtime.getURL("block.html"));
            });
          }
        }
      }
    }
  } else {
    console.error("No se pudieron obtener las URLs desde background.js");
  }
});