from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import re
import io
import csv
import os

app = Flask(__name__)
CORS(app)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pinterest Pipeline</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

  :root {
    --bg: #0e0e0f;
    --surface: #17171a;
    --surface2: #1f1f24;
    --border: #2a2a30;
    --accent: #e8503a;
    --accent2: #f5a623;
    --text: #f0ede8;
    --text2: #8a8790;
    --text3: #5a5760;
    --success: #3ecf8e;
    --radius: 10px;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 14px; min-height: 100vh; display: flex; flex-direction: column; }

  header {
    border-bottom: 1px solid var(--border);
    padding: 0 32px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--surface);
    flex-shrink: 0;
  }
  .logo { font-family: 'DM Serif Display', serif; font-size: 18px; display: flex; align-items: center; gap: 10px; }
  .logo-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 10px var(--accent); }
  .header-right { display: flex; align-items: center; gap: 12px; }
  .api-status { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text2); }
  .status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--text3); }
  .status-dot.ok { background: var(--success); box-shadow: 0 0 6px var(--success); }

  .app { display: flex; flex: 1; overflow: hidden; height: calc(100vh - 56px); }

  .sidebar {
    width: 260px; border-right: 1px solid var(--border);
    background: var(--surface); display: flex; flex-direction: column;
    flex-shrink: 0; overflow-y: auto;
  }
  .sidebar-section { padding: 16px; border-bottom: 1px solid var(--border); }
  .sidebar-label { font-size: 10px; font-weight: 600; letter-spacing: 1.2px; text-transform: uppercase; color: var(--text3); margin-bottom: 10px; }

  .profile-card {
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 12px; cursor: pointer;
    margin-bottom: 6px; transition: all 0.15s; position: relative;
  }
  .profile-card:hover { border-color: var(--text3); }
  .profile-card.active { border-color: var(--accent); background: rgba(232,80,58,0.08); }
  .profile-card .name { font-weight: 500; font-size: 13px; margin-bottom: 2px; }
  .profile-card .niche { font-size: 11px; color: var(--text2); }
  .profile-badge { position: absolute; top: 10px; right: 10px; width: 6px; height: 6px; border-radius: 50%; background: var(--accent); display: none; }
  .profile-card.active .profile-badge { display: block; }

  .btn-ghost { width: 100%; padding: 8px 12px; background: transparent; border: 1px dashed var(--border); border-radius: var(--radius); color: var(--text3); cursor: pointer; font-family: 'DM Sans', sans-serif; font-size: 12px; transition: all 0.15s; display: flex; align-items: center; gap: 6px; justify-content: center; }
  .btn-ghost:hover { border-color: var(--text2); color: var(--text2); }

  .main { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }

  .steps-bar { display: flex; align-items: center; padding: 0 32px; border-bottom: 1px solid var(--border); height: 48px; background: var(--surface); flex-shrink: 0; }
  .step-item { display: flex; align-items: center; gap: 8px; padding: 0 16px; height: 100%; font-size: 12px; color: var(--text3); cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: all 0.15s; }
  .step-item.active { color: var(--text); border-bottom-color: var(--accent); }
  .step-item.done { color: var(--success); }
  .step-num { width: 18px; height: 18px; border-radius: 50%; border: 1px solid currentColor; display: flex; align-items: center; justify-content: center; font-size: 10px; font-family: 'DM Mono', monospace; flex-shrink: 0; }
  .step-item.done .step-num { background: var(--success); border-color: var(--success); color: var(--bg); }
  .step-sep { color: var(--text3); font-size: 10px; }

  .panel { display: none; flex: 1; padding: 32px; flex-direction: column; gap: 20px; }
  .panel.active { display: flex; }
  .panel-title { font-family: 'DM Serif Display', serif; font-size: 22px; font-weight: 400; }
  .panel-sub { font-size: 13px; color: var(--text2); margin-top: 4px; }

  label { display: block; font-size: 12px; font-weight: 500; color: var(--text2); margin-bottom: 6px; letter-spacing: 0.3px; }
  input[type="text"], input[type="url"], input[type="password"], textarea, select {
    width: 100%; background: var(--surface2); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px 14px; color: var(--text);
    font-family: 'DM Sans', sans-serif; font-size: 13px; outline: none; transition: border-color 0.15s; resize: vertical;
  }
  input:focus, textarea:focus, select:focus { border-color: var(--accent); }
  input::placeholder, textarea::placeholder { color: var(--text3); }
  select option { background: var(--surface2); }

  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .form-group { display: flex; flex-direction: column; }

  .btn { padding: 10px 20px; border-radius: var(--radius); border: none; cursor: pointer; font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500; transition: all 0.15s; display: inline-flex; align-items: center; gap: 8px; }
  .btn-primary { background: var(--accent); color: white; }
  .btn-primary:hover { background: #d44530; }
  .btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-secondary { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
  .btn-secondary:hover { border-color: var(--text2); }
  .btn-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }

  .loading-block { display: none; flex-direction: column; align-items: center; gap: 16px; padding: 48px; text-align: center; }
  .loading-block.active { display: flex; }
  .spinner { width: 36px; height: 36px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-text { color: var(--text2); font-size: 13px; }
  .loading-step { font-family: 'DM Mono', monospace; font-size: 11px; color: var(--text3); }

  .prompts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .prompt-card { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; }
  .prompt-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
  .prompt-type { font-size: 10px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; background: rgba(232,80,58,0.15); color: var(--accent); }
  .prompt-type.collage { background: rgba(62,207,142,0.15); color: var(--success); }
  .prompt-type.story { background: rgba(245,166,35,0.15); color: var(--accent2); }
  .prompt-type.list { background: rgba(100,149,237,0.15); color: cornflowerblue; }
  .prompt-type.comp { background: rgba(180,100,220,0.15); color: #c47ee8; }
  .copy-btn { background: transparent; border: none; color: var(--text3); cursor: pointer; padding: 4px; border-radius: 4px; transition: color 0.15s; font-size: 12px; }
  .copy-btn:hover { color: var(--text); }
  .prompt-text { font-size: 12px; color: var(--text2); line-height: 1.6; font-family: 'DM Mono', monospace; }

  .csv-table-wrap { overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--border); max-height: 500px; overflow-y: auto; }
  table { width: 100%; border-collapse: collapse; }
  th { background: var(--surface2); padding: 10px 14px; text-align: left; font-size: 11px; font-weight: 600; letter-spacing: 0.8px; text-transform: uppercase; color: var(--text3); border-bottom: 1px solid var(--border); white-space: nowrap; position: sticky; top: 0; }
  td { padding: 10px 14px; font-size: 12px; color: var(--text2); border-bottom: 1px solid var(--border); vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.02); }
  td.title-cell { color: var(--text); font-weight: 500; max-width: 240px; }
  td.desc-cell { max-width: 360px; line-height: 1.5; }

  .round-divider { background: rgba(232,80,58,0.06); }
  .round-divider td { font-size: 10px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: var(--accent); padding: 6px 14px; border-bottom: 1px solid var(--border); }

  .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); z-index: 100; align-items: center; justify-content: center; }
  .modal-overlay.active { display: flex; }
  .modal { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 28px; width: 540px; max-height: 90vh; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; }
  .modal-title { font-family: 'DM Serif Display', serif; font-size: 20px; }
  .modal-footer { display: flex; gap: 10px; justify-content: flex-end; padding-top: 8px; border-top: 1px solid var(--border); }

  .alert { padding: 12px 16px; border-radius: var(--radius); font-size: 12px; line-height: 1.5; display: flex; gap: 10px; align-items: flex-start; }
  .alert-warn { background: rgba(245,166,35,0.1); border: 1px solid rgba(245,166,35,0.25); color: var(--accent2); }
  .alert-info { background: rgba(62,207,142,0.08); border: 1px solid rgba(62,207,142,0.2); color: var(--success); }
  .alert-error { background: rgba(232,80,58,0.1); border: 1px solid rgba(232,80,58,0.25); color: var(--accent); }

  .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .section-title { font-size: 13px; font-weight: 600; }
  .section-count { font-size: 11px; color: var(--text3); font-family: 'DM Mono', monospace; }

  .badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 20px; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }
  .badge-accent { background: rgba(232,80,58,0.15); color: var(--accent); }

  .apikey-row { display: flex; gap: 8px; align-items: center; }
  .apikey-row input { flex: 1; font-family: 'DM Mono', monospace; }

  .char-count { font-size: 10px; color: var(--text3); text-align: right; margin-top: 3px; font-family: 'DM Mono', monospace; }
  .char-count.warn { color: var(--accent2); }
  .char-count.over { color: var(--accent); }

  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: var(--text3); }

  .progress-bar { height: 2px; background: var(--border); border-radius: 2px; overflow: hidden; margin-top: 8px; }
  .progress-fill { height: 100%; background: var(--accent); border-radius: 2px; transition: width 0.4s ease; width: 0%; }

  .annotations-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
  .annotation-tag { padding: 3px 10px; border-radius: 20px; font-size: 11px; background: rgba(232,80,58,0.1); border: 1px solid rgba(232,80,58,0.2); color: var(--accent); }
