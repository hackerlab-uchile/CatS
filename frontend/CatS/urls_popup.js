function sanitize(input) {
  const div = document.createElement('div');
  div.innerText = input;
  return div.innerHTML;
}

document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.local.get("urlsToShow", (data) => {
    const container = document.getElementById("urlList");
    const title = document.getElementById("title");

    if (!data || !data.urlsToShow) {
      container.textContent = "No se encontraron URLs.";
      return;
    }

    const { community, tag, urls } = data.urlsToShow;
    const safeCommunityName = sanitize(community);
    const safeTagName = sanitize(tag);
    title.textContent = `URLs para ${safeTagName} en ${safeCommunityName}`;

    if (urls.length === 0) {
      container.textContent = "No hay URLs asociadas.";
    } else {
      container.textContent = urls.join("\n");
    }
  });
});
