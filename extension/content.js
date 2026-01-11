const serverUrl = "http://localhost:8000/sendMessage"
const htmlUrl = chrome.runtime.getURL("injected.html");

fetch(htmlUrl)
  .then((response) => response.text())
  .then((htmlText) => {
    // Inject the HTML string into the body
    document.body.insertAdjacentHTML("beforeend", htmlText);

    // --------------------------------------------------------
    // Event Listeners
    // --------------------------------------------------------

    const chatBtn = document.getElementById("chatBtn");
    const chatWindow = document.getElementById("chatWindow");
    const chatInput = document.getElementById("chatInput");
    const chatHistory = document.getElementById("chatHistory");
    const sendBtn = document.getElementById("sendBtn");

    // Toggle chat window on click
    chatBtn.addEventListener("click", () => {
      chatWindow.classList.toggle("active");
    });

    // Send message function
    async function sendMessage() {
      const msg = chatInput.value.trim();
      if (!msg) return;

      // Add user message to chat history
      const userMsg = document.createElement("div");
      userMsg.innerHTML = `<strong>You:</strong> ${msg}`;
      chatHistory.appendChild(userMsg);
      chatHistory.scrollTop = chatHistory.scrollHeight;
      chatInput.value = "";

      // Get response
      const response = await fetch(serverUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          "message": msg,
        }),
      });
      const result = await response.json();

      // Add response message to chat history
      const botMsg = document.createElement("div");
      botMsg.innerHTML = `<strong>Bot:</strong> ${result}`;
      chatHistory.appendChild(botMsg);
      chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") sendMessage();
    });
  })
  .catch((err) => console.error(err));
