const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.resolve(__dirname, '../../assist_ai_router/app/static/app.js'), 'utf8');
function ui() {
  const context = vm.createContext({structuredClone, Intl, document: {querySelectorAll: () => []}});
  // Load the real UI functions without starting network/polling/bootstrap handlers.
  vm.runInContext(source.slice(0, source.indexOf("$('#close-editor').onclick")) + `
    render = () => {}; notice = () => {};
    globalThis.subject = {state, bindApiKeyMask, moveProvider, removeProvider};
  `, context);
  return context;
}
function configure(context, fail = false) {
  const state = context.subject.state;
  state.cfg = {providers: ['a', 'b', 'c'].map(id => ({id, name: id, api_key_set: true, api_key_reference: '!secret ' + id})), rules: [{provider_ids: 'a,c'}]};
  state.revision = 'initial';
  const writes = [];
  context.mockApi = async (route, method, body) => {
    if (route === 'status') return {providers: []};
    assert.equal(route, 'settings'); assert.equal(method, 'PUT');
    if (fail) throw Error('config_conflict');
    writes.push(structuredClone(body));
    return {options: body.options, revision: 'saved'};
  };
  vm.runInContext('api = mockApi;', context);
  return writes;
}

test('key typing, paste and deletion only expose the exact incremental secret marker', () => {
  const {subject} = ui();
  const listeners = {};
  const input = {value: '', addEventListener: (name, fn) => {listeners[name] = fn;}};
  subject.bindApiKeyMask(input);
  assert.equal(input.type, 'password');
  for (const value of ['!', '!s', '!se', '!sec', '!secr', '!secre', '!secret', '!secret existing_key']) {
    input.value = value; listeners.input(); assert.equal(input.type, 'text', value);
  }
  for (const value of ['!secretX', '!sx', ' !secret key', 'literal-key', '!SECRET key', '']) {
    input.value = value; listeners.input(); assert.equal(input.type, 'password', value);
  }
});

test('moving in either direction sends ordered options without overwriting saved credentials', async () => {
  const context = ui(); const writes = configure(context);
  await context.subject.moveProvider('a', 'c', true);
  assert.deepEqual(Array.from(context.subject.state.cfg.providers, p => p.id), ['b', 'c', 'a']);
  await context.subject.moveProvider('a', 'b');
  assert.deepEqual(Array.from(context.subject.state.cfg.providers, p => p.id), ['a', 'b', 'c']);
  assert.equal(writes.length, 2);
  for (const write of writes) {
    for (const profile of write.options.providers) {
      assert(!('api_key' in profile));
      assert(!('api_key_reference' in profile));
      assert(!('api_key_set' in profile));
    }
    assert.equal(write.options.rules[0].provider_ids, 'a,c');
  }
});

test('unchanged or stale drop targets never write options', async () => {
  const context = ui(); const writes = configure(context);
  for (const [id, target, after] of [['a','a',true], ['a','b',false], ['c','b',true], ['missing','b',false], ['a',undefined,false]]) {
    await context.subject.moveProvider(id,target,after);
  }
  assert.equal(writes.length, 0);
});

test('a rejected save preserves the active order and clears the saving flag', async () => {
  const context = ui(); configure(context, true);
  await assert.rejects(context.subject.moveProvider('c','a'), /config_conflict/);
  assert.deepEqual(Array.from(context.subject.state.cfg.providers, p => p.id), ['a','b','c']);
  assert.equal(context.subject.state.revision, 'initial');
  assert.equal(context.subject.state.saving, false);
});

test('sorting is ignored while another settings save is in progress', async () => {
  const context = ui(); const writes = configure(context);
  context.subject.state.saving = true;
  await context.subject.moveProvider('c','a');
  assert.equal(writes.length,0);
});


