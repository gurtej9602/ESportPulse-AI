// Global state
const appState = {
  apiKeySet: false,
  currentMatch: null,
  reports: [],
  selectedGame: null,
  matchInProgress: false,
  matchTimeouts: [],
  currentUser: null,
  isAuthenticated: false,
}

// Game data
const gameData = {
  cs2: { name: "Counter-Strike 2", icon: "🎯" },
  valorant: { name: "Valorant", icon: "⚡" },
  pubg: { name: "PUBG", icon: "🏝️" },
  freefire: { name: "Free Fire", icon: "🔥" },
  cod: { name: "Call of Duty", icon: "💥" },
  apex: { name: "Apex Legends", icon: "🚀" },
  lol: { name: "League of Legends", icon: "⚔️" },
  dota2: { name: "Dota 2", icon: "🛡️" },
}

// Open app - show authentication screen
function openApp() {
  const landingScreen = document.getElementById("landingScreen")
  const authScreen = document.getElementById("authScreen")

  landingScreen.classList.add("hidden")
  authScreen.classList.add("active")
}

// Switch between login and register tabs
function switchAuthTab(tab) {
  const loginTab = document.querySelector(".auth-tab:first-child")
  const registerTab = document.querySelector(".auth-tab:last-child")
  const loginForm = document.getElementById("loginForm")
  const registerForm = document.getElementById("registerForm")

  // Clear any previous status
  hideAuthStatus()
  clearFormErrors()

  if (tab === "login") {
    loginTab.classList.add("active")
    registerTab.classList.remove("active")
    loginForm.classList.add("active")
    registerForm.classList.remove("active")
  } else {
    registerTab.classList.add("active")
    loginTab.classList.remove("active")
    registerForm.classList.add("active")
    loginForm.classList.remove("active")
  }
}

// Handle login
function handleLogin(event) {
  event.preventDefault()

  const username = document.getElementById("loginUsername").value.trim()
  const password = document.getElementById("loginPassword").value.trim()
  const loginBtn = document.getElementById("loginBtn")

  // Clear previous errors
  clearFormErrors()

  // Validation
  let hasErrors = false

  if (!username) {
    showFieldError("loginUsernameError", "Username is required")
    hasErrors = true
  }

  if (!password) {
    showFieldError("loginPasswordError", "Password is required")
    hasErrors = true
  }

  if (hasErrors) return

  // Simulate login process
  loginBtn.disabled = true
  loginBtn.innerHTML = "<span>🔄 Logging in...</span>"

  setTimeout(() => {
    // Simulate successful login (in real app, this would be an API call)
    if (username.length >= 3 && password.length >= 6) {
      appState.currentUser = {
        username: username,
        name: username,
      }
      appState.isAuthenticated = true

      showAuthStatus("✅ Login successful! Redirecting...", "success")

      setTimeout(() => {
        proceedToGameName()
      }, 1500)
    } else {
      showAuthStatus("❌ Invalid username or password", "error")
      loginBtn.disabled = false
      loginBtn.innerHTML = "<span>Login</span>"
    }
  }, 2000)
}

// Handle registration
function handleRegister(event) {
  event.preventDefault()

  const name = document.getElementById("registerName").value.trim()
  const username = document.getElementById("registerUsername").value.trim()
  const password = document.getElementById("registerPassword").value.trim()
  const confirmPassword = document.getElementById("confirmPassword").value.trim()
  const registerBtn = document.getElementById("registerBtn")

  // Clear previous errors
  clearFormErrors()

  // Validation
  let hasErrors = false

  if (!name) {
    showFieldError("registerNameError", "Full name is required")
    hasErrors = true
  }

  if (!username) {
    showFieldError("registerUsernameError", "Username is required")
    hasErrors = true
  } else if (username.length < 3) {
    showFieldError("registerUsernameError", "Username must be at least 3 characters")
    hasErrors = true
  }

  if (!password) {
    showFieldError("registerPasswordError", "Password is required")
    hasErrors = true
  } else if (password.length < 6) {
    showFieldError("registerPasswordError", "Password must be at least 6 characters")
    hasErrors = true
  }

  if (!confirmPassword) {
    showFieldError("confirmPasswordError", "Please confirm your password")
    hasErrors = true
  } else if (password !== confirmPassword) {
    showFieldError("confirmPasswordError", "Passwords do not match")
    hasErrors = true
  }

  if (hasErrors) return

  // Simulate registration process
  registerBtn.disabled = true
  registerBtn.innerHTML = "<span>🔄 Creating account...</span>"

  setTimeout(() => {
    // Simulate successful registration
    appState.currentUser = {
      username: username,
      name: name,
    }
    appState.isAuthenticated = true

    showAuthStatus("✅ Account created successfully! Redirecting...", "success")

    setTimeout(() => {
      proceedToGameName()
    }, 1500)
  }, 2500)
}