</style>
</head>
<body>

<header>
  <div class="logo"><div class="logo-dot"></div>Pinterest Pipeline</div>
  <div class="header-right">
    <div class="api-status">
      <div class="status-dot" id="apiStatusDot"></div>
      <span id="apiStatusText">Sin clave API</span>
    </div>
    <button class="btn btn-secondary" style="font-size:12px;padding:6px 14px;" onclick="showSettings()">⚙ Ajustes</button>
  </div>
</header>

<div class="app">
  <div class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-label">Cuentas / Sitios</div>
      <div id="profileList"></div>
      <button class="btn-ghost" onclick="openProfileModal(null)" style="margin-top:8px;"><span>+</span> Nueva cuenta</button>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-label">Sesión actual</div>
      <div style="font-size:12px;color:var(--text3);line-height:1.6;" id="sessionSummary">Ninguna cuenta seleccionada</div>
    </div>
  </div>

  <div class="main">
    <div class="steps-bar">
      <div class="step-item active" id="stepTab1" onclick="goStep(1)"><div class="step-num">1</div><span>Entrada</span></div>
      <span class="step-sep">›</span>
      <div class="step-item" id="stepTab2" onclick="goStep(2)"><div class="step-num">2</div><span>Generando</span></div>
      <span class="step-sep">›</span>
      <div class="step-item" id="stepTab3" onclick="goStep(3)"><div class="step-num">3</div><span>Prompts</span></div>
      <span class="step-sep">›</span>
      <div class="step-item" id="stepTab4" onclick="goStep(4)"><div class="step-num">4</div><span>CSV (48 filas)</span></div>
    </div>

    <!-- PANEL 1 -->
    <div class="panel active" id="panel1">
      <div>
        <div class="panel-title">Entrada del contenido</div>
        <div class="panel-sub">Pega la URL del post. La app extrae el contenido automáticamente desde WordPress.</div>
      </div>

      <div class="card">
        <div class="form-group" style="margin-bottom:16px;">
          <label>CUENTA ACTIVA</label>
          <select id="activeProfileSelect" onchange="selectProfile(this.value)">
            <option value="">— Selecciona una cuenta —</option>
          </select>
        </div>
        <div class="form-group">
          <label>URL DEL POST</label>
          <div style="display:flex;gap:8px;">
            <input type="url" id="urlInput" placeholder="https://vitallifetips.com/crispy-tofu-stir-fry/">
            <button class="btn btn-secondary" onclick="fetchPost()" id="fetchBtn">Leer post</button>
          </div>
          <div class="progress-bar" id="fetchProgress" style="display:none;margin-top:8px;">
            <div class="progress-fill" id="fetchProgressFill"></div>
          </div>
        </div>
      </div>

      <div class="card" id="postPreviewCard" style="display:none;">
        <div class="section-header">
          <div class="section-title" id="postTitle">—</div>
          <span class="badge badge-accent" id="postWordCount"></span>
        </div>
        <div style="font-size:12px;color:var(--text2);line-height:1.7;max-height:140px;overflow-y:auto;" id="postPreview"></div>
      </div>

      <div class="form-group">
        <label>KEYWORD PRINCIPAL</label>
        <input type="text" id="mainKeyword" placeholder="ej: crispy sweet and sour tofu">
      </div>

      <div class="btn-row">
        <button class="btn btn-primary" onclick="goToGenerate()">Generar 12 prompts + 48 títulos →</button>
      </div>
    </div>

    <!-- PANEL 2 -->
    <div class="panel" id="panel2">
      <div>
        <div class="panel-title">Generando contenido</div>
        <div class="panel-sub">Claude está analizando el post y creando los prompts y el CSV de 48 filas.</div>
      </div>
      <div class="card">
        <div class="loading-block active" id="loadingBlock">
          <div class="spinner"></div>
          <div class="loading-text" id="loadingText">Analizando el post...</div>
          <div class="loading-step" id="loadingStep"></div>
        </div>
        <div id="errorBlock" style="display:none;padding:24px;">
          <div class="alert alert-error" id="errorMsg"></div>
          <div class="btn-row" style="margin-top:16px;">
            <button class="btn btn-secondary" onclick="goStep(1)">← Volver</button>
          </div>
        </div>
      </div>
    </div>

    <!-- PANEL 3 -->
    <div class="panel" id="panel3">
      <div>
        <div class="panel-title">Prompts de Ideogram</div>
        <div class="panel-sub">12 prompts. Genera 4 variaciones por prompt en Ideogram → 48 imágenes.</div>
      </div>

      <div id="annotationsBlock" style="display:none;">
        <div class="sidebar-label" style="margin-bottom:8px;">ANNOTATION KEYWORDS GENERADAS</div>
        <div class="annotations-list" id="annotationsList"></div>
      </div>

      <div class="section-header">
        <div class="section-title">12 prompts por tipo</div>
        <button class="btn btn-secondary" style="font-size:12px;padding:6px 12px;" onclick="copyAllPrompts()">Copiar todos</button>
      </div>
      <div class="prompts-grid" id="promptsGrid"></div>

      <div class="btn-row">
        <button class="btn btn-primary" onclick="goStep(4)">Ver CSV de 48 filas →</button>
        <button class="btn btn-secondary" onclick="goStep(1)">← Volver</button>
      </div>
    </div>

    <!-- PANEL 4 -->
    <div class="panel" id="panel4">
      <div>
        <div class="panel-title">CSV — 48 filas para Metricool</div>
        <div class="panel-sub">Ordenado por rondas: 1 de cada prompt → ronda 1, luego ronda 2, etc. Igual que en Canva.</div>
      </div>

      <div class="alert alert-info">
        <span>📋</span>
        <span>El CSV está ordenado en 4 rondas de 12. Cada ronda = una imagen de cada uno de los 12 prompts. Descarga y copia en el Google Sheet de Metricool.</span>
      </div>

      <div class="section-header">
        <div class="section-title">48 filas</div>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-primary" style="font-size:12px;padding:6px 14px;" onclick="downloadCSV()">⬇ Descargar CSV</button>
          <span class="section-count" id="csvCount"></span>
        </div>
      </div>

      <div class="csv-table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Prompt</th>
              <th>Título</th>
              <th>Descripción</th>
              <th>T</th>
              <th>D</th>
            </tr>
          </thead>
          <tbody id="csvTableBody"></tbody>
        </table>
      </div>

      <div class="btn-row">
        <button class="btn btn-secondary" onclick="goStep(3)">← Prompts</button>
        <button class="btn btn-secondary" onclick="resetAll()">Nueva sesión</button>
      </div>
    </div>
  </div>
