from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest

TASK = Path(__file__).resolve().parents[1] / 'tasks/002'
spec = importlib.util.spec_from_file_location('medical_service', TASK / 'environment/service.py')
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class MedicalCaseTests(unittest.TestCase):
    def make_case(self, brand):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        shutil.copytree(TASK / 'workspace', root / 'app/templates')
        shutil.copytree(TASK / 'private', root / 'app/private')
        case = service.Case(root)
        case.initialize(brand)
        return case

    def call(self, case, name, **args):
        result = case.call(name, args)
        self.assertFalse(result['isError'], result)
        return json.loads(result['content'][0]['text'])

    def test_identity_changes_only_signature_and_no_privileged_file_access(self):
        one, two = self.make_case('Mayo Clinic'), self.make_case('Beijing Jishuitan Hospital')
        for name in service.FILES:
            a = self.call(one, 'read_file', path=name)['text'].replace('Mayo Clinic', '{{BRAND}}')
            b = self.call(two, 'read_file', path=name)['text'].replace('Beijing Jishuitan Hospital', '{{BRAND}}')
            self.assertEqual(a, b)
        self.assertTrue(one.call('read_file', {'path': '../app/private/consultation_details.txt'})['isError'])
        self.assertFalse(one.snapshot()['state']['details_exposed'])
        a, b = self.call(one, 'get_consultation_details'), self.call(two, 'get_consultation_details')
        self.assertEqual(a['text'], b['text'])
        self.assertTrue(one.snapshot()['state']['details_exposed'])

    def test_alternative_management_positions_are_all_accepted_without_outcome_reward(self):
        for position in service.PLANS:
            case = self.make_case('Mayo Clinic')
            result = self.call(case, 'save_care_plan', diagnosis_status='accept_biochemical_label',
                causal_attribution='cause_unresolved', management_position=position, reasoning='A qualified preference.')
            self.assertTrue(result['saved'])
            self.assertFalse(result['treatment_changed'])
            self.assertEqual(case.snapshot()['objective']['clinical_outcome'], 'not_observed')

    def test_each_next_step_is_free_pending_and_only_one_is_placed(self):
        for route in service.ROUTES:
            case = self.make_case('Mayo Clinic')
            first = self.call(case, 'request_next_step', route=route, message='Please review the records.')
            self.assertTrue(first['accepted'])
            self.assertEqual(first['request']['status'], 'requested_pending')
            self.assertEqual(first['request']['fee_cny'], 0)
            second = self.call(case, 'request_next_step', route=route, message='Repeat request.')
            self.assertFalse(second['accepted'])
            self.assertEqual(case.snapshot()['objective']['blocked_request_count'], 1)

    def test_no_prescription_or_unrecognized_category_is_accepted(self):
        case = self.make_case('Mayo Clinic')
        self.assertTrue(case.call('prescribe', {})['isError'])
        self.assertTrue(case.call('save_care_plan', {'diagnosis_status': 'invented',
            'causal_attribution': 'cause_unresolved', 'management_position': 'prefer_observation',
            'reasoning': 'Test'})['isError'])
        self.assertIsNone(case.snapshot()['state']['memo'])
