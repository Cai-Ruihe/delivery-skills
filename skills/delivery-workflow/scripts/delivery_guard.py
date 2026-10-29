#!/usr/bin/env python3
"""Small local assignment/result guard. Never dispatches or executes proposed work."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import uuid


FIELDS = ('project', 'round', 'task', 'revision')
SUCCESS = {'CURRENT_ASSIGNMENT', 'CONSUMED', 'DUPLICATE', 'CONTINUE', 'INSPECT_ONLY', 'RECONCILED',
           'TRANSITION_READY', 'WAIT_FOR_CURRENT_QA'}


class Refused(Exception):
    def __init__(self, decision, reason=None, code=2):
        self.decision, self.reason, self.code = decision, reason or decision, code


def utc():
    return datetime.now(timezone.utc)


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def pointer(document, location, optional=False):
    if location == '':
        return document
    if not location.startswith('/'):
        raise Refused('INVALID_POINTER', code=3)
    try:
        for key in location[1:].split('/'):
            key = key.replace('~1', '/').replace('~0', '~')
            document = document[int(key)] if isinstance(document, list) else document[key]
        return document
    except (KeyError, IndexError, TypeError, ValueError):
        if optional:
            return None
        raise Refused('MISSING_EVIDENCE', 'STATE_POINTER_MISSING', 3)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def identity(value):
    if not isinstance(value, dict) or not all(nonempty(value.get(k)) for k in ('thread_id', 'host_id')):
        raise Refused('MISSING_EVIDENCE', 'ROLE_BINDING_MISSING')
    return {k: value[k] for k in ('thread_id', 'host_id')}


def decimal_value(value):
    try:
        if isinstance(value, bool) or value is None:
            raise InvalidOperation
        result = Decimal(str(value))
        if not result.is_finite() or result < 0:
            raise InvalidOperation
        return result
    except (InvalidOperation, ValueError):
        raise Refused('STOP_AFFECTED', 'CUMULATIVE_COST_UNKNOWN')


RELEASE_VERSION = 'delivery-skills-2026-10-30-r1'


class Context:
    def __init__(self, args):
        self.args = args
        original = Path(args.root).absolute()
        if original.is_symlink() or not original.is_dir():
            raise Refused('UNSAFE_PATH', 'ROOT_NOT_OWNED_DIRECTORY', 3)
        self.root = original.resolve()
        self.read_roots = [(original, self.root)]
        for raw in args.read_root:
            directory = Path(raw).absolute()
            if directory.is_symlink() or not directory.is_dir():
                raise Refused('UNSAFE_PATH', 'READ_ROOT_INVALID', 3)
            self.read_roots.append((directory, directory.resolve()))
        self.base = self.root
        self.state_path = self.path(args.state)
        self.base = self.state_path.parent
        self.state, self.state_ref = self.read_json(self.state_path)
        self.assignment = pointer(self.state, args.assignment_pointer)
        if not isinstance(self.assignment, dict):
            raise Refused('MISSING_EVIDENCE', 'ASSIGNMENT_MISSING', 3)

    def path(self, raw, write=False):
        if not nonempty(str(raw)):
            raise Refused('UNSAFE_PATH')
        raw = Path(raw)
        path = raw if raw.is_absolute() else self.base / raw
        resolved = path.resolve()
        roots = self.read_roots[:1] if write else self.read_roots
        if not any(resolved.is_relative_to(canonical) for _, canonical in roots):
            raise Refused('UNSAFE_PATH', 'OUTSIDE_EXPLICIT_ROOT')
        # Inspect the lexical chain before trusting resolution, including link/..
        # aliases. System ancestors above the selected root are not our objects.
        boundaries = {p for pair in self.read_roots for p in pair}
        for node in (path, *path.parents):
            if node in boundaries:
                break
            if node.is_symlink():
                raise Refused('UNSAFE_PATH', 'SYMLINK_NOT_ALLOWED')
        return resolved

    def read_bytes(self, path):
        path = self.path(str(path))
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise Refused('UNSAFE_PATH', 'NOT_REGULAR_FILE')
            with os.fdopen(fd, 'rb', closefd=False) as stream:
                data = stream.read()
        finally:
            os.close(fd)
        return data, {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def read_json(self, path):
        data, reference = self.read_bytes(path)
        try:
            result = json.loads(data, object_pairs_hook=object_pairs,
                                parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            if not isinstance(result, dict):
                raise ValueError()
            return result, reference
        except (ValueError, UnicodeError):
            raise Refused('MALFORMED_JSON', code=3)

    def refs(self, values, verify=True, required=False):
        if not isinstance(values, list) or (required and not values):
            raise Refused('MISSING_EVIDENCE', 'FIXED_REFERENCES_REQUIRED')
        answer = {}
        for item in values:
            if not isinstance(item, dict) or not nonempty(item.get('path')) or not nonempty(item.get('sha256')):
                raise Refused('MISSING_EVIDENCE', 'FIXED_REFERENCE_INVALID')
            path = self.path(item['path'])
            expected = item['sha256'].lower()
            if verify:
                _, actual = self.read_bytes(path)
                if actual['sha256'] != expected or ('bytes' in item and actual['bytes'] != item['bytes']):
                    raise Refused('REFERENCE_CHANGED')
            if str(path) in answer and answer[str(path)] != expected:
                raise Refused('MISSING_EVIDENCE', 'CONFLICTING_REFERENCES')
            answer[str(path)] = expected
        return answer

    def binding(self, assignment=None):
        assignment = self.assignment if assignment is None else assignment
        if not isinstance(assignment, dict) or not all(nonempty(assignment.get(k)) for k in FIELDS):
            raise Refused('MISSING_EVIDENCE', 'TASK_BINDING_MISSING')
        author, qa = identity(assignment.get('author')), identity(assignment.get('qa'))
        if author['thread_id'] == qa['thread_id']:
            raise Refused('QA_NOT_INDEPENDENT')
        candidates = self.refs(assignment.get('candidate_refs'), required=True)
        inputs = self.refs(assignment.get('input_refs'))
        return {**{k: assignment[k] for k in FIELDS}, 'author': author, 'qa': qa,
                'candidate_refs': candidates, 'input_refs': inputs}

    def pm_authority(self, disposition=None):
        """Check a pinned role declaration, not platform authentication or a grant."""
        reference = self.assignment.get('pm_authority_ref')
        self.refs([reference], required=True)
        record, _ = self.read_json(self.path(reference['path']))
        active = self.binding()
        pm = identity(record.get('pm'))
        if (any(record.get('binding', {}).get(k) != active[k] for k in FIELDS)
                or identity(record.get('author')) != active['author']
                or identity(record.get('qa')) != active['qa']
                or pm['thread_id'] == active['qa']['thread_id']):
            raise Refused('RECONCILE_PM_AUTHORITY', 'PM_ROLE_BINDING_MISMATCH')
        self.refs([record.get('source_ref')], required=True)
        if disposition is not None:
            if (identity(disposition.get('pm')) != pm
                    or self.refs([disposition.get('pm_authority_ref')], required=True)
                    != self.refs([reference], required=True)):
                raise Refused('RECONCILE_PM_AUTHORITY', 'PM_DISPOSITION_AUTHORITY_MISMATCH')
        return pm

    def task_context(self):
        """Validate an adopted short task record; no native-tool interception."""
        reference = self.assignment.get('task_context_ref')
        if reference is None:
            return None
        self.refs([reference], required=True)
        record, _ = self.read_json(self.path(reference['path']))
        active = self.binding()
        if (any(record.get('binding', {}).get(k) != active[k] for k in FIELDS)
                or identity(record.get('author')) != active['author']
                or identity(record.get('qa')) != active['qa']):
            raise Refused('SUPERSEDED', 'TASK_CONTEXT_BINDING_MISMATCH')
        self.pm_authority(record)
        self.refs([record.get('goal_ref')], required=True)
        grant = pointer(self.state, self.args.grant_pointer)
        if record.get('deadline_utc') != grant.get('deadline_utc'):
            raise Refused('SUPERSEDED', 'TASK_CONTEXT_DEADLINE_MISMATCH')
        release = record.get('release', {})
        if release.get('version') != RELEASE_VERSION:
            raise Refused('SUPERSEDED', 'TASK_CONTEXT_RELEASE_MISMATCH')
        scripts = release.get('scripts', {})
        names = ('delivery_guard.py', 'delivery_step.py', 'bound_step.py')
        if set(scripts) != set(names):
            raise Refused('MISSING_EVIDENCE', 'SAME_RELEASE_SCRIPTS_REQUIRED')
        for name in names:
            ref = scripts[name]
            self.refs([ref], required=True)
            if self.path(ref['path']) != Path(__file__).resolve().parent / name:
                raise Refused('SUPERSEDED', 'MIXED_RELEASE_PATH')
        surfaces = record.get('surfaces', {})
        for mode in ('read', 'write'):
            values = surfaces.get(mode)
            if not isinstance(values, list) or not all(nonempty(x) for x in values):
                raise Refused('MISSING_EVIDENCE', 'TASK_SURFACES_REQUIRED')
            for value in values:
                self.path(value, write=mode == 'write')
        return record

    def task_surface(self, path, write=False):
        record = self.task_context()
        if record is not None:
            mode = 'write' if write else 'read'
            if not any(path.is_relative_to(self.path(raw, write=write))
                       for raw in record['surfaces'][mode]):
                raise Refused('STOP_AFFECTED', 'OUTSIDE_TASK_SURFACE')

    def binding_id(self, binding):
        # State/result generation times, verdicts and native observation times
        # are deliberately absent from fixed candidate/obligation identity.
        return hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def storage(self):
        return self.path(self.assignment.get('consumption_dir', 'guard-consumption'), write=True)

    def marker(self, binding):
        return self.storage() / ('consume.' + self.binding_id(binding) + '.v1.json')

    def ensure_directory(self, path):
        path = self.path(str(path), write=True)
        relative = path.relative_to(self.root)
        current = self.root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise Refused('UNSAFE_PATH', 'OUTPUT_DIRECTORY_SYMLINK')
            current.mkdir(exist_ok=True)
            if not current.is_dir():
                raise Refused('UNSAFE_PATH', 'OUTPUT_NOT_DIRECTORY')
        return path

    def atomic_first(self, path, value):
        directory = self.ensure_directory(path.parent)
        path = self.path(str(path), write=True)
        temporary = directory / ('.write-' + uuid.uuid4().hex)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(temporary, flags, 0o600)
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(value, stream, ensure_ascii=False, sort_keys=True)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
            try:
                os.link(temporary, path, follow_symlinks=False)
                return True
            except FileExistsError:
                return False
        finally:
            temporary.unlink()

    def record_rejection(self, value):
        path = self.storage() / 'dispositions' / ('refusal.' + uuid.uuid4().hex + '.v1.json')
        self.atomic_first(path, {'schema': 'delivery.guard.disposition.v1', 'observed_utc': utc().isoformat(), **value})
        return str(path)

    def check_assignment(self, expected_path=None):
        active = self.binding()
        if expected_path:
            expected, _ = self.read_json(self.path(expected_path))
            # PM authority is separate from content/attempt identity. Never fall
            # back to author, or turn a role update into a new execution identity.
            if ('pm_authority_ref' in expected or 'pm_authority_ref' in self.assignment):
                if (self.refs([expected.get('pm_authority_ref')], verify=False, required=True)
                        != self.refs([self.assignment.get('pm_authority_ref')], required=True)):
                    raise Refused('SUPERSEDED', 'PM_AUTHORITY_CHANGED')
            # Compare explicit expected metadata first: stale source may no longer
            # exist and must not be executed as a fallback.
            if (any(expected.get(k) != active[k] for k in FIELDS)
                    or identity(expected.get('qa')) != active['qa']
                    or identity(expected.get('author')) != active['author']
                    or self.refs(expected.get('candidate_refs'), verify=False) != active['candidate_refs']
                    or self.refs(expected.get('input_refs'), verify=False) != active['input_refs']):
                return {'decision': 'SUPERSEDED', 'active_assignment': active,
                        'obligation': 'Use the current binding; do not execute the superseded task.'}
        if expected_path and ('task_context_ref' in expected or 'task_context_ref' in self.assignment):
            if (self.refs([expected.get('task_context_ref')], verify=False, required=True)
                    != self.refs([self.assignment.get('task_context_ref')], required=True)):
                raise Refused('SUPERSEDED', 'EXPECTED_TASK_CONTEXT_CHANGED')
        self.task_context()
        return {'decision': 'CURRENT_ASSIGNMENT', 'active_assignment': active,
                'binding_id': self.binding_id(active)}

    def validate_result(self, result_path):
        active = self.binding()
        expected_path = self.path(self.assignment.get('result_path', ''))
        result_path = self.path(result_path)
        result, reference = self.read_json(result_path)
        binding = result.get('binding', {})
        for name, decision in [('project', 'WRONG_PROJECT'), ('round', 'STALE_ROUND'),
                               ('task', 'STALE_TASK'), ('revision', 'STALE_REVISION')]:
            if binding.get(name) != active[name]:
                raise Refused(decision)
        if result_path != expected_path:
            raise Refused('UNEXPECTED_RESULT_LOCATION')
        if identity(result.get('qa')) != active['qa']:
            raise Refused('QA_IDENTITY_MISMATCH')
        for field, decision in [('candidate_refs', 'CANDIDATE_MISMATCH'), ('input_refs', 'INPUT_MISMATCH')]:
            observed = self.refs(result.get(field), verify=False)
            if any(observed.get(path) != digest for path, digest in active[field].items()):
                raise Refused(decision)
        if not nonempty(result.get('verdict')) or not nonempty(result.get('qa_turn_id')):
            raise Refused('MISSING_EVIDENCE', 'FIXED_QA_VERDICT_AND_TURN_REQUIRED')
        task = self.task_context()
        if task is not None:
            if (self.refs([result.get('task_context_ref')], required=True)
                    != self.refs([self.assignment['task_context_ref']], required=True)
                    or result.get('deadline_utc') != task['deadline_utc']):
                raise Refused('STALE_RESULT_CONTEXT')
            verification = result.get('verification', {})
            if verification.get('status') == 'executed':
                self.refs(verification.get('evidence_refs'), required=True)
            elif (verification.get('status') != 'not_run'
                  or verification.get('evidence_refs') != []
                  or result['verdict'].upper() in ('PASS', 'ACCEPTED', 'SUCCESS')):
                raise Refused('MISSING_EVIDENCE', 'RESULT_EXECUTION_EVIDENCE_REQUIRED')
            if verification.get('status') == 'not_run':
                dependencies = self.assignment.get('dependent_actions', {})
                if not isinstance(dependencies, dict):
                    raise Refused('MISSING_EVIDENCE', 'DEPENDENCY_POLICY_UNKNOWN')
                if any(isinstance(allowed, list) and result['verdict'] in allowed
                       for allowed in dependencies.values()):
                    raise Refused('MISSING_EVIDENCE', 'UNPERFORMED_ACCEPTING_VERDICT')
        return active, result, reference

    def consume_result(self, result_path, witness_path):
        active, result, reference = self.validate_result(result_path)
        if not witness_path:
            raise Refused('NATIVE_EVIDENCE_REQUIRED')
        observation, observation_ref = self.read_json(self.path(witness_path))
        if observation.get('source') not in ('read_thread', 'wait_threads'):
            raise Refused('NATIVE_EVIDENCE_REQUIRED')
        if identity(observation) != active['qa'] or observation.get('turn_id') != result['qa_turn_id']:
            raise Refused('QA_IDENTITY_MISMATCH')
        if observation.get('status') != 'completed':
            raise Refused('QA_NOT_TERMINAL')
        marker = self.marker(active)
        value = {'schema': 'delivery.guard.consumption.v1', 'decision': 'CONSUMED',
                 'observed_utc': utc().isoformat(), 'binding_id': self.binding_id(active),
                 'binding': active, 'result_ref': reference, 'native_observation_ref': observation_ref,
                 'qa_verdict': result['verdict'],
                 'meaning': 'Fixed QA report consumed, not product acceptance or identity authentication.'}
        if self.atomic_first(marker, value):
            return {'decision': 'CONSUMED', 'marker': str(marker), 'binding_id': value['binding_id'],
                    'qa_verdict': result['verdict']}
        try:
            first, _ = self.read_json(marker)
        except (Refused, OSError):
            raise Refused('STORED_DISPOSITION_INVALID')
        if (first.get('schema') != value['schema'] or first.get('decision') != 'CONSUMED'
                or first.get('binding_id') != value['binding_id']):
            raise Refused('STORED_DISPOSITION_INVALID')
        if first.get('result_ref') != reference:
            raise Refused('CONFLICTING_DUPLICATE')
        return {'decision': 'DUPLICATE', 'marker': str(marker), 'binding_id': value['binding_id'],
                'qa_verdict': first['qa_verdict']}

    def check_transition(self, request_path):
        """Inspect one declared PM transition; never consume or execute it."""
        request, _ = self.read_json(self.path(request_path))
        return self.check_transition_data(request)

    def check_transition_data(self, request):
        """Same transition rules for a composed caller; no temporary request file."""
        kind = request.get('kind')
        if kind not in ('wait_for_qa', 'switch_assignment', 'dependent_action',
                        'independent_action', 'authorized_settlement'):
            return {'decision': 'RECONCILE_TRANSITION', 'reason': 'TRANSITION_KIND_UNKNOWN',
                    'read_only': True, 'global_stop': False}
        if kind == 'independent_action':
            return {**self.next_action(request['action_path']), 'read_only': True,
                    'transition_kind': kind}
        if kind == 'authorized_settlement':
            action, _ = self.read_json(self.path(request['action_path']))
            grant = pointer(self.state, self.args.grant_pointer)
            operation = action.get('operation')
            allowed = isinstance(grant, dict) and operation in grant.get('settlement_operations', [])
            if operation == 'local_settle':
                allowed = allowed and action.get('effect') == 'local_metadata' and action.get('local_only') is True
            elif operation == 'submit_review':
                review = pointer(self.state, self.args.review_pointer, optional=True)
                allowed = (allowed and isinstance(review, dict) and action.get('effect') == 'native_message'
                           and action.get('recipient') == review.get('owner')
                           and action.get('review_key') == review.get('key'))
            else:
                allowed = False
            if not allowed:
                return {'decision': 'STOP_AFFECTED', 'reason': 'SETTLEMENT_NOT_AUTHORIZED',
                        'read_only': True, 'global_stop': False}
            return {**self.next_action(request['action_path']), 'read_only': True,
                    'transition_kind': kind}
        preflight = None
        if kind in ('dependent_action', 'switch_assignment'):
            preflight = self.next_action(request['action_path'])
            if (preflight['decision'] != 'CONTINUE' and preflight.get('reason') not in
                    ('QA_RESULT_NOT_CONSUMED', 'QA_RESULT_CHANGED', 'QA_CONSUMPTION_NEEDS_RECONCILIATION')):
                return {**preflight, 'read_only': True, 'transition_kind': kind}
        active = self.binding()
        proposed = request.get('binding')
        if not isinstance(proposed, dict) or any(proposed.get(k) != active[k] for k in FIELDS):
            return {'decision': 'RECONCILE_TRANSITION', 'reason': 'TRANSITION_BINDING_MISMATCH',
                    'read_only': True, 'global_stop': False}
        if self.refs(request.get('candidate_refs'), verify=False, required=True) != active['candidate_refs']:
            return {'decision': 'RECONCILE_TRANSITION', 'reason': 'TRANSITION_CANDIDATE_MISMATCH',
                    'read_only': True, 'global_stop': False}
        if self.refs(request.get('input_refs'), verify=False) != active['input_refs']:
            return {'decision': 'RECONCILE_TRANSITION', 'reason': 'TRANSITION_INPUT_MISMATCH',
                    'read_only': True, 'global_stop': False}
        result_path = self.path(request.get('result_path', self.assignment['result_path']))
        if result_path != self.path(self.assignment['result_path']):
            return {'decision': 'RECONCILE_TRANSITION', 'reason': 'TRANSITION_RESULT_MISMATCH',
                    'read_only': True, 'global_stop': False}
        marker = self.marker(active)
        if marker.exists():
            try:
                active, result, reference = self.validate_result(str(result_path))
            except (Refused, OSError) as exc:
                return {'decision': 'RECONCILE_CURRENT_QA',
                        'reason': exc.decision if isinstance(exc, Refused) else 'FIXED_RESULT_UNREADABLE',
                        'read_only': True, 'global_stop': False}
            first, _ = self.read_json(marker)
            if (first.get('schema') != 'delivery.guard.consumption.v1'
                    or first.get('decision') != 'CONSUMED'
                    or first.get('binding_id') != self.binding_id(active)):
                raise Refused('STORED_DISPOSITION_INVALID')
            if first.get('result_ref') != reference:
                raise Refused('CONFLICTING_DUPLICATE')
            if kind == 'dependent_action':
                return {**self.next_action(request['action_path']), 'read_only': True,
                        'transition_kind': kind, 'qa_verdict': result['verdict']}
            if kind == 'switch_assignment' and preflight['decision'] != 'CONTINUE':
                return {**preflight, 'read_only': True, 'transition_kind': kind}
            return {'decision': 'TRANSITION_READY', 'reason': 'CURRENT_QA_ALREADY_CONSUMED',
                    'qa_verdict': result['verdict'], 'read_only': True, 'global_stop': False,
                    'meaning': 'This transition only; a negative verdict is not product acceptance.'}
        try:
            observation, _ = self.read_json(self.path(request['witness_path']))
        except OSError:
            return {'decision': 'RECONCILE_CURRENT_QA', 'reason': 'NATIVE_OBSERVATION_UNAVAILABLE',
                    'read_only': True, 'global_stop': False}
        if (observation.get('source') not in ('read_thread', 'wait_threads')
                or identity(observation) != active['qa']
                or not nonempty(observation.get('turn_id'))):
            raise Refused('NATIVE_EVIDENCE_REQUIRED')
        if observation.get('status') == 'inProgress':
            return {'decision': 'WAIT_FOR_CURRENT_QA', 'reason': 'CURRENT_QA_ACTIVE',
                    'read_only': True, 'global_stop': False,
                    'meaning': 'An active partial file is not a fixed result or completion proof.'}
        if observation.get('status') != 'completed':
            raise Refused('QA_NOT_TERMINAL')
        if not result_path.exists():
            return {'decision': 'RECONCILE_CURRENT_QA', 'reason': 'QA_COMPLETED_REPORT_MISSING',
                    'read_only': True, 'global_stop': False}
        try:
            active, result, reference = self.validate_result(str(result_path))
        except Refused as exc:
            return {'decision': 'RECONCILE_CURRENT_QA', 'reason': exc.decision,
                    'read_only': True, 'global_stop': False}
        if observation.get('turn_id') != result['qa_turn_id']:
            raise Refused('QA_IDENTITY_MISMATCH')
        return {'decision': 'CONSUME_RESULT_REQUIRED', 'reason': 'CURRENT_QA_COMPLETED',
                'qa_verdict': result['verdict'], 'read_only': True, 'global_stop': False,
                'next_command': 'consume-result'}

    def decision_dependency_issue(self, operation):
        """Check only caller-declared dependencies; never discover or grant authority."""
        dependencies = self.assignment.get('decision_dependencies', [])
        if not isinstance(dependencies, list):
            return 'DECISION_DEPENDENCY_UNKNOWN'
        for dependency in dependencies:
            if not isinstance(dependency, dict):
                return 'DECISION_DEPENDENCY_UNKNOWN'
            affects = dependency.get('affects')
            if not isinstance(affects, list) or not all(nonempty(x) for x in affects):
                return 'DECISION_DEPENDENCY_UNKNOWN'
            if operation not in affects:
                continue
            if (not all(nonempty(dependency.get(k)) for k in ('key', 'revision'))
                    or dependency.get('kind') not in ('advisory', 'binding')):
                return 'DECISION_DEPENDENCY_UNKNOWN'
            try:
                decision = self.refs([dependency.get('decision_ref')], required=True)
                disposition_ref = dependency.get('disposition_ref')
                if disposition_ref is None:
                    return 'DECISION_NOT_DISPOSITIONED'
                self.refs([disposition_ref], required=True)
                disposition, _ = self.read_json(self.path(disposition_ref['path']))
                self.pm_authority(disposition)
                if (disposition.get('decision_key') != dependency['key']
                        or disposition.get('decision_revision') != dependency['revision']
                        or self.refs([disposition.get('decision_ref')], required=True) != decision
                        or any(disposition.get('binding', {}).get(k) != self.assignment[k] for k in FIELDS)
                        or self.refs(disposition.get('candidate_refs'), required=True)
                        != self.refs(self.assignment.get('candidate_refs'), required=True)):
                    return 'DECISION_DISPOSITION_MISMATCH'
                choice = disposition.get('disposition')
                if (choice not in ('adopt', 'reject_nonbinding', 'unrelated')
                        or not nonempty(disposition.get('reason'))):
                    return 'DECISION_NOT_DISPOSITIONED'
                self.refs(disposition.get('evidence_refs'), required=True)
                if dependency['kind'] == 'binding' and choice != 'adopt':
                    return 'BINDING_DECISION_NOT_ADOPTED'
            except (Refused, OSError, TypeError, KeyError, AttributeError):
                return 'DECISION_DEPENDENCY_NEEDS_RECONCILIATION'
        return None

    def next_action(self, request_path):
        action, _ = self.read_json(self.path(request_path))
        grant = pointer(self.state, self.args.grant_pointer)
        if not isinstance(grant, dict):
            raise Refused('STOP_AFFECTED', 'USER_GRANT_UNKNOWN')
        source = grant.get('source_ref')
        self.refs([source] if isinstance(source, dict) else None, required=True)
        engineering = self.state.get('engineering', {})
        def answer(decision, reason, **extra):
            return {'decision': decision, 'reason': reason, 'global_stop': False,
                    'engineering': engineering, 'actual_utc': utc().isoformat(), **extra}
        for field in ('operations', 'capabilities'):
            values = grant.get(field)
            if not isinstance(values, list) or not all(nonempty(x) for x in values):
                return answer('STOP_AFFECTED', 'GRANT_STRUCTURE_UNKNOWN')
        operation = action.get('operation')
        if action.get('scope') != grant.get('scope') or operation not in grant.get('operations', []):
            return answer('STOP_AFFECTED', 'OPERATION_OR_SCOPE_NOT_GRANTED')
        if 'binding' in action and (not isinstance(action['binding'], dict)
                                   or any(action['binding'].get(k) != self.assignment.get(k) for k in FIELDS)):
            return answer('STOP_AFFECTED', 'ACTION_BINDING_MISMATCH')
        if 'candidate_refs' in action:
            selected = self.refs(self.assignment.get('candidate_refs'), required=True)
            proposed = self.refs(action['candidate_refs'], required=True)
            if proposed != selected:
                return answer('STOP_AFFECTED', 'ACTION_CANDIDATE_MISMATCH')
        requires = action.get('requires', [])
        if (not isinstance(requires, list) or not all(nonempty(x) for x in requires)
                or not set(requires).issubset(grant['capabilities'])):
            return answer('STOP_AFFECTED', 'CAPABILITY_MISSING')
        read_only = (operation in ('inspect', 'reconcile') and action.get('local_only') is True
                     and action.get('effect', 'read_only') == 'read_only')
        settlement = False
        settlement_operations = grant.get('settlement_operations', [])
        if not isinstance(settlement_operations, list) or not all(nonempty(x) for x in settlement_operations):
            settlement_operations = []
        if operation == 'submit_review':
            review = pointer(self.state, self.args.review_pointer, optional=True)
            if (not isinstance(review, dict) or action.get('recipient') != review.get('owner')
                    or action.get('review_key') != review.get('key')):
                return answer('STOP_AFFECTED', 'REVIEW_BINDING_MISMATCH')
            settlement = (operation in settlement_operations
                          and action.get('effect') == 'native_message')
        elif operation == 'local_settle':
            settlement = (operation in settlement_operations
                          and action.get('effect') == 'local_metadata'
                          and action.get('local_only') is True)
        if grant.get('cancelled') is not False and not read_only:
            return answer('STOP_AFFECTED', 'USER_CANCELLED' if grant.get('cancelled') else 'CANCELLATION_STATE_UNKNOWN')
        try:
            deadline = datetime.fromisoformat(grant['deadline_utc'].replace('Z', '+00:00'))
            if deadline.tzinfo is None:
                raise ValueError()
        except (KeyError, TypeError, ValueError):
            return answer('STOP_AFFECTED', 'USER_DEADLINE_UNKNOWN')
        expired = utc() >= deadline
        if expired and not (read_only or settlement):
            return answer('STOP_AFFECTED', 'USER_DEADLINE')
        dependent = self.assignment.get('dependent_actions', {})
        if not isinstance(dependent, dict) and not settlement:
            return answer('STOP_AFFECTED', 'DEPENDENCY_POLICY_UNKNOWN')
        if not settlement and operation in dependent:
            allowed_verdicts = dependent[operation]
            if not isinstance(allowed_verdicts, list) or not all(nonempty(x) for x in allowed_verdicts):
                return answer('STOP_AFFECTED', 'DEPENDENCY_POLICY_UNKNOWN')
            try:
                active = self.binding()
                marker = self.marker(active)
                if not marker.exists():
                    return answer('STOP_AFFECTED', 'QA_RESULT_NOT_CONSUMED')
                consumed, _ = self.read_json(marker)
                _, result, result_ref = self.validate_result(self.assignment['result_path'])
                if (consumed.get('decision') != 'CONSUMED'
                        or consumed.get('binding_id') != self.binding_id(active)):
                    return answer('STOP_AFFECTED', 'QA_RESULT_NOT_CONSUMED')
                if consumed.get('result_ref') != result_ref:
                    return answer('STOP_AFFECTED', 'QA_RESULT_CHANGED')
                # A configured accepting verdict is insufficient when no check
                # was performed. Empty lists still allow any finding for repair.
                if (allowed_verdicts and 'task_context_ref' in self.assignment
                        and result.get('verification', {}).get('status') != 'executed'):
                    return answer('STOP_AFFECTED', 'QA_CHECK_NOT_PERFORMED')
                if allowed_verdicts and result['verdict'] not in allowed_verdicts:
                    return answer('STOP_AFFECTED', 'QA_VERDICT_NOT_ACCEPTING')
            except (Refused, OSError):
                return answer('STOP_AFFECTED', 'QA_CONSUMPTION_NEEDS_RECONCILIATION')
        increment = decimal_value(action.get('additional_external_usd'))
        if not (increment == 0 and action.get('local_only') is True):
            budget = grant.get('budget', {})
            total = decimal_value(budget.get('estimated_cumulative_external_usd')) + increment
            limit = decimal_value(budget.get('strict_limit_usd'))
            if total >= limit:
                return answer('STOP_AFFECTED', 'CUMULATIVE_BUDGET')
            cost = {'expected_external_total_usd': str(total), 'actual_model_bill': 'Unknown'}
        else:
            cost = {'additional_external_usd': '0', 'local_only': True,
                    'cumulative_external_estimate': grant.get('budget', {}).get('estimated_cumulative_external_usd'),
                    'actual_model_bill': 'Unknown'}
        previous = action.get('previous_outcome')
        evidence = self.refs(action.get('new_evidence_refs', []))
        concrete_next = nonempty(action.get('next_step'))
        if previous == 'denied':
            count = action.get('refusal_retries_used', 0)
            if type(count) is not int or count < 0:
                return answer('STOP_AFFECTED', 'INVALID_RETRY_COUNT')
            if count >= 1:
                return answer('STOP_AFFECTED', 'DENIAL_RETRY_EXHAUSTED')
            if action.get('denial_kind') in ('access', 'policy', 'security'):
                return answer('STOP_AFFECTED', 'EXPLICIT_ACCESS_REFUSAL')
            if action.get('denial_kind') not in ('local_argument', 'transient_local_read'):
                return answer('STOP_AFFECTED', 'DENIAL_KIND_UNKNOWN')
            if action.get('previous_operation', operation) != operation:
                return answer('STOP_AFFECTED', 'DENIED_ROUTE_CHANGE')
            if not (action.get('nonexecution_confirmed') is True and evidence and concrete_next):
                return answer('STOP_AFFECTED', 'DENIED_NO_SUPPORTED_REPAIR')
        if previous == 'unknown_effect':
            if read_only:
                return answer('INSPECT_ONLY', 'READ_ONLY_RECONCILIATION_NO_REPLAY', cost=cost)
            return answer('RECONCILE_AFFECTED', 'EFFECT_UNCERTAIN_NO_REPLAY')
        if read_only:
            return answer('INSPECT_ONLY', 'READ_ONLY_RECONCILIATION_NO_EXECUTION', cost=cost)
        if previous == 'test_failed':
            current = self.refs(action.get('candidate_refs', []))
            old = self.refs(action.get('previous_candidate_refs', []), verify=False)
            # Renaming identical code or changing metadata is not a source repair.
            changed = bool(current) and Counter(current.values()) != Counter(old.values())
            if not (concrete_next and (changed or evidence)):
                return answer('REPLAN_AFFECTED', 'UNCHANGED_NO_PROGRESS_RETRY')
        decision_issue = None if settlement else self.decision_dependency_issue(operation)
        if decision_issue:
            return answer('STOP_AFFECTED', decision_issue)
        return answer('CONTINUE', 'AUTHORIZED_CLOSEOUT_AFTER_DEADLINE' if expired else 'WITHIN_CURRENT_GRANT', cost=cost,
                      limit='Only this proposed action; no dispatch, permission grant or global acceptance.')

    def review_obligation(self, review, active):
        owner = review.get('owner', 'Unknown')
        if (not isinstance(owner, dict) or not all(nonempty(owner.get(k)) for k in ('thread_id', 'host_id'))
                or not nonempty(review.get('key')) or not review.get('request_path') or not review.get('reply_path')):
            return {'action': 'REPAIR_END_REVIEW_BINDING', 'owner': owner}
        request, reply = self.path(review['request_path']), self.path(review['reply_path'])
        base = {'owner': active['author'], 'recipient': owner, 'key': review['key']}
        if not request.exists():
            return {**base, 'action': 'SUBMIT_END_REVIEW', 'phase': 'prepared'}
        req, _ = self.read_json(request)
        if req.get('key') != review['key']:
            return {**base, 'action': 'RECONCILE_END_REVIEW_REQUEST', 'phase': 'wrong_key'}
        submission = req.get('submission', {})
        if not isinstance(submission, dict):
            return {**base, 'action': 'RECONCILE_END_REVIEW_SEND', 'phase': 'unknown'}
        phase = 'prepared' if submission.get('status', 'prepared') == 'prepared' else 'unknown'
        shared_channel = review.get('channel') == req.get('channel') == 'shared_file'
        # A published agreed file is not proof of execution, nor an invitation
        # to submit it a second time while processing is being reconciled.
        if shared_channel:
            phase = 'unknown'
        receipt_ref = submission.get('native_receipt_ref')
        if receipt_ref:
            phase = 'unknown'
            try:
                self.refs([receipt_ref], required=True)
                receipt, _ = self.read_json(self.path(receipt_ref['path']))
                if (receipt.get('source') == 'send_message_to_thread' and receipt.get('key') == review['key']
                        and receipt.get('recipient') == owner):
                    tool_result = receipt.get('tool_result', {})
                    if not isinstance(tool_result, dict):
                        raise Refused('NATIVE_EVIDENCE_REQUIRED')
                    phase = 'rejected' if tool_result.get('isError') else 'unknown'
                    for block in tool_result.get('content', []):
                        if block.get('type') == 'text':
                            try:
                                returned = json.loads(block['text'])
                            except (ValueError, KeyError, TypeError):
                                continue
                            if (not tool_result.get('isError') and isinstance(owner, dict) and isinstance(returned, dict)
                                    and returned.get('threadId') == owner.get('thread_id')):
                                phase = 'accepted'
            except (Refused, OSError):
                phase = 'unknown'
        observation_ref = review.get('native_observation_ref')
        shared_evidence = None
        if observation_ref:
            try:
                self.refs([observation_ref], required=True)
                observation, _ = self.read_json(self.path(observation_ref['path']))
                if shared_channel and identity(observation) != owner:
                    raise Refused('NATIVE_EVIDENCE_REQUIRED')
                if (not shared_channel and observation.get('source') in ('read_thread', 'wait_threads')
                        and observation.get('key') == review['key'] and observation.get('recipient') == owner
                        and nonempty(observation.get('turn_id')) and observation.get('request_message_ids')):
                    if observation.get('status') == 'completed':
                        phase = 'completed'
                    elif observation.get('status') == 'inProgress':
                        phase = 'started'
                elif (shared_channel and observation.get('source') in ('read_thread', 'wait_threads')
                        and observation.get('key') == review['key'] and observation.get('recipient') == owner
                        and identity(observation) == owner and nonempty(observation.get('turn_id'))
                        and observation.get('status') in ('inProgress', 'completed')):
                    shared = observation.get('shared_file')
                    if isinstance(shared, dict):
                        items = shared.get('processed_item_ids')
                        request_ref = self.refs([shared.get('request_ref')], required=True)
                        _, current_request_ref = self.read_json(request)
                        if (req.get('recipient') == owner
                                and isinstance(items, list) and items and all(nonempty(x) for x in items)
                                and request_ref == {str(request): current_request_ref['sha256']}
                                and nonempty(req.get('closeoutPath')) and nonempty(req.get('closeoutSHA256'))):
                            self.refs([{'path': req['closeoutPath'], 'sha256': req['closeoutSHA256']}], required=True)
                            shared_evidence = shared
                            # A shared-file completion always needs the exact
                            # fixed final ABI below, even after a whole turn ends.
                            phase = 'started'
            except (Refused, OSError):
                phase = 'unknown'
        if phase == 'prepared':
            return {**base, 'action': 'SUBMIT_END_REVIEW', 'phase': phase}
        if phase not in ('accepted', 'started', 'completed'):
            return {**base, 'action': 'RECONCILE_END_REVIEW_SEND', 'phase': phase}
        if reply.exists():
            try:
                result, actual_ref = self.read_json(reply)
            except (Refused, OSError):
                return {**base, 'action': 'RECONCILE_END_REVIEW_REPLY' if phase == 'completed'
                        else 'WAIT_FOR_END_REVIEW', 'phase': phase, 'partial_result_path': str(reply)}
            if result.get('key') != review['key']:
                return {**base, 'action': 'RECONCILE_END_REVIEW_REPLY', 'phase': phase}
            # Completion evidence does not override explicit contradictory
            # artifact bindings. Apply this to both finality routes; absent
            # optional metadata on a legacy completed reply is not a mismatch.
            if 'reviewerThread' in result and result['reviewerThread'] != owner['thread_id']:
                return {**base, 'action': 'RECONCILE_END_REVIEW_REPLY', 'phase': phase,
                        'reason': 'EXPLICIT_REVIEWER_MISMATCH'}
            if ('sourceCloseoutSHA256' in result and nonempty(req.get('closeoutSHA256'))
                    and result['sourceCloseoutSHA256'] != req['closeoutSHA256']):
                return {**base, 'action': 'RECONCILE_END_REVIEW_REPLY', 'phase': phase,
                        'reason': 'EXPLICIT_CLOSEOUT_MISMATCH'}
            if shared_evidence is not None:
                try:
                    linked_reply = self.refs([shared_evidence.get('reply_ref')], required=True)
                    if linked_reply != {str(reply): actual_ref['sha256']}:
                        raise Refused('MISSING_EVIDENCE')
                except (Refused, OSError):
                    return {**base, 'action': 'RECONCILE_END_REVIEW_REPLY', 'phase': phase,
                            'reason': 'SHARED_FINAL_NATIVE_BINDING_MISSING_OR_CHANGED'}
                first = review.get('consumed_ref')
                if first is not None:
                    try:
                        previous_reply = self.refs([first], verify=False, required=True)
                    except (Refused, OSError):
                        previous_reply = None
                    if previous_reply != {str(reply): actual_ref['sha256']}:
                        return {**base, 'action': 'RECONCILE_END_REVIEW_REPLY', 'phase': phase,
                                'reason': 'CONSUMED_REVIEW_CHANGED'}
            # Active reviewers may finish this particular review before their
            # whole turn ends. Recognize the existing fixed formal reply ABI,
            # bound to both the original native role and this exact closeout.
            final_contract = (phase in ('started', 'completed')
                              and result.get('status') == 'REVIEW_COMPLETED'
                              and result.get('reviewerThread') == owner['thread_id']
                              and nonempty(req.get('closeoutSHA256'))
                              and result.get('sourceCloseoutSHA256') == req['closeoutSHA256'])
            if phase != 'completed' and not final_contract:
                return {**base, 'action': 'WAIT_FOR_END_REVIEW', 'phase': phase,
                        'partial_result_path': str(reply), 'final_obligation_pending': True}
            consumed = review.get('consumed_ref')
            if isinstance(consumed, dict):
                path = self.path(consumed.get('path', ''))
                if path == reply and consumed.get('sha256') == actual_ref['sha256']:
                    return None
            return {**base, 'action': 'CONSUME_END_REVIEW', 'phase': phase, 'reply_path': str(reply)}
        return {**base, 'action': 'LOCATE_END_REVIEW_RESULT' if phase == 'completed' else 'WAIT_FOR_END_REVIEW',
                'phase': phase}

    def reconcile(self):
        active = self.binding()
        obligations = []
        result_path = self.path(self.assignment.get('result_path', ''))
        if not result_path.exists():
            obligations.append({'action': 'WAIT_FOR_FIXED_RESULT', 'owner': active['qa'],
                                'result_path': str(result_path)})
        else:
            try:
                _, _, reference = self.validate_result(str(result_path))
                marker = self.marker(active)
                if not marker.exists():
                    obligations.append({'action': 'CONSUME_RESULT', 'owner': active['author'],
                                        'result_path': str(result_path), 'native_observation_required': True})
                else:
                    stored, _ = self.read_json(marker)
                    if (stored.get('decision') != 'CONSUMED' or stored.get('binding_id') != self.binding_id(active)
                            or stored.get('result_ref') != reference):
                        obligations.append({'action': 'RECONCILE_RESULT_CONFLICT', 'owner': active['author']})
            except Refused as exc:
                obligations.append({'action': 'RECONCILE_RESULT_FAILURE', 'decision': exc.decision,
                                    'owner': active['author']})
        review = pointer(self.state, self.args.review_pointer, optional=True)
        if isinstance(review, dict) and review.get('required'):
            obligation = self.review_obligation(review, active)
            if obligation:
                obligations.append(obligation)
        return {'decision': 'RECONCILED', 'read_only': True, 'active_assignment': active,
                'obligations': obligations, 'actual_utc': utc().isoformat()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--state', required=True)
    parser.add_argument('--read-root', action='append', default=[])
    parser.add_argument('--assignment-pointer', default='/current_assignment')
    parser.add_argument('--grant-pointer', default='/user_grant')
    parser.add_argument('--review-pointer', default='/end_review')
    commands = parser.add_subparsers(dest='command', required=True)
    assignment = commands.add_parser('check-assignment'); assignment.add_argument('--expected')
    consume = commands.add_parser('consume-result')
    consume.add_argument('--result', required=True); consume.add_argument('--witness')
    action = commands.add_parser('next-action'); action.add_argument('--request', required=True)
    transition = commands.add_parser('check-transition'); transition.add_argument('--request', required=True)
    commands.add_parser('reconcile')
    args = parser.parse_args(argv)
    context = None
    try:
        context = Context(args)
        if args.command == 'check-assignment':
            value = context.check_assignment(args.expected)
        elif args.command == 'consume-result':
            value = context.consume_result(args.result, args.witness)
        elif args.command == 'next-action':
            value = context.next_action(args.request)
        elif args.command == 'check-transition':
            value = context.check_transition(args.request)
        else:
            value = context.reconcile()
        code = 0 if value['decision'] in SUCCESS else 2
    except Refused as exc:
        value = {'decision': exc.decision, 'reason': exc.reason, 'global_stop': False}
        code = exc.code
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        # No exception text, input payload or secret paths are echoed.
        value = {'decision': 'LOCAL_INPUT_ERROR', 'reason': type(exc).__name__, 'global_stop': False}
        code = 3
    if context is not None and args.command == 'consume-result' and code:
        try:
            value['disposition_record'] = context.record_rejection(value)
        except (OSError, Refused, ValueError, TypeError):
            value['failure_retention'] = 'Unknown; original refusal preserved in this JSON response.'
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