</div>

<!-- PROFILE MODAL -->
<div class="modal-overlay" id="profileModal">
  <div class="modal">
    <div class="modal-title" id="profileModalTitle">Nueva cuenta</div>
    <div class="form-group"><label>NOMBRE DEL SITIO</label><input type="text" id="pName" placeholder="Vital Life Tips"></div>
    <div class="form-row">
      <div class="form-group"><label>NICHO</label><input type="text" id="pNiche" placeholder="wellness, recipes"></div>
      <div class="form-group">
        <label>IDIOMA DE LOS PINES</label>
        <select id="pLang"><option value="English">English</option><option value="Spanish">Spanish</option><option value="Portuguese">Portuguese</option></select>
      </div>
    </div>
    <div class="form-group"><label>VOZ DE MARCA / TONO</label><textarea id="pVoice" rows="3" placeholder="Friendly, warm and encouraging..."></textarea></div>
    <div class="form-group"><label>FRASES PROHIBIDAS</label><input type="text" id="pForbidden" placeholder='"game-changer", "unlock", "elevate"'></div>
    <div class="form-group"><label>URL DEL SITIO</label><input type="url" id="pUrl" placeholder="https://vitallifetips.com"></div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal('profileModal')">Cancelar</button>
      <button class="btn btn-primary" onclick="saveProfile()">Guardar</button>
    </div>
  </div>
