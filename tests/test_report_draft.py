"""Fictional protocol tests; no model weights or inference required."""
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from copy import deepcopy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from un_transcript import report_draft as D


def packet():
    text = 'We support humanitarian access. Literal 😀 <img src=x>.'
    record = dict(id='ga/81/900#0', meeting_slug='ga/81/900', date='2026-11-10', country='Kenya', source_url='https://transcripts.un.org/en/ga/81/900', raw_sha256='a'*64, text_sha256=hashlib.sha256(text.encode()).hexdigest(), json_pointer='/transcript/data/0', text=text, speaker_name='Fictional delegate', speaker_role='Representative', speaker_group='', speaking_capacity='unverified')
    context = dict(schema=D.CONTEXT, meetings=[dict(slug='ga/81/900', date='2026-11-10', title='Fictional meeting 😀', source_url=record['source_url'])], source_record_count=1, source_sha256='b'*64, questions=[dict(heading='Access 😀', query='humanitarian access', record_ids=[record['id']]), dict(heading='Missing', query='nonexistent', record_ids=[])], records=[record])
    return seal(context)


def seal(context):
    return dict(schema=D.INPUT, context=context, context_sha256=hashlib.sha256(D.encoded(context)).hexdigest())


def answer():
    return {'bullets': [{'text': 'A draft claim 😀', 'evidence': [{'record_id': 'ga/81/900#0', 'quote': 'We support humanitarian access.'}]}]}


