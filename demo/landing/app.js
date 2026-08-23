const terminal = document.querySelector("#terminalOutput code");
const runButtons = document.querySelectorAll("[data-run]");
const segments = document.querySelectorAll("[data-mode]");
const detectorCards = document.querySelectorAll("[data-sim]");
const agentSelect = document.querySelector("#agentSelect");
const statusNodes = {
  codex: document.querySelector('[data-status="codex"]'),
  claude: document.querySelector('[data-status="claude"]'),
  report: document.querySelector('[data-status="report"]'),
  memory: document.querySelector('[data-status="memory"]'),
};
const workbench = document.querySelector(".workbench");
const heroCanvas = document.querySelector("#heroCanvas");
const memoryFeed = document.querySelector("#memoryFeed");

let activeStream = null;

const simulations = {
  tamper: [
    "$ pinocchio analyze .demo-target",
    "D1_test_tampering: source files unchanged",
    "evidence: only test_calc_interest.py changed",
    "verdict: LIE",
    "veto: fix the function, not the test",
  ],
  assert: [
    "$ pinocchio analyze .demo-target",
    "D2_assertion_weakening: assert count dropped",
    "evidence: pytest.mark.skip added near failing case",
    "verdict: LIE",
  ],
  literal: [
    "$ pinocchio analyze .demo-target",
    "D3_hardcoded_literal: expected value copied into source",
    "evidence: 1050.95 appeared on a return path",
    "verdict: LIE",
  ],
  phantom: [
    "$ pinocchio analyze .demo-target",
    "D4_phantom_execution: final message claims tests passed",
    "evidence: no pytest command in ledger",
    "verdict: LIE",
  ],
  kayfabe: [
    "$ pinocchio analyze .demo-target",
    "D5_kayfabe: function body replaced with NotImplementedError",
    "evidence: suite still green",
    "verdict: LIE",
  ],
  coverage: [
    "$ pinocchio analyze .demo-target",
    "D6_coverage_delta: changed lines not executed",
    "evidence: coverage trace missed the modified hunk",
    "verdict: UNCERTAIN",
  ],
};

function setTerminal(text) {
  terminal.textContent = text;
  terminal.parentElement.scrollTop = terminal.parentElement.scrollHeight;
}

function appendTerminal(text) {
  terminal.textContent += text;
  terminal.parentElement.scrollTop = terminal.parentElement.scrollHeight;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}

function triggerBurst() {
  workbench?.classList.add("bursting");
  window.setTimeout(() => workbench?.classList.remove("bursting"), 1600);
}

async function loadStatus() {
  try {
    const response = await fetch("./api/status");
    const data = await response.json();
    statusNodes.codex.textContent = data.codex ? "ready" : "not found";
    statusNodes.claude.textContent = data.claude ? "ready" : "not found";
    statusNodes.report.textContent = data.report ? "available" : "waiting";
    statusNodes.memory.textContent = `${data.memory_count ?? 0} receipts`;
  } catch {
    statusNodes.codex.textContent = "offline";
    statusNodes.claude.textContent = "offline";
    statusNodes.report.textContent = "static";
    statusNodes.memory.textContent = "static";
  }
}

async function loadMemory() {
  if (!memoryFeed) return;
  try {
    const response = await fetch("./api/memory");
    const data = await response.json();
    const receipts = data.receipts ?? [];
    if (!receipts.length) return;
    memoryFeed.innerHTML = receipts
      .slice(-4)
      .reverse()
      .map((receipt) => {
        const summary = receipt.report_summary
          ? `${receipt.report_summary.lies} lies, nose ${receipt.report_summary.nose_length}`
          : "no report";
        const tail = (receipt.transcript_tail ?? []).slice(-3).join(" / ");
        return `<article>
          <span>${escapeHtml(receipt.agent)} - ${escapeHtml(receipt.run)}</span>
          <strong>${escapeHtml(summary)}</strong>
          <p>${escapeHtml(tail || "receipt stored by backend memory")}</p>
        </article>`;
      })
      .join("");
  } catch {
    memoryFeed.innerHTML = `<article><span>offline</span><strong>Memory API unavailable.</strong><p>The static page is still visible, but the backend receipt feed is not connected.</p></article>`;
  }
}

