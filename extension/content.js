const serverUrl = "http://localhost:8000/sendMessage";
const htmlUrl = chrome.runtime.getURL("injected.html");

let lastUrl = location.href;

function injectChat() {
  // Prevent duplicate injection
  if (document.getElementById("chatBtn")) return;

  fetch(htmlUrl)
    .then((response) => response.text())
    .then((htmlText) => {
      document.body.insertAdjacentHTML("beforeend", htmlText);

      const chatBtn = document.getElementById("chatBtn");
      const chatWindow = document.getElementById("chatWindow");
      const chatInput = document.getElementById("chatInput");
      const chatHistory = document.getElementById("chatHistory");
      const sendBtn = document.getElementById("sendBtn");

      chrome.storage.local.get(["chatMessages", "chatOpen"], (data) => {
        if (data.chatMessages) {
          chatHistory.innerHTML = data.chatMessages.join("");
          chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        if (data.chatOpen) {
          chatWindow.classList.add("active");
        }
      });

      chatBtn.addEventListener("click", () => {
        chatWindow.classList.toggle("active");
        chrome.storage.local.set({
          chatOpen: chatWindow.classList.contains("active"),
        });
      });

      async function sendMessage() {
        const msg = chatInput.value.trim();
        if (!msg) return;

        const userMsg = document.createElement("div");
        userMsg.innerHTML = `<strong>You:</strong> ${msg}`;
        chatHistory.appendChild(userMsg);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        chatInput.value = "";

        saveChatHistory();

        const botMsg = document.createElement("div");
        botMsg.innerHTML = `<strong>Bot:</strong> Thinking...`;
        chatHistory.appendChild(botMsg);

        const response = await fetch(serverUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: msg,
          }),
        });
        const result = await response.json();
        const message = result.message;

        // Typing effect
        let i = 0;
        function typeChar() {
          if (i <= message.length) {
            botMsg.innerHTML = `<strong>Bot:</strong> ${message.slice(0, i)}<span class="typing-cursor">|</span>`;
            chatHistory.scrollTop = chatHistory.scrollHeight;
            i++;
            setTimeout(typeChar, 30); // Adjust typing speed here (ms per char)
          } else {
            botMsg.innerHTML = `<strong>Bot:</strong> ${message}`;
            chatHistory.scrollTop = chatHistory.scrollHeight;
            saveChatHistory();
            window.location.reload();
          }
        }
        typeChar();
      }

      sendBtn.addEventListener("click", sendMessage);
      chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
      });

      function saveChatHistory() {
        const messages = Array.from(chatHistory.children).map(
          (el) => el.outerHTML
        );
        chrome.storage.local.set({ chatMessages: messages });
      }
    })
    .catch((err) => console.error(err));
}

// Initial injection
injectChat();

// Watch for URL changes
setInterval(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    injectChat();
  }
}, 500);