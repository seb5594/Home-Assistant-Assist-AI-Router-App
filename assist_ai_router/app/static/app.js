'use strict';
const $ = (q, root = document) => root.querySelector(q);
const state = {cfg: null, revision: '', status: null, catalog: [], models: {}, words: {}, lang: 'de', page: 'overview', setupIntegration: 'litellm', saving: false, draggedProviderId: null};
const pages = {overview: '🏠', providers: '🧩', routing: '🔀', activity: '📊', setup: '🔗', settings: '⚙️'};
const t = (key) => state.words[state.lang]?.[key] ?? state.words.en?.[key] ?? key;
const fmt = (n) => new Intl.NumberFormat(state.lang).format(n || 0);
function el(tag, text, cls) { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; if (cls) e.className = cls; return e; }
function button(text, action, cls) { const e = el('button', text, cls); e.type = 'button'; e.addEventListener('click', () => guard(action)); return e; }
function withIcon(element, symbol) { const icon = el('span', symbol, 'ui-icon'); icon.ariaHidden = 'true'; element.prepend(icon, document.createTextNode(' ')); return element; }
const actionIcons = {add_provider: '➕', edit: '✏️', test: '🧪', pause_provider: '⏸️', resume_provider: '▶️', remove: '🗑️', start_setup: '🔗', add_rule: '➕', check_versions: '🔎', reveal_connection: '🔑'};
function actionButton(key, action, cls) { return withIcon(button(t(key), action, cls), actionIcons[key] || '⚙️'); }
function providerIcon(preset) { return ({gemini: '✨', groq: '⚡', cerebras: '🧠', openrouter: '🔀', mistral: '🌬️', huggingface: '🤗', github: '🐙', cloudflare: '☁️', openai: '🌀', anthropic: '💬', azure: '☁️', ollama_chat: '🦙', openai_compatible: '🖥️'})[preset] || '🧠'; }
function link(text, url) { const e = el('a', text); e.href = url; e.target = '_blank'; e.rel = 'noopener noreferrer'; return e; }
function notice(message, error = false) { const e = $('#notice'); e.hidden = false; e.className = error ? 'error' : ''; e.textContent = message; }
async function guard(action) { try { await action(); } catch (error) { notice(t(error.message), true); } }
async function api(path, method = 'GET', body) {
  const response = await fetch(`api/${path}`, {method, headers: {'Content-Type': 'application/json', 'X-Requested-With': 'AssistAIRouter'}, body: body === undefined ? undefined : JSON.stringify(body), cache: 'no-store'});
  const data = await response.json(); if (!response.ok) throw new Error(data.error?.code || 'network_error'); return data;
}
async function save(candidate) {
  if (state.saving) throw new Error('save_in_progress'); state.saving = true;
  try {
    for (const p of candidate.providers) { delete p.api_key_set; delete p.api_key_reference; }
    const data = await api('settings', 'PUT', {options: candidate, revision: state.revision});
    state.cfg = data.options; state.revision = data.revision; state.status = await api('status');
    notice(t('saved')); render();
  } finally { state.saving = false; }
}
function cloneCfg() { return structuredClone(state.cfg); }
function heading(title, action) { const row = el('div', undefined, 'section-head'); row.append(el('h2', title)); if (action) row.append(action); return row; }
function note(text) { return el('p', text, 'note'); }
function empty() { const box = el('div', undefined, 'empty'); box.append(el('span', '◈', 'hero-mark'), el('h2', t('empty_title')), el('p', t('empty_text')), actionButton('add_provider', () => { location.hash = 'providers'; openEditor(); }, 'primary')); return box; }
function field(key, value, type = 'text', help = '', label) {
  const wrap = el('label', undefined, `field${type === 'checkbox' ? ' check' : ''}`);
  const name = el('span', label || t(key)); const input = el('input'); input.name = key; input.type = type;
  if (type === 'checkbox') { input.checked = Boolean(value); wrap.append(input, name); }
  else { input.value = value ?? ''; wrap.append(name, input); }
  if (help) wrap.append(el('small', help));
  return {wrap, input};
}
function selectField(key, value, options, label) {
  const wrap = el('label', undefined, 'field'); wrap.append(el('span', label || t(key))); const input = el('select'); input.name = key;
  for (const [v, text] of options) { const option = el('option', text); option.value = v; input.append(option); } input.value = value; wrap.append(input); return {wrap, input};
}
function bindApiKeyMaskValue(input) {
  const value = input.value;
  input.type = value.startsWith('!') && ('!secret'.startsWith(value) || /^!secret\s/.test(value)) ? 'text' : 'password';
}
function bindApiKeyMask(input) {
  input.addEventListener('input', () => bindApiKeyMaskValue(input)); bindApiKeyMaskValue(input);
}
async function moveProvider(id, targetId, after = false) {
  if (state.saving || id === targetId) return;
  const c = cloneCfg();
  const from = c.providers.findIndex(p => p.id === id);
  if (from < 0 || !c.providers.some(p => p.id === targetId)) return;
  const [profile] = c.providers.splice(from, 1);
  const to = c.providers.findIndex(p => p.id === targetId) + (after ? 1 : 0);
  c.providers.splice(to, 0, profile);
  if (c.providers.every((p, i) => p.id === state.cfg.providers[i].id)) return;
  await save(c);
  notice(`${t('provider_order_saved')} ${profile.name}: ${t('position')} ${to + 1}.`);
  const handle = [...document.querySelectorAll('.drag-handle')].find(e => e.dataset.providerId === id);
  handle?.focus();
}
function providerList(compact = false) {
  const list = el('ol', undefined, 'provider-list');
  list.ariaLabel = t('provider_order');
  const clearDrag = () => {
    state.draggedProviderId = null;
    for (const row of list.children) row.classList.remove('drop-before', 'drop-after', 'dragging');
  };
  state.cfg.providers.forEach((p, index) => {
    const row = el('li'); row.append(providerCard(p, index, compact));
    const handle = $('.drag-handle', row);
    handle.addEventListener('dragstart', event => {
      if (state.saving) { event.preventDefault(); return; }
      state.draggedProviderId = p.id;
      event.dataTransfer.effectAllowed = 'move';
      event.dataTransfer.setData('text/plain', p.id);
      row.classList.add('dragging');
    });
    handle.addEventListener('dragend', clearDrag);
    const isAfter = event => event.clientY > row.getBoundingClientRect().top + row.getBoundingClientRect().height / 2;
    row.addEventListener('dragover', event => {
      if (!state.draggedProviderId || state.draggedProviderId === p.id || state.saving) return;
      event.preventDefault(); event.dataTransfer.dropEffect = 'move';
      for (const item of list.children) item.classList.remove('drop-before', 'drop-after');
      row.classList.add(isAfter(event) ? 'drop-after' : 'drop-before');
    });
    row.addEventListener('dragleave', event => {
      if (!row.contains(event.relatedTarget)) row.classList.remove('drop-before', 'drop-after');
    });
    row.addEventListener('drop', event => {
      if (!state.draggedProviderId) return;
      event.preventDefault();
      const id = state.draggedProviderId; const after = isAfter(event);
      clearDrag(); guard(() => moveProvider(id, p.id, after));
    });
    list.append(row);
  });
  return list;
}
function render() {
  if (!state.cfg || !state.status) return;
  state.page = location.hash.slice(1) in pages ? location.hash.slice(1) : 'overview';
  document.documentElement.lang = state.lang; $('#language').value = state.lang;
  $('#page-title').textContent = t(state.page); $('#refresh').ariaLabel = t('refresh');
  $('#sync').textContent = t(state.status.synchronized ? 'synced' : 'local_mode');
  $('#version').textContent = `${state.status.version} · LiteLLM ${state.status.litellm}`;
  $('#nav').replaceChildren(...Object.entries(pages).map(([key, icon]) => { const a = el('a', undefined, key === state.page ? 'active' : ''); a.href = `#${key}`; const marker = el('span', icon); marker.ariaHidden = 'true'; a.append(marker, document.createTextNode(t(key))); return a; }));
  const content = $('#content'); content.replaceChildren();
  ({overview: renderOverview, providers: renderProviders, routing: renderRouting, activity: renderActivity, setup: renderSetup, settings: renderSettings})[state.page](content);
}
function providerCard(p, index, compact = false) {
  const status = state.status.providers.find(x => x.id === p.id);
  const card = el('article', undefined, 'provider'); const top = el('div', undefined, 'provider-top');
  const order = el('div', undefined, 'provider-order');
  const rank = el('span', `#${index + 1}`, 'provider-rank'); rank.ariaLabel = `${t('position')} ${index + 1}`;
  const handle = button('⠿', () => {}, 'drag-handle'); handle.draggable = true; handle.dataset.providerId = p.id;
  handle.ariaLabel = `${t('drag_provider')}: ${p.name}`; handle.title = t('drag_provider');
  const up = button('↑', () => moveProvider(p.id, state.cfg.providers[index - 1]?.id));
  up.ariaLabel = `${t('move_up')}: ${p.name}`; up.title = t('move_up'); up.disabled = index === 0;
  const down = button('↓', () => moveProvider(p.id, state.cfg.providers[index + 1]?.id, true));
  down.ariaLabel = `${t('move_down')}: ${p.name}`; down.title = t('move_down'); down.disabled = index === state.cfg.providers.length - 1;
  order.append(rank, handle, up, down); card.append(order);
  const name = el('div', undefined, 'provider-name'); name.append(el('h3', p.name), el('small', p.model));
  top.append(el('div', providerIcon(p.preset), 'provider-logo'), name, el('span', t(status?.status || 'untested'), `pill ${status?.status || ''}`)); card.append(top);
  const quota = el('div', undefined, 'quota');
  for (const [key, period, metric] of [['daily_tokens', 'day', 'tokens'], ['monthly_tokens', 'month', 'tokens'], ['daily_requests', 'day', 'requests']]) {
    if (key !== 'daily_tokens' && !p[key]) continue;
    const used = status?.usage[period][metric] || 0; const row = el('div', undefined, 'quota-row');
    row.append(el('span', t(key)), el('span', `${fmt(used)} / ${p[key] ? fmt(p[key]) : t('unknown')}`)); quota.append(row);
    if (p[key]) { const meter = el('progress'); meter.max = p[key]; meter.value = Math.min(used, p[key]); meter.ariaLabel = t(key); quota.append(meter); }
  }
  card.append(quota);
  if (status?.health.until > Date.now() / 1000) card.append(el('p', `${t('retry_at')} ${new Date(status.health.until * 1000).toLocaleTimeString(state.lang)}`, 'muted'));
  const actions = el('div', undefined, 'actions');
  const toggle = actionButton(p.enabled ? 'pause_provider' : 'resume_provider', async () => {
    const c = cloneCfg(); const profile = c.providers.find(item => item.id === p.id);
    profile.enabled = !p.enabled;
    await save(c);
    notice(t(profile.enabled ? 'provider_resumed' : 'provider_paused'));
  });
  toggle.title = t('pause_provider_hint');
  toggle.setAttribute('aria-pressed', String(!p.enabled));
  const test = actionButton('test', async () => { notice(t('testing')); const data = await api('test', 'POST', {provider_id: p.id}); state.status = await api('status'); render(); notice(`${t('test_success')} · ${fmt(data.usage?.total_tokens)} tokens`); });
  test.disabled = !p.enabled;
  if (!p.enabled) test.title = t('resume_before_test');
  actions.append(toggle, actionButton('edit', () => openEditor(p)), test);
  if (!compact) {
    const remove = actionButton('remove', async () => {
      if (!confirm(`${t('remove_confirm')} ${p.name}?`)) return;
      const c = cloneCfg(); c.providers.splice(index, 1);
      c.rules = c.rules.map(r => ({...r, provider_ids: r.provider_ids.split(',').filter(id => id.trim() !== p.id).join(',')})).filter(r => r.provider_ids);
      await save(c);
    }, 'danger'); actions.append(remove);
  }
  const preset = state.catalog.find(x => x.id === p.preset); if (preset) actions.append(link(t('provider_dashboard') + ' ↗', preset.usage_url));
  card.append(actions); return card;
}
function renderOverview(root) {
  const hero = el('section', undefined, 'hero'); const copy = el('div'); copy.append(el('h2', t('hero_title')), el('p', t('hero_text'))); hero.append(copy, el('span', '⇄', 'hero-mark')); root.append(hero);
  const successes = state.status.recent.filter(r => r.status === 'success');
  const cards = [[state.cfg.providers.filter(p => p.enabled).length, 'active_providers', 'configured_order'], [state.status.providers.filter(p => p.status === 'ready').length, 'ready_providers', 'after_test'], [new Set(state.status.recent.filter(r => r.status === 'success' && state.status.recent.some(x => x.request_id === r.request_id && x.id < r.id && x.status === 'error')).map(r => r.request_id)).size, 'rescued', 'recent_100'], [successes.reduce((n, r) => n + r.tokens, 0), 'tokens', 'recent_100']];
  const stats = el('div', undefined, 'stats'); for (const [value, label, hint] of cards) { const box = el('div', undefined, 'stat'); box.append(el('span', t(label), 'muted'), el('strong', fmt(value)), el('span', t(hint), 'muted')); stats.append(box); } root.append(stats);
  root.append(heading(t('your_providers'), actionButton('add_provider', () => { location.hash = 'providers'; openEditor(); }, 'primary')));
  if (!state.cfg.providers.length) root.append(empty());
  else root.append(note(t('provider_order_hint')), providerList(true));
  root.append(note(t('quota_note')));
  const quick = el('section', undefined, 'panel'); quick.append(el('h2', t('connect_assist')), el('p', t('connect_text'), 'muted'), actionButton('start_setup', () => { location.hash = 'setup'; })); root.append(quick);
}
function renderProviders(root) {
  root.append(el('p', t('providers_intro'), 'muted'));
  if (state.cfg.providers.length) root.append(note(t('provider_order_hint')), providerList());
  root.append(heading(t('catalog_title'))); root.append(note(t('catalog_note')));
  const search = el('input'); search.type = 'search'; search.placeholder = t('search_provider'); search.ariaLabel = t('search_provider'); const toolbar = el('div', undefined, 'toolbar'); toolbar.append(search); root.append(toolbar);
  const grid = el('div', undefined, 'catalog');
  function fill() { grid.replaceChildren(); state.catalog.filter(p => p.name.toLowerCase().includes(search.value.toLowerCase())).forEach(p => { const b = button(`${providerIcon(p.id)} ${p.name} +`, () => openEditor(null, p)); b.append(el('small', p.local ? t('local_provider') : t('check_free_tier'))); grid.append(b); }); }
  search.addEventListener('input', fill); fill(); root.append(grid);
}
function openEditor(existing, preset) {
  preset = preset || state.catalog.find(c => c.id === existing?.preset) || state.catalog[0];
  const newId = `p_${Array.from(crypto.getRandomValues(new Uint8Array(6)), x => x.toString(16).padStart(2, '0')).join('')}`;
  let p = existing ? structuredClone(existing) : {id: newId, name: preset.name, preset: preset.id, model: preset.example_model ? `${preset.prefix}/${preset.example_model}` : `${preset.prefix}/`, api_base: preset.local ? 'http://homeassistant.local:11434' : '', enabled: true, free_only: false, local: preset.local, supports_tools: true, supports_vision: false};
  const fields = $('#provider-fields'); fields.replaceChildren(); $('#editor-title').textContent = t(existing ? 'edit_provider' : 'add_provider');
  $('#cancel-editor').textContent = t('cancel'); $('#save-provider').textContent = t('save'); $('#close-editor').ariaLabel = t('close');
  const grid = el('div', undefined, 'form-grid'); const presetField = selectField('preset', p.preset, state.catalog.map(c => [c.id, c.name])); presetField.input.disabled = Boolean(existing); grid.append(presetField.wrap);
  grid.append(field('name', p.name).wrap); const model = field('model', p.model, 'text', t('model_hint')); model.input.required = true; model.input.setAttribute('list', 'model-list'); grid.append(model.wrap);
  const models = el('datalist'); models.id = 'model-list'; grid.append(models);
  const liveStatus = el('small', t('provider_models_auto_hint'), 'full'); liveStatus.setAttribute('role', 'status');
  let keyEdited = false;
  const draftCredentials = () => {
    const draft = {id: p.id, preset: p.preset, api_base: apiBase.input.value.trim()};
    if (clear.input.checked) draft.api_key = '';
    else if ((!existing || keyEdited) && key.input.value.trim()) draft.api_key = key.input.value.trim();
    return draft;
  };
  const fillModels = values => models.replaceChildren(...values.map(value => { const option = el('option'); option.value = value; return option; }));
  const sdkSuggestions = async () => {
    if (!Object.keys(state.models).length) state.models = await api('models');
    const prefix = preset.prefix;
    return (state.models[prefix] || []).map(value => value.startsWith(prefix + '/') ? value : prefix + '/' + value);
  };
  let discoveryGeneration = 0;
  let lastDraft = null;
  const refreshModels = async () => {
    const draft = draftCredentials(); const signature = JSON.stringify(draft);
    if (lastDraft === signature) return;
    lastDraft = signature;
    const generation = ++discoveryGeneration;
    const current = () => generation === discoveryGeneration && liveStatus.isConnected && $('#editor').open && JSON.stringify(draftCredentials()) === signature;
    fillModels([]);
    liveStatus.textContent = t('provider_models_loading');
    guard(() => refreshAccount(draft, current));
    let providerLoaded = false;
    // The SDK catalog is a fallback, never a prerequisite for live discovery.
    sdkSuggestions().then(suggestions => {
      if (current() && !providerLoaded) fillModels(suggestions);
    }).catch(() => { /* Manual entry and live discovery remain available. */ });
    const anonymous = ['openrouter', 'huggingface', 'nvidia_nim', 'openai_compatible', 'ollama_chat'].includes(p.preset);
    if (!(draft.api_key || (p.api_key_set && !clear.input.checked) || anonymous)) {
      liveStatus.textContent = t('provider_models_auto_hint'); return;
    }
    try {
      const data = await api('provider-models', 'POST', draft);
      if (!current()) return;
      providerLoaded = true;
      fillModels(data.models);
      liveStatus.textContent = `${fmt(data.models.length)} ${t(data.complete ? 'provider_models_loaded' : 'provider_models_partial')}`;
    } catch (error) {
      if (!current()) return;
      liveStatus.textContent = `${t(error.message)} ${t('models_fallback_hint')}`;
    }
  };
  const credentialsEdited = () => {
    discoveryGeneration++; lastDraft = null; fillModels([]);
    liveStatus.textContent = t('provider_models_auto_hint');
  };
  const key = field('api_key', p.api_key_reference || '', 'password', t('key_hint')); bindApiKeyMask(key.input); key.input.autocomplete = 'new-password'; key.input.spellcheck = false; key.input.autocapitalize = 'none'; key.input.placeholder = p.api_key_set ? t('keep_key') : '!secret my_ai_key'; grid.append(key.wrap);
  const revealKey = button(t('show_hide'), () => { key.input.type = key.input.type === 'password' ? 'text' : 'password'; });
  key.wrap.append(revealKey);
  key.input.addEventListener('input', () => { keyEdited = true; });
  const clear = field('clear_key', false, 'checkbox'); if (existing) grid.append(clear.wrap);
  const apiBase = field('api_base', p.api_base || '', 'text', t('base_hint'));
  grid.append(apiBase.wrap, liveStatus);
  for (const input of [key.input, apiBase.input]) { input.addEventListener('input', credentialsEdited); input.addEventListener('change', () => guard(refreshModels)); }
  clear.input.addEventListener('change', () => { credentialsEdited(); guard(refreshModels); });
  for (const k of ['enabled', 'free_only', 'local', 'supports_tools', 'supports_vision']) grid.append(field(k, p[k], 'checkbox').wrap);
  fields.append(grid);
  const advanced = el('details'); advanced.append(el('summary', t('advanced_limits'))); const limits = el('div', undefined, 'form-grid');
  for (const k of ['rpm', 'tpm', 'daily_tokens', 'daily_requests', 'monthly_tokens', 'context_tokens', 'input_price', 'output_price', 'monthly_budget']) { const f = field(k, p[k] || 0, 'number'); f.input.min = '0'; f.input.step = k.includes('price') || k === 'monthly_budget' ? '0.000001' : '1'; limits.append(f.wrap); }
  limits.append(field('quota_group', p.quota_group || '', 'text', t('quota_group_hint')).wrap, field('api_version', p.api_version || '').wrap); advanced.append(limits, note(t('limit_hint'))); fields.append(advanced);
  const account = el('section', undefined, 'account-panel'); account.append(el('h3', t('provider_account')));
  const accountStatus = el('p', t('provider_account_hint'), 'muted'); accountStatus.setAttribute('role', 'status');
  const accountValues = el('div'); account.append(accountStatus, accountValues);
  const info = preset.offer;
  if (info) {
    account.append(el('p', `${t('documented_plans')}: ${info.name}`, 'muted'), note(t('offer_' + p.preset)), link(`${t('official_limits')} · ${info.checked} ↗`, info.source));
    const examples = el('div', undefined, 'actions');
    const showExample = () => {
      examples.replaceChildren();
      const limits = info.limits_by_model[model.input.value.trim()];
      if (!limits) return;
      examples.append(button(t('apply_limit_example'), () => {
        for (const [name, value] of Object.entries(limits)) fields.querySelector(`[name=${name}]`).value = value;
        const advanced = $('details', fields); advanced.open = true;
        notice(t('limit_example_applied'));
      }), el('small', Object.entries(limits).map(([name, value]) => `${t(name)}: ${fmt(value)}`).join(' · ')));
    };
    model.input.addEventListener('input', showExample); model.input.addEventListener('change', showExample);
    showExample(); account.append(examples, note(t('limit_example_warning')));
  } else account.append(note(t('provider_account_unknown')));
  fields.append(account);
  async function refreshAccount(draft, current) {
    accountValues.replaceChildren(); accountStatus.textContent = t('provider_account_loading');
    try {
      const data = await api('provider-account', 'POST', draft);
      if (!current()) return;
      accountStatus.textContent = data.status === 'available' ? `${t(data.plan)} · ${new Date(data.checked_at * 1000).toLocaleString(state.lang)}` : t('provider_account_' + data.status);
      for (const value of data.values) accountValues.append(el('p', `${t('account_' + value.kind)}: ${new Intl.NumberFormat(state.lang, {maximumFractionDigits: 6}).format(value.value)} ${value.unit === 'requests' ? t('requests') : value.unit}`, 'account-value'));
      if (data.status === 'available') accountValues.append(note(t('account_values_hint')));
    } catch (error) { if (current()) accountStatus.textContent = t(error.message); }
  }
  const portal = el('div', undefined, 'actions'); portal.append(link(t('get_key') + ' ↗', preset.setup_url)); fields.append(portal);
  presetField.input.addEventListener('change', () => {
    const chosen = state.catalog.find(x => x.id === presetField.input.value); $('#editor').close(); openEditor(null, chosen);
  });
  $('#provider-form').onsubmit = (event) => {
    event.preventDefault(); guard(async () => {
      const c = cloneCfg(); const next = {id: p.id};
      for (const input of fields.querySelectorAll('input,select')) {
        if (!input.name || ['api_key', 'clear_key'].includes(input.name)) continue;
        next[input.name] = input.type === 'checkbox' ? input.checked : input.type === 'number' ? Number(input.value) : input.value.trim();
      }
      if (!existing || (keyEdited && key.input.value) || clear.input.checked) next.api_key = clear.input.checked ? '' : key.input.value.trim();
      if (!next.name || !next.model.split('/')[1]) throw new Error('invalid_model');
      const index = c.providers.findIndex(x => x.id === next.id); if (index < 0) c.providers.push(next); else c.providers[index] = next;
      $('#save-provider').disabled = true;
      try { await save(c); $('#editor').close(); } finally { $('#save-provider').disabled = false; }
    });
  };
  $('#editor').showModal();
  guard(refreshModels);
  if (existing) guard(async () => {
    const revision = state.revision;
    const data = await api('provider-credential', 'POST', {provider_id: p.id, revision});
    if (!key.input.isConnected || !$('#editor').open) return;
    if (!keyEdited && !clear.input.checked) { key.input.value = data.api_key; bindApiKeyMaskValue(key.input); }
  });
}
function renderRouting(root) {
  root.append(el('p', t('routing_intro'), 'muted'));
  const presets = el('div', undefined, 'presets'); for (const k of ['priority', 'quota', 'round_robin', 'local_first']) { const b = button('', async () => { const c = cloneCfg(); c.routing = k; await save(c); }, `preset ${state.cfg.routing === k ? 'selected' : ''}`); b.append(el('h3', `${state.cfg.routing === k ? '●' : '○'} ${t(k)}`), el('p', t(k + '_description'))); presets.append(b); } root.append(presets);
  root.append(note(t('rule_semantics'))); const panel = el('section', undefined, 'panel'); panel.append(el('h2', t('custom_rules')));
  state.cfg.rules.forEach((r, index) => { const row = el('div', undefined, 'rule'); const title = el('div'); title.append(el('strong', r.name), el('small', `${r.alias} → ${state.cfg.providers.filter(p => r.provider_ids.split(',').map(id => id.trim()).includes(p.id)).map(p => p.name).join(' → ')}${r.require_tools ? ' · ' + t('require_tools') : ''}`)); row.append(title, button('↑', async () => { if (!index) return; const c = cloneCfg(); [c.rules[index - 1], c.rules[index]] = [c.rules[index], c.rules[index - 1]]; await save(c); }), actionButton('remove', async () => { const c = cloneCfg(); c.rules.splice(index, 1); await save(c); }, 'danger')); panel.append(row); });
  if (!state.cfg.rules.length) panel.append(el('p', t('no_rules'), 'muted'));
  const form = el('form'); const grid = el('div', undefined, 'form-grid'); const name = field('rule_name', ''); name.input.required = true; const alias = field('alias', 'assist-auto', 'text', t('alias_hint')); alias.input.required = true;
  const tools = field('require_tools', false, 'checkbox'); grid.append(name.wrap, alias.wrap, tools.wrap); form.append(grid);
  const ids = el('div', undefined, 'form-grid'); const choices = []; state.cfg.providers.forEach(p => { const f = field(p.id, false, 'checkbox', '', p.name); choices.push(f.input); ids.append(f.wrap); }); form.append(el('p', t('rule_targets'), 'muted'), ids);
  const submit = el('button', t('add_rule'), 'primary'); submit.type = 'submit'; form.append(submit);
  form.addEventListener('submit', e => { e.preventDefault(); guard(async () => { const targets = choices.filter(x => x.checked).map(x => x.name); if (!targets.length) throw new Error('invalid_rules'); const c = cloneCfg(); c.rules.push({name: name.input.value.trim(), alias: alias.input.value.trim(), require_tools: tools.input.checked, provider_ids: targets.join(',')}); await save(c); }); }); panel.append(form); root.append(panel);
}
function renderActivity(root) {
  root.append(el('p', t('activity_intro'), 'muted'), note(t('estimate_note')));
  const panel = el('div', undefined, 'panel'); const toolbar = el('div', undefined, 'toolbar'); const filter = el('input'); filter.type = 'search'; filter.placeholder = t('filter_requests'); filter.ariaLabel = t('filter_requests');
  toolbar.append(filter, button(t('export_csv'), () => { const columns = ['request_id', 'provider', 'ts', 'status', 'input_tokens', 'output_tokens', 'tokens', 'estimated', 'cost', 'latency_ms', 'reason']; const csv = [columns.join(','), ...state.status.recent.map(r => columns.map(k => '"' + String(r[k] ?? '').replaceAll('"', '""') + '"').join(','))].join('\r\n'); const url = URL.createObjectURL(new Blob([csv], {type: 'text/csv;charset=utf-8'})); const a = el('a'); a.href = url; a.download = 'assist-ai-router-usage.csv'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); })); panel.append(toolbar);
  const wrap = el('div', undefined, 'table-wrap'); const table = el('table'); const head = el('thead'); const row = el('tr'); for (const key of ['time', 'provider', 'status', 'input', 'output', 'total', 'latency', 'request_id']) row.append(el('th', t(key))); head.append(row); const body = el('tbody'); table.append(head, body); wrap.append(table); panel.append(wrap); root.append(panel);
  function fill() { body.replaceChildren(); for (const r of state.status.recent.filter(r => [r.request_id, r.provider, r.reason].join(' ').includes(filter.value))) { const tr = el('tr'); const name = state.cfg.providers.find(p => p.id === r.provider)?.name || r.provider; const values = [new Date(r.ts * 1000).toLocaleTimeString(state.lang), name, t(r.reason || r.status), `${r.estimated ? '≈ ' : ''}${fmt(r.input_tokens)}`, `${r.estimated ? '≈ ' : ''}${fmt(r.output_tokens)}`, fmt(r.tokens), `${fmt(r.latency_ms)} ms`, r.request_id.slice(0, 12)]; values.forEach(v => tr.append(el('td', v))); body.append(tr); } if (!body.children.length) { const tr = el('tr'); const td = el('td', t('no_requests')); td.colSpan = 8; tr.append(td); body.append(tr); } }
  filter.addEventListener('input', fill); fill();
}
function connectionRow(label, value, secret = false) {
  const wrapper = el('div'); wrapper.append(el('small', label)); const row = el('div', undefined, 'connection-row'); const input = el('input'); input.value = value; input.readOnly = true; input.type = secret ? 'password' : 'text'; input.ariaLabel = label;
  row.append(input, button(t('copy'), async () => { if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(value); else { input.type = 'text'; input.focus(); input.select(); if (!document.execCommand('copy')) throw new Error('copy_manually'); if (secret) input.type = 'password'; } notice(t('copied')); })); if (secret) row.append(button(t('show_hide'), () => { input.type = input.type === 'password' ? 'text' : 'password'; })); wrapper.append(row); return wrapper;
}
function renderSetup(root) {
  root.append(el('p', t('setup_intro'), 'muted'));
  const integration = selectField('setup_integration', state.setupIntegration, [['litellm', t('integration_native')], ['mcp_assist', t('integration_mcp_assist')]]);
  integration.input.addEventListener('change', () => { state.setupIntegration = integration.input.value; render(); });
  root.append(integration.wrap);
  const steps = el('section', undefined, 'panel steps');
  function step(title, description) { const row = el('div', undefined, 'step'); const box = el('div'); box.append(el('h2', title), el('p', description)); row.append(box); steps.append(row); return box; }
  const first = step(t('setup_1'), t('setup_1_text')); first.append(button(t('manage_providers'), () => { location.hash = 'providers'; }));
  if (state.setupIntegration === 'mcp_assist') {
    const install = step(t('mcp_assist_install'), t('mcp_assist_install_text'));
    const installLinks = el('div', undefined, 'actions');
    installLinks.append(link(t('open_hacs_repository') + ' ↗', 'https://my.home-assistant.io/redirect/hacs_repository/?owner=mike-nott&repository=mcp-assist&category=integration'), link(t('mcp_assist_project') + ' ↗', 'https://github.com/mike-nott/mcp-assist'));
    install.append(installLinks);
    const connect = step(t('mcp_assist_connect'), t('mcp_assist_connect_text'));
    const connection = el('div');
    connect.append(actionButton('reveal_connection', async () => {
      const data = await api('connection', 'POST', {integration: 'mcp_assist'});
      connection.replaceChildren(connectionRow(t('mcp_assist_server_type'), data.server_type), connectionRow(t('mcp_assist_base_url'), data.base_url), connectionRow(t('router_key'), data.api_key, true), connectionRow(t('model'), data.model), connectionRow(t('mcp_assist_timeout'), String(data.request_timeout)));
      connection.append(note(t('mcp_assist_url_hint')));
      const actions = el('div', undefined, 'actions'); actions.append(link(t('open_mcp_assist') + ' ↗', data.assist_url), link(t('mcp_assist_project') + ' ↗', data.docs_url)); connection.append(actions);
    }), connection);
    const finish = step(t('mcp_assist_finish'), t('mcp_assist_finish_text'));
    finish.append(link(t('open_assist') + ' ↗', 'https://my.home-assistant.io/redirect/voice_assistants/'));
    root.append(steps, note(t('mcp_assist_boundary')));
    return;
  }
  const second = step(t('setup_2'), t('setup_2_text')); const connection = el('div'); second.append(actionButton('reveal_connection', async () => { const data = await api('connection', 'POST', {}); connection.replaceChildren(connectionRow(t('base_url'), data.base_url), connectionRow(t('router_key'), data.api_key, true), connectionRow(t('model'), data.model)); const actions = el('div', undefined, 'actions'); actions.append(link(t('open_litellm') + ' ↗', data.assist_url), link(t('official_docs') + ' ↗', data.docs_url)); connection.append(actions); }), connection);
  const third = step(t('setup_3'), t('setup_3_text')); third.append(link(t('open_assist') + ' ↗', 'https://my.home-assistant.io/redirect/voice_assistants/'));
  const fourth = step(t('setup_4'), t('setup_4_text')); const actions = el('div', undefined, 'actions'); actions.append(link(t('mcp_server') + ' ↗', 'https://my.home-assistant.io/redirect/config_flow_start/?domain=mcp_server'), link(t('mcp_client') + ' ↗', 'https://my.home-assistant.io/redirect/config_flow_start/?domain=mcp')); fourth.append(actions); root.append(steps, note(t('setup_boundary')));
}
function renderSettings(root) {
  const form = el('form', undefined, 'panel'); form.append(el('h2', t('gateway_settings'))); const grid = el('div', undefined, 'form-grid');
  for (const key of ['max_output_tokens', 'request_timeout', 'attempt_timeout', 'max_attempts', 'cooldown_seconds', 'reserve_percent', 'history_days']) { const f = field(key, state.cfg[key], 'number'); f.input.min = key === 'reserve_percent' ? '0' : '1'; f.input.step = '1'; grid.append(f.wrap); }
  grid.append(field('gateway_url', state.cfg.gateway_url, 'text', t('gateway_url_hint')).wrap, field('allow_paid', state.cfg.allow_paid, 'checkbox').wrap); form.append(grid, note(t('paid_hint'))); const submit = el('button', t('save'), 'primary'); submit.type = 'submit'; form.append(submit); root.append(form);
  form.addEventListener('submit', e => { e.preventDefault(); guard(async () => { const c = cloneCfg(); for (const input of form.querySelectorAll('input')) c[input.name] = input.type === 'checkbox' ? input.checked : input.type === 'number' ? Number(input.value) : input.value.trim(); await save(c); }); });
  const versions = el('section', undefined, 'panel'); versions.append(el('h2', t('versions')), el('p', `LiteLLM ${state.status.litellm} · ${t('reviewed_pin')} ${state.status.pinned}`, 'muted'), actionButton('check_versions', async () => { const data = await api('versions', 'POST', {}); notice(`${t(data.update_available ? 'update_available' : 'up_to_date')} · ${data.latest}`); versions.append(link(t('release_notes') + ' ↗', data.url)); }), note(t('version_hint'))); root.append(versions);
}
async function load() { const [settings, status, catalog] = await Promise.all([api('settings'), api('status'), api('catalog')]); state.cfg = settings.options; state.revision = settings.revision; state.status = status; state.catalog = catalog; state.lang = state.cfg.language; render(); }
$('#close-editor').onclick = $('#cancel-editor').onclick = () => $('#editor').close();
$('#editor').addEventListener('close', () => { const key = $('[name=api_key]', $('#provider-fields')); if (key) { key.value = ''; key.type = 'password'; } });
$('#refresh').onclick = () => guard(load);
$('#language').onchange = () => guard(async () => { const lang = $('#language').value; const c = cloneCfg(); c.language = lang; await save(c); state.lang = lang; render(); });
window.addEventListener('hashchange', render);
window.addEventListener('unhandledrejection', () => notice(t('network_error'), true));
(async () => { state.words = await (await fetch('i18n.json')).json(); $('#content').append(el('p', t('loading'), 'loading')); await guard(load); })();
setInterval(() => { if (!state.cfg || state.saving || state.draggedProviderId || document.hidden || $('#editor').open || !['overview', 'providers', 'activity'].includes(state.page)) return; guard(async () => { const status = await api('status'); if (state.saving || state.draggedProviderId || $('#editor').open) return; state.status = status; render(); }); }, 15000);
