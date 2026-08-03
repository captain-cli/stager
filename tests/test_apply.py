import json,tempfile,unittest
from pathlib import Path
from captain_stager.service import apply
class ApplyTests(unittest.TestCase):
    def test_apply(self):
        with tempfile.TemporaryDirectory() as d:
            t=Path(d); root=t/'target'; m=t/'m.json'; m.write_text(json.dumps({'id':'t','name':'T','version':'1','directories':['a/b'],'files':[{'path':'a/b/r.txt','content':'ready'}]}))
            report=apply(str(m),root_override=str(root)); self.assertTrue(report.succeeded); self.assertEqual((root/'a/b/r.txt').read_text(),'ready')
    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            t=Path(d); root=t/'target'; m=t/'m.json'; m.write_text(json.dumps({'id':'t','name':'T','version':'1','directories':['a']}))
            report=apply(str(m),root_override=str(root),dry_run=True); self.assertFalse(root.exists()); self.assertEqual(report.results[0].status,'planned')