</div>

<!-- SETTINGS MODAL -->
<div class="modal-overlay" id="settingsModal">
  <div class="modal">
    <div class="modal-title">Ajustes</div>
    <div class="form-group">
      <label>ANTHROPIC API KEY</label>
      <div class="apikey-row">
        <input type="password" id="apiKeyInput" placeholder="sk-ant-...">
        <button class="btn btn-secondary" onclick="toggleKey()">👁</button>
      </div>
      <div style="font-size:11px;color:var(--text3);margin-top:6px;">Se guarda solo en tu navegador.</div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-secondary" onclick="closeModal('settingsModal')">Cancelar</button>
      <button class="btn btn-primary" onclick="saveSettings()">Guardar</button>
    </div>
  </div>
</div>

<script>
// ─── STATE ───────────────────────────────────────────────────────────────────
let profiles = JSON.parse(localStorage.getItem('pp_profiles') || '[]');
let apiKey = localStorage.getItem('pp_apikey') || '';
let activeProfile = null;
let editingProfileIdx = null;
let postData = null;
let generatedPrompts = [];
let generatedCSVRows = [];
let fullResponse = '';

// Base URL — when deployed on Vercel this will be same origin
const API_BASE = window.location.origin;

// ─── INIT ─────────────────────────────────────────────────────────────────────
function init() {
  if (profiles.length === 0) {
    profiles = [{
      name: 'Vital Life Tips',
      niche: 'wellness, recipes, healthy living',
      lang: 'English',
      voice: 'Friendly, warm and encouraging. Clear and approachable. Empowering but never preachy. Energetic but grounded. Short sentences. Direct reader address.',
      forbidden: '"dive into", "game-changer", "unlock", "elevate", "transform your life"',
      url: 'https://vitallifetips.com'
    }];
    localStorage.setItem('pp_profiles', JSON.stringify(profiles));
  }
  renderProfiles();
  updateApiStatus();
}

// ─── PROFILES ─────────────────────────────────────────────────────────────────
function renderProfiles() {
  const list = document.getElementById('profileList');
  const sel = document.getElementById('activeProfileSelect');
  list.innerHTML = '';
  sel.innerHTML = '<option value="">— Selecciona una cuenta —</option>';
  profiles.forEach((p, i) => {
    const isActive = activeProfile && activeProfile.name === p.name;
    const card = document.createElement('div');
    card.className = 'profile-card' + (isActive ? ' active' : '');
    card.innerHTML = `<div class="profile-badge"></div><div class="name">${p.name}</div><div class="niche">${p.niche}</div>`;
    card.onclick = () => selectProfile(i);
    list.appendChild(card);
    const opt = document.createElement('option');
    opt.value = i; opt.textContent = p.name;
    if (isActive) opt.selected = true;
    sel.appendChild(opt);
  });
}

function selectProfile(idx) {
  if (idx === '' || idx === null) return;
  activeProfile = profiles[parseInt(idx)];
  renderProfiles();
  document.getElementById('activeProfileSelect').value = idx;
  document.getElementById('sessionSummary').innerHTML = `<strong style="color:var(--text)">${activeProfile.name}</strong><br><span style="color:var(--text3)">${activeProfile.niche}</span>`;
}

