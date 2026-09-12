#!/usr/bin/env bash
# Seed-aware grader for SPEC1: Specification to Implementation
#
# Reads domain and expected values from expected.json.
# Runs the agent's implemented code against acceptance criteria that
# cannot be inferred from the workspace skeleton alone.
#
# Args: $1=WORKSPACE $2=REPORTS $3=SUBMISSION $4=TASK_DIR [$5=EXPECTED_JSON]
set -o pipefail
WORKSPACE="$1"
REPORTS="$2"
SUBMISSION="$3"
TASK_DIR="$4"
EXPECTED="${5:-$REPORTS/expected.json}"

mkdir -p "$REPORTS"

CHECKS=0; PASSED=0; FAILURES=""
check() {
  CHECKS=$((CHECKS + 1))
  if eval "$1" 2>/dev/null; then
    PASSED=$((PASSED + 1))
  else
    FAILURES="${FAILURES:+${FAILURES},}$2"
  fi
}

cd "$WORKSPACE"

# ── Read domain from expected.json ──────────────────────────────────────────
DOMAIN=$(python3 -c "
import json
e = json.load(open('$EXPECTED'))
print(e.get('domain', 'unknown'))
" 2>/dev/null || echo "unknown")

# ── 1. Tests pass ────────────────────────────────────────────────────────────
check "python3 -m pytest tests/ -q --tb=no 2>/dev/null | tail -1 | grep -E '^[0-9]+ passed'" \
  "tests_fail"

# ── 2. No NotImplementedError (all TODOs implemented) ────────────────────────
check "python3 -c \"
import subprocess, sys
result = subprocess.run(
    ['python3', '-m', 'pytest', 'tests/', '-q', '--tb=short'],
    capture_output=True, text=True, cwd='$WORKSPACE'
)
assert 'NotImplementedError' not in result.stdout + result.stderr, 'TODOs not implemented'
assert 'not implemented' not in (result.stdout + result.stderr).lower() or result.returncode == 0
print('IMPLEMENTED_OK')
\"" "todos_not_implemented"

# ── 3-10. Domain-specific acceptance criteria ─────────────────────────────────

if [ "$DOMAIN" = "task_management" ]; then

  FORBIDDEN=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(json.dumps(e['forbidden_transitions']))" 2>/dev/null || echo "[]")
  MAX_TITLE=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('max_title_len',100))" 2>/dev/null || echo "100")
  DATE_FMT=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('date_format','%Y-%m-%d'))" 2>/dev/null || echo "%Y-%m-%d")
  DATE_EX=$(python3 -c "
from datetime import datetime
fmt = '$DATE_FMT'
d = datetime(2024, 6, 15)
print(d.strftime(fmt))
" 2>/dev/null || echo "2024-06-15")

  # Check: TASK_NOT_FOUND on missing id
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import TaskStore
from app import AppError, get_task
store = TaskStore()
try:
    get_task(store, 9999)
    assert False, 'Should have raised'
except AppError as e:
    assert e.code == 'TASK_NOT_FOUND', f'Wrong code: {e.code}'
print('NOT_FOUND_OK')
\"" "task_not_found_wrong_code"

  # Check: INVALID_PRIORITY enforced with exact code
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import TaskStore
from app import AppError, create_task
store = TaskStore()
try:
    create_task(store, 'Test', 'URGENT')
    assert False, 'Should have raised'
except AppError as e:
    assert e.code == 'INVALID_PRIORITY', f'Wrong code: {e.code}'
print('PRIORITY_CODE_OK')
\"" "invalid_priority_wrong_code"

  # Check: title too long raises TITLE_TOO_LONG
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import TaskStore
from app import AppError, create_task
store = TaskStore()
long_title = 'x' * ($MAX_TITLE + 1)
try:
    create_task(store, long_title, 'HIGH')
    assert False, 'Should have raised'
except AppError as e:
    assert e.code == 'TITLE_TOO_LONG', f'Wrong code: {e.code}'
print('TITLE_TOO_LONG_OK')
\"" "title_too_long_wrong_code"

  # Check: forbidden transitions raise INVALID_TRANSITION
  check "python3 -c \"
import sys, json; sys.path.insert(0, '$WORKSPACE')
from models import TaskStore
from app import AppError, create_task, update_task_status
forbidden = json.loads('$FORBIDDEN')
if not forbidden:
    print('NO_FORBIDDEN_SKIP')
    exit(0)
from_s, to_s = forbidden[0]
# Build a task in from_s status by navigating there
store = TaskStore()
create_task(store, 'T', 'HIGH')
# Navigate to from_s
transitions = {'TODO': [], 'IN_PROGRESS': ['IN_PROGRESS'], 'DONE': ['IN_PROGRESS', 'DONE'], 'CANCELLED': ['CANCELLED']}
for st in transitions.get(from_s, []):
    try: update_task_status(store, 1, st)
    except: pass
try:
    update_task_status(store, 1, to_s)
    assert False, f'Should forbid {from_s} -> {to_s}'
except AppError as e:
    assert e.code == 'INVALID_TRANSITION', f'Wrong code: {e.code}'
print('FORBIDDEN_TRANSITION_OK')
\"" "forbidden_transition_wrong_code"

  # Check: list_tasks sort order (priority then due_date)
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import TaskStore
from app import create_task, list_tasks
store = TaskStore()
date_ex = '$DATE_EX'
create_task(store, 'Low task', 'LOW', date_ex)
create_task(store, 'High task', 'HIGH', date_ex)
create_task(store, 'Medium task', 'MEDIUM', date_ex)
tasks = list_tasks(store)
priorities = [t['priority'] for t in tasks]
# HIGH should come before MEDIUM before LOW in the sorted list
assert priorities.index('HIGH') < priorities.index('MEDIUM'), f'HIGH should be before MEDIUM: {priorities}'
assert priorities.index('MEDIUM') < priorities.index('LOW'), f'MEDIUM should be before LOW: {priorities}'
print('SORT_ORDER_OK')
\"" "list_tasks_sort_wrong"

  # Check: INVALID_DATE_FORMAT with bad date string
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import TaskStore
from app import AppError, create_task
store = TaskStore()
# Use a date format that is plausibly wrong for this seed
wrong_dates = ['not-a-date', '99/99/9999', '2024-13-01']
raised = False
for d in wrong_dates:
    try:
        create_task(store, 'T', 'HIGH', d)
    except AppError as e:
        if e.code == 'INVALID_DATE_FORMAT':
            raised = True
            break
assert raised, 'INVALID_DATE_FORMAT not raised for bad date'
print('DATE_FORMAT_OK')
\"" "invalid_date_format_not_raised"

  # Check: delete_task removes the task
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import TaskStore
from app import AppError, create_task, delete_task, get_task
store = TaskStore()
create_task(store, 'Delete me', 'LOW')
deleted = delete_task(store, 1)
assert deleted['title'] == 'Delete me'
try:
    get_task(store, 1)
    assert False, 'Task should be gone'
except AppError as e:
    assert e.code == 'TASK_NOT_FOUND'
print('DELETE_OK')
\"" "delete_task_fail"

  # Check: whitespace-only title raises INVALID_TITLE
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import TaskStore
from app import AppError, create_task
store = TaskStore()
try:
    create_task(store, '   ', 'HIGH')
    assert False, 'Whitespace-only title should raise'
except AppError as e:
    assert e.code == 'INVALID_TITLE', f'Wrong code: {e.code}'
print('WHITESPACE_TITLE_OK')
\"" "whitespace_title_not_rejected"

elif [ "$DOMAIN" = "inventory_system" ]; then

  REORDER_THRESH=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('reorder_threshold',10))" 2>/dev/null || echo "10")
  MAX_QTY=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('max_quantity',1000))" 2>/dev/null || echo "1000")
  ERR_INSUFF=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('error_insufficient','INSUFFICIENT_STOCK'))" 2>/dev/null || echo "INSUFFICIENT_STOCK")
  LOG_ADD=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('log_add_action','RESTOCK'))" 2>/dev/null || echo "RESTOCK")
  LOG_ADJUST=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('log_adjust_action','ADJUST'))" 2>/dev/null || echo "ADJUST")

  # Check: ITEM_NOT_FOUND on restock of nonexistent item
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import InventoryStore
from app import AppError, restock
store = InventoryStore()
try:
    restock(store, 9999, 10)
    assert False
