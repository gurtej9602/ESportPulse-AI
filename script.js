// Cleaned and fixed complete script.js

const appState = {
  apiKeySet: true, // Set to true as key is hardcoded in backend
  currentMatch: null,
  reports: [],
  selectedGame: null,
  matchInProgress: false,
  currentUser: null,
  isAuthenticated: false,
  // geminiApiKey: null, // Removed as it's now hardcoded in backend
  lastGeminiResponse: null, // Store the last Gemini response for export
};

const gameData = {
  cs2: { name: "Counter-Strike 2", icon: "🎯" },
  valorant: { name: "Valorant", icon: "⚡" },
  pubg: { name: "PUBG", icon: "🏝️" },
  freefire: { name: "Free Fire", icon: "🔥" },
  cod: { name: "Call of Duty", icon: "💥" },
  apex: { name: "Apex Legends", icon: "🚀" },
  lol: { name: "League of Legends", icon: "⚔️" },
  dota2: { name: "Dota 2", icon: "🛡️" },
};

function openApp() {
  document.getElementById("landingScreen").classList.add("hidden");
  document.getElementById("landingScreen").style.display = "none";
  document.getElementById("authScreen").classList.add("active");
  document.getElementById("authScreen").style.display = "flex";
}

function switchAuthTab(tab) {
  hideAuthStatus();
  clearFormErrors();

  const loginTab = document.querySelector(".auth-tab:first-child");
  const registerTab = document.querySelector(".auth-tab:last-child");
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");

  if (tab === "login") {
    loginTab.classList.add("active");
    registerTab.classList.remove("active");
    loginForm.classList.add("active");
    registerForm.classList.remove("active");
  } else {
    registerTab.classList.add("active");
    loginTab.classList.remove("active");
    registerForm.classList.add("active");
    loginForm.classList.remove("active");
  }
}

function handleLogin(event) {
  event.preventDefault();
  clearFormErrors();

  const username = document.getElementById("loginUsername").value.trim();
  const password = document.getElementById("loginPassword").value.trim();
  const loginBtn = document.getElementById("loginBtn");

  if (!username || !password) {
    if (!username) showFieldError("loginUsernameError", "Username is required");
    if (!password) showFieldError("loginPasswordError", "Password is required");
    return;
  }

  loginBtn.disabled = true;
  loginBtn.innerHTML = "<span>🔄 Logging in...</span>";

  setTimeout(() => {
    appState.currentUser = { username, name: username };
    appState.isAuthenticated = true;
    showAuthStatus("✅ Login successful! Redirecting...", "success");
    loginBtn.disabled = false;
    loginBtn.innerHTML = "<span>Login</span>";
    setTimeout(proceedToGameName, 1500);
  }, 2000);
}

function handleRegister(event) {
  event.preventDefault();
  clearFormErrors();

  const name = document.getElementById("registerName").value.trim();
  const username = document.getElementById("registerUsername").value.trim();
  const password = document.getElementById("registerPassword").value.trim();
  const confirmPassword = document.getElementById("confirmPassword").value.trim();
  const registerBtn = document.getElementById("registerBtn");

  if (!name || !username || !password || !confirmPassword || password !== confirmPassword) {
    if (!name) showFieldError("registerNameError", "Full name is required");
    if (!username || username.length < 3) showFieldError("registerUsernameError", "Username must be at least 3 characters");
    if (!password || password.length < 6) showFieldError("registerPasswordError", "Password must be at least 6 characters");
    if (password !== confirmPassword) showFieldError("confirmPasswordError", "Passwords do not match");
    return;
  }

  registerBtn.disabled = true;
  registerBtn.innerHTML = "<span>🔄 Creating account...</span>";

  setTimeout(() => {
    appState.currentUser = { username, name };
    appState.isAuthenticated = true;
    showAuthStatus("✅ Account created successfully! Redirecting...", "success");
    registerBtn.disabled = false;
    registerBtn.innerHTML = "<span>Register</span>";
    setTimeout(proceedToGameName, 1500);
  }, 2500);
}

function showFieldError(id, message) {
  const el = document.getElementById(id);
  el.textContent = message;
  el.classList.add("show");
}

function clearFormErrors() {
  document.querySelectorAll(".form-error").forEach(e => {
    e.classList.remove("show");
    e.textContent = "";
  });
}

