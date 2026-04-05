const csrftoken = getCookie("csrftoken");

let timer = null;
let timeLeft = 25 * 60;
let startingTime = timeLeft;  // what reset returns to
let elapsedSeconds = 0;       // how long they've actually studied in this session
let totalPausedDuration = 0;
let startedAt = null;
let pausedAt = null;
let isRunning = false;

const timerElement = document.getElementById("timer");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn"); //Also the pause button. When the timer is running, it shows "Pause". When paused, it shows "Stop".
const subjectSelect = document.getElementById("subjectSelect");
const saveStatus = document.getElementById("saveStatus");

// ---------- UI: update timer ----------
function updateTimerDisplay() {
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, "0")}`;
}
updateTimerDisplay();

// ---------- Validate manual edit (only when not running) ----------
timerElement.addEventListener("blur", () => {
  if (isRunning) {
    updateTimerDisplay();
    return;
  }

  const userInput = timerElement.textContent.trim();
  const match = userInput.match(/^(\d{1,3}):(\d{2})$/);

  if (match) {
    const minutes = parseInt(match[1], 10);
    const seconds = parseInt(match[2], 10);

    if (minutes >= 0 && minutes <= 120 && seconds >= 0 && seconds <= 59) {
      timeLeft = minutes * 60 + seconds;
      startingTime = timeLeft;
      elapsedSeconds = 0;      // new session setup
      updateTimerDisplay();
      return;
    }
  }

  alert("Invalid format! Please use MM:SS (0–120 mins, 0–59 secs).");
  updateTimerDisplay();
});

// ---------- Save session to backend ----------
async function saveSession() {
  const subjectId = subjectSelect.value;
  const sessionType = subjectSelect.options[subjectSelect.selectedIndex].getAttribute("type") || "unknown";
  if (!subjectId) {
    saveStatus.textContent = "Pick a subject before saving.";
    saveStatus.className = "d-block mt-2 text-danger";
    return false;
  }

  if (elapsedSeconds <= 0) {
    saveStatus.textContent = "Nothing to save yet.";
    saveStatus.className = "d-block mt-2 text-muted";
    return false;
  }

  try {
    const res = await fetch("/api/sessions/create/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({
        item_id: subjectId,
        duration_seconds: elapsedSeconds,
        session_type: sessionType,
      }),
    });

    const data = await res.json();

    if (!data.ok) {
      saveStatus.textContent = data.error || "Failed to save session.";
      saveStatus.className = "d-block mt-2 text-danger";
      return false;
    }

    saveStatus.textContent = "Saved ✅";
    saveStatus.className = "d-block mt-2 text-success";
    return true;
  } catch (e) {
    saveStatus.textContent = "Network/server error while saving.";
    saveStatus.className = "d-block mt-2 text-danger";
    return false;
  }
}

function syncTimer() {
  elapsedSeconds = Math.floor((Date.now() - startedAt - totalPausedDuration) / 1000);
  timeLeft = Math.max(0, startingTime - elapsedSeconds);
  updateTimerDisplay();
  return timeLeft;
}

async function endTimer() {
  await saveSession();
  // Reset the timer
  clearInterval(timer);
  timer = null;
  timeLeft = startingTime;
  elapsedSeconds = 0;
  startedAt = null;
  pausedAt = null;
  totalPausedDuration = 0;
  updateTimerDisplay();
  stopBtn.textContent = "Stop";
  isRunning = false;
};

// ---------- Start ----------
startBtn.addEventListener("click", () => {
  if (isRunning) return;

  // If timer is at 0, reset first
  if (timeLeft <= 0) {
    timeLeft = startingTime;
    elapsedSeconds = 0;
    updateTimerDisplay();
  }
  if (pausedAt !== null && startedAt !== null) {
    totalPausedDuration += Date.now() - pausedAt;
    pausedAt = null;
  }
  if (startedAt === null) {
    startedAt = Date.now();
  }
  isRunning = true;
  stopBtn.textContent = "Pause";
  saveStatus.textContent = "";

timer = setInterval(async () => {
    const remaining = syncTimer();
    if (remaining <= 0) {
        isRunning = false;
        await endTimer();
        alert("Time's up!");
    }
}, 1000);
});

// ---------- Pause / Stop ----------
stopBtn.addEventListener("click", async () => {
  if (isRunning) {
    // Pause
    pausedAt = Date.now();
    clearInterval(timer);
    timer = null;
    isRunning = false;
    stopBtn.textContent = "Stop";
    return;
  }
  // Reset the timer
  await endTimer();
});

document.addEventListener("visibilitychange", async () => {
  if (document.visibilityState === "visible" && isRunning) {
    // Tab is back in focus, sync the display immediately
    const timeRemaining = syncTimer();
    if (timeRemaining <= 0) {
      await endTimer();
    }
  }
});