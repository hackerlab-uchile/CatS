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
          const justification = entry.justification;
          const contextSuffix = `Comunidad: ${entry.community_name} (ID: ${entry.community_id}, Tag: ${entry.tag_name}): `;

          if (action === "alert") {
              alert(justification + "\n\n" + contextSuffix);
          }
          if (action === "notify") {
            chrome.runtime.sendMessage({
              type: "notify",
              message: justification + "\n\n" + contextSuffix
            });
          }
          if (action === "block") {
            chrome.runtime.sendMessage({
              type: "block",
              url: entry.url,
              justification: justification + "\n\n" + contextSuffix
            });
          }
        }
      }
    }
  } else {
    console.error("No se pudieron obtener las URLs desde background.js");
  }
});