function showAuthStatus(message, type) {
  const el = document.getElementById("authStatus");
  el.textContent = message;
  el.className = `auth-status ${type} show`;
}

function hideAuthStatus() {
  document.getElementById("authStatus").classList.remove("show");
}

function proceedToGameName() {
  document.getElementById("authScreen").classList.remove("active");
  document.getElementById("authScreen").style.display = "none";
  document.getElementById("gameNameScreen").classList.add("active");
  document.getElementById("gameNameScreen").style.display = "flex";
}

function enterDashboard() {
  const gameName = document.getElementById("gameNameInput").value.trim();
  if (!gameName) {
    showMessageBox("Error", "Please enter a game name before proceeding.", "error");
    return;
  }

  appState.selectedGame = gameName.toLowerCase().replace(/\s+/g, "");
  document.getElementById("selectedGameSubtitle").textContent = `🎮 ${gameName} Analytics - Welcome ${appState.currentUser.name}!`;
  // FIX: Changed "gameNameNameScreen" to "gameNameScreen"
  document.getElementById("gameNameScreen").style.display = "none";
  document.getElementById("gameNameScreen").classList.remove("active"); // Also remove active class
  document.getElementById("appContainer").classList.add("active");
  document.getElementById("appContainer").style.display = "block";
}

function showMessageBox(title, message, type = "info") {
  let msgBox = document.getElementById("messageBox");
  if (!msgBox) {
    msgBox = document.createElement("div");
    msgBox.id = "messageBox";
    msgBox.className = "message-box";
    msgBox.innerHTML = `
      <div class="message-box-content">
        <h3 class="message-box-title"></h3>
        <p class="message-box-text"></p>
        <button class="message-box-close-btn">OK</button>
      </div>
    `;
    document.body.appendChild(msgBox);
    msgBox.querySelector(".message-box-close-btn").addEventListener("click", () => {
      msgBox.classList.remove("show");
    });
  }

  msgBox.querySelector(".message-box-title").textContent = title;
  msgBox.querySelector(".message-box-text").textContent = message;
  msgBox.classList.remove("info", "success", "error");
  msgBox.classList.add(type, "show");
}

