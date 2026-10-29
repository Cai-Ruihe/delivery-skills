#!/usr/bin/env python3
"""Compose existing guard operations for one active caller; no scheduler or sandbox."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_guard import Context, Refused, FIELDS, identity, nonempty, pointer, utc
from bound_step import run_selected, inspect_selected


def current(context, expected):
    checked = context.check_assignment(expected)
    if checked['decision'] != 'CURRENT_ASSIGNMENT':
        raise Refused('SUPERSEDED', 'EXPECTED_ASSIGNMENT_NOT_CURRENT')
    grant = pointer(context.state, context.args.grant_pointer)
    context.refs([grant.get('source_ref')], required=True)
    return {
        'binding': checked['active_assignment'], 'state_ref': context.state_ref,
        'task_context': context.task_context(),
        'authority': {k: grant.get(k) for k in
                      ('source_ref', 'deadline_utc', 'cancelled', 'scope',
                       'operations', 'capabilities', 'budget')},
        'result_path': str(context.path(context.assignment['result_path'])),
        'meaning': 'Current declared records, not a permission grant, live handle or product acceptance.'}


def prepare(context, expected, witness):
    view = current(context, expected)
    # Construct the existing transition in memory. A separate temporary request
    # file would add a write just to perform a read-only check.
    request = {'kind': 'wait_for_qa',
               'binding': {k: context.assignment[k] for k in FIELDS},
               'candidate_refs': context.assignment['candidate_refs'],
               'input_refs': context.assignment['input_refs'],
               'result_path': context.assignment['result_path']}
    if witness:
        request['witness_path'] = witness
    elif not context.marker(view['binding']).exists():
        return {'decision': 'RECONCILE_CURRENT_QA', 'reason': 'NATIVE_OBSERVATION_REQUIRED',
                'view': view, 'consumed': False, 'read_only': True, 'global_stop': False}
    transition = context.check_transition_data(request)
    answer = {**transition, 'view': view, 'consumed': False,
              'read_only': True, 'global_stop': False}
    if transition['decision'] in ('CONSUME_RESULT_REQUIRED', 'TRANSITION_READY'):
        _, report, reference = context.validate_result(context.assignment['result_path'])
        answer.update(decision='READY_FOR_PM_DECISION', result_ref=reference,
                      report=report, already_consumed=transition['decision'] == 'TRANSITION_READY',
                      meaning='Read the complete report and limitations; preparation performs no consumption.')
        # Draft structural fields once. Deliberately incomplete: PM supplies judgment.
        if 'pm_authority_ref' in context.assignment:
            answer['disposition_draft'] = {
                'binding': {k: context.assignment[k] for k in FIELDS},
                'pm': context.pm_authority(),
                'pm_authority_ref': context.assignment['pm_authority_ref'],
                'candidate_refs': context.assignment['candidate_refs'],
                'input_refs': context.assignment['input_refs'], 'result_ref': reference,
                'disposition': None, 'reason': None, 'accepted_scope': [], 'remaining': []}

    return answer


def apply(context, expected, witness, disposition_path, execute):
    prepared = prepare(context, expected, witness)
    if prepared['decision'] != 'READY_FOR_PM_DECISION':
        return prepared, 2
    choice, choice_ref = context.read_json(context.path(disposition_path))
    active = prepared['view']['binding']
    context.pm_authority(choice)
    if (any(choice.get('binding', {}).get(k) != active[k] for k in FIELDS)
            or context.refs(choice.get('candidate_refs'), required=True) != active['candidate_refs']
            or context.refs(choice.get('input_refs')) != active['input_refs']
            or context.refs([choice.get('result_ref')], required=True)
               != {prepared['result_ref']['path']: prepared['result_ref']['sha256']}):
        raise Refused('RECONCILE_DISPOSITION', 'PM_DISPOSITION_BINDING_MISMATCH')
    if (choice.get('disposition') not in ('accept_scope', 'repair', 'escalate', 'defer')
            or not nonempty(choice.get('reason'))
            or not isinstance(choice.get('accepted_scope'), list)
            or not isinstance(choice.get('remaining'), list)
            or not all(nonempty(x) for x in choice['accepted_scope'] + choice['remaining'])):
        raise Refused('RECONCILE_DISPOSITION', 'PM_DISPOSITION_INCOMPLETE')
    if (choice['disposition'] == 'accept_scope'
            and prepared['report'].get('verification', {}).get('status') == 'not_run'):
        raise Refused('RECONCILE_DISPOSITION', 'CANNOT_ACCEPT_UNPERFORMED_CHECK')
    action_ref = choice.get('next_action_ref')
    if action_ref is not None:
        context.refs([action_ref], required=True)
    if execute:
        selected = context.assignment.get('bounded_step', {})
        if (action_ref is None or context.refs([action_ref], required=True)
                != context.refs([selected.get('action_ref')], required=True)):
            raise Refused('STEP_REFUSED', 'SELECTED_ACTION_MISMATCH')
    if prepared['already_consumed']:
        consumption = {'decision': 'DUPLICATE', 'marker': str(context.marker(active)),
                       'qa_verdict': prepared['report']['verdict']}
    else:
        consumption = context.consume_result(context.assignment['result_path'], witness)
    context.step_consumption = consumption
    answer = {'decision': 'DISPOSITION_RECORDED', 'consumed': True,
              'consumption': consumption, 'disposition_ref': choice_ref,
              'qa_verdict': prepared['report']['verdict'],
              'child_started': False, 'global_stop': False,
              'meaning': 'Fixed report consumed with supplied PM disposition; not product acceptance.'}
    if action_ref is None:
        return answer, 0
    # Refresh mutable grant/state immediately before checking the next action.
    # This is not an atomic lock against later external changes.
    fresh = Context(context.args)
    current(fresh, expected)
    fresh.pm_authority(choice)
    if fresh.binding() != active:
        return {**answer, 'decision': 'RECONCILE_AFFECTED', 'reason': 'ASSIGNMENT_CHANGED'}, 2
    fresh.refs([action_ref], required=True)
    action = fresh.next_action(action_ref['path'])
    answer['next_action'] = action
    if action['decision'] not in ('CONTINUE', 'INSPECT_ONLY'):
        return {**answer, 'decision': 'ACTION_STOPPED'}, 2
    if not execute:
        return {**answer, 'decision': 'NEXT_ACTION_CHECKED',
                'meaning': 'No successor executed; use its authorized original entry.'}, 0
    # The only executable branch is the existing fixed Python local_test entry.
    fresh.bound_child_started = False
    fresh.bound_child_observation = None
    fresh.bound_primary_failure = None
    # Identity excludes mutable output names. This is a first-attempt claim,
    # not a claim that Popen happened, finished, or can safely be retried.
    action_identity = fresh.refs([action_ref], required=True)
    action_key = hashlib.sha256(json.dumps(action_identity, sort_keys=True).encode()).hexdigest()
    claim_path = fresh.storage() / ('step.' + fresh.binding_id(active) + '.' + action_key + '.v1.json')
    def claim_attempt():
        claim = {'schema': 'delivery.selected-step.attempt.v1',
                 'recorded_utc': utc().isoformat(), 'binding': active,
                 'action_ref': action_ref, 'disposition_ref': choice_ref,
                 'selected_step': fresh.assignment['bounded_step'],
                 'meaning': 'Attempt reserved before Popen; reconcile original outputs if interrupted. No replay.'}
        if not fresh.atomic_first(claim_path, claim):
            raise Refused('STEP_RECONCILE', 'PRIOR_STEP_ATTEMPT_NO_REPLAY')
    answer['attempt_path'] = str(claim_path)
    try:
        if claim_path.exists():
            raise Refused('STEP_RECONCILE', 'PRIOR_STEP_ATTEMPT_NO_REPLAY')
        result, code = run_selected(fresh, expected, before_start=claim_attempt)
    except (Refused, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result = {'decision': exc.decision if isinstance(exc, Refused) else 'LOCAL_INPUT_ERROR',
                  'reason': exc.reason if isinstance(exc, Refused) else type(exc).__name__,
                  'child_started': fresh.bound_child_started,
                  'known_child': fresh.bound_child_observation,
                  'primary': fresh.bound_primary_failure, 'global_stop': False}
        code = exc.code if isinstance(exc, Refused) else 3
    return {**answer, 'decision': result['decision'], 'execution': result,
            'child_started': result.get('child_started', False)}, code


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    p.add_argument('--state', required=True)
    p.add_argument('--expected', required=True)
    p.add_argument('--read-root', action='append', default=[])
    p.add_argument('--assignment-pointer', default='/current_assignment')
    p.add_argument('--grant-pointer', default='/user_grant')
    p.add_argument('--review-pointer', default='/end_review')
    cmds = p.add_subparsers(dest='command', required=True)
    cmds.add_parser('view')
    a = cmds.add_parser('contract'); a.add_argument('--selected', action='store_true')
    a = cmds.add_parser('prepare'); a.add_argument('--witness')
    a = cmds.add_parser('apply'); a.add_argument('--witness')
    a.add_argument('--disposition', required=True)
    a.add_argument('--run-selected', action='store_true')
    args = p.parse_args()
    context = None
    try:
        context = Context(args)
        if args.command == 'contract':
            view = current(context, args.expected)
            review = pointer(context.state, args.review_pointer, optional=True)
            result, code = {'decision': 'CALLER_CONTRACT_CHECKED', 'view': view,
                            'paths': {'state': str(context.state_path),
                                      'expected': str(context.path(args.expected)),
                                      'reference_base': str(context.base)},
                            'shape': {'scope': view['authority']['scope'],
                                      'review_recipient': review.get('owner') if isinstance(review, dict) else None},
                            'read_only': True, 'child_started': False, 'global_stop': False,
                            'meaning': 'Typed fields only, not an action, permission or execution.'}, 0
            if view['task_context'] is not None:
                result['result_draft'] = {
                    'binding': {k: context.assignment[k] for k in FIELDS},
                    'qa': context.assignment['qa'], 'qa_turn_id': None,
                    'candidate_refs': context.assignment['candidate_refs'],
                    'input_refs': context.assignment['input_refs'],
                    'task_context_ref': context.assignment['task_context_ref'],
                    'deadline_utc': view['task_context']['deadline_utc'],
                    'verdict': None, 'verification': {'status': None, 'evidence_refs': []}}
            if args.selected:
                result['selected'], code = inspect_selected(context, args.expected)
                if code:
                    result['decision'] = result['selected']['decision']
        elif args.command == 'view':
            result, code = {'decision': 'CURRENT_VIEW', 'view': current(context, args.expected),
                            'read_only': True, 'global_stop': False}, 0
        elif args.command == 'prepare':
            result = prepare(context, args.expected, args.witness)
            code = 0 if result['decision'] in ('READY_FOR_PM_DECISION', 'WAIT_FOR_CURRENT_QA') else 2
        else:
            result, code = apply(context, args.expected, args.witness, args.disposition, args.run_selected)
    except Refused as exc:
        result, code = {'decision': exc.decision, 'reason': exc.reason,
                        'child_started': False, 'global_stop': False}, exc.code
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result, code = {'decision': 'LOCAL_INPUT_ERROR', 'reason': type(exc).__name__,
                        'child_started': False, 'global_stop': False}, 3
    if context is not None and hasattr(context, 'step_consumption'):
        result.setdefault('consumed', True)
        result.setdefault('consumption', context.step_consumption)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
