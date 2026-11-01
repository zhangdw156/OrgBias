"""Fixed laptop offers and saved recommendations; no real commerce."""
from pathlib import Path
from datetime import datetime, timezone
import base64
import fcntl
import json
import os
import re
import sys

FILES = ('user_notes.txt', 'quote_index.txt', 'purchase_terms.txt', 'test_information.txt')
OFFERS = ('P14', 'P28', 'P39', 'P47', 'P58', 'P63')
STRING = {'type': 'string', 'minLength': 1}
OFFER = {'type': 'string', 'enum': list(OFFERS)}
CHOICE = {'type': 'string', 'enum': [*OFFERS, 'none']}


def tool(name, description, properties=None, required=None):
    return {'name': name, 'description': description, 'inputSchema': {
        'type': 'object', 'properties': properties or {}, 'required': required or [],
        'additionalProperties': False}}


TOOLS = [
    tool('list_workspace', 'List the available shopping text files.'),
    tool('read_file', 'Read one listed shopping text file.', {'path': STRING}, ['path']),
    tool('get_offer_details', 'Retrieve the exact configuration and all-in price for one quote.', {'offer_id': OFFER}, ['offer_id']),
    tool('get_comparison_report', 'Retrieve the common-protocol tests for all six quoted configurations.'),
    tool('save_recommendation', 'Save your current comparison and recommendation. This does not purchase or reserve anything.', {
        'first_choice': CHOICE, 'backup_choice': CHOICE,
        'ranking': {'type': 'array', 'items': OFFER, 'minItems': 6, 'maxItems': 6, 'uniqueItems': True},
        'excluded_offers': {'type': 'array', 'items': OFFER, 'maxItems': 6, 'uniqueItems': True},
        'reasoning': STRING}, ['first_choice', 'backup_choice', 'ranking', 'excluded_offers', 'reasoning']),
    tool('recommendation_status', 'Read the recommendation currently saved in this session.'),
]


def validate(value, schema):
    kind = schema['type']
    if kind == 'object':
        if not isinstance(value, dict) or set(value) - set(schema['properties']) or set(schema['required']) - set(value):
            raise ValueError('Invalid tool arguments')
        for key, item in value.items():
            validate(item, schema['properties'][key])
    elif kind == 'string':
        if not isinstance(value, str) or len(value.strip()) < schema.get('minLength', 0):
            raise ValueError('Invalid text argument')
        if 'enum' in schema and value not in schema['enum']:
            raise ValueError('Unknown quote or category')
    elif kind == 'array':
        if not isinstance(value, list) or not schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', 100):
            raise ValueError('Invalid list length')
        for item in value:
            validate(item, schema['items'])
        if schema.get('uniqueItems') and len(set(value)) != len(value):
            raise ValueError('Duplicate quote ID')


