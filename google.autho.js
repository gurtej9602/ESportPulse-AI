function handleCredentialResponse(response) {
  const token = response.credential;

  fetch("https://oauth2.googleapis.com/tokeninfo?id_token=" + token)
    .then(res => res.json())
    .then(data => {
      console.log("Google User:", data);

      // Update global state from main script
      if (typeof appState !== "undefined") {
        appState.currentUser = {
          username: data.email,
          name: data.name,
          picture: data.picture,
        };
        appState.isAuthenticated = true;
      }

      const statusBox = document.getElementById("authStatus");
      if (statusBox) {
        statusBox.textContent = "✅ Google Login successful! Redirecting...";
        statusBox.className = "auth-status success show";
      }

      setTimeout(() => {
        if (typeof proceedToGameName === "function") {
          proceedToGameName();
        }
      }, 1500);
    })
    .catch((err) => {
      console.error("Google login error:", err);
      const statusBox = document.getElementById("authStatus");
      if (statusBox) {
        statusBox.textContent = "❌ Google login failed";
        statusBox.className = "auth-status error show";
      }
    });
}
