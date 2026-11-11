"""Publication configuration must not expose credentials or private endpoints."""
import importlib.util
from pathlib import Path
import unittest

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


if __name__ == '__main__':
    unittest.main()
