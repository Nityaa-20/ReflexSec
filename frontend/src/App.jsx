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

  /* ── INVESTIGATION FORM ── */
  .investigation-form-container {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    padding: 24px;
    margin-bottom: 24px;
    position: relative;
    animation: fadeSlideUp 0.5s ease both;
  }

  .investigation-form-container::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, var(--accent-cyan), transparent);
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .form-group.full-width {
    grid-column: span 2;
  }

  .form-label {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-secondary);
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  .form-input, .form-textarea {
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-primary);
    font-family: var(--font-body);
    font-size: 13px;
    padding: 10px 14px;
    transition: all 0.2s;
    outline: none;
  }

  .form-input:focus, .form-textarea:focus {
    border-color: var(--accent-cyan);
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.1);
    background: var(--bg-card-hover);
  }

  .form-textarea {
    min-height: 80px;
    resize: vertical;
  }

  .form-input::placeholder, .form-textarea::placeholder {
    color: var(--text-dim);
    font-family: var(--font-mono);
    font-size: 11px;
    opacity: 0.6;
  }

  .form-actions {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
  }

  .btn-run {
    background: rgba(0, 212, 255, 0.05);
    border: 1px solid var(--accent-cyan);
    color: var(--accent-cyan);
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    padding: 12px 24px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.05);
  }

  .btn-run:hover:not(:disabled) {
    background: var(--accent-cyan);
    color: var(--bg-void);
    box-shadow: var(--glow-cyan);
  }

  .btn-run:disabled {
    border-color: var(--text-dim);
    color: var(--text-dim);
    background: transparent;
    cursor: not-allowed;
  }

  /* ── LOADING & ERROR ── */
  .investigation-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    background: var(--bg-panel);
    border: 1px solid var(--border);
    margin-bottom: 24px;
    text-align: center;
    gap: 16px;
    animation: fadeSlideUp 0.5s ease both;
  }

  .loading-spinner-container {
    position: relative;
    width: 48px;
    height: 48px;
  }

  .loading-spinner {
    position: absolute;
    width: 100%;
    height: 100%;
    border: 2px solid transparent;
    border-top-color: var(--accent-cyan);
    border-bottom-color: var(--accent-cyan);
    border-radius: 50%;
    animation: spin 1.2s linear infinite;
  }

  .loading-spinner-inner {
    position: absolute;
    top: 5px; left: 5px; right: 5px; bottom: 5px;
    border: 2px solid transparent;
    border-left-color: var(--accent-green);
    border-right-color: var(--accent-green);
    border-radius: 50%;
    animation: spin-reverse 1s linear infinite;
  }

  .loading-text {
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--accent-cyan);
    letter-spacing: 2px;
    text-transform: uppercase;
    text-shadow: var(--glow-cyan);
  }

  .loading-subtext {
    font-family: var(--font-body);
    font-size: 11px;
    color: var(--text-secondary);
  }

  .investigation-error {
    background: rgba(255, 58, 58, 0.03);
    border: 1px solid var(--accent-red);
    padding: 20px;
    margin-bottom: 24px;
    position: relative;
    animation: fadeSlideUp 0.5s ease both;
  }

  .investigation-error::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: var(--accent-red);
    box-shadow: var(--glow-red);
  }

  .error-title {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--accent-red);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .error-message {
    font-family: var(--font-body);
    font-size: 13px;
    color: var(--text-primary);
  }

  /* ── RESULTS ── */
  .results-container {
    animation: fadeSlideUp 0.6s ease both;
    margin-bottom: 24px;
  }

  .results-grid-top {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-bottom: 16px;
  }

  .results-grid-bottom {
    display: grid;
    grid-template-columns: 3fr 2fr;
    gap: 16px;
  }

  .result-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    position: relative;
    overflow: hidden;
  }

  .result-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 2px; height: 100%;
    background: var(--card-accent, var(--border));
  }

  .result-card.threat { --card-accent: var(--accent-cyan); }
  .result-card.cve { --card-accent: var(--accent-amber); }
  .result-card.ioc { --card-accent: var(--accent-red); }
  .result-card.report { --card-accent: var(--accent-green); }
  .result-card.soc { --card-accent: var(--accent-cyan); }

  .result-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(26, 45, 66, 0.4);
    padding-bottom: 10px;
  }

  .result-card-title {
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--text-primary);
  }

  .result-card-subtitle {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--text-secondary);
    letter-spacing: 1px;
  }

  .metrics-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .metric-item {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .metric-label {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--text-secondary);
    letter-spacing: 1px;
    text-transform: uppercase;
  }

  .metric-value {
    font-family: var(--font-body);
    font-size: 13px;
    color: var(--text-primary);
    line-height: 1.4;
  }

  .metric-value.mono {
    font-family: var(--font-mono);
    color: var(--accent-cyan);
  }

  .severity-indicator {
    display: inline-block;
    padding: 1px 6px;
    font-family: var(--font-mono);
    font-size: 9px;
    font-weight: 600;
    border: 1px solid;
    text-transform: uppercase;
  }

  .severity-indicator.high {
    color: var(--accent-red);
    border-color: rgba(255, 58, 58, 0.3);
    background: rgba(255, 58, 58, 0.05);
  }

  .severity-indicator.medium {
    color: var(--accent-amber);
    border-color: rgba(255, 170, 0, 0.3);
    background: rgba(255, 170, 0, 0.05);
  }

  .severity-indicator.low {
    color: var(--accent-green);
    border-color: rgba(0, 255, 136, 0.3);
    background: rgba(0, 255, 136, 0.05);
  }

  .report-sections {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .report-section {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .report-section-title {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--accent-green);
    letter-spacing: 1.5px;
    text-transform: uppercase;
    border-bottom: 1px dashed rgba(26, 45, 66, 0.3);
    padding-bottom: 2px;
    margin-bottom: 2px;
  }

  .report-text {
    font-family: var(--font-body);
    font-size: 13px;
    line-height: 1.5;
    color: var(--text-primary);
  }

  .soc-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .soc-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 10px 14px;
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-primary);
    position: relative;
    padding-left: 24px;
  }

  .soc-item::before {
    content: '❯';
    position: absolute;
    left: 10px;
    top: 13px;
    font-size: 8px;
    color: var(--accent-cyan);
  }

  .card-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 4px;
  }

  .card-list-item {
    font-family: var(--font-body);
    font-size: 13px;
    line-height: 1.4;
    color: var(--text-primary);
    position: relative;
    padding-left: 14px;
  }

  .card-list-item::before {
    content: '•';
    position: absolute;
    left: 2px;
    color: var(--accent-cyan);
    font-weight: bold;
  }

  .intel-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 4px;
  }

  .intel-list li {
    font-family: var(--font-body);
    font-size: 13px;
    line-height: 1.4;
    color: var(--text-primary);
    position: relative;
    padding-left: 14px;
  }

  .intel-list li::before {
    content: '•';
    position: absolute;
    left: 2px;
    color: var(--accent-cyan);
    font-weight: bold;
  }

  .result-card.soc .intel-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 0;
  }

  .result-card.soc .intel-list li {
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 10px 14px;
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-primary);
    position: relative;
    padding-left: 24px;
  }

  .result-card.soc .intel-list li::before {
    content: '❯';
    position: absolute;
    left: 10px;
    top: 13px;
    font-size: 8px;
    color: var(--accent-cyan);
    font-weight: normal;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes spin-reverse {
    0% { transform: rotate(360deg); }
    100% { transform: rotate(0deg); }
  }

  @media (max-width: 1024px) {
    .results-grid-top {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 768px) {
    .form-grid {
      grid-template-columns: 1fr;
    }
    .form-group.full-width {
      grid-column: span 1;
    }
    .results-grid-top {
      grid-template-columns: 1fr;
    }
    .results-grid-bottom {
      grid-template-columns: 1fr;
    }
  }

  /* --- NEW STYLES --- */
  .engine-history-layout {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 24px;
    margin-bottom: 24px;
  }
  
  .engine-column {
    display: flex;
    flex-direction: column;
  }
  
  .history-column {
    display: flex;
    flex-direction: column;
  }
  
  .history-container {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    max-height: 480px;
    overflow-y: auto;
    position: relative;
  }
  
  .history-container::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: linear-gradient(90deg, var(--accent-cyan), transparent);
  }
  
  .history-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .history-item {
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    transition: all 0.2s;
  }
  
  .history-item:hover {
    background: var(--bg-card-hover);
    border-color: var(--border-active);
  }
  
  .history-item-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
  }
  
  .history-item-title {
    font-family: var(--font-body);
    font-weight: 600;
    font-size: 13px;
    color: var(--text-primary);
    line-height: 1.4;
  }
  
  .history-item-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 4px;
  }
  
  .history-item-time {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-dim);
  }
  
  .btn-view-history {
    background: transparent;
    border: 1px solid var(--border-active);
    color: var(--accent-cyan);
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 4px 10px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .btn-view-history:hover {
    background: rgba(0, 212, 255, 0.1);
    border-color: var(--accent-cyan);
    box-shadow: 0 0 8px rgba(0, 212, 255, 0.2);
  }
  
  .results-summary-strip {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
    animation: fadeSlideUp 0.5s ease both;
  }
  
  .summary-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    padding: 20px;
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .summary-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 2px;
    background: var(--card-accent, var(--border));
  }
  
  .summary-card.risk-score { --card-accent: var(--accent-red); }
  .summary-card.confidence-score { --card-accent: var(--accent-green); }
  .summary-card.mitre-attack { --card-accent: var(--accent-cyan); }
  
  .summary-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .summary-card-title {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-secondary);
  }
  
  .summary-card-body {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }
  
  .summary-card-value {
    font-family: var(--font-display);
    font-size: 40px;
    font-weight: 900;
    line-height: 1;
    color: var(--text-primary);
  }
  
  .summary-card-max {
    font-family: var(--font-mono);
    font-size: 16px;
    color: var(--text-dim);
  }
  
  .summary-card-label {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-weight: 600;
  }
  
  .summary-card-desc {
    font-size: 11px;
    line-height: 1.4;
    color: var(--text-secondary);
  }
  
  .meter-bar {
    width: 100%;
    height: 6px;
    background: var(--border);
    position: relative;
    border-radius: 3px;
    overflow: hidden;
  }
  
  .meter-fill {
    height: 100%;
    background: var(--card-accent);
    box-shadow: 0 0 10px var(--card-accent);
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .mitre-tags-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 4px;
  }
  
  .mitre-tag {
    background: rgba(0, 212, 255, 0.05);
    border: 1px solid rgba(0, 212, 255, 0.2);
    color: var(--accent-cyan);
    font-family: var(--font-mono);
    font-size: 10px;
    padding: 4px 8px;
    border-radius: 2px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  
  .mitre-tag-code {
    font-weight: bold;
    border-right: 1px solid rgba(0, 212, 255, 0.2);
    padding-right: 6px;
  }

  .btn-export-pdf {
    background: rgba(0, 255, 136, 0.05);
    border: 1px solid var(--accent-green);
    color: var(--accent-green);
    font-family: var(--font-mono);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 6px 14px;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 0 8px rgba(0, 255, 136, 0.05);
  }
  
  .btn-export-pdf:hover {
    background: var(--accent-green);
    color: var(--bg-void);
    box-shadow: var(--glow-green);
  }
  
  @media (max-width: 1024px) {
    .engine-history-layout {
      grid-template-columns: 1fr;
    }
  }
`

const STATUS_SERVICES = [
  { key: 'backend', label: 'Service', name: 'Backend API', endpoint: '/health' },
  { key: 'database', label: 'Storage', name: 'PostgreSQL DB', endpoint: '/health/database' },
  { key: 'ollama', label: 'Inference', name: 'Ollama LLM', endpoint: '/health/ollama' },
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

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    cve_id: '',
    cve_description: '',
    ioc_value: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/investigations`)
      setHistory(response.data)
    } catch (err) {
      console.error("Failed to fetch history:", err)
    }
  }

  useEffect(() => {
    fetchHistory()
  }, [])

  const indicatorColor = {
    online: 'var(--accent-green)',
    offline: 'var(--accent-red)',
    loading: 'var(--accent-amber)',
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleInvestigate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_BASE}/investigate/`, formData)
      setResult(response.data)
      fetchHistory()
    } catch (err) {
      console.error(err)
      const errMsg = err.response?.data?.detail || err.message || 'Unknown network error occurred.'
      setError(errMsg)
    } finally {
      setLoading(false)
    }
  }

  const handleViewHistoryReport = async (id) => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${API_BASE}/investigations/${id}`)
      const data = response.data.report_json
      data.investigation_id = response.data.id
      setResult(data)
    } catch (err) {
      console.error(err)
      setError("Failed to fetch historical report details.")
    } finally {
      setLoading(false)
    }
  }

  const handleExportPDF = async (investigationId) => {
    if (!investigationId) return
    try {
      const response = await axios.get(`${API_BASE}/reports/export/${investigationId}`, {
        responseType: 'blob'
      })
      
      let filename = `reflexsec_report_${investigationId.slice(0, 8)}.pdf`
      const disposition = response.headers['content-disposition']
      if (disposition && disposition.indexOf('attachment') !== -1) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/
        const matches = filenameRegex.exec(disposition)
        if (matches != null && matches[1]) { 
          filename = matches[1].replace(/['"]/g, '')
        }
      }

      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error("Failed to export PDF", err)
      alert("Failed to export PDF report. Please try again.")
    }
  }

  const extractMitreTechniques = (res) => {
    if (!res) return []
    const textToScan = [
      res.report?.threat_assessment || '',
      res.report?.executive_summary || '',
      res.threat_analysis?.attack_vector || '',
      res.threat_analysis?.threat_type || '',
      res.cve_analysis?.exploitability || '',
      res.ioc_analysis?.reasoning || '',
    ].join(' ')

    const techniqueRegex = /\b(T\d{4}(?:\.\d{3})?)\b/g
    const matches = textToScan.match(techniqueRegex)
    if (!matches) return []
    
    const uniqueMatches = Array.from(new Set(matches.map(m => m.toUpperCase())))
    
    const techniqueNames = {
      'T1566': 'Phishing',
      'T1059': 'Command and Scripting Interpreter',
      'T1190': 'Exploit Public-Facing Application',
      'T1203': 'Exploitation for Client Execution',
      'T1078': 'Valid Accounts',
      'T1547': 'Boot or Logon Autostart Execution',
      'T1021': 'Remote Services',
      'T1047': 'Windows Management Instrumentation',
      'T1068': 'Exploitation for Privilege Escalation',
      'T1562': 'Impair Defenses',
      'T1071': 'Application Layer Protocol',
      'T1573': 'Encrypted Channel',
      'T1048': 'Exfiltration Over Alternative Protocol',
      'T1486': 'Data Encrypted for Impact',
    }
    
    return uniqueMatches.map(code => ({
      code,
      name: techniqueNames[code] || 'Unclassified Technique'
    }))
  }

  const getOverallConfidence = (res) => {
    if (!res) return 0
    const scores = []
    if (res.threat_analysis?.confidence_score !== undefined) scores.push(res.threat_analysis.confidence_score)
    if (res.cve_analysis?.confidence_score !== undefined) scores.push(res.cve_analysis.confidence_score)
    if (res.ioc_analysis?.confidence_score !== undefined) scores.push(res.ioc_analysis.confidence_score)
    
    if (scores.length === 0) return 0.75
    return scores.reduce((sum, val) => sum + val, 0) / scores.length
  }

  const getRiskScore = (res) => {
    if (!res) return { score: 0, label: 'NONE', color: 'var(--text-dim)' }
    
    let maxSev = 'info'
    const sevs = []
    if (res.threat_analysis?.severity) sevs.push(res.threat_analysis.severity.toLowerCase())
    if (res.cve_analysis?.severity) sevs.push(res.cve_analysis.severity.toLowerCase())
    if (res.ioc_analysis?.threat_level) sevs.push(res.ioc_analysis.threat_level.toLowerCase())
    
    const severityWeights = {
      critical: 5,
      high: 4,
      medium: 3,
      low: 2,
      info: 1,
      benign: 1,
      unknown: 1
    }
    
    let maxWeight = 0
    for (const s of sevs) {
      const w = severityWeights[s] || 1
      if (w > maxWeight) {
        maxWeight = w
        maxSev = s
      }
    }
    
    if (maxWeight === 0) {
      return { score: 5.0, label: 'MEDIUM', color: 'var(--accent-amber)' }
    }
    
    const scoreMap = {
      critical: { score: 9.5, label: 'CRITICAL', color: 'var(--accent-red)' },
      high: { score: 8.2, label: 'HIGH', color: 'var(--accent-red)' },
      medium: { score: 5.5, label: 'MEDIUM', color: 'var(--accent-amber)' },
      low: { score: 3.0, label: 'LOW', color: 'var(--accent-green)' },
      info: { score: 1.5, label: 'INFORMATIONAL', color: 'var(--accent-cyan)' },
      benign: { score: 1.0, label: 'BENIGN', color: 'var(--accent-green)' }
    }
    
    return scoreMap[maxSev] || { score: 5.0, label: 'MEDIUM', color: 'var(--accent-amber)' }
  }

  const renderSeverityBadge = (sev) => {
    if (!sev) return 'N/A'
    const s = sev.toLowerCase()
    let severityClass = 'medium'
    if (s.includes('high') || s.includes('critical')) {
      severityClass = 'high'
    } else if (s.includes('low') || s.includes('info')) {
      severityClass = 'low'
    }
    return <span className={`severity-indicator ${severityClass}`}>{sev.toUpperCase()}</span>
  }

  const formatConfidence = (score) => {
    if (score === undefined || score === null) return 'N/A'
    const numericScore = parseFloat(score)
    if (isNaN(numericScore)) return score
    if (numericScore >= 0 && numericScore <= 1) {
      return `${Math.round(numericScore * 100)}%`
    }
    return `${numericScore}%`
  }

  const renderList = (value) => {
    if (!value) return <span className="metric-value">N/A</span>

    if (Array.isArray(value)) {
      return (
        <ul className="intel-list">
          {value.map((item, index) => (
            <li key={index}>{String(item)}</li>
          ))}
        </ul>
      )
    }

    return <span className="metric-value">{String(value)}</span>
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

        {/* INVESTIGATION CONSOLE */}
        <div className="section-label">// investigation console</div>
        <div className="engine-history-layout">
          <div className="engine-column">
            <div className="investigation-form-container">
              <form onSubmit={handleInvestigate}>
                <div className="form-grid">
                  <div className="form-group">
                    <label className="form-label" htmlFor="title">Incident Title</label>
                    <input
                      id="title"
                      type="text"
                      className="form-input"
                      placeholder="e.g. APT29 Phishing Campaign"
                      value={formData.title}
                      onChange={handleChange}
                      name="title"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="ioc_value">IOC Value (IP/Domain/Hash)</label>
                    <input
                      id="ioc_value"
                      type="text"
                      className="form-input"
                      placeholder="e.g. 198.51.100.42"
                      value={formData.ioc_value}
                      onChange={handleChange}
                      name="ioc_value"
                    />
                  </div>
                  <div className="form-group full-width">
                    <label className="form-label" htmlFor="description">Incident Description</label>
                    <textarea
                      id="description"
                      className="form-textarea"
                      placeholder="Describe the detected threat, suspicious activity, or logs..."
                      value={formData.description}
                      onChange={handleChange}
                      name="description"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="cve_id">CVE ID</label>
                    <input
                      id="cve_id"
                      type="text"
                      className="form-input"
                      placeholder="e.g. CVE-2023-38831"
                      value={formData.cve_id}
                      onChange={handleChange}
                      name="cve_id"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="cve_description">CVE Description</label>
                    <input
                      id="cve_description"
                      type="text"
                      className="form-input"
                      placeholder="e.g. WinRAR Remote Code Execution vulnerability..."
                      value={formData.cve_description}
                      onChange={handleChange}
                      name="cve_description"
                    />
                  </div>
                </div>
                <div className="form-actions">
                  <button type="submit" className="btn-run" disabled={loading}>
                    {loading ? 'Analyzing...' : 'Run Investigation'}
                  </button>
                </div>
              </form>
            </div>

            {/* LOADING INDICATOR */}
            {loading && (
              <div className="investigation-loading">
                <div className="loading-spinner-container">
                  <div className="loading-spinner" />
                  <div className="loading-spinner-inner" />
                </div>
                <div>
                  <div className="loading-text">Running Multi-Agent Investigation...</div>
                  <div className="loading-subtext">Correlating threat intelligence feeds, verifying vulnerability score, and generating recommendations.</div>
                </div>
              </div>
            )}

            {/* ERROR DISPLAY */}
            {error && (
              <div className="investigation-error">
                <div className="error-title">
                  <span>⚠️</span> Investigation Failed
                </div>
                <div className="error-message">{error}</div>
              </div>
            )}
          </div>

          {/* HISTORY COLUMN */}
          <div className="history-column">
            <div className="history-container">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span className="form-label" style={{ color: 'var(--accent-cyan)' }}>// history_log</span>
                <span className="history-item-time">{history.length} records</span>
              </div>
              <div className="history-list">
                {history.length === 0 ? (
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', textAlign: 'center', padding: '20px' }}>
                    NO PAST RECORDS
                  </div>
                ) : (
                  history.map((item) => (
                    <div key={item.id} className="history-item">
                      <div className="history-item-header">
                        <span className="history-item-title">{item.title}</span>
                        {renderSeverityBadge(item.severity)}
                      </div>
                      <div className="history-item-meta">
                        <span className="history-item-time">
                          {item.created_at.replace('T', ' ').slice(0, 19)} UTC
                        </span>
                        <button
                          onClick={() => handleViewHistoryReport(item.id)}
                          className="btn-view-history"
                        >
                          View Report
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* INVESTIGATION RESULTS */}
        {result && (
          <div className="results-container">
            <div className="section-label">// investigation analysis results</div>

            {/* SUMMARY METRICS CARDS */}
            <div className="results-summary-strip">
              {/* Risk Score Card */}
              <div className="summary-card risk-score">
                <div className="summary-card-header">
                  <span className="summary-card-title">// risk_score</span>
                  <span className="summary-card-label" style={{ color: getRiskScore(result).color }}>
                    {getRiskScore(result).label}
                  </span>
                </div>
                <div className="summary-card-body">
                  <span className="summary-card-value">{getRiskScore(result).score.toFixed(1)}</span>
                  <span className="summary-card-max">/ 10.0</span>
                </div>
                <div className="meter-bar">
                  <div className="meter-fill" style={{ width: `${getRiskScore(result).score * 10}%` }} />
                </div>
                <span className="summary-card-desc">Derived index based on maximum detected system severity</span>
              </div>

              {/* Confidence Score Card */}
              <div className="summary-card confidence-score">
                <div className="summary-card-header">
                  <span className="summary-card-title">// confidence_score</span>
                  <span className="summary-card-label" style={{ color: 'var(--accent-green)' }}>
                    {getOverallConfidence(result) >= 0.8 ? 'HIGH' : getOverallConfidence(result) >= 0.5 ? 'MEDIUM' : 'LOW'}
                  </span>
                </div>
                <div className="summary-card-body">
                  <span className="summary-card-value">{Math.round(getOverallConfidence(result) * 100)}%</span>
                </div>
                <div className="meter-bar">
                  <div className="meter-fill" style={{ width: `${getOverallConfidence(result) * 100}%` }} />
                </div>
                <span className="summary-card-desc">Average model confidence across all analytical agents</span>
              </div>

              {/* MITRE ATT&CK Card */}
              {extractMitreTechniques(result).length > 0 && (
                <div className="summary-card mitre-attack">
                  <div className="summary-card-header">
                    <span className="summary-card-title">// mitre_attack_techniques</span>
                  </div>
                  <div className="mitre-tags-list">
                    {extractMitreTechniques(result).map((tech, i) => (
                      <span key={i} className="mitre-tag" title={tech.name}>
                        <span className="mitre-tag-code">{tech.code}</span>
                        <span>{tech.name}</span>
                      </span>
                    ))}
                  </div>
                  <span className="summary-card-desc" style={{ marginTop: 'auto' }}>Identified adversary TTP alignments extracted from findings</span>
                </div>
              )}
            </div>

            <div className="results-grid-top">
              {/* A. Threat Analysis Card */}
              <div className="result-card threat">
                <div className="result-card-header">
                  <div className="result-card-title">Threat Analysis</div>
                  <span className="result-card-subtitle">// core_threat</span>
                </div>
                <div className="metrics-list">
                  <div className="metric-item">
                    <span className="metric-label">Threat Type</span>
                    <span className="metric-value">{result.threat_analysis?.threat_type || 'N/A'}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Severity</span>
                    <span className="metric-value">
                      {renderSeverityBadge(result.threat_analysis?.severity)}
                    </span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Attack Vector</span>
                    <span className="metric-value">{result.threat_analysis?.attack_vector || 'N/A'}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Mitigation</span>
                    {renderList(result.threat_analysis?.mitigation)}
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Confidence Score</span>
                    <span className="metric-value mono">
                      {formatConfidence(result.threat_analysis?.confidence_score)}
                    </span>
                  </div>
                </div>
              </div>

              {/* B. CVE Analysis Card */}
              <div className="result-card cve">
                <div className="result-card-header">
                  <div className="result-card-title">CVE Analysis</div>
                  <span className="result-card-subtitle">// vulnerability_risk</span>
                </div>
                <div className="metrics-list">
                  <div className="metric-item">
                    <span className="metric-label">CVE ID</span>
                    <span className="metric-value mono">{result.cve_analysis?.cve_id || 'N/A'}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Severity</span>
                    <span className="metric-value">
                      {renderSeverityBadge(result.cve_analysis?.severity)}
                    </span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Exploitability</span>
                    <span className="metric-value">{result.cve_analysis?.exploitability || 'N/A'}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Affected Systems</span>
                    {renderList(result.cve_analysis?.affected_systems)}
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Recommendations</span>
                    {renderList(result.cve_analysis?.mitigation)}
                  </div>
                </div>
              </div>

              {/* C. IOC Analysis Card */}
              <div className="result-card ioc">
                <div className="result-card-header">
                  <div className="result-card-title">IOC Analysis</div>
                  <span className="result-card-subtitle">// indicators_of_compromise</span>
                </div>
                <div className="metrics-list">
                  <div className="metric-item">
                    <span className="metric-label">IOC Value</span>
                    <span className="metric-value mono">{result.ioc_analysis?.ioc_value || 'N/A'}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">IOC Type</span>
                    <span className="metric-value">{result.ioc_analysis?.ioc_type || 'N/A'}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Associated Risks</span>
                    {renderList(result.ioc_analysis?.associated_risks)}
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Threat Level</span>
                    <span className="metric-value">
                      {renderSeverityBadge(result.ioc_analysis?.threat_level)}
                    </span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Recommended Actions</span>
                    {renderList(result.ioc_analysis?.recommended_actions)}
                  </div>
                </div>
              </div>
            </div>

            <div className="results-grid-bottom">
              {/* D. Executive Report Card */}
              <div className="result-card report">
                <div className="result-card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div className="result-card-title">Executive Report</div>
                    <span className="result-card-subtitle">// executive_summary</span>
                  </div>
                  {result.investigation_id && (
                    <button
                      onClick={() => handleExportPDF(result.investigation_id)}
                      className="btn-export-pdf"
                    >
                      Export PDF
                    </button>
                  )}
                </div>
                <div className="report-sections">
                  <div className="report-section">
                    <span className="report-section-title">Executive Summary</span>
                    <p className="report-text">{result.report?.executive_summary || 'N/A'}</p>
                  </div>
                  <div className="report-section">
                    <span className="report-section-title">Threat Assessment</span>
                    <p className="report-text">{result.report?.threat_assessment || 'N/A'}</p>
                  </div>
                  <div className="report-section">
                    <span className="report-section-title">Risk Analysis</span>
                    <p className="report-text">{result.report?.risk_analysis || 'N/A'}</p>
                  </div>
                  <div className="report-section">
                    <span className="report-section-title">Mitigation Strategy</span>
                    <p className="report-text">{result.report?.mitigation_strategy || 'N/A'}</p>
                  </div>
                  <div className="report-section">
                    <span className="report-section-title">Confidence Assessment</span>
                    <p className="report-text">{result.report?.confidence_assessment || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* E. SOC Recommendations Card */}
              <div className="result-card soc">
                <div className="result-card-header">
                  <div className="result-card-title">SOC Recommendations</div>
                  <span className="result-card-subtitle">// technical_playbook</span>
                </div>
                {renderList(result.report?.soc_recommendations)}
              </div>
            </div>
          </div>
        )}

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