except AppError as e:
    assert e.code == 'ITEM_NOT_FOUND', f'Wrong code: {e.code}'
print('ITEM_NOT_FOUND_OK')
\"" "item_not_found_wrong_code"

  # Check: INSUFFICIENT_STOCK exact code
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import InventoryStore
from app import AppError, add_item, remove_stock
store = InventoryStore()
add_item(store, 'Widget', 'cat', 5)
try:
    remove_stock(store, 1, 100)
    assert False
except AppError as e:
    assert e.code == '$ERR_INSUFF', f'Wrong code: {e.code}'
print('INSUFFICIENT_OK')
\"" "insufficient_stock_wrong_code"

  # Check: EXCEEDS_MAX_QUANTITY on add_item
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import InventoryStore
from app import AppError, add_item
store = InventoryStore()
try:
    add_item(store, 'X', 'cat', $MAX_QTY + 1)
    assert False
except AppError as e:
    assert e.code == 'EXCEEDS_MAX_QUANTITY', f'Wrong code: {e.code}'
print('EXCEEDS_MAX_OK')
\"" "exceeds_max_wrong_code"

  # Check: reorder list includes items at exactly threshold
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import InventoryStore
from app import add_item, get_reorder_list
store = InventoryStore()
add_item(store, 'AtThreshold', 'cat', $REORDER_THRESH)
add_item(store, 'AboveThreshold', 'cat', $REORDER_THRESH + 1)
reorder = get_reorder_list(store)
names = [r['name'] for r in reorder]
assert 'AtThreshold' in names, f'Item at threshold should be in reorder list: {names}'
assert 'AboveThreshold' not in names, f'Item above threshold should not be in list: {names}'
print('REORDER_INCLUSIVE_OK')
\"" "reorder_threshold_inclusive_fail"

  # Check: reorder sorted by quantity asc then id asc
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import InventoryStore
from app import add_item, get_reorder_list
store = InventoryStore()
add_item(store, 'Mid', 'cat', max(1, $REORDER_THRESH - 1))
add_item(store, 'Low', 'cat', 0)
add_item(store, 'Also', 'cat', max(1, $REORDER_THRESH - 1))
reorder = get_reorder_list(store)
qtys = [r['quantity'] for r in reorder]
assert qtys == sorted(qtys), f'Reorder list not sorted by quantity: {qtys}'
print('REORDER_SORT_OK')
\"" "reorder_sort_wrong"

  # Check: batch_update atomicity (no partial apply)
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import InventoryStore
from app import AppError, add_item, batch_update, get_audit_log
store = InventoryStore()
add_item(store, 'A', 'cat', 5)
add_item(store, 'B', 'cat', 5)
log_before = len(get_audit_log(store))
try:
    batch_update(store, [(1, -3), (2, -100)])  # second will fail