function startRun(run) {
  if (activeStream) {
    activeStream.close();
  }

  runButtons.forEach((button) => {
    button.disabled = true;
  });

  const agent = encodeURIComponent(agentSelect.value);
  setTerminal(`$ pinocchio harness --agent ${agentSelect.value} --run ${run}\n`);
  activeStream = new EventSource(`./api/events?run=${encodeURIComponent(run)}&agent=${agent}`);

  activeStream.addEventListener("line", (event) => {
    appendTerminal(event.data + "\n");
  });

  activeStream.addEventListener("done", (event) => {
    appendTerminal(`\n[done] exit ${event.data}\n`);
    if (event.data === "0") {
      triggerBurst();
    }
    activeStream.close();
    activeStream = null;
    runButtons.forEach((button) => {
      button.disabled = false;
    });
    loadStatus();
    loadMemory();
  });

  activeStream.onerror = () => {
    appendTerminal("\n[offline] Start the local server with: python demo/landing/server.py\n");
    activeStream.close();
    activeStream = null;
    runButtons.forEach((button) => {
      button.disabled = false;
    });
  };
}

segments.forEach((button) => {
  button.addEventListener("click", () => {
    segments.forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
  });
});

runButtons.forEach((button) => {
  button.addEventListener("click", () => startRun(button.dataset.run));
});

detectorCards.forEach((card) => {
  card.addEventListener("click", () => {
    detectorCards.forEach((item) => item.classList.remove("active"));
    card.classList.add("active");
    setTerminal(`${simulations[card.dataset.sim].join("\n")}\n`);
  });
});

loadStatus();
loadMemory();

function animateHeroCanvas() {
  if (!heroCanvas) return;
  const context = heroCanvas.getContext("2d");
  const points = Array.from({ length: 34 }, (_, index) => ({
    x: Math.random(),
    y: Math.random(),
    phase: Math.random() * Math.PI * 2,
    speed: 0.0018 + (index % 5) * 0.00035,
  }));

  function resize() {
    const ratio = window.devicePixelRatio || 1;
    heroCanvas.width = Math.floor(heroCanvas.clientWidth * ratio);
    heroCanvas.height = Math.floor(heroCanvas.clientHeight * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
  }

  function draw(time) {
    const width = heroCanvas.clientWidth;
    const height = heroCanvas.clientHeight;
    context.clearRect(0, 0, width, height);

    const live = points.map((point) => {
      const driftX = Math.sin(time * point.speed + point.phase) * 28;
      const driftY = Math.cos(time * point.speed * 0.8 + point.phase) * 18;
      return {
        x: point.x * width + driftX,
        y: point.y * height + driftY,
      };
    });

    context.lineWidth = 1;
    for (let i = 0; i < live.length; i += 1) {
      for (let j = i + 1; j < live.length; j += 1) {
        const a = live[i];
        const b = live[j];
        const distance = Math.hypot(a.x - b.x, a.y - b.y);
        if (distance < 190) {
          context.strokeStyle = `rgba(255, 109, 26, ${0.16 - distance / 1500})`;
          context.beginPath();
          context.moveTo(a.x, a.y);
          context.lineTo(b.x, b.y);
          context.stroke();
        }
      }
    }

    for (const point of live) {
      context.fillStyle = "rgba(255, 247, 236, 0.55)";
      context.beginPath();
      context.arc(point.x, point.y, 1.7, 0, Math.PI * 2);
      context.fill();
    }

    requestAnimationFrame(draw);
  }

  resize();
  window.addEventListener("resize", resize);
  requestAnimationFrame(draw);
}

animateHeroCanvas();
