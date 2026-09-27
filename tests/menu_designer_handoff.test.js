const { chromium } = require('playwright');
const PID = 'ddc4bb5b-70e6-4581-8aae-1b4042cd75ef', PROP = '39f31e1d-e41a-4382-9e38-731789ae325c';
let fails = 0; const out = [];
const check = (n, c, d) => { out.push((c ? 'PASS ' : 'FAIL ') + n + (d !== undefined ? ' :: ' + JSON.stringify(d) : '')); if (!c) fails++; };
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium', args: ['--no-sandbox'] });
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 } });
  const calls = [];
  await ctx.route('**/*', async r => {
    const u = r.request().url();
    if (u.startsWith('file://') || u.startsWith('data:')) return r.continue();
    const body = JSON.parse(r.request().postData() || '{}');
    if (u.includes('phg-menu-design')) {
      calls.push('design:' + body.action + (body.revision ? '@' + body.revision : ''));
      if (body.sync_token !== 'tok' || body.menu_project_id !== PID) return r.fulfill({ status: 403, contentType: 'application/json', body: '{"error":"invalid_menu_token"}' });
      if (body.action === 'design_status') return r.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'ok', tasks: [{ task_id: 't1', status: 'approved', source: 'user_prompt_flow', request: 'One-page cocktail menu', created_at: '2026-09-28T01:00:00Z', proposals: [{ proposal_id: PROP, version: 2, status: 'approved', reasoning: 'Signature cocktails first', problems: [] }, { proposal_id: 'x', version: 1, status: 'auto_rejected', problems: ['item not in the draft or the inputs (invented?): Unicorn Spritz'] }] }] }) });
      if (body.action === 'request_design') return r.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'queued', task_id: 't2', base_revision: 3 }) });
      if (body.action === 'take_approved') return r.fulfill({ contentType: 'application/json', body: JSON.stringify({ proposal_id: PROP, doc: { title: 'Designed Menu', sections: [{ id: 'sec1', name: 'Signature Cocktails', items: [{ id: 'itm1', name: 'Dry Cider', prices: [{ value: 9 }], badges: [], meta: {} }], subs: [] }] }, current_revision: 3 }) });
      if (body.action === 'mark_applied') return r.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'applied', revision: body.revision }) });
    }
    if (u.includes('phg-menu-adapter')) {
      calls.push('adapter:' + body.action + '@' + body.expected_revision + ':' + (body.doc && body.doc.title));
      if (body.action === 'sync_menu') return r.fulfill({ contentType: 'application/json', body: JSON.stringify({ menu_project_id: PID, revision: 4, mappings: [], synced_at: '2026-09-28T01:05:00Z' }) });
      return r.fulfill({ contentType: 'application/json', body: '{}' });
    }
    return r.abort();
  });
  const p = await ctx.newPage(); const errs = [];
  p.on('pageerror', e => errs.push(String(e.message).slice(0, 200)));
  await p.goto('file:///home/user/phg-harmony-app/index.html', { waitUntil: 'load', timeout: 60000 });
  await p.evaluate(() => { PHGAUTH.session = { access_token: 'user' }; });
  const setup = await p.evaluate((PID) => {
    try {
      MDC.doc = { title: 'Old Menu', sections: [mdcSection('Cocktails')], phg: { menu_project_id: PID, revision: 3, sync_token: 'tok' } };
      MDC.doc.sections[0].items.push(mdcItem('Dry Cider'));
      MDC.hist = [mdcSnap()]; MDC.histAt = 0; MDC.savedSnap = MDC.hist[0];
      return 'ok';
    } catch (e) { return 'ERR ' + e.message; }
  }, PID);
  check('test doc set up', setup === 'ok', setup);
  await p.evaluate(() => mdcDesignToggle()); await p.waitForTimeout(400);
  const panel = await p.evaluate(() => mdcDesignPanel());
  check('panel lists the approved proposal with Apply', /Apply to draft/.test(panel) && /Approved, ready to apply/.test(panel), panel.length);
  check('panel shows the failed check reason', /Unicorn Spritz/.test(panel));
  await p.evaluate(() => mdcDesignRequest('Make a brunch menu', 'user_prompt_flow')); await p.waitForTimeout(400);
  check('request sent then status reloaded', calls.includes('design:request_design'), calls);
  await p.evaluate((PROP) => mdcDesignApply(PROP), PROP); await p.waitForTimeout(200);
  await p.evaluate(() => phgConfirmAccept()); await p.waitForTimeout(800);
  const st = await p.evaluate(() => ({ title: MDC.doc.title, link: MDC.doc.phg, hist: MDC.hist.length, msg: MDDES.msg, sec: MDC.doc.sections[0].name }));
  check('design applied on screen, PHG link kept', st.title === 'Designed Menu' && st.sec === 'Signature Cocktails' && st.link.menu_project_id === PID && st.link.sync_token === 'tok', st);
  check('saved through Sync PHG with expected revision 3', calls.some(c => c === 'adapter:sync_menu@3:Designed Menu'), calls);
  check('marked applied at the new revision 4', calls.includes('design:mark_applied@4'), calls);
  check('undo history kept (old menu restorable)', st.hist >= 2, st.hist);
  const undone = await p.evaluate(() => { const seen = []; for (let i = 0; i < 3 && MDC.doc.title !== 'Old Menu'; i++) { mdcUndo(); seen.push(MDC.doc.title); } return seen; });
  check('undo brings the old menu back within 2 steps', undone.length <= 2 && undone[undone.length - 1] === 'Old Menu', undone);
  check('no page errors', !errs.length, errs);
  console.log(out.join('\n')); console.log(fails ? fails + ' FAILED' : 'ALL PASSED');
  await b.close(); process.exit(fails ? 1 : 0);
})();