except AppError:
    pass
log_after = len(get_audit_log(store))
assert log_after == log_before, f'Partial apply detected: log grew from {log_before} to {log_after}'
print('BATCH_ATOMIC_OK')
\"" "batch_update_not_atomic"

  # Check: audit log action for batch_update uses ADJUST not ADD/REMOVE
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import InventoryStore
from app import add_item, batch_update, get_audit_log
store = InventoryStore()
add_item(store, 'X', 'cat', 100)
batch_update(store, [(1, 10)])
log = get_audit_log(store, item_id=1)
actions = [e['action'] for e in log]
assert '$LOG_ADJUST' in actions, f'Expected $LOG_ADJUST in log actions: {actions}'
print('BATCH_LOG_ACTION_OK')
\"" "batch_log_action_wrong"

  # Check: INVALID_QUANTITY raised for zero quantity on restock
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import InventoryStore
from app import AppError, add_item, restock
store = InventoryStore()
add_item(store, 'Item', 'cat', 10)
try:
    restock(store, 1, 0)
    assert False, 'Zero quantity should raise'
except AppError as e:
    assert e.code == 'INVALID_QUANTITY', f'Wrong code: {e.code}'
print('ZERO_QTY_OK')
\"" "zero_qty_not_rejected"

elif [ "$DOMAIN" = "booking_system" ]; then

  MAX_ADV=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('max_advance_days',30))" 2>/dev/null || echo "30")
  CANCEL_HRS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('cancellation_hours',24))" 2>/dev/null || echo "24")
  WAITLIST_MAX=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('waitlist_max',5))" 2>/dev/null || echo "5")
  ERR_CONFLICT=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('error_conflict','SLOT_CONFLICT'))" 2>/dev/null || echo "SLOT_CONFLICT")
  ERR_CANCEL=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('error_too_late_cancel','CANCELLATION_TOO_LATE'))" 2>/dev/null || echo "CANCELLATION_TOO_LATE")
  ERR_ADV=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('error_too_far_advance','TOO_FAR_IN_ADVANCE'))" 2>/dev/null || echo "TOO_FAR_IN_ADVANCE")
  ERR_WAITLIST=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('error_waitlist_full','WAITLIST_FULL'))" 2>/dev/null || echo "WAITLIST_FULL")

  # Check: SLOT_NOT_FOUND on missing slot
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import BookingStore
from app import AppError, book_slot
store = BookingStore()
try:
    book_slot(store, 9999, 'alice', '2024-06-01T10:00:00')
    assert False
