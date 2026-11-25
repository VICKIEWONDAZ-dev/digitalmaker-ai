// Application State
let appState = {
  chatgptAccounts: [],
  googleflowAccounts: [],
  selectedStyle: "Cinematic Realism",
  selectedRatio: "9:16",
  inputMode: "topic", // "topic" or "custom_script"
  currentStoryboard: null,
  currentProject: null
};

document.addEventListener("DOMContentLoaded", () => {
  initUIEvents();
  fetchAccounts();
});

// ---------------- UI Event Handlers ----------------

function initUIEvents() {
  // Style cards
  const styleCards = document.querySelectorAll(".style-card");
  styleCards.forEach(card => {
    card.addEventListener("click", () => {
      styleCards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      appState.selectedStyle = card.getAttribute("data-style");
    });
  });

  // Aspect ratio buttons
  const ratioBtns = document.querySelectorAll(".ratio-btn");
  ratioBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      ratioBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      appState.selectedRatio = btn.getAttribute("data-ratio");
    });
  });
}

function useSuggestion(text) {
  document.getElementById("topicInput").value = text;
}

function toggleFlowAuthFields() {
  const authType = document.getElementById("flowAuthTypeSelect").value;
  const tokenGroup = document.getElementById("flowTokenGroup");
  const apiKeyGroup = document.getElementById("flowApiKeyGroup");

  if (authType === "session_cookie") {
    tokenGroup.classList.remove("hidden");
    apiKeyGroup.classList.add("hidden");
  } else {
    tokenGroup.classList.add("hidden");
    apiKeyGroup.classList.remove("hidden");
  }
}

// ---------------- Modal & Accounts Logic ----------------

function openAccountsModal(targetTab = "all") {
  const modal = document.getElementById("accountsModal");
  modal.classList.remove("hidden");
  if (targetTab === "chatgpt") switchModalTab("chatgpt");
  else if (targetTab === "flow") switchModalTab("flow");
}

function closeAccountsModal() {
  document.getElementById("accountsModal").classList.add("hidden");
}

function switchModalTab(tab) {
  const tabChatgptBtn = document.getElementById("tabChatgptBtn");
  const tabFlowBtn = document.getElementById("tabFlowBtn");
  const paneChatgpt = document.getElementById("paneChatgpt");
  const paneFlow = document.getElementById("paneFlow");

  if (tab === "chatgpt") {
    tabChatgptBtn.classList.add("active");
    tabFlowBtn.classList.remove("active");
    paneChatgpt.classList.add("active");
    paneFlow.classList.remove("active");
  } else {
    tabChatgptBtn.classList.remove("active");
    tabFlowBtn.classList.add("active");
    paneChatgpt.classList.remove("active");
    paneFlow.classList.add("active");
  }
}

async function fetchAccounts() {
  try {
    const res = await fetch("/api/accounts");
    const data = await res.json();
    appState.chatgptAccounts = data.chatgpt_accounts || [];
    appState.googleflowAccounts = data.google_flow_accounts || [];

    renderHeaderAccountPills();
    renderAccountLists();
  } catch (err) {
    console.error("Failed to load accounts:", err);
  }
}

function renderHeaderAccountPills() {
  const activeGpt = appState.chatgptAccounts.find(a => a.is_active);
  const activeFlow = appState.googleflowAccounts.find(a => a.is_active);

  const gptLabel = document.getElementById("activeChatgptLabel");
  const flowLabel = document.getElementById("activeFlowLabel");

  gptLabel.innerText = activeGpt ? activeGpt.label : "Add Account";
  flowLabel.innerText = activeFlow ? activeFlow.label : "Add Account";
}