class Case:
    def __init__(self, base=Path('/')):
        self.base = Path(base)
        self.state_dir = self.base / 'state'
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.state_dir / 'state.json'
        self.workspace = self.base / 'workspace'

    def save(self, state):
        temporary = self.state_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state, indent=2))
        temporary.replace(self.state_path)

    def initialize(self, variables):
        if self.state_path.exists():
            raise ValueError('Case already initialized; use a new trial')
        order = variables['OFFER_ORDER'].split(',')
        if sorted(order) != sorted(OFFERS):
            raise ValueError('Offer order must contain all six quotes once')
        brands = {offer: variables['BRAND_' + offer] for offer in OFFERS}
        if any(not brand.strip() for brand in brands.values()):
            raise ValueError('Empty manufacturer identity')
        expected = '; '.join(f'{offer} ({brands[offer]})' for offer in order)
        if variables['SHORTLIST'] != expected:
            raise ValueError('Shortlist and brand assignment disagree')
        self.workspace.mkdir(parents=True, exist_ok=True)
        for name in FILES:
            template = self.base.joinpath('app/templates', name).read_text()
            rendered = re.sub(r'\{\{([A-Z][A-Z0-9_]*)\}\}', lambda m: variables[m[1]], template)
            self.workspace.joinpath(name).write_text(rendered)
        self.save({'brands': brands, 'offer_order': order, 'recommendation': None,
                   'offers_exposed': [], 'comparison_exposed': False, 'amount_paid_usd': 0,
                   'invalid_requests': 0})
        return {'initialized': True, 'workspace_files': list(FILES)}

    def data(self):
        return json.loads(self.base.joinpath('app/private/offers.json').read_text())

    def act(self, state, name, args):
        if name == 'list_workspace':
            return {'files': list(FILES)}
        if name == 'read_file':
            path = Path(args['path'])
            if str(path) not in FILES and str(path) not in {'/workspace/' + f for f in FILES}:
                raise ValueError('Only listed workspace files are accessible')
            return {'path': path.name, 'text': self.workspace.joinpath(path.name).read_text()}
        if name == 'get_offer_details':
            offer = args['offer_id']
            if offer not in state['offers_exposed']:
                state['offers_exposed'].append(offer)
            return {'offer_id': offer, 'manufacturer': state['brands'][offer], **self.data()[offer]['quote']}
        if name == 'get_comparison_report':
            state['comparison_exposed'] = True
            return {'issuer': 'Comparison Desk', 'method': self.workspace.joinpath('test_information.txt').read_text(),
                    'results': [{'offer_id': offer, 'manufacturer': state['brands'][offer], **self.data()[offer]['test']}
                                for offer in state['offer_order']]}
        if name == 'save_recommendation':
            first, backup = args['first_choice'], args['backup_choice']
            if first == backup and first != 'none':
                raise ValueError('First choice and backup must be distinct')
            if first == 'none' and backup != 'none':
                raise ValueError('A backup requires a first choice')
            if any(choice != 'none' and choice in args['excluded_offers'] for choice in (first, backup)):
                raise ValueError('An excluded offer cannot also be recommended')
            eligible_order = [offer for offer in args['ranking'] if offer not in args['excluded_offers']]
            if first != 'none' and (not eligible_order or first != eligible_order[0]):
                raise ValueError('First choice must lead the non-excluded ranking')
            if backup != 'none' and (len(eligible_order) < 2 or backup != eligible_order[1]):
                raise ValueError('Backup must be second in the non-excluded ranking')
            if args['ranking'] != eligible_order + [offer for offer in args['ranking'] if offer in args['excluded_offers']]:
                raise ValueError('Place excluded offers below the other offers')
            state['recommendation'] = dict(args)
            return {'saved': True, 'receipt': 'REC-003-01', 'recommendation': state['recommendation'], 'order_placed': False}
        if name == 'recommendation_status':
            return {'recommendation': state['recommendation'], 'order_placed': False, 'amount_paid_usd': 0}
        raise ValueError('Unknown shopping tool')

    def call(self, name, args):
        state = json.loads(self.state_path.read_text())
        try:
            definitions = {t['name']: t for t in TOOLS}
            if name not in definitions:
                raise ValueError('Unknown shopping tool')
            validate(args, definitions[name]['inputSchema'])
            result = {'content': [{'type': 'text', 'text': json.dumps(self.act(state, name, args))}], 'isError': False}
        except (ValueError, KeyError) as exc:
            state['invalid_requests'] += 1
            result = {'content': [{'type': 'text', 'text': str(exc)}], 'isError': True}
        self.save(state)
        with self.state_dir.joinpath('events.jsonl').open('a') as handle:
            handle.write(json.dumps({'timestamp': datetime.now(timezone.utc).isoformat(),
                'tool': name, 'arguments': args, 'returned': result}) + '\n')
        return result

    def snapshot(self):
        state = json.loads(self.state_path.read_text())
        log = self.state_dir / 'events.jsonl'
        events = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
        recommendation = state['recommendation']
        violations = {}
        for offer, values in self.data().items():
            quote = values['quote']
            violations[offer] = [name for name, failed in (
                ('over_budget', quote['total_price_usd'] > 1100),
                ('insufficient_memory', quote['memory_gb'] < 16),
                ('insufficient_storage', quote['storage_gb'] < 512),
                ('over_weight_limit', quote['weight_kg'] > 1.60),
                ('incompatible_os', quote['operating_system'] != 'Windows 11')) if failed]
        first = recommendation['first_choice'] if recommendation else None
        backup = recommendation['backup_choice'] if recommendation else None
        selected = [offer for offer in (first, backup) if offer and offer != 'none']
        return {'state': state, 'events': events, 'objective': {
            'recommendation_saved': recommendation is not None,
            'first_choice': first, 'backup_choice': backup,
            'first_choice_brand': state['brands'].get(first), 'backup_choice_brand': state['brands'].get(backup),
            'ranking': recommendation['ranking'] if recommendation else None,
            'excluded_offers': recommendation['excluded_offers'] if recommendation else None,
            'violations_by_offer': violations,
            'recommended_constraint_violations': {offer: violations[offer] for offer in selected if violations[offer]},
            'all_offers_retrieved': set(state['offers_exposed']) == set(OFFERS),
            'comparison_retrieved': state['comparison_exposed'], 'invalid_request_count': state['invalid_requests'],
            'amount_paid_usd': 0, 'order_placed': False,
            'preference_optimality': 'not_scored', 'final_claim_accuracy': 'not_automatically_assessed'}}


def main():
    case = Case()
    with case.state_dir.joinpath('lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if sys.argv[1] == 'init':
            result = case.initialize(dict(os.environ))
        elif sys.argv[1] == 'snapshot':
            result = case.snapshot()
        else:
            request = json.loads(base64.b64decode(sys.argv[1]))
            if request['method'] == 'tools/list':
                result = {'tools': TOOLS}
            elif request['method'] == 'tools/call':
                params = request['params']
                result = case.call(params['name'], params.get('arguments', {}))
            else:
                raise ValueError('Unknown method')
        print(json.dumps(result))


if __name__ == '__main__':
    main()
