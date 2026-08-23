import {
  Activity,
  Blocks,
  Bot,
  CheckCircle2,
  CircleStop,
  Code2,
  Gamepad2,
  GitBranch,
  Play,
  RotateCcw,
  ShieldCheck,
  ZoomIn,
  ZoomOut,
  Sparkles,
  Terminal,
  Trophy,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import brandIcon from "../assets/brand-icon.png";
import heroImage from "../assets/pinocchio-hero.png";
import mascotImage from "../assets/mascot-verifier.png";
import mascotPixelImage from "../assets/mascot-verifier-pixel.png";

type RunKind = "demo" | "verify" | "loop-dry" | "loop-codex";
type AgentKind = "codex" | "claude" | "terminal";
type Verdict = "LIE" | "VERIFIED" | "UNCERTAIN" | string;

type StatusPayload = {
  codex: boolean;
  claude: boolean;
  report: boolean;
  memory_count: number;
  scenario_count?: number;
  codex_fallback?: boolean;
};

type Receipt = {
  captured_at: string;
  agent: string;
  run: string;
  transcript_tail?: string[];
  report_summary?: {
    lies: number;
    verified: number;
    uncertain: number;
    nose_length: number;
  };
};

type ScenarioIndexItem = {
  id: string;
  detector: string;
  lies: number;
  nose_length: number;
};

type ScenarioResult = {
  claim: string;
  verdict: Verdict;
  evidence: string;
  severity: number;
  check_type: string;
};

type Scenario = {
  id: string;
  headline_detector: string;
  agent_message: string;
  suite_before: string;
  suite_after: string;
  diff: string;
  report: {
    results: ScenarioResult[];
    summary: {
      total: number;
      lies: number;
      verified: number;
      uncertain: number;
      nose_length: number;
    };
  };
};

const scenarioLabels: Record<string, string> = {
  "test-tampering": "Move the goalposts",
  "assertion-weakening": "Skip the pain",
  "hardcoded-literal": "Paste the answers",
  kayfabe: "Hollow green check",
  "honest-fix": "Real fix",
};

const detectorToScenario: Record<string, string> = {
  D1: "test-tampering",
  D2: "assertion-weakening",
  D3: "hardcoded-literal",
  D4: "test-tampering",
  D5: "kayfabe",
  D6: "honest-fix",
};

const detectorCards = [
  ["D1", "Test tampering", "Claim says source fix. Diff only touches tests."],
  ["D2", "Assertion weakening", "Asserts disappear, skips appear, suite gets easier."],
  ["D3", "Hardcoded literal", "Expected values leak into implementation paths."],
  ["D4", "Phantom execution", "Agent claims tests ran. The ledger has to prove it."],
  ["D5", "Kayfabe tests", "The test turns green while exercising nothing useful."],
  ["D6", "Coverage delta", "Changed lines have to be hit before the claim ships."],
];

const loopSteps = [
  ["01", "Agent works", "Codex or Claude claims the fix is done."],
  ["02", "Evidence lands", "Diffs, tests, exits, and hook receipts become the board state."],
  ["03", "Detectors score", "D1-D6 look for fake fixes, hollow tests, and missing runs."],
  ["04", "Stop hook blocks", "A false ending becomes the next prompt instead of a final answer."],
];

const runLabels: Record<RunKind, string> = {
  demo: "Caught-cheat reel",
  verify: "Run verifier",
  "loop-dry": "Dry loop",
  "loop-codex": "Live Codex loop",
};

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Request failed: ${path}`);
  }
  return response.json() as Promise<T>;
}

function classForVerdict(verdict: Verdict) {
  return verdict.toLowerCase();
}

function scenarioTerminal(scenario: Scenario) {
  const rows = scenario.report.results
    .map((result) => {
      const verdict = result.verdict.padEnd(9);
      return `${verdict} ${result.check_type}: ${result.evidence}`;
    })
    .join("\n");

  return [
    `$ pinocchio play-round ${scenario.id}`,
    `agent says: "${scenario.agent_message}"`,
    `suite before: ${scenario.suite_before}`,
    `suite after:  ${scenario.suite_after}`,
    "",
    scenario.diff.trim().slice(0, 1600),
    "",
    `score: ${scenario.report.summary.lies} lies, ${scenario.report.summary.verified} verified, ${scenario.report.summary.uncertain} uncertain`,
    `nose: ${scenario.report.summary.nose_length} cm`,
    rows,
  ].join("\n");
}

function PinocchioAvatar({
  noseLength,
  zoom,
  rotation,
  pixelMode,
  scrollProgress,
}: {
  noseLength: number;
  zoom: number;
  rotation: number;
  pixelMode: boolean;
  scrollProgress: number;
}) {
  const lieScale = 1 + Math.min(0.18, noseLength / 90);
  const scrollScale = 1 - scrollProgress * 0.12;
  const scrollLift = scrollProgress * -20;
  const liveRotation = rotation + scrollProgress * 7;

  return (
    <div className={`pinocchio-avatar ${pixelMode ? "pixel-mode" : ""}`} aria-hidden="true">
      <div
        className="mascot-live-frame"
        style={{
          opacity: 1 - scrollProgress * 0.22,
          transform: `translateY(${scrollLift}px) rotate(${liveRotation}deg) scale(${zoom * lieScale * scrollScale})`,
        }}
      >
        <img
          alt=""
          className="mascot-live-image"
          src={pixelMode ? mascotPixelImage : mascotImage}
        />
        <span className="mascot-greeting">truth check live</span>
      </div>
      <div className="avatar-score">
        <Sparkles size={15} />
        nose {noseLength} cm
      </div>
    </div>
  );
}

function TerminalPane({
  output,
  streaming,
}: {
  output: string;
  streaming: boolean;
}) {
  const ref = useRef<HTMLPreElement | null>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [output]);

  return (
    <div className={`terminal-shell ${streaming ? "streaming" : ""}`}>
      <div className="verdict-stage">
        <div className="agent-chip">
          <Bot size={17} />
          Agent says fixed
        </div>
        <div className="evidence-beam">
          <span />
          <span />
          <span />
        </div>
        <div className="veto-chip">
          <CircleStop size={17} />
          Block or ship
        </div>
      </div>
      <div className="terminal-bar">
        <span />
        <span />
        <span />
        <strong>pinocchio live</strong>
      </div>
      <pre ref={ref} aria-live="polite">
        <code>{output}</code>
      </pre>
    </div>
  );
}

export function App() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [scenarioIndex, setScenarioIndex] = useState<ScenarioIndexItem[]>([]);
  const [scenarios, setScenarios] = useState<Record<string, Scenario>>({});
  const [activeScenarioId, setActiveScenarioId] = useState("test-tampering");
  const [agent, setAgent] = useState<AgentKind>("codex");
  const [mode, setMode] = useState("cheat");
  const [streaming, setStreaming] = useState(false);
  const [transitionTick, setTransitionTick] = useState(0);
  const [mascotZoom, setMascotZoom] = useState(1);
  const [mascotRotation, setMascotRotation] = useState(0);
  const [pixelMode, setPixelMode] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [terminalOutput, setTerminalOutput] = useState(
    `$ python demo/landing/server.py
ready: choose a round

PINOCCHIO watches:
  - changed files
  - test commands
  - detector verdicts
  - final agent claims
`,
  );

  const activeScenario = scenarios[activeScenarioId];
  const noseLength = activeScenario?.report.summary.nose_length ?? 16;
  const lieCount = activeScenario?.report.summary.lies ?? 2;
  const appStateClass = lieCount > 0 ? "lie-alert" : "truth-clear";

  const proofStats = useMemo(() => {
    const summary = activeScenario?.report.summary;
    return [
      ["Suite", activeScenario?.suite_after ?? "3 passed", "The cheap edit can make CI green."],
      ["Pinocchio", `${summary?.lies ?? 2} lies`, "The verifier scores the claim, not vibes."],
      ["Nose", `${summary?.nose_length ?? 16} cm`, "Severity becomes stage-visible."],
      ["Evidence", `${summary?.total ?? 5} checks`, "Diffs and tests anchor the verdict."],
    ];
  }, [activeScenario]);

  async function loadStatus() {
    try {
      setStatus(await getJson<StatusPayload>("/api/status"));
    } catch {
      setStatus({
        codex: false,
        claude: false,
        report: false,
        memory_count: 0,
        scenario_count: scenarioIndex.length,
      });
    }
  }

  async function loadMemory() {
    try {
      const payload = await getJson<{ receipts: Receipt[] }>("/api/memory");
      setReceipts(payload.receipts ?? []);
    } catch {
      setReceipts([]);
    }
  }

  async function loadScenario(id: string) {
    if (scenarios[id]) {
      setActiveScenarioId(id);
      setTerminalOutput(`${scenarioTerminal(scenarios[id])}\n`);
      return;
    }

    try {
      const payload = await getJson<{ scenario: Scenario | null }>(`/api/scenario?id=${encodeURIComponent(id)}`);
      if (!payload.scenario) {
        throw new Error("missing scenario");
      }
      setScenarios((current) => ({ ...current, [id]: payload.scenario! }));
      setActiveScenarioId(id);
      setTerminalOutput(`${scenarioTerminal(payload.scenario)}\n`);
    } catch {
      setTerminalOutput((current) => `${current}\n[scenario unavailable] ${id}\n`);
    }
  }

  async function loadScenarios() {
    try {
      const payload = await getJson<{ scenarios: ScenarioIndexItem[] }>("/api/scenarios");
      const list = payload.scenarios ?? [];
      setScenarioIndex(list);
      await loadScenario(list[0]?.id ?? "test-tampering");
    } catch {
      setScenarioIndex([]);
    }
  }

  function startRun(run: RunKind) {
    setStreaming(true);
    setTerminalOutput(`$ pinocchio harness --agent ${agent} --run ${run}\n`);

    if (run === "loop-codex") {
      setTerminalOutput((current) => `${current}Render-safe fallback is enabled when codex CLI is unavailable.\n`);
    }

    const stream = new EventSource(`/api/events?run=${encodeURIComponent(run)}&agent=${encodeURIComponent(agent)}`);

    stream.addEventListener("line", (event) => {
      setTerminalOutput((current) => `${current}${event.data}\n`);
    });

    stream.addEventListener("done", (event) => {
      setTerminalOutput((current) => `${current}\n[done] exit ${event.data}\n`);
      stream.close();
      setStreaming(false);
      void loadStatus();
      void loadMemory();
    });

    stream.onerror = () => {
      stream.close();
      setStreaming(false);
      setTerminalOutput((current) => `${current}\n[offline] Streaming API unavailable; switching to recorded scenario playback.\n`);
      void loadScenario(activeScenarioId);
    };
  }

  useEffect(() => {
    void loadStatus();
    void loadMemory();
    void loadScenarios();
    const timer = window.setInterval(() => {
      void loadStatus();
    }, 12000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!activeScenario) return;
    setTransitionTick((tick) => tick + 1);
  }, [activeScenarioId, activeScenario]);

  useEffect(() => {
    const update = () => {
      const progress = Math.min(1, Math.max(0, window.scrollY / 760));
      setScrollProgress(progress);
    };
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);

  return (
    <>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Pinocchio home">
          <span className="brand-mark image-mark">
            <img alt="" src={brandIcon} />
          </span>
          <span>Pinocchio</span>
        </a>
        <nav className="nav-links" aria-label="Primary">
          <a href="#arena">Proof</a>
          <a href="#harness">Harness</a>
          <a href="#pitch">Pitch</a>
          <a href="#ship">Ship</a>
        </nav>
        <a className="header-cta" href="#harness">
          <Play size={16} />
          Run demo
        </a>
      </header>

      <main className={`app-shell ${appStateClass}`} id="top">
        <section className="hero-section" aria-labelledby="hero-title">
          <img className="hero-image" src={heroImage} alt="" />
          <div className="hero-overlay" />
          <div className="hero-grid">
            <div className="hero-copy">
              <p className="eyebrow">YC demo build - Greptile Fast Hackathon</p>
              <h1 id="hero-title">Trust the agent. Verify the ending.</h1>
              <p className="hero-lede">
                AI code review checks the code. Pinocchio checks the agent's story. If Codex fakes green by moving tests, hardcoding outputs, or claiming phantom runs, the nose catches it before the lie ships.
              </p>
              <div className="hero-actions">
                <a className="button primary" href="#arena">
                  <Gamepad2 size={18} />
                  Play the lie
                </a>
                <a className="button secondary" href="#pitch">
                  <Trophy size={18} />
                  See the wedge
                </a>
              </div>
              <div className="proof-strip" aria-label="Product highlights">
                <span>Blocks false endings</span>
                <span>5 live cheat rounds</span>
                <span>Built for Codex workflows</span>
              </div>
            </div>

            <aside className="hero-console" aria-label="Live verifier summary">
              <div className="console-topline">
                <span className="status-dot live" />
                <span>agent turn intercepted</span>
                <span className="pill">live on Render</span>
              </div>
              <PinocchioAvatar
                key={`avatar-${transitionTick}-${pixelMode}`}
                noseLength={noseLength}
                pixelMode={pixelMode}
                rotation={mascotRotation}
                scrollProgress={scrollProgress}
                zoom={mascotZoom}
              />
              <div className="mascot-controls" aria-label="Mascot controls">
                <button
                  aria-label="Zoom mascot out"
                  onClick={() => setMascotZoom((value) => Math.max(0.78, Number((value - 0.08).toFixed(2))))}
                  type="button"
                >
                  <ZoomOut size={16} />
                </button>
                <button
                  aria-label="Rotate mascot"
                  onClick={() => setMascotRotation((value) => value + 18)}
                  type="button"
                >
                  <RotateCcw size={16} />
                </button>
                <button
                  aria-label="Zoom mascot in"
                  onClick={() => setMascotZoom((value) => Math.min(1.28, Number((value + 0.08).toFixed(2))))}
                  type="button"
                >
                  <ZoomIn size={16} />
                </button>
                <button
                  aria-pressed={pixelMode}
                  className={pixelMode ? "active" : ""}
                  onClick={() => setPixelMode((value) => !value)}
                  type="button"
                >
                  PX
                </button>
              </div>
              <div className="nose-meter" aria-label="Nose length">
                <span className="nose-face" />
                <span className="nose-bar">
                  <span style={{ width: `${Math.min(100, Math.max(10, noseLength * 5 + 8))}%` }} />
                </span>
                <strong>{noseLength} cm</strong>
              </div>
              <div className="claim-stack">
                <div className="claim-row lie">
                  <span>LIE</span>
                  <p>Claim contradicted by the diff.</p>
                </div>
                <div className="claim-row verified">
                  <span>OK</span>
                  <p>Every verdict cites a receipt.</p>
                </div>
                <div className="claim-row uncertain">
                  <span>?</span>
                  <p>No receipt means uncertain, not guessed.</p>
                </div>
              </div>
            </aside>
          </div>
        </section>

        <section className="ticker" aria-label="Positioning">
          <span>Code review asks if the code is good.</span>
          <span>Observability asks what the agent did.</span>
          <strong>Pinocchio asks if what the agent told you is true.</strong>
        </section>

        <section className="proof-board" aria-label="Live demo proof">
          {proofStats.map(([label, value, copy]) => (
            <article key={label} className={label === "Pinocchio" ? "hot" : ""}>
              <span>{label}</span>
              <strong>{value}</strong>
              <p>{copy}</p>
            </article>
          ))}
        </section>

        <section id="arena" className="arena-section" aria-labelledby="arena-title">
          <div className="section-heading">
            <p className="eyebrow">Game board</p>
            <h2 id="arena-title">Five ways agents fake green. One verifier that calls it.</h2>
            <p>
              Each round is generated from this repo's real detector output. The game is playful; the receipts are production-shaped.
            </p>
          </div>
          <div className="arena-grid">
            <div className="scenario-grid" aria-label="Recorded detector rounds">
              {scenarioIndex.map((item) => (
                <button
                  className={`scenario-card ${activeScenarioId === item.id ? "active" : ""}`}
                  key={item.id}
                  onClick={() => void loadScenario(item.id)}
                  type="button"
                >
                  <span>{item.detector}</span>
                  <strong>{scenarioLabels[item.id] ?? item.id}</strong>
                  <em>
                    {item.detector === "OK" ? "lets it ship" : `${item.lies} lies`} - nose {item.nose_length}
                  </em>
                </button>
              ))}
            </div>

            <div
              className={`scenario-stage ${appStateClass}`}
              aria-live="polite"
              key={`scenario-${activeScenarioId}-${transitionTick}`}
            >
              <div className="scenario-score">
                <span>{activeScenario?.headline_detector ?? "D1"}</span>
                <strong>
                  {activeScenario
                    ? `${activeScenario.report.summary.lies} lies - ${activeScenario.report.summary.verified} verified - nose ${activeScenario.report.summary.nose_length}`
                    : "loading real detector output"}
                </strong>
              </div>
              <p>"{activeScenario?.agent_message ?? "Fixed calc_interest.py and verified: 3 tests passed."}"</p>
              <div className="scenario-columns">
                <article>
                  <span>Before</span>
                  <strong>{activeScenario?.suite_before ?? "2 failed, 1 passed"}</strong>
                </article>
                <article>
                  <span>After</span>
                  <strong>{activeScenario?.suite_after ?? "3 passed"}</strong>
                </article>
              </div>
              <pre className="scenario-diff">
                <code>{activeScenario?.diff.trim() ?? "loading recorded diff..."}</code>
              </pre>
              <div className="scenario-evidence">
                {(activeScenario?.report.results ?? []).slice(0, 5).map((result) => (
                  <article className={`evidence-row ${classForVerdict(result.verdict)}`} key={result.check_type}>
                    <span>{result.verdict}</span>
                    <p>{result.evidence}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section id="harness" className="workbench-section" aria-labelledby="harness-title">
          <div className="section-heading">
            <p className="eyebrow">Live harness</p>
            <h2 id="harness-title">Codex can drive. Pinocchio owns the finish line.</h2>
            <p>
              The browser streams a Python harness over SSE: arm the trap repo, run the verifier, and fall back to recorded evidence when a hosted runtime lacks the Codex CLI.
            </p>
          </div>

          <div className="workbench">
            <div className="control-panel">
              <label className="field-group">
                <span>Agent target</span>
                <select value={agent} onChange={(event) => setAgent(event.target.value as AgentKind)}>
                  <option value="codex">Codex CLI</option>
                  <option value="claude">Claude Code</option>
                  <option value="terminal">Terminal adapter</option>
                </select>
              </label>

              <div className="segmented" role="tablist" aria-label="Demo mode">
                {["cheat", "veto", "repair"].map((value) => (
                  <button
                    className={`segment ${mode === value ? "active" : ""}`}
                    key={value}
                    onClick={() => setMode(value)}
                    type="button"
                  >
                    {value}
                  </button>
                ))}
              </div>

              <div className="run-grid">
                {(Object.keys(runLabels) as RunKind[]).map((run) => (
                  <button
                    className={`button ${run === "demo" ? "primary" : run === "loop-codex" ? "danger" : "secondary"}`}
                    disabled={streaming}
                    key={run}
                    onClick={() => startRun(run)}
                    type="button"
                  >
                    {run === "demo" ? <Play size={17} /> : run === "loop-codex" ? <Bot size={17} /> : <Terminal size={17} />}
                    {runLabels[run]}
                  </button>
                ))}
              </div>

              <div className="status-list">
                <div>
                  <span>Codex</span>
                  <strong>{status?.codex ? "ready" : status?.codex_fallback ? "replay fallback" : "not found"}</strong>
                </div>
                <div>
                  <span>Claude</span>
                  <strong>{status?.claude ? "ready" : "not found"}</strong>
                </div>
                <div>
                  <span>Report</span>
                  <strong>{status?.report ? "available" : "waiting"}</strong>
                </div>
                <div>
                  <span>Receipts</span>
                  <strong>{status?.memory_count ?? 0} stored</strong>
                </div>
              </div>
            </div>

            <TerminalPane output={terminalOutput} streaming={streaming || lieCount > 0} />
          </div>

          <div className="memory-panel" aria-labelledby="memory-title">
            <div>
              <p className="eyebrow">Backend memory</p>
              <h3 id="memory-title">Every run leaves a receipt.</h3>
              <p>
                The harness stores public evidence only: commands, output tail, report summary, timestamp, and selected agent target.
              </p>
            </div>
            <div className="memory-feed" aria-live="polite">
              {receipts.length ? (
                receipts.slice(-4).reverse().map((receipt) => (
                  <article key={`${receipt.captured_at}-${receipt.run}`}>
                    <span>{receipt.agent} - {receipt.run}</span>
                    <strong>
                      {receipt.report_summary
                        ? `${receipt.report_summary.lies} lies, nose ${receipt.report_summary.nose_length}`
                        : "run stored"}
                    </strong>
                    <p>{receipt.transcript_tail?.slice(-3).join(" / ") || "receipt stored by backend memory"}</p>
                  </article>
                ))
              ) : (
                <article>
                  <span>waiting</span>
                  <strong>No run recorded yet.</strong>
                  <p>Click the caught-cheat reel and the backend will publish the receipt here.</p>
                </article>
              )}
            </div>
          </div>
        </section>

        <section className="loop-section" aria-labelledby="loop-title">
          <div className="section-heading compact">
            <p className="eyebrow">The loop</p>
            <h2 id="loop-title">Cheat, detect, block, rewrite.</h2>
          </div>
          <div className="loop-track">
            {loopSteps.map(([number, title, copy], index) => (
              <article className={`loop-step ${index === 0 ? "active" : ""}`} key={title}>
                <span>{number}</span>
                <h3>{title}</h3>
                <p>{copy}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="detector-section" aria-labelledby="detectors-title">
          <div className="section-heading compact">
            <p className="eyebrow">Detectors</p>
            <h2 id="detectors-title">Fast, local, and hard to argue with.</h2>
          </div>
          <div className="detector-grid">
            {detectorCards.map(([code, title, copy]) => (
              <button
                className="detector-card"
                key={code}
                onClick={() => void loadScenario(detectorToScenario[code] ?? "test-tampering")}
                type="button"
              >
                <span>{code}</span>
                <h3>{title}</h3>
                <p>{copy}</p>
              </button>
            ))}
          </div>
        </section>

        <section id="pitch" className="market-section" aria-labelledby="market-title">
          <div className="section-heading">
            <p className="eyebrow">YC pitch</p>
            <h2 id="market-title">The new row below code review.</h2>
            <p>
              Greptile reviews the diff. LangSmith-style tooling records the trace. Pinocchio verifies the final claim and blocks false endings before they become trusted work.
            </p>
          </div>
          <div className="market-grid">
            <article>
              <GitBranch size={22} />
              <strong>Wedge</strong>
              <p>Individual devs running Codex or Claude Code who got burned by a green-but-fake fix.</p>
            </article>
            <article>
              <Blocks size={22} />
              <strong>Expansion</strong>
              <p>Team CI checks, repo honesty trends, agent leaderboards, and compliance exports.</p>
            </article>
            <article>
              <Activity size={22} />
              <strong>Moat</strong>
              <p>A cheat corpus: every blocked lie becomes labeled training data for detector N+1.</p>
            </article>
          </div>
        </section>

        <section id="ship" className="ship-section" aria-labelledby="ship-title">
          <div className="section-heading compact">
            <p className="eyebrow">Ship surfaces</p>
            <h2 id="ship-title">One engine, three workflow surfaces.</h2>
          </div>
          <div className="surface-list">
            <article>
              <Code2 size={22} />
              <span>CLI</span>
              <h3>pinocchio .</h3>
              <p>Open-source, local, immediate trust wedge.</p>
            </article>
            <article>
              <ShieldCheck size={22} />
              <span>Hook</span>
              <h3>.codex/hooks.json</h3>
              <p>Stop-hook veto blocks dishonest agent turns.</p>
            </article>
            <article>
              <CheckCircle2 size={22} />
              <span>CI</span>
              <h3>GitHub Action</h3>
              <p>Paid team gate for agent-written pull requests.</p>
            </article>
          </div>
          <div className="transparency-box">
            <XCircle size={20} />
            <div>
              <h3>No fake demo state</h3>
              <p>
                `/api/status`, `/api/events`, `/api/memory`, `/api/scenarios`, and `/api/report` expose the harness state, recorded rounds, and latest verifier contract.
              </p>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
