#!/usr/bin/env python3
"""Experimental one-entry local test adapter; not an OS sandbox or tool hook."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delivery_guard import Context, Refused, decimal_value

MAX_SECONDS = 10
SETTLE_RESERVE_SECONDS = 5
RETAIN_BYTES_PER_STREAM = 65_536


def now():
    return datetime.now(timezone.utc).isoformat()


def inspect_selected(context, expected_path):
    """Shared read-only validation of the selected local caller."""
    checked = context.check_assignment(expected_path)
    if checked['decision'] != 'CURRENT_ASSIGNMENT':
        return {**checked, 'child_started': False}, 2
    expected, _ = context.read_json(context.path(expected_path))
    selected = context.assignment.get('bounded_step')
    expected_step = expected.get('bounded_step')
    if (not isinstance(selected, dict) or not isinstance(expected_step, dict)
            or selected.get('adapter') != 'python-test-file'
            or any(selected.get(k) != expected_step.get(k)
                   for k in ('adapter', 'outputs', 'timeout_seconds'))):
        raise Refused('STEP_REFUSED', 'STEP_DECLARATION_MISMATCH')
    for field in ('entry_ref', 'action_ref'):
        if (context.refs([selected.get(field)], verify=False, required=True)
                != context.refs([expected_step.get(field)], verify=False, required=True)):
            raise Refused('STEP_REFUSED', 'STEP_DECLARATION_MISMATCH')
    active = context.binding()
    current_refs = {**active['candidate_refs'], **active['input_refs']}
    for field in ('entry_ref', 'action_ref'):
        chosen = context.refs([selected.get(field)], required=True)
        if any(current_refs.get(path) != digest for path, digest in chosen.items()):
            raise Refused('STEP_REFUSED', 'STEP_REFERENCE_NOT_CURRENT')
    entry = context.path(selected['entry_ref']['path'])
    action_path = context.path(selected['action_ref']['path'])
    context.task_surface(entry)
    context.task_surface(action_path)
    action, _ = context.read_json(action_path)
    if (entry.suffix != '.py' or action.get('operation') != 'local_test'
            or action.get('local_only') is not True
            or decimal_value(action.get('additional_external_usd')) != 0):
        raise Refused('STEP_REFUSED', 'LOCAL_TEST_ADAPTER_ONLY')
    allowed = context.next_action(str(action_path))
    if allowed['decision'] != 'CONTINUE':
        return {**allowed, 'child_started': False}, 2
    seconds = selected.get('timeout_seconds')
    if (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
            or not math.isfinite(seconds) or not 0 < seconds <= MAX_SECONDS):
        raise Refused('STEP_REFUSED', 'STEP_DURATION_INVALID')
    grant = context.state
    from delivery_guard import pointer
    grant = pointer(grant, context.args.grant_pointer)
    deadline = datetime.fromisoformat(grant['deadline_utc'].replace('Z', '+00:00'))
    if (deadline - datetime.now(timezone.utc)).total_seconds() < seconds + SETTLE_RESERVE_SECONDS:
        raise Refused('STEP_REFUSED', 'INSUFFICIENT_EXIT_TIME')
    outputs = selected.get('outputs')
    if not isinstance(outputs, dict) or set(outputs) != {'stdout', 'stderr', 'receipt'}:
        raise Refused('STEP_REFUSED', 'OUTPUT_DECLARATION_INVALID')
    paths = {name: context.path(raw, write=True) for name, raw in outputs.items()}
    if len(set(paths.values())) != 3 or any(path.exists() for path in paths.values()):
        raise Refused('STEP_REFUSED', 'OUTPUT_ALREADY_EXISTS_OR_ALIASED')
    # Recheck exact fixed inputs after all metadata validation, just before launch.
    context.binding()
    for field in ('entry_ref', 'action_ref'):
        context.refs([selected[field]], required=True)
    context.check_assignment(expected_path)
    context.task_surface(entry)
    for path in paths.values():
        context.task_surface(path, write=True)
    return {'decision': 'LOCAL_STEP_CHECKED', 'child_started': False,
            'entry': str(entry), 'paths': {k: str(v) for k, v in paths.items()},
            'seconds': seconds, 'binding': active, 'selected': selected,
            'argv': [sys.executable, '-I', '-B', str(entry)],
            'global_stop': False, 'meaning': 'Read-only check, not execution or reserved permission.'}, 0


def run_selected(context, expected_path, before_start=None):
    plan, code = inspect_selected(context, expected_path)
    if code:
        return plan, code
    entry = Path(plan['entry'])
    paths = {k: Path(v) for k, v in plan['paths'].items()}
    seconds, active, selected = plan['seconds'], plan['binding'], plan['selected']
    handles = {}
    try:
        for name in ('stdout', 'stderr'):
            context.ensure_directory(paths[name].parent)
            fd = os.open(paths[name], os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
            handles[name] = os.fdopen(fd, 'wb')
        argv = [sys.executable, '-I', '-B', str(entry)]
        if before_start is not None:
            before_start()
        started = now()
        child = None
        out, err = b'', b''
        primary = None
        try:
            child = subprocess.Popen(argv, cwd=context.root, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            context.bound_child_started = True
            try:
                out, err = child.communicate(timeout=seconds)
            except subprocess.TimeoutExpired:
                primary = 'CHILD_TIMEOUT'
                child.terminate()
                try:
                    out, err = child.communicate(timeout=1)
                except subprocess.TimeoutExpired:
                    child.kill()
                    try:
                        out, err = child.communicate(timeout=1)
                    except subprocess.TimeoutExpired as partial:
                        out, err = partial.output or b'', partial.stderr or b''
                        primary = 'CHILD_OR_INHERITED_STREAM_UNSETTLED'
            try:
                child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                primary = 'DIRECT_CHILD_SETTLEMENT_UNKNOWN'
        except OSError:
            primary = primary or ('CHILD_START_FAILED' if child is None else 'CHILD_SETTLEMENT_ERROR')
        finally:
            if child is not None:
                if child.returncode is None:
                    try:
                        child.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        primary = primary or 'DIRECT_CHILD_SETTLEMENT_UNKNOWN'
                for stream in (child.stdout, child.stderr):
                    if stream is not None:
                        stream.close()
            context.bound_child_observation = {
                'pid': None if child is None else child.pid,
                'returncode': None if child is None else child.returncode,
                'samePopenWaitReaped': child is not None and child.returncode is not None,
                'stdoutClosed': child is not None and child.stdout.closed,
                'stderrClosed': child is not None and child.stderr.closed,
            }
        if any(len(raw) > RETAIN_BYTES_PER_STREAM for raw in (out, err)) and primary is None:
            primary = 'RETAINED_OUTPUT_TRUNCATED'
        closed = child is not None and child.returncode is not None
        if primary is None and closed and child.returncode != 0:
            primary = 'CHILD_TEST_FAILED'
        context.bound_primary_failure = primary
        for name, raw in [('stdout', out), ('stderr', err)]:
            handles[name].write(raw[:RETAIN_BYTES_PER_STREAM])
            handles[name].flush()
            os.fsync(handles[name].fileno())
        receipt = {
            'schema': 'delivery.bound-step.local-receipt.v1',
            'startedUtc': started, 'finishedUtc': now(),
            'binding': active, 'adapter': 'python-test-file', 'entry_ref': selected['entry_ref'],
            'argv': argv, 'primary': primary,
            'child': {'pid': None if child is None else child.pid,
                      'returncode': None if child is None else child.returncode,
                      'samePopenWaitReaped': closed,
                      'stdoutClosed': child is not None and child.stdout.closed,
                      'stderrClosed': child is not None and child.stderr.closed},
            'retained': {name: {'path': str(paths[name]), 'bytes': min(len(raw), RETAIN_BYTES_PER_STREAM),
                                'sha256': hashlib.sha256(raw[:RETAIN_BYTES_PER_STREAM]).hexdigest(),
                                'truncated': len(raw) > RETAIN_BYTES_PER_STREAM}
                         for name, raw in [('stdout', out), ('stderr', err)]},
            'limits': 'Only selected caller/known direct child; no native role authentication, '
                      'OS sandbox, capture-memory cap, grandchildren/global closure or unadopted bypass protection.',
        }
        if not context.atomic_first(paths['receipt'], receipt):
            return {'decision': 'STEP_UNCERTAIN', 'reason': 'RECEIPT_ALREADY_EXISTS',
                    'child_started': child is not None,
                    'known_child': context.bound_child_observation,
                    'primary': context.bound_primary_failure,
                    'global_stop': False}, 4
        okay = primary is None and closed and child.returncode == 0
        return {'decision': 'RUN_COMPLETED' if okay else 'RUN_FAILED', 'reason': primary,
                'receipt_path': str(paths['receipt']), 'child_started': child is not None,
                'global_stop': False}, 0 if okay else 4
    finally:
        for handle in handles.values():
            handle.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--state', required=True)
    parser.add_argument('--expected', required=True)
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--read-root', action='append', default=[])
    parser.add_argument('--assignment-pointer', default='/current_assignment')
    parser.add_argument('--grant-pointer', default='/user_grant')
    parser.add_argument('--review-pointer', default='/end_review')
    args = parser.parse_args()
    context = None
    try:
        context = Context(args)
        context.bound_child_started = False
        context.bound_child_observation = None
        context.bound_primary_failure = None
        result, code = (inspect_selected(context, args.expected) if args.check_only
                        else run_selected(context, args.expected))
    except Refused as exc:
        result, code = {'decision': exc.decision, 'reason': exc.reason,
                        'child_started': context is not None and context.bound_child_started,
                        'known_child': None if context is None else context.bound_child_observation,
                        'primary': None if context is None else context.bound_primary_failure,
                        'global_stop': False}, exc.code
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        result, code = {'decision': 'LOCAL_INPUT_ERROR',
                        'child_started': context is not None and context.bound_child_started,
                        'known_child': None if context is None else context.bound_child_observation,
                        'primary': None if context is None else context.bound_primary_failure,
                        'global_stop': False}, 3
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