// Show field error
function showFieldError(errorId, message) {
  const errorElement = document.getElementById(errorId)
  errorElement.textContent = message
  errorElement.classList.add("show")
}

// Clear form errors
function clearFormErrors() {
  const errors = document.querySelectorAll(".form-error")
  errors.forEach((error) => {
    error.classList.remove("show")
    error.textContent = ""
  })
}

// Show auth status
function showAuthStatus(message, type) {
  const authStatus = document.getElementById("authStatus")
  authStatus.textContent = message
  authStatus.className = `auth-status ${type} show`
}

// Hide auth status
function hideAuthStatus() {
  const authStatus = document.getElementById("authStatus")
  authStatus.classList.remove("show")
}

// Proceed to game name input
function proceedToGameName() {
  const authScreen = document.getElementById("authScreen")
  const gameNameScreen = document.getElementById("gameNameScreen")

  authScreen.classList.remove("active")
  gameNameScreen.classList.add("active")
}

// Enter dashboard
function enterDashboard() {
  const gameName = document.getElementById("gameNameInput").value.trim()

  if (!gameName) {
    // Add shake animation to input
    const input = document.getElementById("gameNameInput")
    input.style.animation = "shake 0.5s ease-in-out"
    input.focus()
    setTimeout(() => {
      input.style.animation = ""
    }, 500)
    return
  }

  // Set the selected game
  appState.selectedGame = gameName.toLowerCase().replace(/\s+/g, "")

  const gameNameScreen = document.getElementById("gameNameScreen")
  const appContainer = document.getElementById("appContainer")
  const selectedGameSubtitle = document.getElementById("selectedGameSubtitle")

  // Update subtitle with entered game name and user
  selectedGameSubtitle.textContent = `🎮 ${gameName} Analytics - Welcome ${appState.currentUser.name}!`

  gameNameScreen.classList.remove("active")
  appContainer.classList.add("active")
}

// Start new match
function startNewMatch() {
  if (appState.matchInProgress) return

  appState.matchInProgress = true
  const beforeColumn = document.querySelector(".match-column:first-child .match-placeholder")
  const afterColumn = document.querySelector(".match-column:last-child .match-placeholder")
  const startBtn = document.getElementById("startMatchBtn")
  const stopBtn = document.getElementById("stopMatchBtn")

  // Show stop button, hide start button
  startBtn.style.display = "none"
  stopBtn.classList.add("visible")

  // Add loading animation
  beforeColumn.classList.add("loading")
  beforeColumn.innerHTML = '<div style="color: var(--accent-primary); font-weight: 600;">🔄 Loading match data...</div>'
  afterColumn.innerHTML = '<div style="color: var(--text-muted);">⏳ Waiting for match completion...</div>'

  // Get game name from input or use default
  const gameName = document.getElementById("gameNameInput")?.value || "Your Game"

  // Simulate match data after delay
  const timeout1 = setTimeout(() => {
    if (!appState.matchInProgress) return

    beforeColumn.classList.remove("loading")
    beforeColumn.innerHTML = `
            <div style="font-size: 0.95rem; line-height: 1.5;">
                <div style="color: var(--accent-primary); font-weight: 700; margin-bottom: 0.5rem;">🎮 Team A vs Team B</div>
                <div style="color: var(--text-secondary);">🎯 Game: ${gameName}</div>
                <div style="color: var(--text-secondary);">🏆 Mode: Competitive</div>
                <div style="color: var(--success-color);">👥 Players: 10/10</div>
                <div style="color: var(--warning-color); margin-top: 0.5rem;">🔴 Match in progress...</div>
            </div>
        `

    // Simulate match completion
    const timeout2 = setTimeout(() => {
      if (!appState.matchInProgress) return

      afterColumn.innerHTML = ``
      updateGeminiAnalysis()
      updateReport()

      // Reset buttons after match completion
      appState.matchInProgress = false
      startBtn.style.display = "block"
      stopBtn.classList.remove("visible")
    }, 3000)

    appState.matchTimeouts.push(timeout2)
  }, 1500)

  appState.matchTimeouts.push(timeout1)
}

