import importlib.util
from pathlib import Path
from unittest.mock import Mock, patch
import unittest

spec=importlib.util.spec_from_file_location('drill',Path(__file__).parents[1]/'tools/storage_recovery_drill.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Isolation(unittest.TestCase):
    def test_every_read_and_commit_stays_under_drill_namespace(self):
        api=Mock();download=Mock();store=m.DrillStorage('owner/private','drills/12-1/store/',api=api,downloader=download)
        store._entries(['latest.json','snapshots/x/snapshot.json'],'a'*40)
        self.assertEqual(api.get_paths_info.call_args.args[1],['drills/12-1/store/latest.json','drills/12-1/store/snapshots/x/snapshot.json'])
        store.downloader('raw/test.json','a'*40)
        download.assert_called_once_with('drills/12-1/store/raw/test.json','a'*40)
        with patch.object(m.HFStorage,'_commit',return_value='b'*40) as commit:
            store._commit({'latest.json':b'{}'},'a'*40,'test')
            self.assertEqual(commit.call_args.args[0],{'drills/12-1/store/latest.json':b'{}'})
            store.interrupt=True
            with self.assertRaises(m.SimulatedInterruption):store._commit({'latest.json':b'{}'},'b'*40,'test')
            self.assertEqual(commit.call_count,1)

    def test_production_and_traversal_prefixes_rejected(self):
        for prefix in ('','snapshots/','drills/../store/','drills/x/store/'):
            with self.assertRaises(ValueError):m.DrillStorage('owner/private',prefix,api=Mock(),downloader=Mock())
