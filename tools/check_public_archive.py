"""Anonymous real-browser checks; public metadata only, never UN source requests."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

SITES = {'source':'https://lystadjs.github.io/UNGA81-Transcript-Agent/',
         'portfolio':'https://lystadjs.github.io/un/transcript-agent/'}


def verify_site(browser, name, url, width, cutoff=None):
    context = browser.new_context(viewport={'width':width, 'height':900}, reduced_motion='reduce')
    page = context.new_page()
    manifests, errors, forbidden = [], [], []
    def response_seen(response):
        if response.status == 200 and urlsplit(response.url).path.endswith('/latest.json'):
            value = response.json()
            if value.get('schema') == 'un.archive.v1':
                manifests.append(value)
    def request_seen(request):
        if urlsplit(request.url).hostname == 'transcripts.un.org' or request.method not in ('GET','HEAD'):
            forbidden.append('source_or_write_request')
        if 'authorization' in request.headers:
            forbidden.append('credential_header')
    page.on('response', response_seen)
    page.on('request', request_seen)
    page.on('pageerror', lambda _: errors.append('page_error'))
    try:
        page.goto(url+'archive.html', wait_until='load', timeout=30000)
        expect(page.locator('#snapshotId')).to_have_text(re.compile(r'^\d{8}T\d{6}Z-[0-9a-f]+$'), timeout=60000)
        expect(page.locator('#verificationStatus')).to_contain_text('SHA-256')
        assert manifests, 'No actual public manifest response observed'
        manifest = manifests[-1]
        expect(page.locator('#snapshotId')).to_have_text(manifest['snapshot_id'])
        stamp = datetime.fromisoformat(manifest['generated_at'].replace('Z','+00:00'))
        now = datetime.now(timezone.utc)
        assert stamp.tzinfo and -300 <= (now-stamp).total_seconds() <= 48*3600, 'Public snapshot freshness bound failed'
        if cutoff:
            assert stamp >= cutoff, 'Public snapshot predates the successful warehouse run'
        count = int(page.locator('#meetingCount').inner_text().replace(',',''))
        assert count == manifest['coverage']['meetings'] and count > 0
        expect(page.get_by_role('columnheader',name='Archived text',exact=True)).to_be_visible()
        expect(page.get_by_role('columnheader',name='Latest collection check',exact=True)).to_be_visible()
        visible_rows=page.locator('#meetingRows tr').evaluate_all('(rows) => rows.map(row => Array.from(row.cells, cell => cell.textContent))')
        assert visible_rows, 'No actual meeting rows for availability verification'
        for cells in visible_rows:
            assert len(cells)==6 and cells[5].isdigit(), 'Unexpected availability table contract'
            assert cells[3]==('Text archived' if int(cells[5])>0 else 'No text archived'), 'Archived text confused with collection attempt'
        overview=page.locator('#coverageSummary').inner_text()
        match=re.fullmatch(r'(\d+) meetings with archived text\. Latest collection checks: .+\.',overview)
        assert match and 0<=int(match[1])<=count, 'Missing separate archive/attempt coverage'
        accepted = manifest['model_status'] in ('accepted','evaluated_accepted')
        if not accepted:
            expect(page.locator('#modelStatus')).to_contain_text('withheld')
        page.locator('#archiveSearch').fill('__synthetic_absent_query_8372__')
        expect(page.locator('#meetingRows tr')).to_have_count(0)
        page.locator('#clearFilters').click()
        expect(page.locator('#meetingRows tr').first).to_be_visible()
        page.locator('#archiveSearch').focus()
        expect(page.locator('#archiveSearch')).to_be_focused()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Page overflow'
        descriptor = manifest['downloads'][0]
        with page.expect_download(timeout=30000) as download:
            page.locator('#downloadList button').first.click()
        data = Path(download.value.path()).read_bytes()
        assert len(data) == descriptor['bytes'] and hashlib.sha256(data).hexdigest() == descriptor['sha256']
        expect(page.locator('#downloadStatus')).to_have_text('Verified download saved.')
        assert not forbidden and not errors, 'Unexpected source/write/credential request or page error'
        return {'site':name, 'width':width, 'snapshot_id':manifest['snapshot_id'],
                'generated_at':manifest['generated_at'], 'known_meetings':count,
                'model_accepted':accepted, 'hash_verified_download':True, 'source_requests':0,
                'availability_columns_verified':True,'visible_availability_rows_verified':len(visible_rows),
                'meetings_with_archived_text':int(match[1])}
    finally:
        context.close()


def main():
    target = os.environ.get('VERIFY_TARGET') or 'both'
    if target not in ('source','portfolio','both'):
        raise ValueError('Unknown verification target')
    value = os.environ.get('EXPECTED_NOT_BEFORE', '')
    cutoff = datetime.fromisoformat(value.replace('Z','+00:00')) if value else None
    if cutoff and cutoff.tzinfo is None:
        raise ValueError('Expected timestamp must have timezone')
    results = []
    with sync_playwright() as pw:
        options = {'executable_path':os.environ['CHROMIUM_PATH']} if os.environ.get('CHROMIUM_PATH') else {}
        browser = pw.chromium.launch(headless=True, **options)
        try:
            for name, url in SITES.items():
                if target not in (name,'both'):
                    continue
                for width in (1440,390):
                    results.append(verify_site(browser,name,url,width,cutoff))
        finally:
            browser.close()
    receipt = {'schema':'un.public-archive-browser.v1','status':'passed','results':results,
               'source_text_in_receipt':False,'human_usability_acceptance':False}
    Path('public-archive-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