async function startNewMatch() {
  const startBtn = document.getElementById('startMatchBtn');
  const stopBtn = document.getElementById('stopMatchBtn');
  const reportBox = document.getElementById('reportBox');

  reportBox.innerHTML = '<div class="report-placeholder">Starting match analysis...</div>';

  startBtn.disabled = true;
  startBtn.classList.add('btn-loading');
  startBtn.innerHTML = '<span>Starting...</span>';

  stopBtn.style.display = "block";
  stopBtn.classList.add("visible");
  stopBtn.disabled = false;

  try {
    const response = await fetch('/start-match', { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
      showMessageBox("Success", data.message, "success");
      appState.matchInProgress = true;
      reportBox.innerHTML = '<div class="report-placeholder">Recording and analyzing... This may take some time. Press "🛑 Stop Match" to terminate early and get results.</div>';
    } else {
      showMessageBox("Error", `Failed to start match: ${data.message}`, "error");
      startBtn.disabled = false;
      startBtn.classList.remove('btn-loading');
      startBtn.innerHTML = '<span>Start New Match</span>';
      stopBtn.style.display = "none";
      stopBtn.classList.remove("visible");
      stopBtn.disabled = true;
    }
  } catch (err) {
    console.error("Error starting match:", err);
    showMessageBox("Error", `Network error or server unavailable: ${err.message}`, "error");
    startBtn.disabled = false;
    startBtn.classList.remove('btn-loading');
    startBtn.innerHTML = '<span>Start New Match</span>';
    stopBtn.style.display = "none";
    stopBtn.classList.remove("visible");
    stopBtn.disabled = true;
  }
}

async function stopMatch() {
  const startBtn = document.getElementById('startMatchBtn');
  const stopBtn = document.getElementById('stopMatchBtn');
  const reportBox = document.getElementById('reportBox');

  stopBtn.disabled = true;
  stopBtn.classList.add('btn-loading');
  stopBtn.innerHTML = '<span>Stopping...</span>';
  reportBox.innerHTML = '<div class="report-placeholder">Stopping analysis and fetching report... Please wait.</div>';

  try {
    const response = await fetch('/stop', { method: 'GET' });
    const data = await response.json();

    if (response.ok) {
      showMessageBox("Success", data.message, "success");
      appState.matchInProgress = false;
      setTimeout(async () => {
        await fetchReport();
      }, 2500);
    } else {
      showMessageBox("Error", `Failed to stop match: ${data.message}`, "error");
    }
  } catch (err) {
    console.error("Error stopping match:", err);
    showMessageBox("Error", `Network error or server unavailable: ${err.message}`, "error");
  } finally {
    stopBtn.disabled = true;
    stopBtn.classList.remove('btn-loading');
    stopBtn.innerHTML = '<span>🛑 Stop Match</span>';
    stopBtn.style.display = "none";
    stopBtn.classList.remove("visible");

    startBtn.disabled = false;
    startBtn.classList.remove('btn-loading');
    startBtn.innerHTML = '<span>Start New Match</span>';
  }
}

async function fetchReport() {
  const reportBox = document.getElementById('reportBox');
  reportBox.innerHTML = '<div class="report-placeholder">Loading report...</div>';

  try {
    const response = await fetch('/get-report', { method: 'GET' });
    const data = await response.json();

    if (response.ok && data.report) {
      reportBox.textContent = data.report;
      document.querySelector('.gemini-results').textContent = "Gemini AI has analyzed the session and generated a detailed report.";
    } else {
      reportBox.innerHTML = `<div class="report-placeholder">${data.message || 'Report not available.'}</div>`;
      document.querySelector('.gemini-results').textContent = "Gemini AI analysis not available.";
    }
  } catch (err) {
    console.error("Error fetching report:", err);
    reportBox.innerHTML = `<div class="report-placeholder">Error loading report: ${err.message}. Please ensure the analysis completed or try again.</div>`;
    document.querySelector('.gemini-results').textContent = `Error in Gemini AI analysis: ${err.message}`;
  }
}

function exportReport() {
  const reportBox = document.getElementById("reportBox");
  const placeholderTexts = [
      "Match statistics and detailed reports will be displayed here",
      "Starting match analysis...",
      "Recording and analyzing...",
      "Stopping analysis and fetching report...",
      "Fetching report...",
      "Report not available.",
      "Error loading report:",
      "Loading report...",
      "Please provide the API key in the frontend."
  ];
  const currentContent = reportBox.textContent.trim();

  if (placeholderTexts.some(text => currentContent.includes(text)) || currentContent === "") {
      showMessageBox("Info", "No valid report available to export yet.", "info");
      return;
  }

  const blob = new Blob([reportBox.innerText], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "match_report.txt";
  a.click();
  URL.revokeObjectURL(a.href);
  showMessageBox("Success", "Match Report exported to match_report.txt!", "success");
}

// Removed submitApiKey function as API key is now hardcoded in backend
/*
async function submitApiKey() {
    // ... (removed content)
}
*/

// Function to send prompt to Gemini
async function sendGeminiPrompt() {
    const promptInput = document.getElementById('geminiPromptInput');
    const responseDiv = document.getElementById('geminiPromptResponse');
    const sendButton = document.getElementById('sendGeminiPromptBtn');
    const exportButton = document.getElementById('exportGeminiResponseBtn');
    const prompt = promptInput.value.trim();

    // No need to check appState.apiKeySet or appState.geminiApiKey here,
    // as the key is expected to be hardcoded in the backend.
    // The backend's /generate-gemini-text endpoint will handle key availability.

    if (!prompt) {
        showMessageBox("Error", "Please enter a prompt for Gemini.", "error");
        return;
    }

    responseDiv.textContent = "Asking Gemini... Please wait.";
    sendButton.disabled = true;
    sendButton.classList.add('btn-loading');
    sendButton.innerHTML = '<span>Asking...</span>';
    exportButton.style.display = 'none'; // Hide export button during new query

    try {
        const response = await fetch('/generate-gemini-text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ prompt: prompt }), // Send the prompt
        });
        const data = await response.json();

        if (response.ok && data.text) {
            responseDiv.textContent = data.text;
            appState.lastGeminiResponse = data.text; // Store for export
            exportButton.style.display = 'block'; // Show export button
            showMessageBox("Success", "Gemini responded!", "success");
        } else {
            responseDiv.textContent = data.message || "Failed to get response from Gemini.";
            appState.lastGeminiResponse = null;
            exportButton.style.display = 'none';
            showMessageBox("Error", data.message || "Error from Gemini API.", "error");
        }
    } catch (err) {
        console.error("Error asking Gemini:", err);
        responseDiv.textContent = `Network error or server unavailable: ${err.message}`;
        appState.lastGeminiResponse = null;
        exportButton.style.display = 'none';
        showMessageBox("Error", `Network error when asking Gemini: ${err.message}`, "error");
    } finally {
        sendButton.disabled = false;
        sendButton.classList.remove('btn-loading');
        sendButton.innerHTML = '<span>Ask Gemini</span>';
    }
}

// Function to export Gemini response
function exportGeminiResponse() {
    if (!appState.lastGeminiResponse) {
        showMessageBox("Info", "No Gemini response available to export.", "info");
        return;
    }

    const blob = new Blob([appState.lastGeminiResponse], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "gemini_response.txt";
    a.click();
    URL.revokeObjectURL(a.href);
    showMessageBox("Success", "Gemini response exported to gemini_response.txt!", "success");
}


document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("loginForm")?.addEventListener("submit", handleLogin);
  document.getElementById("registerForm")?.addEventListener("submit", handleRegister);

  document.getElementById('stopMatchBtn').style.display = "none";
  document.getElementById('stopMatchBtn').classList.remove("visible");

  // Add event listeners for Gemini prompt section
  document.getElementById('sendGeminiPromptBtn')?.addEventListener('click', sendGeminiPrompt);
  document.getElementById('exportGeminiResponseBtn')?.addEventListener('click', exportGeminiResponse);


  if (!document.getElementById('messageBoxStyle')) {
      const style = document.createElement('style');
      style.id = 'messageBoxStyle';
      style.innerHTML = `
          .message-box {
              position: fixed;
              top: 50%;
              left: 50%;
              transform: translate(-50%, -50%);
              background-color: var(--bg-card);
              border: 2px solid var(--border-color);
              border-radius: var(--border-radius);
              box-shadow: var(--shadow-lg);
              padding: 2rem;
              z-index: 1000;
              display: none;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              text-align: center;
              max-width: 400px;
              width: 90%;
              opacity: 0;
              transform: translate(-50%, -50%) scale(0.9);
              transition: opacity 0.3s ease-out, transform 0.3s ease-out;
          }
          .message-box.show {
              display: flex;
              opacity: 1;
              transform: translate(-50%, -50%) scale(1);
          }
          .message-box.info { border-color: var(--accent-tertiary); }
          .message-box.success { border-color: var(--success-color); }
          .message-box.error { border-color: var(--error-color); }

          .message-box-content {
              width: 100%;
          }

          .message-box-title {
              font-size: 1.8rem;
              font-weight: 700;
              margin-bottom: 0.75rem;
              background: var(--gradient-primary);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              background-clip: text;
          }
          .message-box.error .message-box-title {
              background: var(--gradient-danger);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              background-clip: text;
          }
          .message-box.success .message-box-title {
              background: linear-gradient(135deg, var(--success-color), #059669);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              background-clip: text;
          }
          .message-box.info .message-box-title {
              background: linear-gradient(135deg, var(--accent-tertiary), #0f766e);
              -webkit-background-clip: text;
              -webkit-text-fill-color: transparent;
              background-clip: text;
          }

          .message-box-text {
              color: var(--text-secondary);
              margin-bottom: 1.5rem;
              font-size: 1rem;
          }
          .message-box-close-btn {
              background: var(--gradient-primary);
              color: white;
              border: none;
              padding: 0.75rem 1.5rem;
              border-radius: var(--border-radius-sm);
              cursor: pointer;
              font-size: 0.9rem;
              font-weight: 600;
              transition: var(--transition);
          }
          .message-box-close-btn:hover {
              transform: translateY(-2px);
              box-shadow: 0 4px 10px rgba(79, 70, 229, 0.3);
          }

          @keyframes fadeInScale {
              from { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
              to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
          }
      `;
      document.head.appendChild(style);
  }
});
