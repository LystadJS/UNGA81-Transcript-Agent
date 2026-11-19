"""Publication configuration must not expose credentials or private endpoints."""
import importlib.util
from pathlib import Path
import unittest
import json
import tempfile

SPEC = importlib.util.spec_from_file_location('public_build', Path(__file__).resolve().parents[1] / 'tools/build_pages.py')
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class PublicBuildConfigurationTests(unittest.TestCase):
    def test_unconfigured_archive_is_explicit(self):
        self.assertEqual(BUILD.archive_configuration(None), {'schema': 'un.archive-config.v1', 'manifest_url': None})

    def test_public_dataset_manifest(self):
        url = 'https://huggingface.co/datasets/example/public-archive/resolve/main/latest.json'
        self.assertEqual(BUILD.archive_configuration(url)['manifest_url'], url)

    def test_no_secret_or_unapproved_host(self):
        for url in [
            'http://huggingface.co/datasets/a/b/resolve/main/latest.json',
            'https://token@huggingface.co/datasets/a/b/resolve/main/latest.json',
            'https://huggingface.co/datasets/a/b/resolve/main/latest.json?token=secret',
            'https://huggingface.co/datasets/a/b/resolve/main/latest.json#secret',
            'https://example.test/latest.json',
            'https://huggingface.co:443/datasets/a/b/resolve/main/latest.json',
            'https://huggingface.co/datasets/a/b/resolve/main/../../secret',
        ]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                BUILD.archive_configuration(url)


class CheckedArchiveTests(unittest.TestCase):
    def test_research_only_modules_stay_out_of_public_build(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'public'
            BUILD.build(output)
            for name in BUILD.RESEARCH_ONLY_MODULES:
                self.assertTrue((repo / 'site' / name).is_file())
                self.assertFalse((output / name).exists())
                # A future UI dependency must explicitly revisit this boundary.
                for asset in output.rglob('*'):
                    if asset.suffix in {'.html', '.js', '.css'}:
                        self.assertNotIn(name.encode('ascii'), asset.read_bytes(), str(asset))
            for name in ['index.html', 'meeting-reports.html', 'campaign-notebook.html',
                         'issue-archive-worker.js', 'issue-report.js']:
                self.assertTrue((output / name).is_file(), name)

    def test_build_uses_versioned_endpoint_and_rejects_conflicting_override(self):
        repo = Path(__file__).resolve().parents[1]
        expected = json.loads((repo/'site/archive-config.json').read_bytes())
        self.assertEqual(BUILD.configured_archive(repo, ''), expected)
        self.assertEqual(BUILD.configured_archive(repo, expected['manifest_url']), expected)
        with self.assertRaises(ValueError):
            BUILD.configured_archive(repo, 'https://huggingface.co/datasets/other/unrelated/resolve/main/latest.json')


if __name__ == '__main__':
    unittest.main()