except AppError as e:
    assert e.code == 'SLOT_NOT_FOUND', f'Wrong code: {e.code}'
print('SLOT_NOT_FOUND_OK')
\"" "slot_not_found_wrong_code"

  # Check: TOO_FAR_IN_ADVANCE enforced with exact code
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import date, timedelta
from models import BookingStore
from app import AppError, add_slot, book_slot
store = BookingStore()
far_date = (date(2024, 6, 1) + timedelta(days=$MAX_ADV + 1)).strftime('%Y-%m-%d')
add_slot(store, far_date, 9, 3, 'Room')
try:
    book_slot(store, 1, 'alice', '2024-06-01T10:00:00')
    assert False, 'Should raise TOO_FAR_IN_ADVANCE'
except AppError as e:
    assert e.code == '$ERR_ADV', f'Wrong code: {e.code}'
print('ADVANCE_DAYS_OK')
\"" "too_far_advance_wrong_code"

  # Check: exactly max_advance_days is allowed (boundary)
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from datetime import date, timedelta
from models import BookingStore
from app import AppError, add_slot, book_slot
store = BookingStore()
boundary_date = (date(2024, 6, 1) + timedelta(days=$MAX_ADV)).strftime('%Y-%m-%d')
add_slot(store, boundary_date, 9, 3, 'Room')
b = book_slot(store, 1, 'alice', '2024-06-01T10:00:00')
assert b['status'] == 'CONFIRMED'
print('BOUNDARY_DATE_OK')
\"" "boundary_date_rejected"

  # Check: duplicate booking raises correct conflict error
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import BookingStore
from app import AppError, add_slot, book_slot
store = BookingStore()
add_slot(store, '2024-06-10', 9, 5, 'Room')
book_slot(store, 1, 'alice', '2024-06-01T10:00:00')
try:
    book_slot(store, 1, 'alice', '2024-06-01T10:00:00')
    assert False
except AppError as e:
    assert e.code == '$ERR_CONFLICT', f'Wrong code: {e.code}'
print('CONFLICT_CODE_OK')
\"" "conflict_wrong_code"

  # Check: waitlist promotion is FIFO on cancellation
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import BookingStore
from app import add_slot, book_slot, cancel_booking, get_bookings
store = BookingStore()
add_slot(store, '2024-06-10', 9, 1, 'Room')
book_slot(store, 1, 'alice', '2024-06-01T09:00:00')   # confirmed
book_slot(store, 1, 'bob',   '2024-06-01T09:01:00')   # waitlisted first
book_slot(store, 1, 'carol', '2024-06-01T09:02:00')   # waitlisted second
cancel_booking(store, 1, '2024-06-01T10:00:00')       # alice cancels
confirmed = get_bookings(store, slot_id=1, status='CONFIRMED')
assert len(confirmed) == 1, f'Expected 1 confirmed, got {len(confirmed)}'
assert confirmed[0]['user_id'] == 'bob', f'FIFO failed: expected bob, got {confirmed[0][\"user_id\"]}'
print('FIFO_PROMOTION_OK')
\"" "waitlist_fifo_fail"

  # Check: cancellation too late raises correct code
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import BookingStore
from app import AppError, add_slot, book_slot, cancel_booking
store = BookingStore()
# Slot at 2024-06-10 09:00 UTC; cancel within $CANCEL_HRS hours of start
add_slot(store, '2024-06-10', 9, 3, 'Room')
book_slot(store, 1, 'alice', '2024-06-01T10:00:00')
# now = just before the window closes
from datetime import datetime, timedelta
slot_start = datetime(2024, 6, 10, 9, 0, 0)
too_late_now = (slot_start - timedelta(hours=$CANCEL_HRS - 1)).strftime('%Y-%m-%dT%H:%M:%S')
try:
    cancel_booking(store, 1, too_late_now)
    assert False, 'Should raise $ERR_CANCEL'
