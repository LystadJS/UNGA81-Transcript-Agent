'use strict';

/* Real Chromium UI QA. Only invented fixtures. No real speech sources. */

const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');
const { makeSyntheticFrame } = require('./synthetic_fixture.cjs');
const { summarize, validateReport } = require('./position_core.cjs');

const ROOT = __dirname;
const codebook = JSON.parse(fs.readFileSync(path.join(ROOT, 'propositions.v1.json'), 'utf8'));
const report = summarize(makeSyntheticFrame(codebook), codebook);
validateReport(report);

async function startPage(browser, file, width, height) {
  const context = await browser.newContext({
    viewport: { width, height },
    acceptDownloads: true,
    reducedMotion: 'reduce'
  });
  let externalRequests = 0;
  await context.route(/^https?:\/\//, route => {
    externalRequests++;
    return route.abort('blockedbyclient');
  });
  const page = await context.newPage();
  const problems = [];
  page.on('pageerror', error => problems.push(error.message));
  await page.goto(pathToFileURL(path.join(ROOT, file)).href, { waitUntil: 'load' });
  return {
    page,
    context,
    problems,
    getExternalRequests: () => externalRequests
  };
}

async function assertNoOverflow(page) {
  const sizing = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    width: window.innerWidth
  }));
  assert.ok(sizing.scrollWidth <= sizing.width + 2,
    'Unexpected horizontal overflow: ' + JSON.stringify(sizing));
}

async function checkViewer(browser, temporary, width) {
  const { page, context, problems, getExternalRequests } =
    await startPage(browser, 'viewer.html', width, 900);
  try {
    assert.match(await page.locator('h1').innerText(), /Country Position/);
    assert.match(await page.locator('body').innerText(), /fictional/i);
    assert.equal(await page.locator('#results').isHidden(), true);
    const reportPath = path.join(temporary, 'fictional-report-' + width + '.json');
    fs.writeFileSync(reportPath, JSON.stringify(report), { flag: 'wx' });
    await page.locator('#file').setInputFiles(reportPath);
    await page.waitForFunction(() => !document.getElementById('results').hidden);
    assert.equal(await page.locator('#year').isEnabled(), true);
    assert.equal(await page.locator('#year option').count(), 2);
    assert.equal(await page.locator('#network circle').count(), 6);
    assert.ok((await page.locator('#matrix tbody tr').count()) === 6);
    assert.ok((await page.locator('#pairs button').count()) >= 1);
    assert.match(await page.locator('#status').innerText(), /Fictional/);
    assert.match(await page.locator('#inspection').innerText(), /Inspect source evidence/);

    const firstCell = page.locator('#matrix tbody tr:first-child td button').first();
    await firstCell.focus();
    await page.keyboard.press('Enter');
    assert.match(await page.locator('#inspection').innerText(), /synthetic|Fictional|retained/i);
    assert.ok(await page.locator('#inspection .evidence').count() >= 1);

    await page.locator('#pairs button').first().click();
    assert.ok(await page.locator('#inspection .evidence').count() >= 2);
    assert.match(await page.locator('#inspection').innerText(), /SHA-256/);

    await page.locator('#year').selectOption('2026');
    assert.match(await page.locator('#status').innerText(), /2026/);
    await page.locator('#year').selectOption('2025');
    assert.match(await page.locator('#status').innerText(), /2025/);
    assert.equal(await page.locator('#network circle').count(), 6);
    await assertNoOverflow(page);

    // Viewer must refuse even a one-field rebranding of an empirical result.
    const bad = { ...report, publication_eligible: true };
    const badPath = path.join(temporary, 'forbidden-report-' + width + '.json');
    fs.writeFileSync(badPath, JSON.stringify(bad), { flag: 'wx' });
    await page.locator('#file').setInputFiles(badPath);
    await page.waitForFunction(() => document.getElementById('results').hidden);
    assert.match(await page.locator('#status').innerText(), /Report rejected/);
    assert.equal(getExternalRequests(), 0);
    assert.deepEqual(problems, []);
  } finally {
    await context.close();
  }
}