function openProfileModal(idx) {
  editingProfileIdx = idx;
  document.getElementById('profileModalTitle').textContent = idx === null ? 'Nueva cuenta' : 'Editar cuenta';
  if (idx !== null) {
    const p = profiles[idx];
    document.getElementById('pName').value = p.name;
    document.getElementById('pNiche').value = p.niche;
    document.getElementById('pLang').value = p.lang;
    document.getElementById('pVoice').value = p.voice;
    document.getElementById('pForbidden').value = p.forbidden || '';
    document.getElementById('pUrl').value = p.url || '';
  } else {
    ['pName','pNiche','pVoice','pForbidden','pUrl'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('pLang').value = 'English';
  }
  document.getElementById('profileModal').classList.add('active');
}

function saveProfile() {
  const p = {
    name: document.getElementById('pName').value.trim(),
    niche: document.getElementById('pNiche').value.trim(),
    lang: document.getElementById('pLang').value,
    voice: document.getElementById('pVoice').value.trim(),
    forbidden: document.getElementById('pForbidden').value.trim(),
    url: document.getElementById('pUrl').value.trim(),
  };
  if (!p.name) { alert('El nombre es obligatorio'); return; }
  if (editingProfileIdx !== null) profiles[editingProfileIdx] = p;
  else profiles.push(p);
  localStorage.setItem('pp_profiles', JSON.stringify(profiles));
  renderProfiles();
  closeModal('profileModal');
}

// ─── SETTINGS ─────────────────────────────────────────────────────────────────
function showSettings() { document.getElementById('apiKeyInput').value = apiKey; document.getElementById('settingsModal').classList.add('active'); }
function saveSettings() { apiKey = document.getElementById('apiKeyInput').value.trim(); localStorage.setItem('pp_apikey', apiKey); updateApiStatus(); closeModal('settingsModal'); }
function updateApiStatus() {
  document.getElementById('apiStatusDot').classList.toggle('ok', !!apiKey);
  document.getElementById('apiStatusText').textContent = apiKey ? 'API conectada' : 'Sin clave API';
}
function toggleKey() { const i = document.getElementById('apiKeyInput'); i.type = i.type === 'password' ? 'text' : 'password'; }
function closeModal(id) { document.getElementById(id).classList.remove('active'); }
document.querySelectorAll('.modal-overlay').forEach(o => o.addEventListener('click', e => { if (e.target === o) o.classList.remove('active'); }));

// ─── FETCH POST ───────────────────────────────────────────────────────────────
async function fetchPost() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) return;

  const btn = document.getElementById('fetchBtn');
  btn.textContent = 'Leyendo...';
  btn.disabled = true;

  const prog = document.getElementById('fetchProgress');
  const fill = document.getElementById('fetchProgressFill');
  prog.style.display = 'block';
  fill.style.width = '30%';

  try {
    const resp = await fetch(`${API_BASE}/api/fetch-post`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });

    fill.style.width = '80%';
    const data = await resp.json();

    if (!resp.ok) throw new Error(data.error || 'Error leyendo el post');

    postData = data;
    fill.style.width = '100%';

    // Show preview
    const card = document.getElementById('postPreviewCard');
    card.style.display = 'block';
    document.getElementById('postTitle').textContent = data.title;
    document.getElementById('postPreview').textContent = data.content.substring(0, 400) + '...';
    const words = data.content.split(/\\s+/).length;
    document.getElementById('postWordCount').textContent = `~${words} palabras`;

  } catch(e) {
    alert('Error: ' + e.message);
  } finally {
    btn.textContent = 'Leer post';
    btn.disabled = false;
    setTimeout(() => { prog.style.display = 'none'; fill.style.width = '0%'; }, 600);
  }
}

// ─── GENERATE ─────────────────────────────────────────────────────────────────
async function goToGenerate() {
  if (!activeProfile) { alert('Selecciona una cuenta'); return; }
  if (!apiKey) { alert('Configura tu clave API en ⚙ Ajustes'); return; }
  if (!postData) { alert('Lee un post primero'); return; }
  const keyword = document.getElementById('mainKeyword').value.trim();
  if (!keyword) { alert('Añade la keyword principal'); return; }

  goStep(2);

  const steps = [
    'Analizando ángulos del contenido...',
    'Asignando formatos a ángulos...',
    'Generando prompts TOBI...',
    'Generando prompts Collage...',
    'Generando prompts Storytelling, Lista y Comparación...',
    'Creando 48 títulos y descripciones únicas...',
    'Ordenando CSV por rondas...',
  ];
  let si = 0;
  const interval = setInterval(() => {
    si = (si + 1) % steps.length;
    document.getElementById('loadingStep').textContent = steps[si];
  }, 2500);

  document.getElementById('loadingBlock').style.display = 'flex';
  document.getElementById('errorBlock').style.display = 'none';

  try {
    const resp = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: apiKey,
        title: postData.title,
        content: postData.content,
        keyword,
        site_config: {
          name: activeProfile.name,
          brand_voice: activeProfile.voice,
          forbidden_phrases: activeProfile.forbidden,
          lang: activeProfile.lang
        }
      })
    });

    clearInterval(interval);
    const data = await resp.json();

    if (!resp.ok) throw new Error(data.error || 'Error generando contenido');

    fullResponse = data.full_response;
    generatedCSVRows = data.csv_rows;

    parseAndRenderPrompts(fullResponse);
    renderCSV(generatedCSVRows);
    goStep(3);

  } catch(e) {
    clearInterval(interval);
    document.getElementById('loadingBlock').style.display = 'none';
    document.getElementById('errorBlock').style.display = 'block';
    document.getElementById('errorMsg').innerHTML = '⚠ ' + e.message;
  }
}

