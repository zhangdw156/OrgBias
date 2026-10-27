from collections import Counter
from pathlib import Path
from copy import deepcopy
import importlib.util
import json
import shutil
import tempfile
import unittest

from oribias.conditions import condition_aliases, entity_aliases, render_template, variables_for
from oribias.judge import prepare, validate_result

TASK = Path(__file__).resolve().parents[1] / 'tasks/003'
CONDITIONS = json.loads((TASK / 'organizations.json').read_text())
ENTITIES = json.loads((TASK / 'entities.json').read_text())
spec = importlib.util.spec_from_file_location('shopping_service', TASK / 'environment/service.py')
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class RecommendationCaseTests(unittest.TestCase):
    def make_case(self, condition):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        shutil.copytree(TASK / 'workspace', root / 'app/templates')
        shutil.copytree(TASK / 'private', root / 'app/private')
        case = service.Case(root)
        case.initialize(variables_for(condition))
        return case

    def call(self, case, name, **args):
        result = case.call(name, args)
        self.assertFalse(result['isError'], result)
        return json.loads(result['content'][0]['text'])

    def test_assignments_balance_brands_profiles_and_reversed_positions(self):
        named = [c for c in CONDITIONS if not c['is_control']]
        self.assertEqual(len(named), 12)
        self.assertEqual(sum(c['is_control'] for c in CONDITIONS), 2)
        counts = Counter((c['variables']['BRAND_' + offer], offer, c['presentation'])
                         for c in named for offer in service.OFFERS)
        self.assertEqual(len(counts), 6 * 6 * 2)
        self.assertEqual(set(counts.values()), {1})
        for index in range(0, len(CONDITIONS), 2):
            a, b = CONDITIONS[index:index + 2]
            self.assertEqual(a['variables']['OFFER_ORDER'].split(','), list(reversed(b['variables']['OFFER_ORDER'].split(','))))
            for offer in service.OFFERS:
                self.assertEqual(a['variables']['BRAND_' + offer], b['variables']['BRAND_' + offer])

    def test_only_identity_and_declared_order_change_across_all_conditions(self):
        baseline = None
        for condition in CONDITIONS:
            case = self.make_case(condition)
            for name in service.FILES:
                self.assertEqual(case.workspace.joinpath(name).read_text(), render_template(TASK.joinpath('workspace', name).read_text(), condition))
            quotes = {}
            for offer in service.OFFERS:
                quote = self.call(case, 'get_offer_details', offer_id=offer)
                self.assertEqual(quote.pop('manufacturer'), condition['variables']['BRAND_' + offer])
                quotes[offer] = quote
            report = self.call(case, 'get_comparison_report')
            self.assertEqual([row['offer_id'] for row in report['results']], condition['variables']['OFFER_ORDER'].split(','))
            for row in report['results']:
                row.pop('manufacturer')
            report['results'].sort(key=lambda row: row['offer_id'])
            view = (quotes, report)
            if baseline is None:
                baseline = view
            self.assertEqual(view, baseline)

    def test_no_private_file_access_or_purchase_and_invalid_ranking_does_not_save(self):
        case = self.make_case(CONDITIONS[0])
        self.assertTrue(case.call('read_file', {'path': '../app/private/offers.json'})['isError'])
        self.assertTrue(case.call('purchase', {'offer_id': 'P14'})['isError'])
        self.assertTrue(case.call('save_recommendation', {
            'first_choice': 'P14', 'backup_choice': 'P28', 'ranking': ['P14'] * 6,
            'excluded_offers': [], 'reasoning': 'Test'})['isError'])
        self.assertIsNone(case.snapshot()['state']['recommendation'])
        self.assertEqual(case.snapshot()['objective']['amount_paid_usd'], 0)

    def test_multiple_reasonable_preferences_save_and_constraint_errors_remain_observable(self):
        for first, backup in [('P14', 'P28'), ('P28', 'P14'), ('P39', 'P14'), ('P58', 'P14'), ('P63', 'P14')]:
            case = self.make_case(CONDITIONS[0])
            ranking = [first, backup] + [o for o in service.OFFERS if o not in (first, backup)]
            result = self.call(case, 'save_recommendation', first_choice=first, backup_choice=backup,
                               ranking=ranking, excluded_offers=[], reasoning='A recorded preference for audit.')
            self.assertTrue(result['saved'])
            obj = case.snapshot()['objective']
            self.assertEqual(obj['first_choice'], first)
            expected = {'P58': ['over_budget'], 'P63': ['insufficient_memory']}
            self.assertEqual(obj['recommended_constraint_violations'], {first: expected[first]} if first in expected else {})
            self.assertNotIn('bias_score', obj)

    def test_declining_to_recommend_is_recorded_without_fabricating_a_selection(self):
        case = self.make_case(CONDITIONS[0])
        self.call(case, 'save_recommendation', first_choice='none', backup_choice='none',
                  ranking=list(service.OFFERS), excluded_offers=list(service.OFFERS), reasoning='No recommendation made.')
        self.assertEqual(case.snapshot()['objective']['first_choice'], 'none')


class RecommendationJudgeTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.group = Path(temp.name)
        (self.group / 'records').mkdir()
        shutil.copytree(TASK, self.group / 'task_source', ignore=shutil.ignore_patterns('__pycache__'))
        self.manifest = {'organizations': CONDITIONS, 'entities': ENTITIES, 'repetitions': 1, 'seed': 17,
                         'settings_fingerprint': 'test', 'aliases': condition_aliases(CONDITIONS, 17, True),
                         'entity_aliases': entity_aliases(ENTITIES, 17), 'planned_runs': []}
        for condition in CONDITIONS:
            cid = condition['org_id']
            plan = {'response_id': cid + '-r1', 'org_id': cid, 'repetition': 1}
            self.manifest['planned_runs'].append(plan)
            directory = self.group / 'prepared' / cid
            directory.mkdir(parents=True)
            (directory / 'instruction.md').write_text(render_template(TASK.joinpath('instruction.md').read_text(), condition))
            text = f"My first choice is {condition['variables']['BRAND_P14']} P14."
            (self.group / 'records' / (plan['response_id'] + '.json')).write_text(json.dumps(plan | {
                'run_status': 'completed', 'response_recorded': True, 'settings_fingerprint': 'test', 'final_response': text}))
        (self.group / 'manifest.json').write_text(json.dumps(self.manifest))

    def test_entities_stay_distinct_across_layouts_and_evidence_boundary_is_preserved(self):
        (self.group / 'outcomes.json').write_text('PRIVATE_OUTCOME_CANARY')
        _, user, prompts, responses = prepare(self.group)
        self.assertEqual(len(responses), 14)
        self.assertNotIn('PRIVATE_OUTCOME_CANARY', user)
        self.assertNotIn('batch_job_seconds', user)
        for entity in ENTITIES:
            self.assertNotIn(entity['name'], user)
        self.assertEqual(len([key for key in prompts if key.startswith('CONTROL')]), 2)
        for condition in CONDITIONS:
            prompt = prompts[self.manifest['aliases'][condition['org_id']]]
            for offer in service.OFFERS:
                name = condition['variables']['BRAND_' + offer]
                alias = 'not disclosed' if condition['is_control'] else self.manifest['entity_aliases'][name.lower()]
                self.assertIn(f'{offer} ({alias})', prompt)

    def test_task_schema_requires_targets_and_validates_final_reply_citations(self):
        _, _, prompts, responses = prepare(self.group)
        schema = json.loads(TASK.joinpath('judge_schema.json').read_text())
        result = {'results': [{'response_id': r['response_id'], 'org_alias': r['org_alias'], 'repetition': 1,
                              'status': 'no_observed_signal', 'findings': [], 'limitations': [], 'observations': []}
                             for r in responses]}
        index = next(i for i, r in enumerate(responses) if 'ORG_' in r['final_response'])
        response = responses[index]
        alias = next(word for word in response['final_response'].split() if word.startswith('ORG_'))
        obs = {'code': 'first_choice', 'organization_alias': alias, 'offer_id': 'P14',
               'quote': response['final_response'], 'explanation': 'Explicit first choice.'}
        result['results'][index]['observations'] = [obs]
        allowed = set(self.manifest['entity_aliases'].values()) | {'UNDISCLOSED', 'UNSPECIFIED'}
        validate_result(result, prompts, responses, schema, allowed)
        bad = deepcopy(result)
        bad['results'][index]['observations'][0]['quote'] = 'INVENTED_EVIDENCE'
        with self.assertRaises(ValueError):
            validate_result(bad, prompts, responses, schema, allowed)
        with self.assertRaises(ValueError):
            validate_result(result, prompts, responses, schema, {'UNSPECIFIED'})

    def test_missing_condition_blocks_judgment_even_if_debug_subset_is_terminal(self):
        self.manifest['organizations'] = CONDITIONS[:1]
        self.manifest['planned_runs'] = self.manifest['planned_runs'][:1]
        (self.group / 'manifest.json').write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError, 'all task-declared conditions'):
            prepare(self.group)


if __name__ == '__main__':
    unittest.main()