except AppError as e:
    assert e.code == '$ERR_CANCEL', f'Wrong code: {e.code}'
print('CANCEL_TOO_LATE_OK')
\"" "cancel_too_late_wrong_code"

  # Check: get_slot_availability returns correct counts
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import BookingStore
from app import add_slot, book_slot, get_slot_availability
store = BookingStore()
add_slot(store, '2024-06-10', 9, 2, 'Room')
book_slot(store, 1, 'alice', '2024-06-01T10:00:00')
book_slot(store, 1, 'bob',   '2024-06-01T10:00:00')  # fills capacity
book_slot(store, 1, 'carol', '2024-06-01T10:00:00')  # waitlisted
avail = get_slot_availability(store, 1)
assert avail['confirmed_count'] == 2, f'confirmed_count: {avail[\"confirmed_count\"]}'
assert avail['waitlisted_count'] == 1, f'waitlisted_count: {avail[\"waitlisted_count\"]}'
assert avail['available_seats'] == 0, f'available_seats: {avail[\"available_seats\"]}'
print('AVAILABILITY_OK')
\"" "slot_availability_wrong"

  # Check: WAITLIST_FULL raised when waitlist at capacity
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import BookingStore
from app import AppError, add_slot, book_slot
store = BookingStore()
add_slot(store, '2024-06-10', 9, 1, 'Room')
book_slot(store, 1, 'user0', '2024-06-01T10:00:00')  # confirmed
for i in range(1, $WAITLIST_MAX + 1):
    try:
        book_slot(store, 1, f'user{i}', '2024-06-01T10:00:00')
    except Exception:
        break
try:
    book_slot(store, 1, 'overflow', '2024-06-01T10:00:00')
    assert False, 'Should raise $ERR_WAITLIST'
except AppError as e:
    assert e.code == '$ERR_WAITLIST', f'Wrong code: {e.code}'
print('WAITLIST_FULL_OK')
\"" "waitlist_full_wrong_code"

elif [ "$DOMAIN" = "grading_calculator" ]; then

  A_CUT=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('a_cutoff',90))" 2>/dev/null || echo "90")
  B_CUT=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('b_cutoff',80))" 2>/dev/null || echo "80")
  C_CUT=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('c_cutoff',70))" 2>/dev/null || echo "70")
  D_CUT=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('d_cutoff',60))" 2>/dev/null || echo "60")
  DROP=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('drop_lowest_count',0))" 2>/dev/null || echo "0")
  CURVE=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('curve_points',0))" 2>/dev/null || echo "0")
  DP=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('decimal_places',2))" 2>/dev/null || echo "2")

  # Check: letter grade A boundary (score >= a_cutoff)
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import GradeEntry
from app import calculate_grade
entry = GradeEntry('test', $A_CUT, 1.0)
report = calculate_grade([entry], drop_lowest=0, curve=0)
assert report['letter_grade'] == 'A', f'Expected A for score=$A_CUT: {report[\"letter_grade\"]}'
print('GRADE_A_BOUNDARY_OK')
\"" "grade_a_boundary_wrong"

  # Check: letter grade B boundary
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import GradeEntry
from app import calculate_grade
entry = GradeEntry('test', $B_CUT, 1.0)
report = calculate_grade([entry], drop_lowest=0, curve=0)
assert report['letter_grade'] == 'B', f'Expected B for score=$B_CUT: {report[\"letter_grade\"]}'
print('GRADE_B_BOUNDARY_OK')
\"" "grade_b_boundary_wrong"

  # Check: F grade for score below d_cutoff
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import GradeEntry
from app import calculate_grade
entry = GradeEntry('test', $D_CUT - 1, 1.0)
report = calculate_grade([entry], drop_lowest=0, curve=0)
assert report['letter_grade'] == 'F', f'Expected F for score={$D_CUT - 1}: {report[\"letter_grade\"]}'
print('GRADE_F_OK')
\"" "grade_f_wrong"

  # Check: curve cap at 100
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import GradeEntry
from app import calculate_grade
entry = GradeEntry('test', 99.0, 1.0)
report = calculate_grade([entry], drop_lowest=0, curve=10)
assert report['curved_average'] == 100.0, f'Curve not capped: {report[\"curved_average\"]}'
print('CURVE_CAP_OK')
\"" "curve_cap_wrong"

  # Check: WEIGHTS_NOT_ONE validation
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import GradeEntry
from app import AppError, calculate_grade
entries = [GradeEntry('a', 80, 0.3), GradeEntry('b', 90, 0.3)]
try:
    calculate_grade(entries, drop_lowest=0, curve=0)
    assert False
