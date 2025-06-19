// fetches justifications and suffix from local database
document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.local.get(["block_msg", "block_suffix"], (result) => {
    document.getElementById("justification").textContent =
      result.block_msg || "Este sitio ha sido bloqueado.";
    document.getElementById("context").textContent =
      result.block_suffix || "";

    // clean after show
    chrome.storage.local.remove(["block_msg", "block_suffix"]);
  });
});
