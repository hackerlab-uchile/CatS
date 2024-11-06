// Lista de URLs en las que deseas mostrar el mensaje
const allowedUrls = [
    "https://www.mozilla.org/",
    "https://www.example.com/",
    // Agrega más URLs según sea necesario
];

// Verifica si la URL actual está en la lista
if (allowedUrls.some(url => window.location.href.startsWith(url))) {
    // Crea la caja de "Hello World"
    const helloBox = document.createElement("div");
    helloBox.textContent = "Hello World";
    helloBox.style.position = "fixed";
    helloBox.style.top = "10px";
    helloBox.style.right = "10px";
    helloBox.style.backgroundColor = "white";
    helloBox.style.color = "black";
    helloBox.style.padding = "10px";
    helloBox.style.border = "2px solid black";
    helloBox.style.zIndex = "1000";

    // Agrega la caja al documento
    document.body.appendChild(helloBox);
}