async function checkAnnotation(browser, temporary, width) {
  const { page, context, problems, getExternalRequests } =
    await startPage(browser, 'annotation.html', width, 900);
  try {
    assert.equal(await page.locator('#save').isDisabled(), true);
    const pkt = {
      schema: 'un.country-positions.annotation-packet.v1',
      dataset_kind: 'unreviewed',
      publication_eligible: false,
      packet_sha256: 'a'.repeat(64),
      items: [{
        item_id: 'fictional-review-item',
        country_affiliation: 'ALP',
        event_date: '2026-09-24',
        source_id: 'fictional-source-1',
        issue_id: 'ai_governance',
        proposition_id: 'ai_binding',
        proposition: 'Fictional actor explicitly supports binding international AI governance rules.',
        scope: 'Fictional AI governance policy object.',
        exclusion_rule: 'Generic AI mentions cannot establish a stance.',
        quote: 'Invented example supports a fictional binding AI rule.',
        context_before: 'Invented preceding context only.',
        context_after: 'Invented following context only.',
        source_url: 'https://example.org/fictional-original',
        start: 0, end: 52
      }]
    };
    const packetPath = path.join(temporary, 'fictional-annotation-packet-' + width + '.json');
    fs.writeFileSync(packetPath, JSON.stringify(pkt), { flag: 'wx' });
    await page.locator('#packet').setInputFiles(packetPath);
    await page.waitForFunction(() => !document.getElementById('save').disabled);
    assert.equal(await page.locator('#items article').count(), 1);
    assert.equal(await page.locator('#items a').count(), 1);
    assert.equal(await page.locator('article details').count(), 1);
    await page.locator('article summary').click();
    assert.match(await page.locator('article details').innerText(), /Invented preceding context/);
    assert.equal(await page.locator('#items a').first().getAttribute('rel'), 'noopener noreferrer');

    await page.locator('#reviewer').fill('reviewer-test');
    await page.locator('#attest').check();
    const selects = page.locator('article .answers select');
    await selects.nth(0).selectOption('relevant');
    await selects.nth(1).selectOption('support');
    await page.locator('article textarea').fill(
      'This is entirely invented, and the fictional text explicitly endorses the rule.'
    );
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.locator('#save').click()
    ]);
    assert.match(download.suggestedFilename(), /private-draft.json/);
    const downloaded = JSON.parse(fs.readFileSync(await download.path(), 'utf8'));
    assert.equal(downloaded.finalized, false);
    assert.equal(downloaded.human_gold, false);
    assert.equal(downloaded.human_confirmation, true);
    assert.equal(downloaded.publication_eligible, false);
    assert.equal(downloaded.decisions.length, 1);
    assert.equal(downloaded.decisions[0].issue_label, 'relevant');
    assert.equal(downloaded.decisions[0].stance_label, 'support');

    // Re-opening the saved human draft must restore the selections and notes.
    const draftPath = path.join(temporary, 'fictional-review-draft-' + width + '.json');
    fs.writeFileSync(draftPath, JSON.stringify(downloaded), { flag: 'wx' });
    await page.locator('#resume').setInputFiles(draftPath);
    assert.equal(await selects.nth(0).inputValue(), 'relevant');
    assert.equal(await selects.nth(1).inputValue(), 'support');
    assert.match(await page.locator('article textarea').inputValue(), /entirely invented/);
    assert.equal(await page.locator('#attest').isChecked(), true);

    // A duplicated ID inside the imported draft remains invalid, even though
    // a legitimate one-item replay over existing local state is now allowed.
    const duplicated = { ...downloaded,
      decisions: [...downloaded.decisions, downloaded.decisions[0]] };
    const duplicatePath = path.join(temporary, 'duplicate-draft-' + width + '.json');
    fs.writeFileSync(duplicatePath, JSON.stringify(duplicated), { flag: 'wx' });
    await page.locator('#resume').setInputFiles(duplicatePath);
    await page.waitForFunction(() => document.getElementById('status')
      .textContent.includes('Unknown/duplicate draft item'));
    assert.match(await page.locator('#status').innerText(), /duplicate/);

    // Incompatible packet digests must fail closed, not restore another review.
    const wrong = { ...downloaded, packet_sha256: 'b'.repeat(64) };
    const wrongPath = path.join(temporary, 'wrong-draft-' + width + '.json');
    fs.writeFileSync(wrongPath, JSON.stringify(wrong), { flag: 'wx' });
    await page.locator('#resume').setInputFiles(wrongPath);
    assert.match(await page.locator('#status').innerText(), /mismatch/);
    await assertNoOverflow(page);
    assert.equal(getExternalRequests(), 0);
    assert.deepEqual(problems, []);
  } finally {
    await context.close();
  }
}

async function main() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'un-supervised-browser-'));
  const browserOptions = { headless: true };
  if (process.env.PW_CHANNEL) browserOptions.channel = process.env.PW_CHANNEL;
  const browser = await chromium.launch(browserOptions);
  let passes = 0;
  try {
    for (const width of [1440, 390]) {
      await checkViewer(browser, tmp, width);
      console.log('PASS viewer: ' + width + 'px, evidence, year change, publication refusal');
      passes++;
      await checkAnnotation(browser, tmp, width);
      console.log('PASS annotation: ' + width + 'px, keyboard, export, replay, digest mismatch');
      passes++;
    }
    console.log('PASS browser QA; scenarios=' + passes +
      '; original/private source requests=0');
  } finally {
    await browser.close();
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

main().catch(error => {
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
