"""Scheduling controls using local fake subprocesses, not model inference."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import tempfile
import unittest

from oribias.matrix import run_matrix


class MatrixSchedulingTests(unittest.TestCase):
    def run_fixture(self, judge_status=200):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            pairs=[{'model':'glm-5.3','task':'002'}, {'model':'kimi-k3','task':'001'}]
            jobs=root/'jobs.json';jobs.write_text(json.dumps({'jobs':pairs}))
            calls=[]
            def popen(command, **kwargs):
                calls.append(command)
                group=root/f'group-{len(calls)}';(group/'judge').mkdir(parents=True)
                (group/'judge/http_status.json').write_text(json.dumps({'status':judge_status}))
                self.assertTrue(kwargs['env']['ORIBIAS_MATRIX_CONTROL'].endswith('/stop.json'))
                return SimpleNamespace(stdout=iter([f'Group: {group}\n']),pid=12345,
                                       wait=lambda: 0 if judge_status==200 else 1)
            with patch('oribias.matrix.ROOT',root), patch.dict('os.environ',{},clear=True), \
                 patch('oribias.matrix.Settings.load',return_value=SimpleNamespace(public=lambda:{})), \
                 patch('oribias.matrix.subprocess.check_output',return_value='test-commit\n'), \
                 patch('oribias.matrix.subprocess.Popen',side_effect=popen):
                directory=run_matrix(concurrency=1,jobs_file=jobs)
            result=json.loads((directory/'manifest.json').read_text())
            return calls,result,pairs

    def test_exact_pairs_do_not_expand_to_cartesian_product(self):
        calls,result,pairs=self.run_fixture()
        self.assertEqual(len(calls),2)
        self.assertEqual([{k:j[k] for k in ['model','task']} for j in result['jobs']],pairs)
        self.assertEqual(result['status'],'finished')

    def test_unavailable_fixed_judge_blocks_queued_groups(self):
        calls,result,_=self.run_fixture(401)
        self.assertEqual(len(calls),1)
        self.assertEqual(result['jobs'][1]['status'],'blocked_before_start')
        self.assertEqual(result['stop_reason']['code'],'JudgeHTTP401')
        self.assertEqual(result['status'],'blocked')


if __name__=='__main__':
    unittest.main()
