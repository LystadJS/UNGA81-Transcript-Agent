"""Browser acceptance: use --live for UN requests, or --fixtures for captured responses.

The optional Playwright dependency is for developers/CI only, never website users.
Every live run retains its downloaded corpus and analysis, not just a pass flag.
"""
import argparse
import csv
import functools
import http.server
import json
import os
from pathlib import Path
import threading
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', default='site')
    parser.add_argument('--output', default='live-check/browser')
    parser.add_argument('--fixtures', type=Path)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if args.live == bool(args.fixtures):
        parser.error('Choose exactly one of --live or --fixtures DIRECTORY.')

    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    checks, errors, requests = [], [], []

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *unused):
            pass

    handler = functools.partial(QuietHandler, directory=str(Path(args.site).resolve()))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def downloaded(page, selector, filename):
        with page.expect_download(timeout=30000) as event:
            page.locator(selector).click()
        path = output / filename
        event.value.save_as(path)
        return path

    def generate(page):
        page.locator('#runAnalysis').click()
        page.wait_for_function("""() => !document.getElementById('analysisOutput').hidden &&
            !document.getElementById('runAnalysis').disabled""", timeout=180000)

    try:
        with sync_playwright() as playwright:
            executable = os.environ.get('CHROMIUM_PATH')
            browser = playwright.chromium.launch(
                executable_path=executable or None, headless=True,
                args=['--no-sandbox']
            )
            context = browser.new_context(viewport={'width': 1440, 'height': 1000},
                                          timezone_id='America/New_York')
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda response: requests.append({
                'url': response.url, 'status': response.status
            }) if response.url.startswith('https://transcripts.un.org/') else None)

            if args.fixtures:
                def replay(route):
                    path = urlsplit(route.request.url).path
                    filenames = {
                        '/en/meetings.json': 'response-1.txt',
                        '/en/ga/c3/81/1.json': 'response-2.txt',
                        '/en/ga/c3/81/2.json': 'response-3.txt'
                    }
                    if path not in filenames:
                        raise AssertionError('Unexpected UN request: ' + route.request.url)
                    route.fulfill(status=200, content_type='application/json',
                                  headers={'Access-Control-Allow-Origin': '*'},
                                  body=(args.fixtures / filenames[path]).read_bytes())
                page.route('https://transcripts.un.org/**', replay)

            page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='networkidle')
            page.wait_for_function("document.querySelectorAll('#region option').length > 1")
            check('Blank Topic is valid without HTML required', page.locator('#topic').input_value() == ''
                  and page.locator('#topic').get_attribute('required') is None)
            check('Blank Topic disables related phrases', page.locator('#phrases').is_disabled())
            page.locator('#meetingScope').select_option('committee_3')
            check('Committee selection updates untouched historic dates',
                  'Switched untouched' in page.locator('#dateRangeNote').inner_text())
            page.locator('#startDate').fill('2026-10-01')
            page.locator('#endDate').fill('2026-10-01')
            page.locator('#meetingScope').select_option('committee_2')
            check('User dates survive scope changes', page.locator('#startDate').input_value() == '2026-10-01'
                  and page.locator('#endDate').input_value() == '2026-10-01')
            page.locator('#meetingScope').select_option('committee_3')
            page.locator('#topic').fill('AI')
            page.locator('#phrases').fill('not-a-real-filter')
            page.locator('#analysisForm details').first.locator('summary').click()
            page.locator('#excludePhrases').fill('the')
            page.locator('#topic').fill('')
            check('Blank Topic disables stale exclusions', page.locator('#excludePhrases').is_disabled())
            for control in page.locator('input[name=method]').all():
                control.check()

            generate(page)
            all_result = json.loads(downloaded(page, '#exportResult', 'all-analysis.json').read_text())
            raw_path = downloaded(page, '#exportCorpus', 'corpus.json')
            raw = json.loads(raw_path.read_text())
            check('Actual collection returns passages', len(raw['records']) > 0)
            check('Only Third Committee collected', all(row['scope'] == 'committee_3' for row in raw['records']))
            check('All unique passages included', all_result['counts']['matched'] == all_result['counts']['eligible'] > 0)
            check('Stale search fields ignored', all_result['parameters']['phrases'] == []
                  and all_result['parameters']['exclude'] == [])
            check('Both October 1 meetings collected', raw['collection']['selected_meetings'] == 2)
            check('All five methods execute', len(all_result['methods']) == 5)
            check('All-mode count charts labeled correctly', 'Passages by region' in page.locator('#analysisReport').inner_text()
                  and 'Topic frequency by region' not in page.locator('#analysisReport').inner_text())
            check('Collector and analysis counts are separate', 'Passages collected' in page.locator('#analysisReport').inner_text())
            rows = list(csv.DictReader(downloaded(page, '#exportCSV', 'all-passages.csv').open(encoding='utf-8-sig')))
            check('CSV contains every included unique passage', len(rows) == all_result['counts']['eligible'])
            html = downloaded(page, '#exportHTML', 'report.html').read_text()
            check('Standalone report identifies all-mode and committee', 'All passages' in html and 'Third Committee' in html)

            for width in [1440, 390]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.locator('#analyze').scroll_into_view_if_needed()
                page.screenshot(path=str(output / f'form-{width}.png'))
                page.evaluate("document.getElementById('analysisReport').scrollIntoView({block: 'start'})")
                page.screenshot(path=str(output / f'report-{width}.png'))
                check(f'No horizontal overflow at {width}px', page.evaluate(
                    'document.documentElement.scrollWidth <= window.innerWidth + 1'))
            page.set_viewport_size({'width': 1440, 'height': 1000})

            # Reimport the actual collected corpus; no duplicate network downloads.
            page.locator('#corpusSource').select_option('import')
            page.locator('#corpusFile').set_input_files(raw_path)
            page.locator('#topic').fill('unmatchablexyz987654321')
            page.locator('#phrases').fill('')
            page.locator('#excludePhrases').fill('')
            check('Changed query disables stale exports', page.locator('#exportResult').is_disabled())
            generate(page)
            no_match = json.loads(downloaded(page, '#exportResult', 'no-match.json').read_text())
            check('No matches does not erase collected count', no_match['counts']['input'] == len(raw['records'])
                  and no_match['counts']['matched'] == 0)
            check('No-match message offers blank Topic', 'leave Topic blank' in page.locator('#analysisStatus').inner_text())
            page.locator('#topic').fill(' ')
            page.locator('#region').select_option('Africa')
            generate(page)
            regional = json.loads(downloaded(page, '#exportResult', 'region.json').read_text())
            check('Blank mode still honors region', all(row['region'] == 'Africa' for row in regional['matched'])
                  and 0 < regional['counts']['matched'] < all_result['counts']['matched'])
            page.locator('#recentDates').click()
            check('Date preset invalidates exports', page.locator('#exportResult').is_disabled())
            page.locator('#debateDates').click()
            check('General Debate preset remains explicit', page.locator('#startDate').input_value() == '2026-09-22')

            # Controlled error scenarios: not represented as real network results.
            page.unroute('https://transcripts.un.org/**')
            page.locator('#corpusSource').select_option('live')
            page.locator('#region').select_option('All regions')
            page.locator('#startDate').fill('2026-10-01')
            page.locator('#endDate').fill('2026-10-01')
            page.route('https://transcripts.un.org/**', lambda route: route.abort())
            generate(page)
            check('Network failure not represented as zero matches',
                  'Collection incomplete:' in page.locator('#analysisStatus').inner_text())
            check('Failure coverage auto-expanded', page.locator('.coverage-panel').get_attribute('open') is not None)
            page.unroute('https://transcripts.un.org/**')
            page.route('https://transcripts.un.org/**', lambda route: route.fulfill(
                status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'},
                body=json.dumps({'meetings': [], 'total': 0, 'hasMore': False, 'page': 1})))
            generate(page)
            check('Empty inventory has a distinct date/scope message',
                  'No meetings found for Third Committee' in page.locator('#analysisStatus').inner_text())
            check('No uncaught JavaScript errors', not errors)
            browser.close()

            result = {
                'mode': 'live browser UN fetch' if args.live else 'browser replay of captured real UN responses',
                'commit': os.environ.get('GITHUB_SHA'), 'passed': len(checks), 'checks': checks,
                'collected_passages': len(raw['records']), 'analysis_counts': all_result['counts'],
                'selected_meetings': raw['collection']['selected_meetings'],
                'requests': requests, 'page_errors': errors
            }
            (output / 'result.json').write_text(json.dumps(result, indent=2))
            print(json.dumps({k: v for k, v in result.items() if k not in ('checks', 'requests')}, indent=2))
    except Exception as error:
        (output / 'failure.json').write_text(json.dumps({
            'error': str(error), 'completed_checks': checks, 'page_errors': errors, 'requests': requests
        }, indent=2))
        raise
    finally:
        server.shutdown()


if __name__ == '__main__':
    main()
