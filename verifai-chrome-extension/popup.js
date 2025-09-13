const checkBtn = document.getElementById("check-btn");
const copyBtn = document.getElementById("copy-btn");
const clearBtn = document.getElementById("clear-btn");
const darkModeToggle = document.getElementById("dark-mode-toggle");
const darkModeIcon = document.getElementById("dark-mode-icon");
const resultEl = document.getElementById("result");
const spinner = document.getElementById("spinner");
const helpIcon = document.getElementById("help-icon");
const helpPopup = document.getElementById("help-popup");

// UTILITIES
function animateResult(success = true) {
  resultEl.classList.remove("success", "error");
  void resultEl.offsetWidth; // reflow to restart animation
  resultEl.classList.add(success ? "success" : "error");
}

// DARK MODE SETUP WITH ICON TOGGLE AND BUTTON STYLE
function setDarkMode(isDark) {
  if (isDark) {
    document.body.classList.add("light-mode");
    resultEl.classList.add("light-mode");
    helpPopup.classList.add("light-mode");
    copyBtn.classList.add("light-mode");
    clearBtn.classList.remove("light-mode");
    // Set sun icon for light mode
    darkModeIcon.innerHTML = `
      <circle cx="12" cy="12" r="5" fill="none" stroke="currentColor" stroke-width="2"/>
      <g stroke="currentColor" stroke-width="2">
        <line x1="12" y1="1" x2="12" y2="3"/>
        <line x1="12" y1="21" x2="12" y2="23"/>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
        <line x1="1" y1="12" x2="3" y2="12"/>
        <line x1="21" y1="12" x2="23" y2="12"/>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
      </g>
    `;
  } else {
    document.body.classList.remove("light-mode");
    resultEl.classList.remove("light-mode");
    helpPopup.classList.remove("light-mode");
    copyBtn.classList.remove("light-mode");
    clearBtn.classList.remove("light-mode");
    // Set moon icon for dark mode
    darkModeIcon.innerHTML = `
      <path d="M21 12.79A9 9 0 1111.213 3a7 7 0 009.786 9.79z"/>
    `;
  }
  localStorage.setItem("verifai_dark_mode", isDark ? "1" : "0");
}

darkModeToggle.addEventListener("click", () => {
  const isCurrentlyLight = document.body.classList.contains("light-mode");
  setDarkMode(!isCurrentlyLight);
});

// Initialize theme on load
setDarkMode(localStorage.getItem("verifai_dark_mode") === "1");

// HELP POPUP TOGGLE
helpIcon.addEventListener("click", () => {
  if (helpPopup.style.display === "block") {
    helpPopup.style.display = "none";
    helpIcon.setAttribute("aria-expanded", "false");
  } else {
    helpPopup.style.display = "block";
    helpIcon.setAttribute("aria-expanded", "true");
  }
});

// CHECK BUTTON ACTION
checkBtn.addEventListener("click", () => {
  copyBtn.disabled = true;
  resultEl.textContent = "";
  spinner.style.display = "block";

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.tabs.sendMessage(
      tabs[0].id,
      { action: "getSelection" },
      (selection) => {
        if (!selection) {
          spinner.style.display = "none";
          resultEl.textContent = "No text selected! Please highlight some text.";
          animateResult(false);
          return;
        }

        fetch("http://localhost:5000/verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: selection }),
        })
          .then((resp) => resp.json())
          .then((data) => {
            spinner.style.display = "none";
            copyBtn.disabled = false;
            if (data.result) {
              resultEl.textContent = data.result;
              animateResult(true);
            } else {
              resultEl.textContent = "No result from server.";
              animateResult(false);
            }
          })
          .catch((err) => {
            spinner.style.display = "none";
            resultEl.textContent = "Error: " + err.message;
            animateResult(false);
          });
      }
    );
  });
});

// COPY BUTTON ACTION
copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(resultEl.textContent).then(() => {
    alert("Result copied to clipboard!");
  });
});

// CLEAR BUTTON ACTION with style reset
clearBtn.addEventListener("click", () => {
  resultEl.textContent = "Select some text on the page and press \"Check Selected Text\".";
  copyBtn.disabled = true;
  resultEl.classList.remove("success", "error", "light-mode");
  copyBtn.classList.remove("light-mode");
  clearBtn.classList.remove("light-mode");
});