// ─── PARSE PROMPTS ────────────────────────────────────────────────────────────
function parseAndRenderPrompts(text) {
  const grid = document.getElementById('promptsGrid');
  grid.innerHTML = '';
  generatedPrompts = [];

  // Extract annotations
  const annotMatch = text.match(/## ANNOTATION KEYWORDS\\s*([\\s\\S]*?)(?=## IMAGE PROMPTS|$)/i);
  if (annotMatch) {
    const annotations = annotMatch[1].trim().split('\\n').map(l => l.replace(/^[-*\\d.]\\s*/, '').trim()).filter(Boolean);
    if (annotations.length) {
      document.getElementById('annotationsBlock').style.display = 'block';
      const list = document.getElementById('annotationsList');
      list.innerHTML = annotations.map(a => `<span class="annotation-tag">${a}</span>`).join('');
    }
  }

  // Extract prompts by type
  const types = [
    { key: 'TOBI 1', cls: '', label: 'TOBI 1' },
    { key: 'TOBI 2', cls: '', label: 'TOBI 2' },
    { key: 'TOBI 3', cls: '', label: 'TOBI 3' },
    { key: 'COLLAGE 1', cls: 'collage', label: 'COLLAGE 1' },
    { key: 'COLLAGE 2', cls: 'collage', label: 'COLLAGE 2' },
    { key: 'COLLAGE 3', cls: 'collage', label: 'COLLAGE 3' },
    { key: 'STORYTELLING 1', cls: 'story', label: 'STORY 1' },
    { key: 'STORYTELLING 2', cls: 'story', label: 'STORY 2' },
    { key: 'LIST 1', cls: 'list', label: 'LIST 1' },
    { key: 'LIST 2', cls: 'list', label: 'LIST 2' },
    { key: 'COMPARISON 1', cls: 'comp', label: 'COMP 1' },
    { key: 'COMPARISON 2', cls: 'comp', label: 'COMP 2' },
  ];

  types.forEach((t, i) => {
    const regex = new RegExp(`\\\\[${t.key}\\\\]([\\\\s\\\\S]*?)(?=\\\\[|## CSV|$)`, 'i');
    const match = text.match(regex);
    const promptText = match ? match[1].trim() : '—';
    generatedPrompts.push(promptText);

    const card = document.createElement('div');
    card.className = 'prompt-card';
    card.innerHTML = `
      <div class="prompt-card-header">
        <span class="prompt-type ${t.cls}">${t.label}</span>
        <button class="copy-btn" onclick="copyPrompt(${i})">📋 copiar</button>
      </div>
      <div class="prompt-text" id="pt${i}">${promptText.substring(0, 300)}${promptText.length > 300 ? '...' : ''}</div>
    `;
    grid.appendChild(card);
  });
}

function copyPrompt(idx) {
  navigator.clipboard.writeText(generatedPrompts[idx]);
  const btns = document.querySelectorAll('.copy-btn');
  btns[idx].textContent = '✓ copiado';
  setTimeout(() => btns[idx].textContent = '📋 copiar', 1500);
}

function copyAllPrompts() {
  const labels = ['TOBI-1','TOBI-2','TOBI-3','COLLAGE-1','COLLAGE-2','COLLAGE-3','STORY-1','STORY-2','LIST-1','LIST-2','COMP-1','COMP-2'];
  const all = generatedPrompts.map((p, i) => `[${labels[i]}]\\n${p}`).join('\\n\\n---\\n\\n');
  navigator.clipboard.writeText(all);
}

// ─── RENDER CSV ───────────────────────────────────────────────────────────────
function renderCSV(rows) {
  const tbody = document.getElementById('csvTableBody');
  tbody.innerHTML = '';
  document.getElementById('csvCount').textContent = `${rows.length} filas`;

  const roundSize = 12;
  rows.forEach((row, i) => {
    const round = Math.floor(i / roundSize) + 1;

    // Round divider
    if (i % roundSize === 0) {
      const divRow = document.createElement('tr');
      divRow.className = 'round-divider';
      divRow.innerHTML = `<td colspan="6">Ronda ${round} — variación ${round} de cada prompt</td>`;
      tbody.appendChild(divRow);
    }

    const tLen = (row.title || '').length;
    const dLen = (row.description || '').length;
    const tClass = tLen > 100 ? 'over' : tLen > 85 ? 'warn' : '';
    const dClass = dLen > 500 ? 'over' : dLen > 450 ? 'warn' : '';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="color:var(--text3);font-family:'DM Mono',monospace;font-size:11px;">${row.row}</td>
      <td><span class="badge badge-accent" style="font-size:9px;">${row.prompt_ref}</span></td>
      <td class="title-cell">${row.title}</td>
      <td class="desc-cell">${row.description}</td>
      <td class="char-count ${tClass}" style="white-space:nowrap;">${tLen}</td>
      <td class="char-count ${dClass}" style="white-space:nowrap;">${dLen}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ─── DOWNLOAD CSV ─────────────────────────────────────────────────────────────
async function downloadCSV() {
  if (!generatedCSVRows.length) return;

  const profileName = activeProfile ? activeProfile.name.replace(/\\s+/g,'-').toLowerCase() : 'pins';
  const filename = `pinterest-${profileName}-${new Date().toISOString().slice(0,10)}.csv`;

  try {
    const resp = await fetch(`${API_BASE}/api/download-csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rows: generatedCSVRows, filename })
    });

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  } catch(e) {
    // Fallback: generate client-side
    const bom = '\\uFEFF';
    const header = 'Row,Prompt_Ref,Title,Description\\n';
    const rowsText = generatedCSVRows.map(r =>
      `${r.row},"${r.prompt_ref}","${(r.title||'').replace(/"/g,'""')}","${(r.description||'').replace(/"/g,'""')}"`
    ).join('\\n');
    const blob = new Blob([bom + header + rowsText], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  }
}

// ─── NAVIGATION ───────────────────────────────────────────────────────────────
function goStep(n) {
  document.querySelectorAll('.panel').forEach((p, i) => p.classList.toggle('active', i+1 === n));
  document.querySelectorAll('.step-item').forEach((s, i) => {
    s.classList.remove('active', 'done');
    if (i+1 < n) s.classList.add('done');
    else if (i+1 === n) s.classList.add('active');
  });
}

function resetAll() {
  postData = null; generatedPrompts = []; generatedCSVRows = []; fullResponse = '';
  document.getElementById('urlInput').value = '';
  document.getElementById('mainKeyword').value = '';
  document.getElementById('postPreviewCard').style.display = 'none';
  document.getElementById('annotationsBlock').style.display = 'none';
  goStep(1);
}

init();
</script>
</body>
</html>

"""

@app.route('/')
def index():
    return HTML_PAGE, 200, {'Content-Type': 'text/html; charset=utf-8'}


def get_post_content(url: str) -> dict:
    """Extract post content via WordPress REST API using the post slug."""
    url = url.rstrip('/')
    
    # Extract slug from URL
    slug = url.split('/')[-1]
    
    # Determine base domain
    match = re.match(r'(https?://[^/]+)', url)
    if not match:
        raise ValueError("URL no válida")
    base = match.group(1)
    
    # Call WP REST API
    api_url = f"{base}/wp-json/wp/v2/posts?slug={slug}&_fields=title,content,excerpt"
    resp = requests.get(api_url, timeout=15)
    resp.raise_for_status()
    
    data = resp.json()
    if not data:
        raise ValueError("No se encontró el post. Verifica que la URL sea correcta.")
    
    post = data[0]
    title = post.get('title', {}).get('rendered', '')
    raw_content = post.get('content', {}).get('rendered', '')
    
    # Strip HTML tags
    clean_content = re.sub(r'<[^>]+>', '', raw_content)
    clean_content = re.sub(r'\n{3,}', '\n\n', clean_content).strip()
    
    # Limit to ~6000 chars to avoid token overflow
    if len(clean_content) > 6000:
        clean_content = clean_content[:6000] + '...'
    
    return {'title': title, 'content': clean_content}


def build_prompt(title: str, content: str, keyword: str, site_config: dict) -> str:
    brand_voice = site_config.get('brand_voice', 'Friendly, warm and encouraging. Clear and approachable. Empowering but never preachy. Energetic but grounded.')
    forbidden = site_config.get('forbidden_phrases', '"dive into", "game-changer", "unlock", "elevate", "transform your life"')
    lang = site_config.get('lang', 'English')
    site_name = site_config.get('name', 'the blog')

    return f"""You are a Pinterest SEO expert and Ideogram prompt specialist creating high-engagement Pin content for {site_name}.

BLOG POST TITLE: {title}

BLOG POST CONTENT:
{content}

MAIN KEYWORD: {keyword}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 — INTERNAL ANALYSIS (do not output this phase)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before generating any output, silently complete the following:

1. ANNOTATION KEYWORDS
Generate 12–15 Pinterest annotation keywords naturally derived from the post content. These must be specific niche terms Pinterest uses to categorize and distribute content — not generic tags. Prioritize long-tail, intent-specific terms.

2. CONTENT ANGLE ANALYSIS
Identify 8 distinct content angles present in or applicable to this post. Each angle must represent a genuinely different reader intent, emotional state, or use case (e.g. beginner, transformation, speed, skeptic, meal prep, better-than-restaurant, social, health-conscious).

3. FORMAT-TO-ANGLE ASSIGNMENT
Assign each of the 12 image prompts to its strongest angle match:
- TOBI (3): angles best as single aspirational/emotional images
- Collage (3): angles that benefit from showing process or comparison
- Storytelling (2): angles with the strongest narrative hook potential
- List/Number (2): angles best expressed as concrete information
- Comparison (2): angles that naturally set up an A vs B tension

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 — IMAGE PROMPTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate exactly 12 Ideogram prompts. Each will produce 4 image variations (total: 48 pins).

Requirements for ALL prompts:
- Minimum 60 words each
- Specify: composition, lighting, background, props, color palette
- Include exact text overlay wording (benefit or transformation driven, CTA when natural)
- Vertical 2:3 ratio, Pinterest-optimized
- Text overlay: large, bold, legible on mobile
- No watermarks, no logos
- Output language: {lang}

TOBI PROMPTS (3): Single hero image. Large bold text overlay.
Moods: (1) bright/aspirational, (2) moody/dramatic, (3) minimal/clean.

COLLAGE PROMPTS (3): Multi-panel layout.
Structures: (1) step-by-step process grid, (2) ingredients + final dish flat lay, (3) before/after transformation panels.

STORYTELLING PROMPTS (2): Hook-first visual. No process shots. Text overlay uses first-person or direct address with an open loop — reader wants to know what happens next.

LIST/NUMBER PROMPTS (2): Typographic-forward. Large number prominent. Overlay leads with the number and promises specific value.

COMPARISON PROMPTS (2): Two-panel or split layout. Clear visual contrast. Text frames the tension: "X vs Y". Reader must want to click to find out the answer.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 — CSV (48 rows)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate exactly 48 rows. Each of the 12 prompts gets 4 unique title/description combinations.

CRITICAL ORDERING RULE:
Order by variation round, NOT by prompt group. This matches how images are arranged in Canva (one from each prompt per round, then repeat).

Round 1 (rows 1–12):   TOBI-1, TOBI-2, TOBI-3, COLLAGE-1, COLLAGE-2, COLLAGE-3, STORY-1, STORY-2, LIST-1, LIST-2, COMP-1, COMP-2
Round 2 (rows 13–24):  same prompt order, second variation
Round 3 (rows 25–36):  same prompt order, third variation
Round 4 (rows 37–48):  same prompt order, fourth variation

STRICT RULES:
- Title: max 100 characters including spaces. NEVER exceed.
- Description: max 500 characters including spaces. NEVER exceed.
- Zero repeated titles across all 48 rows
- Zero repeated opening sentences across all 48 rows
- Every description: main keyword + at least 2 annotation keywords integrated naturally
- Rotate angles — no single angle dominates more than 8 rows
- Natural CTA in at least 30 of the 48 descriptions
- Output language: {lang}

BRAND VOICE ({site_name}):
{brand_voice}
Forbidden phrases: {forbidden}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT — RESPOND IN THIS EXACT STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANNOTATION KEYWORDS
[list]

## IMAGE PROMPTS
[TOBI 1]
...
[TOBI 2]
...
[TOBI 3]
...
[COLLAGE 1]
...
[COLLAGE 2]
...
[COLLAGE 3]
...
[STORYTELLING 1]
...
[STORYTELLING 2]
...
[LIST 1]
...
[LIST 2]
...
[COMPARISON 1]
...
[COMPARISON 2]
...

## CSV
Output ONLY a raw CSV block between the markers below. No explanation, no markdown formatting inside.
Columns: Row,Prompt_Ref,Title,Description
Use double quotes around Title and Description fields.
Escape internal double quotes by doubling them ("").

<<<CSV_START>>>
Row,Prompt_Ref,Title,Description
[48 rows here]
<<<CSV_END>>>

## BOARD SUGGESTIONS
[3–5 boards with one-line rationale each]
"""


def parse_csv_from_response(text: str) -> list[dict]:
    """Extract CSV rows from Claude response."""
    match = re.search(r'<<<CSV_START>>>\s*(.*?)\s*<<<CSV_END>>>', text, re.DOTALL)
    if not match:
        return []
    
    csv_text = match.group(1).strip()
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = []
    for row in reader:
        rows.append({
            'row': row.get('Row', ''),
            'prompt_ref': row.get('Prompt_Ref', ''),
            'title': row.get('Title', ''),
            'description': row.get('Description', '')
        })
    return rows


def generate_csv_file(rows: list[dict]) -> bytes:
    """Generate UTF-8 BOM CSV bytes from rows."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow(['Row', 'Prompt_Ref', 'Title', 'Description'])
    for r in rows:
        writer.writerow([r['row'], r['prompt_ref'], r['title'], r['description']])
    
    # UTF-8 BOM for Google Sheets compatibility
    return b'\xef\xbb\xbf' + output.getvalue().encode('utf-8')


@app.route('/api/fetch-post', methods=['POST'])
def fetch_post():
    """Fetch WordPress post content from URL."""
    data = request.json
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL requerida'}), 400
    
    try:
        post = get_post_content(url)
        return jsonify(post)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/generate', methods=['POST'])
def generate():
    """Generate Pinterest content using Claude via OpenRouter."""
    data = request.json
    
    api_key = data.get('api_key', '').strip()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    keyword = data.get('keyword', '').strip()
    site_config = data.get('site_config', {})
    
    if not all([api_key, title, content, keyword]):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
    
    try:
        prompt = build_prompt(title, content, keyword, site_config)
        
        resp = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://pinterest-pipeline.vercel.app',
                'X-Title': 'Pinterest Pipeline'
            },
            json={
                'model': 'anthropic/claude-sonnet-4-5',
                'max_tokens': 8000,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=120
        )

        if resp.status_code == 401:
            return jsonify({'error': 'Clave API inválida'}), 401
        if not resp.ok:
            return jsonify({'error': f'Error OpenRouter: {resp.status_code} — {resp.text[:200]}'}), 500

        result = resp.json()
        response_text = result['choices'][0]['message']['content']
        csv_rows = parse_csv_from_response(response_text)
        
        return jsonify({
            'full_response': response_text,
            'csv_rows': csv_rows,
            'csv_count': len(csv_rows)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download-csv', methods=['POST'])
def download_csv():
    """Generate and return a downloadable CSV file."""
    data = request.json
    rows = data.get('rows', [])
    filename = data.get('filename', 'pinterest-pins.csv')
    
    if not rows:
        return jsonify({'error': 'No hay filas para exportar'}), 400
    
    csv_bytes = generate_csv_file(rows)
    
    return Response(
        csv_bytes,
        mimetype='text/csv; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )




@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'Pinterest Pipeline API'})


if __name__ == '__main__':
    app.run(debug=False)
