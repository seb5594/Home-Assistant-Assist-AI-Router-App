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
    globalThis.subject = {state, bindApiKeyMask, moveProvider};
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
