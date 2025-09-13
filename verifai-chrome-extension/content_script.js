// Listen for messages from popup.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getSelection") {
    // Return the currently selected text on the page
    sendResponse(window.getSelection().toString());
  }
});