function editorUi(handlers) {
  class Element {
    constructor(tag) { this.tagName = tag; this.children = []; this.listeners = {}; this.isConnected = true; this.value = ''; }
    append(...items) { this.children.push(...items); }
    prepend(...items) { this.children.unshift(...items); }
    replaceChildren(...items) { this.children = items; }
    setAttribute(name, value) { this[name] = value; }
    removeAttribute(name) { delete this[name]; }
    contains(item) { return item === this || this.children.some(child => child.contains?.(item)); }
    focus() {}
    dispatchEvent(event) { for (const fn of this.listeners[event.type] || []) fn(event); }
    addEventListener(name, fn) { (this.listeners[name] ||= []).push(fn); }
    showModal() { this.open = true; }
  }
  const nodes = Object.fromEntries(['provider-fields','editor-title','cancel-editor','save-provider','close-editor','provider-form','editor','notice'].map(id => ['#'+id,new Element('div')]));
  const document = {createElementNS: (_, tag) => new Element(tag), createElement: tag => new Element(tag), createTextNode: text => text, querySelector: q => nodes[q]};
  const context = vm.createContext({structuredClone, Intl, document, crypto: {getRandomValues: a => a}, Event, calls: [], handlers});
  vm.runInContext(source.slice(0, source.indexOf("$('#close-editor').onclick")) + `
    api = async (route, method, body) => { calls.push({route, body}); return handlers[route] ? handlers[route](body) : {}; };
    state.catalog = [{id:'groq',name:'Groq',prefix:'groq'}];
    globalThis.open = () => openEditor({id:'a',name:'Saved',preset:'groq',model:'groq/previous',api_key_set:true,api_base:''});
  `, context);
  const walk = e => [e, ...(e.children || []).flatMap(walk)];
  const all = () => walk(nodes['#provider-fields']);
  const toggle = () => all().find(e => e.className === 'model-toggle').listeners.click[0]();
  return {context, nodes, all, toggle, options: () => { toggle(); const list = all().find(e => e.id === 'model-options'); const result = list.children.filter(e => e.role === 'option').map(e => e.textContent); toggle(); return result; }};
}
const flush = () => new Promise(resolve => setImmediate(resolve));

test('saved-provider discovery works even if original-credential prefill fails', async () => {
  const page = editorUi({
    'provider-credential': () => { throw Error('supervisor_unavailable'); },
    models: () => ({groq:['sdk-fallback']}),
    'provider-models': () => ({models:['groq/live'],complete:true})
  });
  page.context.open(); await flush(); await flush();
  assert.deepEqual(Array.from(page.options()), ['groq/live']);
  assert(page.context.calls.some(c => c.route === 'provider-models'));
  assert(page.context.calls.filter(c => c.route === 'provider-models').every(c => !('api_key' in c.body)));
});

test('slow credential prefill and SDK catalog cannot block live provider results', async () => {
  let sdkResolve;
  const page = editorUi({
    'provider-credential': () => new Promise(() => {}),
    models: () => new Promise(resolve => { sdkResolve = resolve; }),
    'provider-models': () => ({models:['groq/live'],complete:true})
  });
  page.context.open(); await flush(); await flush();
  assert.deepEqual(Array.from(page.options()), ['groq/live']);
  sdkResolve({groq:['stale-sdk']}); await flush();
  assert.deepEqual(Array.from(page.options()), ['groq/live']);
});


test('editing keeps the saved model while the dropdown exposes and selects other provider models', async () => {
  const page = editorUi({
    'provider-credential': () => ({api_key:'original'}),
    models: () => ({groq:[]}),
    'provider-models': () => ({models:['groq/other-a','groq/other-b'],complete:true})
  });
  page.context.open(); await flush(); await flush();
  const input = page.all().find(e => e.name === 'model');
  assert.equal(input.value, 'groq/previous');
  assert.deepEqual(Array.from(page.options()), ['groq/other-a','groq/other-b']);
  page.toggle();
  const option = page.all().find(e => e.textContent === 'groq/other-b' && e.role === 'option');
  option.listeners.click[0]();
  assert.equal(input.value, 'groq/other-b');
  assert.equal(page.all().find(e => e.id === 'model-options').hidden, true);
});


test('model dropdown supports keyboard navigation and Escape', async () => {
  const page = editorUi({'provider-models': () => ({models:['groq/a','groq/b'],complete:true}), models: () => ({groq:[]})});
  page.context.open(); await flush(); await flush();
  const input = page.all().find(e => e.name === 'model');
  const key = name => input.listeners.keydown[0]({key:name,preventDefault(){},stopPropagation(){}});
  key('ArrowUp'); key('Enter');
  assert.equal(input.value,'groq/b');
  key('ArrowDown'); key('Enter');
  assert.equal(input.value,'groq/a');
  page.toggle(); key('Escape');
  assert.equal(page.all().find(e => e.id === 'model-options').hidden,true);
});


test('provider deletion requires confirmation and cleans rule targets while preserving other profiles', async () => {
  const context = ui(); const writes = configure(context);
  context.subject.state.cfg.rules.push({provider_ids:'a'});
  context.confirm = () => false;
  await context.subject.removeProvider('a','First'); assert.equal(writes.length,0);
  context.confirm = () => true;
  await context.subject.removeProvider('a','First');
  assert.deepEqual(Array.from(context.subject.state.cfg.providers,p=>p.id),['b','c']);
  assert.deepEqual(Array.from(context.subject.state.cfg.rules,r=>r.provider_ids),['c']);
  assert.equal(writes.length,1);
});