@contextmanager
def server(reply=None, status=200, headers=None):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(status)
            for key, value in (headers or {}).items(): self.send_header(key, value)
            self.end_headers()
            self.wfile.write(reply if reply is not None else D.encoded({'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(answer())}}]}))
        def log_message(self, *args): pass
    instance = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=instance.serve_forever, daemon=True); thread.start()
    try: yield f'http://127.0.0.1:{instance.server_port}/v1/chat/completions', requests
    finally: instance.shutdown(); instance.server_close(); thread.join()


class DraftTests(unittest.TestCase):
    def test_http_protocol_and_proxy_bypass(self):
        with server() as (url, calls), patch.dict(os.environ, {'HTTP_PROXY': 'http://127.0.0.1:1', 'http_proxy': 'http://127.0.0.1:1', 'NO_PROXY': '', 'no_proxy': ''}):
            result = D.generate(packet(), 'fictional-model', endpoint=url)
        self.assertEqual(result['request_count'], 1); self.assertEqual(result['review_status'], 'unreviewed')
        self.assertEqual([s['status'] for s in result['sections']], ['generated', 'no_matching_source'])
        self.assertEqual(len(calls), 1); call = calls[0]
        self.assertFalse(call['stream']); self.assertEqual(call['response_format'], {'type': 'json_object'})
        self.assertEqual(call['model'], 'fictional-model'); self.assertEqual(len(call['messages']), 2)
        user = json.loads(call['messages'][1]['content']); self.assertEqual(len(user['source_records']), 1)
        self.assertNotIn('Missing', call['messages'][1]['content'])

    def test_no_source_never_calls_model(self):
        p = packet(); p['context']['records'] = []; p['context']['questions'] = p['context']['questions'][1:]; p = seal(p['context'])
        result = D.generate(p, 'fictional', requester=lambda *a, **kw: self.fail('Must not call'))
        self.assertEqual(result['request_count'], 0)
        for timeout in (float('nan'), 0, 601, True):
            with self.assertRaises(ValueError): D.generate(p, 'fictional', timeout=timeout)

    def test_input_validation_before_requests(self):
        mutations = [lambda c: c['records'][0].update(text='altered'), lambda c: c['meetings'][0].update(date='2026-10-05'), lambda c: c['meetings'][0].update(date='2026-02-30'), lambda c: c['questions'][0].update(record_ids=['unknown#0']), lambda c: c.update(source_record_count=True), lambda c: c['records'][0].update(meeting_slug=[]), lambda c: c['records'][0].update(speaking_capacity='verified'), lambda c: c['records'][0].update(json_pointer='/transcript/data/9')]
        for mutate in mutations:
            p = packet(); mutate(p['context']); p = seal(p['context'])
            with self.assertRaises(ValueError): D.generate(p, 'fictional', requester=lambda *a, **kw: self.fail('Invalid input reached provider'))
        p = packet(); p['context_sha256'] = 'b'*64
        with self.assertRaises(ValueError): D.validate_input(p)
        with self.assertRaises(ValueError): D.parse('{"a":1,"a":2}')
        with self.assertRaises(ValueError): D.parse('{"a":NaN}')

    def test_claim_and_quote_boundaries(self):
        p = packet(); q = p['context']['questions'][0]; records = {r['id']:r for r in p['context']['records']}
        self.assertEqual(D.validate_bullets(answer(), q, records), answer()['bullets'])
        mutations = [lambda v: v['bullets'][0]['evidence'][0].update(quote='Invented'), lambda v: v['bullets'][0]['evidence'][0].update(record_id='unknown'), lambda v: v['bullets'][0].update(text='😀'*501), lambda v: v['bullets'][0].update(text='bad\ud800'), lambda v: v['bullets'][0]['evidence'].append(deepcopy(v['bullets'][0]['evidence'][0])), lambda v: v.update(extra=True)]
        for mutate in mutations:
            v = answer(); mutate(v)
            with self.assertRaises(ValueError): D.validate_bullets(v, q, records)
        result = D.generate(p, 'fictional', requester=lambda *a, **kw: {'bullets': []})
        self.assertEqual(result['sections'][0]['status'], 'model_abstained')

    def test_endpoint_boundaries(self):
        for endpoint in ('https://example.org/v1/chat/completions', 'http://127.0.0.1.evil.invalid/chat/completions', 'http://user:pw@localhost/chat/completions', 'http://localhost/chat/completions?q=1', 'http://localhost/chat/completions#fragment', 'file:///chat/completions', 'http://localhost:0/chat/completions', 'http://localhost:99999/chat/completions', 'http://localhost/v1/models'):
            with self.assertRaises(ValueError): D.validate_endpoint(endpoint)
        for endpoint in (D.ENDPOINT, 'http://localhost/v1/chat/completions', 'http://[::1]:8000/v1/chat/completions'):
            self.assertEqual(D.validate_endpoint(endpoint), endpoint)

    def test_redirect_truncated_malformed_and_oversized_responses(self):
        with server(status=302, headers={'Location': 'https://example.invalid/v1/chat/completions'}) as (url, calls):
            with self.assertRaisesRegex(ValueError, 'redirect'): D.generate(packet(), 'fictional', endpoint=url)
            self.assertEqual(len(calls), 1)
        for reply in ({'choices': [None]}, {'choices': [{'finish_reason': 'length', 'message': {'content': '{}'}}]}, {'choices': [{'finish_reason': 'stop', 'message': {'content': '{}', 'tool_calls': [{}]}}]}):
            with server(D.encoded(reply)) as (url, calls):
                with self.assertRaises(ValueError): D.generate(packet(), 'fictional', endpoint=url)
        with server(b'x'*(D.RESPONSE_LIMIT+1)) as (url, calls):
            with self.assertRaisesRegex(ValueError, '1 MiB'): D.generate(packet(), 'fictional', endpoint=url)

    def test_cli_private_no_overwrite_and_failure_no_output(self):
        with tempfile.TemporaryDirectory() as temp, server() as (url, calls):
            source = Path(temp)/'input.json'; out = Path(temp)/'draft.json'; source.write_bytes(D.encoded(packet()))
            args = [str(source), '--output', str(out), '--model', 'fictional', '--endpoint', url]
            with redirect_stdout(io.StringIO()) as receipt:
                self.assertEqual(D.main(args), 0)
            self.assertNotIn('humanitarian', receipt.getvalue()); self.assertEqual(out.stat().st_mode & 0o777, 0o600)
            original = out.read_bytes(); self.assertLessEqual(len(original), D.OUTPUT_LIMIT); self.assertEqual(D.parse(original)['review_status'], 'unreviewed')
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): D.main(args)
            self.assertEqual(out.read_bytes(), original); self.assertEqual(len(calls), 1)
            out.unlink()
            with patch.object(D, 'request_model', return_value={'bullets':[{'text':'unsupported','evidence':[]}]}), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): D.main(args)
            self.assertFalse(out.exists())

    def test_exact_output_byte_bound(self):
        with patch.object(D, 'OUTPUT_LIMIT', 1):
            with self.assertRaisesRegex(ValueError, '256 KiB'): D.generate(packet(), 'fictional', requester=lambda *a, **kw: answer())


if __name__ == '__main__': unittest.main()
