/*
const urlsToBlock = [
  "https://example.com",
  "https://www.u-cursos.cl",
  "https://another-site.org"
];
*/

fetch(chrome.runtime.getURL("blocked_urls.json"))  //Read the json with the urls to block
  .then(response => response.json())
  .then(urlsToBlock => {
    const dynamicRules = urlsToBlock.map((url, index) => ({
      id: index + 1,
      priority: 1,
      action: { type: "block" },
      condition: {
        urlFilter: url,
        resourceTypes: ["main_frame"]
      }
    }));

    //Dynamic addition of rules
    chrome.declarativeNetRequest.updateDynamicRules(
      {
        addRules: dynamicRules,
        removeRuleIds: dynamicRules.map(rule => rule.id)
      },
      () => {
        if (chrome.runtime.lastError) {
          console.error("Error al actualizar reglas:", chrome.runtime.lastError);
        } else {
          console.log("Reglas dinámicas agregadas exitosamente.");
        }
      }
    );
  });