except AppError as e:
    assert e.code == 'WEIGHTS_NOT_ONE', f'Wrong code: {e.code}'
print('WEIGHTS_NOT_ONE_OK')
\"" "weights_not_one_wrong_code"

  # Check: drop_lowest renormalizes weights correctly
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import GradeEntry
from app import calculate_grade
# 3 entries, drop 1 lowest; remaining weights must renormalize
entries = [GradeEntry('a', 100, 0.4), GradeEntry('b', 100, 0.4), GradeEntry('c', 0, 0.2)]
report = calculate_grade(entries, drop_lowest=1, curve=0)
# After dropping c (score=0), weights 0.4 and 0.4 renorm to 0.5 each -> avg = 100
assert report['weighted_average'] == 100.0, f'Renorm failed: {report[\"weighted_average\"]}'
print('DROP_RENORM_OK')
\"" "drop_lowest_renorm_fail"

  # Check: class_statistics grade_distribution includes all grades even if 0
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import GradeEntry
from app import calculate_grade, class_statistics
r = calculate_grade([GradeEntry('x', 95, 1.0)], drop_lowest=0, curve=0)
stats = class_statistics([r])
dist = stats['grade_distribution']
for g in ('A', 'B', 'C', 'D', 'F'):
    assert g in dist, f'Missing grade {g} in distribution: {dist}'
print('GRADE_DIST_COMPLETE_OK')
\"" "grade_dist_incomplete"

  # Check: decimal_places rounding applied correctly
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import GradeEntry
from app import calculate_grade
entry = GradeEntry('test', 1/3 * 100, 1.0)  # 33.333...
report = calculate_grade([entry], drop_lowest=0, curve=0)
wa = report['weighted_average']
# Check it's rounded to $DP decimal places
assert round(wa, $DP) == wa, f'weighted_average not rounded to $DP dp: {wa}'
print('DECIMAL_ROUNDING_OK')
\"" "decimal_rounding_wrong"

else
  # Domain: expense_tracker (seed 4 % 5 = 4)

  BUDGET=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('budget_limit',1000))" 2>/dev/null || echo "1000")
  BASE_CUR=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('base_currency','USD'))" 2>/dev/null || echo "USD")
  PERIOD=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e.get('report_period','monthly'))" 2>/dev/null || echo "monthly")
  CURRENCIES_JSON=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(json.dumps(e.get('currencies',['USD'])))" 2>/dev/null || echo '["USD"]')
  FIRST_CUR=$(python3 -c "import json; print(json.loads('$CURRENCIES_JSON')[0])" 2>/dev/null || echo "USD")
  REPORT_FN="${PERIOD}_report"

  # Check: INVALID_AMOUNT for zero
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import ExpenseStore
from app import AppError, add_expense
store = ExpenseStore()
try:
    add_expense(store, 'X', 0, '$FIRST_CUR', 'misc', '2024-06-01')
    assert False
except AppError as e:
    assert e.code == 'INVALID_AMOUNT', f'Wrong code: {e.code}'
print('ZERO_AMOUNT_OK')
\"" "zero_amount_not_rejected"

  # Check: UNKNOWN_CURRENCY for bad currency
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import ExpenseStore
from app import AppError, add_expense
store = ExpenseStore()
try:
    add_expense(store, 'X', 10, 'XYZ', 'misc', '2024-06-01')
    assert False
except AppError as e:
    assert e.code == 'UNKNOWN_CURRENCY', f'Wrong code: {e.code}'
print('UNKNOWN_CURRENCY_OK')
\"" "unknown_currency_wrong_code"

  # Check: INVALID_DATE on bad date
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import ExpenseStore
from app import AppError, add_expense
store = ExpenseStore()
try:
    add_expense(store, 'X', 10, '$FIRST_CUR', 'misc', 'not-a-date')
    assert False