function renderAccountLists() {
  // Render ChatGPT Accounts
  const gptList = document.getElementById("chatgptAccountList");
  if (appState.chatgptAccounts.length === 0) {
    gptList.innerHTML = `<p style="color: #64748b; font-size: 13px; text-align: center; padding: 10px;">No ChatGPT accounts added yet.</p>`;
  } else {
    gptList.innerHTML = appState.chatgptAccounts.map(acc => `
      <div class="account-item ${acc.is_active ? 'active' : ''}">
        <div class="account-info">
          <strong>${acc.label} ${acc.is_active ? '<span class="badge">Active</span>' : ''}</strong>
          <span>Model: ${acc.model} | Key: ${acc.masked_key}</span>
        </div>
        <div class="account-actions">
          ${!acc.is_active ? `<button class="btn btn-outline" onclick="setActiveAccount('chatgpt', '${acc.id}')">Set Active</button>` : ''}
          <button class="btn btn-outline" style="color: #ef4444;" onclick="deleteAccount('chatgpt', '${acc.id}')">Delete</button>
        </div>
      </div>
    `).join("");
  }

  // Render Google Flow Accounts
  const flowList = document.getElementById("googleflowAccountList");
  if (appState.googleflowAccounts.length === 0) {
    flowList.innerHTML = `<p style="color: #64748b; font-size: 13px; text-align: center; padding: 10px;">No Google Flow accounts added yet.</p>`;
  } else {
    flowList.innerHTML = appState.googleflowAccounts.map(acc => `
      <div class="account-item ${acc.is_active ? 'active' : ''}">
        <div class="account-info">
          <strong>${acc.label} ${acc.is_active ? '<span class="badge">Active</span>' : ''}</strong>
          <span>${acc.auth_type === 'session_cookie' ? 'Session Token' : 'API Key'} | Credits: ~${acc.estimated_credits}</span>
        </div>
        <div class="account-actions">
          ${!acc.is_active ? `<button class="btn btn-outline" onclick="setActiveAccount('google-flow', '${acc.id}')">Set Active</button>` : ''}
          <button class="btn btn-outline" style="color: #ef4444;" onclick="deleteAccount('google-flow', '${acc.id}')">Delete</button>
        </div>
      </div>
    `).join("");
  }
}

async function addChatgptAccount() {
  const label = document.getElementById("gptLabelInput").value.trim();
  const apiKey = document.getElementById("gptApiKeyInput").value.trim();
  const model = document.getElementById("gptModelSelect").value;

  if (!apiKey) {
    alert("Please enter an OpenAI API Key.");
    return;
  }

  const res = await fetch("/api/accounts/chatgpt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label, api_key: apiKey, model, set_active: true })
  });
  const data = await res.json();
  if (data.success) {
    document.getElementById("gptLabelInput").value = "";
    document.getElementById("gptApiKeyInput").value = "";
    fetchAccounts();
  } else {
    alert(data.error || "Failed to add account");
  }
}

async function addGoogleFlowAccount() {
  const label = document.getElementById("flowLabelInput").value.trim();
  const email = document.getElementById("flowEmailInput").value.trim();
  const authType = document.getElementById("flowAuthTypeSelect").value;
  const token = document.getElementById("flowTokenInput").value.trim();
  const apiKey = document.getElementById("flowApiKeyInput").value.trim();
  const credits = document.getElementById("flowCreditsInput").value;

  if (!token && !apiKey) {
    alert("Please provide either a session token or an API key.");
    return;
  }

  const res = await fetch("/api/accounts/google-flow", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      label,
      email,
      auth_type: authType,
      session_token: token,
      api_key: apiKey,
      estimated_credits: credits,
      set_active: true
    })
  });
  const data = await res.json();
  if (data.success) {
    document.getElementById("flowLabelInput").value = "";
    document.getElementById("flowEmailInput").value = "";
    document.getElementById("flowTokenInput").value = "";
    document.getElementById("flowApiKeyInput").value = "";
    fetchAccounts();
  } else {
    alert(data.error || "Failed to add account");
  }
}

async function setActiveAccount(type, id) {
  const res = await fetch(`/api/accounts/${type}/active`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ account_id: id })
  });
  if (res.ok) fetchAccounts();
}

async function deleteAccount(type, id) {
  if (!confirm("Are you sure you want to remove this account?")) return;
  const res = await fetch(`/api/accounts/${type}/${id}`, { method: "DELETE" });
  if (res.ok) fetchAccounts();
}

