import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow:wght@300;400;600;700&family=Barlow+Condensed:wght@700;900&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg-void: #04060a;
    --bg-panel: #080d14;
    --bg-card: #0c1520;
    --bg-card-hover: #101c2a;
    --border: #1a2d42;
    --border-active: #1e4a6e;
    --accent-cyan: #00d4ff;
    --accent-green: #00ff88;
    --accent-red: #ff3a3a;
    --accent-amber: #ffaa00;
    --text-primary: #c8dff0;
    --text-secondary: #5a7a96;
    --text-dim: #2d4a60;
    --font-mono: 'Share Tech Mono', monospace;
    --font-body: 'Barlow', sans-serif;
    --font-display: 'Barlow Condensed', sans-serif;
    --glow-cyan: 0 0 20px rgba(0,212,255,0.15), 0 0 60px rgba(0,212,255,0.05);
    --glow-green: 0 0 20px rgba(0,255,136,0.15);
    --glow-red: 0 0 20px rgba(255,58,58,0.2);
  }

  body {
    background: var(--bg-void);
    color: var(--text-primary);
    font-family: var(--font-body);
    min-height: 100vh;
    overflow-x: hidden;
  }

  .scanline {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.03) 2px,
      rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
  }

  .grid-bg {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image:
      linear-gradient(rgba(0,212,255,0.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,212,255,0.025) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
  }

  .app {
    position: relative;
    z-index: 1;
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 24px 60px;
  }

  /* ── HEADER ── */
  .header {
    padding: 40px 0 36px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 24px;
    flex-wrap: wrap;
    animation: fadeSlideDown 0.6s ease both;
  }

  .header-left { display: flex; flex-direction: column; gap: 6px; }

  .brand-tag {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--accent-cyan);
    letter-spacing: 4px;
    text-transform: uppercase;
    opacity: 0.7;
  }

  .title {
    font-family: var(--font-display);
    font-size: clamp(48px, 7vw, 88px);
    font-weight: 900;
    line-height: 0.9;
    letter-spacing: -1px;
    color: var(--text-primary);
    text-transform: uppercase;
  }

  .title span {
    color: var(--accent-cyan);
    text-shadow: var(--glow-cyan);
  }

  .subtitle {
    font-family: var(--font-body);
    font-weight: 300;
    font-size: 13px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-top: 8px;
  }

  .header-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 6px;
  }

  .live-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--accent-green);
    letter-spacing: 2px;
  }

  .pulse-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--accent-green);
    box-shadow: var(--glow-green);
    animation: pulse 1.8s ease-in-out infinite;
  }

  .timestamp {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 1px;
  }

  /* ── STATUS STRIP ── */
  .status-strip {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin: 28px 0;
    animation: fadeSlideDown 0.6s 0.1s ease both;
  }

  .status-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 16px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    transition: border-color 0.2s, background 0.2s;
    position: relative;
    overflow: hidden;
  }

  .status-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 2px; height: 100%;
    background: var(--indicator-color, var(--text-dim));
    box-shadow: 0 0 12px var(--indicator-color, transparent);
  }

  .status-card:hover { background: var(--bg-card-hover); border-color: var(--border-active); }

  .status-label {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-secondary);
  }

  .status-name {
    font-family: var(--font-body);
    font-weight: 600;
    font-size: 14px;
    color: var(--text-primary);
    margin-top: 2px;
  }

  .status-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 1.5px;
    padding: 4px 10px;
    border: 1px solid;
    text-transform: uppercase;
  }

  .status-badge.online  { color: var(--accent-green); border-color: rgba(0,255,136,0.3); background: rgba(0,255,136,0.05); }
  .status-badge.offline { color: var(--accent-red);   border-color: rgba(255,58,58,0.3);  background: rgba(255,58,58,0.05); }
  .status-badge.loading { color: var(--accent-amber); border-color: rgba(255,170,0,0.3);  background: rgba(255,170,0,0.05); }

  /* ── SECTION LABEL ── */
  .section-label {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--text-dim);
    margin: 36px 0 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  /* ── MODULE GRID ── */
  .module-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
  }

  .module-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 24px;
    cursor: pointer;
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
    opacity: 0;
    animation: fadeSlideUp 0.5s ease forwards;
  }

  .module-card:hover {
    background: var(--bg-card-hover);
    border-color: var(--accent-cyan);
    transform: translateY(-2px);
    box-shadow: var(--glow-cyan);
  }

  .module-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
    opacity: 0;
    transition: opacity 0.3s;
  }

  .module-card:hover::after { opacity: 1; }

  .module-icon {
    font-size: 22px;
    margin-bottom: 14px;
    display: block;
  }

  .module-title {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 18px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: var(--text-primary);
    margin-bottom: 6px;
  }

  .module-desc {
    font-size: 12px;
    line-height: 1.6;
    color: var(--text-secondary);
  }

  .module-tag {
    display: inline-block;
    margin-top: 14px;
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent-cyan);
    opacity: 0.6;
  }

  /* ── FOOTER ── */
  .footer {
    margin-top: 60px;
    padding-top: 20px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
  }

  .footer-text {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 2px;
  }

  .footer-version {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
    letter-spacing: 1px;
  }

  /* ── ANIMATIONS ── */
  @keyframes fadeSlideDown {
    from { opacity: 0; transform: translateY(-16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  @keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.4; transform: scale(0.85); }
  }

  @media (max-width: 640px) {
    .status-strip { grid-template-columns: 1fr; }
    .header { flex-direction: column; align-items: flex-start; }
    .header-right { align-items: flex-start; }
  }
`

const STATUS_SERVICES = [
  { key: 'backend',  label: 'Service',  name: 'Backend API',     endpoint: '/health' },
  { key: 'database', label: 'Storage',  name: 'PostgreSQL DB',   endpoint: '/health/db' },
  { key: 'ollama',   label: 'Inference',name: 'Ollama LLM',      endpoint: '/health/ollama' },
]

const MODULES = [
  {
    icon: '⚡',
    title: 'Threat Intelligence',
    desc: 'Ingest and correlate threat feeds from multiple sources. Identify emerging attack patterns and adversary TTPs in real time.',
    tag: 'INTEL · FUSION',
    delay: '0.2s',
  },
  {
    icon: '🔍',
    title: 'CVE Analysis',
    desc: 'Automated vulnerability scoring, exploitability assessment, and patch prioritization driven by contextual risk models.',
    tag: 'VULN · SCORING',
    delay: '0.3s',
  },
  {
    icon: '🌐',
    title: 'IOC Analysis',
    desc: 'Detect and pivot on indicators of compromise — IPs, domains, hashes, and behavioral signatures — across your environment.',
    tag: 'IOC · PIVOTING',
    delay: '0.4s',
  },
  {
    icon: '📋',
    title: 'Report Generation',
    desc: 'Produce structured intelligence reports for technical and executive audiences with auto-summarization and confidence scoring.',
    tag: 'REPORTS · EXPORT',
    delay: '0.5s',
  },
  {
    icon: '🧠',
    title: 'Self-Critique Engine',
    desc: 'Meta-reasoning layer that audits its own outputs for logical gaps, hallucinations, and analytical blind spots before delivery.',
    tag: 'META · REASONING',
    delay: '0.6s',
  },
]

function useStatuses() {
  const [statuses, setStatuses] = useState(
    Object.fromEntries(STATUS_SERVICES.map(s => [s.key, 'loading']))
  )

  useEffect(() => {
    STATUS_SERVICES.forEach(({ key, endpoint }) => {
      axios.get(`${API_BASE}${endpoint}`, { timeout: 4000 })
        .then(() => setStatuses(prev => ({ ...prev, [key]: 'online' })))
        .catch(() => setStatuses(prev => ({ ...prev, [key]: 'offline' })))
    })
  }, [])

  return statuses
}

function useClock() {
  const [time, setTime] = useState(() => new Date().toISOString())
  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toISOString()), 1000)
    return () => clearInterval(id)
  }, [])
  return time
}

export default function App() {
  const statuses = useStatuses()
  const time = useClock()

  const indicatorColor = {
    online:  'var(--accent-green)',
    offline: 'var(--accent-red)',
    loading: 'var(--accent-amber)',
  }

  return (
    <>
      <style>{styles}</style>
      <div className="scanline" />
      <div className="grid-bg" />

      <div className="app">
        {/* HEADER */}
        <header className="header">
          <div className="header-left">
            <span className="brand-tag">// threat intelligence platform</span>
            <h1 className="title">
              Reflex<span>Sec</span>
            </h1>
            <p className="subtitle">Self-Critiquing Cyber Threat Intelligence Agent</p>
          </div>
          <div className="header-right">
            <div className="live-indicator">
              <span className="pulse-dot" />
              SYSTEM ACTIVE
            </div>
            <span className="timestamp">{time.replace('T', ' ').slice(0, 19)} UTC</span>
          </div>
        </header>

        {/* STATUS STRIP */}
        <div className="section-label">// system health</div>
        <div className="status-strip">
          {STATUS_SERVICES.map(({ key, label, name }) => (
            <div
              key={key}
              className="status-card"
              style={{ '--indicator-color': indicatorColor[statuses[key]] }}
            >
              <div>
                <div className="status-label">{label}</div>
                <div className="status-name">{name}</div>
              </div>
              <div className={`status-badge ${statuses[key]}`}>
                {statuses[key] === 'loading' ? 'PROBING' : statuses[key].toUpperCase()}
              </div>
            </div>
          ))}
        </div>

        {/* MODULES */}
        <div className="section-label">// intelligence modules</div>
        <div className="module-grid">
          {MODULES.map((mod) => (
            <div
              key={mod.title}
              className="module-card"
              style={{ animationDelay: mod.delay }}
            >
              <span className="module-icon">{mod.icon}</span>
              <div className="module-title">{mod.title}</div>
              <div className="module-desc">{mod.desc}</div>
              <span className="module-tag">{mod.tag}</span>
            </div>
          ))}
        </div>

        {/* FOOTER */}
        <footer className="footer">
          <span className="footer-text">REFLEXSEC · SELF-CRITIQUING CTI AGENT</span>
          <span className="footer-version">v0.1.0 · DEVELOPMENT BUILD</span>
        </footer>
      </div>
    </>
  )
}