except AppError as e:
    assert e.code == 'INVALID_DATE', f'Wrong code: {e.code}'
print('INVALID_DATE_OK')
\"" "invalid_date_wrong_code"

  # Check: get_total empty returns 0.0
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import ExpenseStore
from app import get_total
store = ExpenseStore()
assert get_total(store) == 0.0, 'Empty total should be 0.0'
print('EMPTY_TOTAL_OK')
\"" "empty_total_not_zero"

  # Check: get_total base currency addition is correct
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import ExpenseStore
from app import add_expense, get_total
store = ExpenseStore()
add_expense(store, 'A', 100.0, '$BASE_CUR', 'food', '2024-06-01')
add_expense(store, 'B', 50.0, '$BASE_CUR', 'travel', '2024-06-01')
total = get_total(store)
assert abs(total - 150.0) < 0.01, f'Expected 150.0, got {total}'
print('TOTAL_CORRECT_OK')
\"" "total_calculation_wrong"

  # Check: category filter on get_total
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import ExpenseStore
from app import add_expense, get_total
store = ExpenseStore()
add_expense(store, 'A', 100.0, '$BASE_CUR', 'food', '2024-06-01')
add_expense(store, 'B', 50.0, '$BASE_CUR', 'travel', '2024-06-01')
food_total = get_total(store, category='food')
assert abs(food_total - 100.0) < 0.01, f'Category filter wrong: {food_total}'
print('CATEGORY_FILTER_OK')
\"" "category_filter_wrong"

  # Check: report has budget_limit and over_budget fields
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import ExpenseStore
from app import add_expense, ${REPORT_FN}
store = ExpenseStore()
add_expense(store, 'X', 10.0, '$BASE_CUR', 'misc', '2024-06-01')
report = ${REPORT_FN}(store, '2024-06-01')
assert 'budget_limit' in report, f'Missing budget_limit: {report}'
assert 'over_budget' in report, f'Missing over_budget: {report}'
assert report['budget_limit'] == $BUDGET, f'Wrong budget_limit: {report[\"budget_limit\"]}'
print('REPORT_FIELDS_OK')
\"" "report_fields_missing"

  # Check: over_budget flag set correctly
  check "python3 -c \"
import sys; sys.path.insert(0, '$WORKSPACE')
from models import ExpenseStore
from app import add_expense, ${REPORT_FN}
store = ExpenseStore()
add_expense(store, 'Big', $BUDGET + 1, '$BASE_CUR', 'misc', '2024-06-01')
report = ${REPORT_FN}(store, '2024-06-01')
assert report['over_budget'] == True, f'over_budget should be True: {report[\"over_budget\"]}'
print('OVER_BUDGET_OK')
\"" "over_budget_flag_wrong"

fi

# ── Attestation ───────────────────────────────────────────────────────────────
# ── Attestation recorded as METADATA, never scored ───────────────────────
# de-scored-by: scripts/repair_graders.py (R3 attestation-is-protocol)
# attestation.json is a PROTOCOL property of the run (already enforced as a
# hard gate in harness/grade_task.py), not a property of the submitted
# artifact. Scoring it let an agent buy partial credit by writing one JSON
# file, which is the confound behind the withdrawn "removing the Verifier
# improves partial score" result. Recorded here, excluded from partial_score.
echo "metadata: attestation_present=$([ -f "${SUBMISSION:-}/attestation.json" ] && echo yes || echo no)"

# ── Score ─────────────────────────────────────────────────────────────────────
PARTIAL=$(python3 -c "print(round($PASSED/max(1,$CHECKS), 2))")
if [ "$PASSED" -eq "$CHECKS" ]; then
    SUCCESS=1; PASS=true
else
    SUCCESS=0; PASS=false
fi
FM=$(python3 -c "import json; print(json.dumps([x for x in '${FAILURES}'.split(',') if x]))")

cat > "$REPORTS/score.json" <<JSON
{
  "pass": $PASS,
  "primary": {"success": $SUCCESS},
  "secondary": {
    "checks_passed": $PASSED,
    "checks_total": $CHECKS,
    "partial_score": $PARTIAL,
    "domain": "$DOMAIN"
  },
  "failure_modes": $FM
}
JSON