function switchInputMode(mode) {
  appState.inputMode = mode;
  const topicBtn = document.getElementById("modeTopicBtn");
  const scriptBtn = document.getElementById("modeScriptBtn");
  const topicGroup = document.getElementById("topicInputGroup");
  const scriptGroup = document.getElementById("customScriptInputGroup");
  const btnText = document.getElementById("generateBtnText");

  if (mode === "topic") {
    topicBtn.classList.add("active");
    scriptBtn.classList.remove("active");
    topicGroup.classList.remove("hidden");
    scriptGroup.classList.add("hidden");
    if (btnText) btnText.innerText = "Generate Storyboard & Character Arc";
  } else {
    topicBtn.classList.remove("active");
    scriptBtn.classList.add("active");
    topicGroup.classList.add("hidden");
    scriptGroup.classList.remove("hidden");
    if (btnText) btnText.innerText = "Refine Script & Build Storyboard";
  }
}

// ---------------- Storyboard & Video Creation ----------------

async function generateStoryboard() {
  const isScriptMode = appState.inputMode === "custom_script";
  const content = isScriptMode
    ? document.getElementById("customScriptInput").value.trim()
    : document.getElementById("topicInput").value.trim();
  const charPref = document.getElementById("characterPrefInput").value.trim();
  const refinementStyle = isScriptMode ? document.getElementById("refinementSelect").value : "enhance_pacing";
  const generateBtn = document.getElementById("generateBtn");

  if (!content) {
    alert(isScriptMode ? "Please paste your script." : "Please enter a topic or concept for your video.");
    return;
  }

  // Ensure ChatGPT account exists
  const activeGpt = appState.chatgptAccounts.find(a => a.is_active);
  if (!activeGpt) {
    openAccountsModal("chatgpt");
    alert("Please add your ChatGPT (OpenAI) API Key first to generate scripts!");
    return;
  }

  generateBtn.disabled = true;
  generateBtn.innerHTML = isScriptMode
    ? `⏳ ChatGPT is refining your script & matching Google Flow characters...`
    : `⏳ ChatGPT is generating characters & scenes...`;

  try {
    const res = await fetch("/api/generate-storyboard", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        input_mode: appState.inputMode,
        content: content,
        style: appState.selectedStyle,
        aspect_ratio: appState.selectedRatio,
        character_preference: charPref,
        character_mode: document.getElementById("charModeSelect") ? document.getElementById("charModeSelect").value : "multi",
        refinement_style: refinementStyle
      })
    });
    const data = await res.json();
    if (data.success) {
      appState.currentStoryboard = data.storyboard;
      displayStoryboard(data.storyboard);
    } else {
      alert("Error: " + (data.error || "Failed to generate storyboard"));
    }
  } catch (err) {
    alert("Network error: " + err.message);
  } finally {
    generateBtn.disabled = false;
    const btnText = isScriptMode ? "Refine Script & Build Storyboard" : "Generate Storyboard & Character Arc";
    generateBtn.innerHTML = `<span class="btn-icon">⚡</span> <span id="generateBtnText">${btnText}</span>`;
  }
}