// Stop match
function stopMatch() {
  if (!appState.matchInProgress) return

  appState.matchInProgress = false

  // Clear all timeouts
  appState.matchTimeouts.forEach((timeout) => clearTimeout(timeout))
  appState.matchTimeouts = []

  const beforeColumn = document.querySelector(".match-column:first-child .match-placeholder")
  const afterColumn = document.querySelector(".match-column:last-child .match-placeholder")
  const startBtn = document.getElementById("startMatchBtn")
  const stopBtn = document.getElementById("stopMatchBtn")

  // Reset UI
  beforeColumn.classList.remove("loading")
  beforeColumn.innerHTML = '<div style="color: var(--text-muted);">Pre-match data will appear here</div>'
  afterColumn.innerHTML = '<div style="color: var(--text-muted);">Post-match results will appear here</div>'

  // Reset buttons
  startBtn.style.display = "block"
  stopBtn.classList.remove("visible")

  // Clear analysis and report
  const geminiResults = document.querySelector(".gemini-results")
  const reportBox = document.getElementById("reportBox")

  geminiResults.innerHTML = "Gemini AI predictions and analysis will appear here"
  reportBox.innerHTML =
    '<div class="report-placeholder">Match statistics and detailed reports will be displayed here</div>'
}

// Submit API key
function submitApiKey() {
  const apiInput = document.getElementById("apiKeyInput")
  const apiStatus = document.getElementById("apiStatus")
  const apiKey = apiInput.value.trim()

  if (!apiKey) {
    showApiStatus("Please enter a Gemini API key", "error")
    return
  }

  // Simulate API validation
  apiStatus.style.display = "block"
  apiStatus.textContent = "🔄 Validating Gemini API key..."
  apiStatus.className = "api-status"

  setTimeout(() => {
    if (apiKey.length >= 8) {
      showApiStatus("✅ Gemini API key validated successfully", "success")
      appState.apiKeySet = true
      apiInput.value = "" // Clear input for security
    } else {
      showApiStatus("❌ Invalid Gemini API key format", "error")
    }
  }, 2000)
}

// Show API status
function showApiStatus(message, type) {
  const apiStatus = document.getElementById("apiStatus")
  apiStatus.style.display = "block"
  apiStatus.textContent = message
  apiStatus.className = `api-status ${type}`

  if (type === "success") {
    setTimeout(() => {
      apiStatus.style.display = "none"
    }, 4000)
  }
}

// Update Gemini AI analysis
function updateGeminiAnalysis() {
  const geminiResults = document.querySelector(".gemini-results")
  const gameName = document.getElementById("gameNameInput")?.value || "Your Game"

  geminiResults.innerHTML = ``
}

// Update report
function updateReport() {
  const reportBox = document.getElementById("reportBox")
  const gameName = document.getElementById("gameNameInput")?.value || "Your Game"

  const reportData = ``
  reportBox.innerHTML = reportData
}

// Export report
function exportReport() {
  const exportBtn = document.querySelector(".export-btn")
  const originalText = exportBtn.textContent

  exportBtn.textContent = "📤 Exporting..."
  exportBtn.disabled = true
  exportBtn.style.opacity = "0.7"

  setTimeout(() => {
    exportBtn.textContent = "✅ Exported!"
    setTimeout(() => {
      exportBtn.textContent = originalText
      exportBtn.disabled = false
      exportBtn.style.opacity = "1"
    }, 1500)
  }, 2500)
}

// Handle Enter key for various inputs
document.addEventListener("DOMContentLoaded", () => {
  // API input enter key
  const apiInput = document.getElementById("apiKeyInput")
  if (apiInput) {
    apiInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        submitApiKey()
      }
    })
  }

  // Game name input enter key
  const gameNameInput = document.getElementById("gameNameInput")
  if (gameNameInput) {
    gameNameInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        enterDashboard()
      }
    })
  }

  // Form submissions
  const loginForm = document.getElementById("loginForm")
  const registerForm = document.getElementById("registerForm")

  if (loginForm) {
    loginForm.addEventListener("submit", handleLogin)
  }

  if (registerForm) {
    registerForm.addEventListener("submit", handleRegister)
  }

  // Add enhanced hover effects
  const sections = document.querySelectorAll(".section")
  sections.forEach((section) => {
    section.addEventListener("mouseenter", function () {
      this.style.borderColor = "var(--accent-primary)"
    })

    section.addEventListener("mouseleave", function () {
      this.style.borderColor = "var(--border-color)"
    })
  })
})