function displayStoryboard(sb) {
  document.getElementById("storyboardSection").classList.remove("hidden");
  document.getElementById("storyboardTitle").innerText = sb.project_title || "Project Storyboard";
  document.getElementById("storyboardSummary").innerText = sb.summary || "";

  // Render Multiple Characters Cast Grid
  const chars = sb.characters && sb.characters.length > 0 ? sb.characters : [sb.character || { name: "Protagonist", role: "Lead" }];
  const charCountBadge = document.getElementById("charCountBadge");
  if (charCountBadge) {
    charCountBadge.innerText = `${chars.length} Character${chars.length > 1 ? 's' : ''}`;
  }

  const charactersGrid = document.getElementById("charactersGrid");
  if (charactersGrid) {
    charactersGrid.innerHTML = chars.map((ch, idx) => `
      <div class="character-card">
        <div class="char-header">
          <div class="char-avatar">${idx === 0 ? '👤' : idx === 1 ? '🎭' : '✨'}</div>
          <div class="char-meta">
            <h4>${ch.name || 'Character'}</h4>
            <span class="char-role">${ch.role || 'Cast Member'}</span>
          </div>
        </div>
        ${ch.voice_tone ? `<div class="char-voice">🎙️ Tone: ${ch.voice_tone}</div>` : ''}
        <p class="char-desc">${ch.appearance_prompt || ''}</p>
      </div>
    `).join("");
  }

  // Scenes list
  const scenesContainer = document.getElementById("scenesContainer");
  scenesContainer.innerHTML = (sb.scenes || []).map(sc => {
    const featured = sc.featured_characters && sc.featured_characters.length > 0 ? sc.featured_characters.join(", ") : null;
    return `
      <div class="scene-card">
        <div class="scene-badge">Scene ${sc.scene_number}</div>
        <div class="scene-narration">
          ${sc.speaker ? `<div class="speaker-pill">🗣️ Speaker: ${sc.speaker}</div>` : ''}
          <h4>Spoken Line</h4>
          <p>"${sc.narration}"</p>
          ${featured ? `<div class="featured-chars-pill">👥 In Shot: ${featured}</div>` : ''}
        </div>
        <div class="scene-prompt">
          <h4>Google Flow (Veo) Prompt</h4>
          <p>${sc.flow_veo_prompt}</p>
          <span class="badge" style="margin-top: 6px;">🎥 ${sc.camera_motion || 'Cinematic'}</span>
        </div>
      </div>
    `;
  }).join("");

  // Smooth scroll
  document.getElementById("storyboardSection").scrollIntoView({ behavior: "smooth" });
}

async function createFlowProject() {
  if (!appState.currentStoryboard) return;

  const activeFlow = appState.googleflowAccounts.find(a => a.is_active);
  if (!activeFlow) {
    openAccountsModal("flow");
    alert("Please connect a Google Flow account first!");
    return;
  }

  const buildBtn = document.getElementById("buildVideoBtn");
  buildBtn.disabled = true;
  buildBtn.innerHTML = `🚀 Sending to Google Flow...`;

  try {
    // 1. Create project & character in Google Flow
    const res = await fetch("/api/create-flow-project", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ storyboard: appState.currentStoryboard })
    });
    const data = await res.json();
    if (!data.success) {
      alert("Google Flow Error: " + data.error);
      return;
    }

    const projectId = data.project.project_id;
    appState.currentProject = data.project;

    // Show result section
    document.getElementById("resultSection").classList.remove("hidden");
    document.getElementById("renderStatus").innerText = `Rendering scenes in Google Flow (${activeFlow.label}) and assembling with FFmpeg...`;
    document.getElementById("resultSection").scrollIntoView({ behavior: "smooth" });

    // 2. Trigger Assembly & Render
    const assembleRes = await fetch(`/api/projects/${projectId}/assemble`, { method: "POST" });
    const assembleData = await assembleRes.json();

    if (assembleData.success) {
      document.getElementById("renderStatus").innerText = "✅ Video Ready! Character Arc & Scenes successfully assembled.";
      const player = document.getElementById("finalVideoPlayer");
      player.src = assembleData.manifest.final_video_url;
      document.getElementById("downloadVideoBtn").href = assembleData.manifest.final_video_url;
    } else {
      alert("Assembly Error: " + assembleData.error);
    }

  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    buildBtn.disabled = false;
    buildBtn.innerHTML = `🚀 Send to Google Flow & Build Video`;
  }
}

function resetStudio() {
  document.getElementById("topicInput").value = "";
  if (document.getElementById("customScriptInput")) {
    document.getElementById("customScriptInput").value = "";
  }
  document.getElementById("characterPrefInput").value = "";
  document.getElementById("storyboardSection").classList.add("hidden");
  document.getElementById("resultSection").classList.add("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}
