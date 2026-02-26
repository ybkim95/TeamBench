#!/usr/bin/env bash
# Seed-aware grader for SPEC3: Data Model from ERD
#
# Reads domain and expected values from expected.json.
# Checks that all entity classes are present, fields have correct types,
# FK relationships are correct, constraints are applied, and tests pass.
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

# ── Read domain from expected.json ───────────────────────────────────────────
DOMAIN=$(python3 -c "
import json, sys
try:
    e = json.load(open('$EXPECTED'))
    print(e.get('domain', 'unknown'))
except Exception:
    print('unknown')
" 2>/dev/null || echo "unknown")

# ── 1. models.py is syntactically valid Python ───────────────────────────────
check "python3 -m py_compile models.py" "models_syntax_error"

# ── 2. Basic tests pass ───────────────────────────────────────────────────────
check "python3 -m pytest test_models.py -q --tb=no 2>/dev/null | grep -E '^[0-9]+ passed'" \
  "basic_tests_fail"

# ── Helper: run inline Python checks ─────────────────────────────────────────
py_check() {
  python3 -c "
import sys
sys.path.insert(0, '$WORKSPACE')
$1
" 2>/dev/null
}

# ── Domain-specific checks ────────────────────────────────────────────────────

if [ "$DOMAIN" = "ecommerce" ]; then

  USERNAME_MAX=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['username_max'])" 2>/dev/null || echo "50")
  PRODUCT_NAME_MAX=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['product_name_max'])" 2>/dev/null || echo "150")
  MAX_RATING=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_rating'])" 2>/dev/null || echo "5")
  MIN_PRICE=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['min_price'])" 2>/dev/null || echo "0")
  FIRST_STATUS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['order_statuses'][0])" 2>/dev/null || echo "pending")

  # 3. All entity classes importable
  check "py_check \"
from models import Base, User, Product, Order, OrderItem, Review
assert Base is not None
print('IMPORT_OK')
\"" "entities_not_importable"

  # 4. All tables creatable without FK errors
  check "py_check \"
from models import Base
from sqlalchemy import create_engine
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
from sqlalchemy import inspect as sqlinspect
insp = sqlinspect(engine)
tables = set(insp.get_table_names())
required = {'users', 'products', 'orders', 'order_items', 'reviews'}
missing = required - tables
assert not missing, f'Missing tables: {missing}'
print('TABLES_OK')
\"" "tables_not_created"

  # 5. User table has correct columns
  check "py_check \"
from models import Base, User
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('users')}
required = {'id', 'username', 'email', 'password_hash'}
missing = required - cols
assert not missing, f'Missing User columns: {missing}'
print('USER_COLS_OK')
\"" "user_columns_missing"

  # 6. Product table has correct columns including price and stock
  check "py_check \"
from models import Base, Product
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('products')}
required = {'id', 'name', 'price', 'stock_quantity'}
missing = required - cols
assert not missing, f'Missing Product columns: {missing}'
print('PRODUCT_COLS_OK')
\"" "product_columns_missing"

  # 7. OrderItem table has correct FK columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('order_items')}
required = {'order_id', 'product_id', 'quantity', 'unit_price'}
missing = required - cols
assert not missing, f'Missing OrderItem columns: {missing}'
print('ORDER_ITEM_COLS_OK')
\"" "order_item_columns_missing"

  # 8. Review table has user_id, product_id, rating columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('reviews')}
required = {'user_id', 'product_id', 'rating'}
missing = required - cols
assert not missing, f'Missing Review columns: {missing}'
print('REVIEW_COLS_OK')
\"" "review_columns_missing"

  # 9. FK: Order.user_id → users.id exists
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('orders')
fk_cols = [fk['constrained_columns'][0] for fk in fks]
assert 'user_id' in fk_cols, f'No FK on orders.user_id, found: {fk_cols}'
print('ORDER_FK_OK')
\"" "order_user_fk_missing"

  # 10. FK: OrderItem.order_id → orders.id exists
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('order_items')
fk_cols = [fk['constrained_columns'][0] for fk in fks]
assert 'order_id' in fk_cols, f'No FK on order_items.order_id, found: {fk_cols}'
print('ORDER_ITEM_FK_OK')
\"" "order_item_order_fk_missing"

  # 11. FK: Review references both user_id and product_id
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('reviews')
fk_cols = {fk['constrained_columns'][0] for fk in fks}
assert 'user_id' in fk_cols and 'product_id' in fk_cols, f'Missing Review FKs, found: {fk_cols}'
print('REVIEW_FK_OK')
\"" "review_fk_missing"

  # 12. User unique constraint on username and email
  check "py_check \"
from models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    s.add(User(username='testuser', email='t1@x.com', password_hash='h'))
    s.commit()
try:
    with Session(engine) as s:
        s.add(User(username='testuser', email='t2@x.com', password_hash='h'))
        s.commit()
    raise AssertionError('Duplicate username should fail')
except IntegrityError:
    pass
print('USER_UNIQUE_OK')
\"" "user_unique_constraint_missing"

  # 13. Review unique constraint (user_id, product_id)
  check "py_check \"
from models import Base, User, Product, Review
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    u = User(username='reviewer', email='rv@x.com', password_hash='h')
    p = Product(name='Widget', price=9.99, stock_quantity=5)
    s.add_all([u, p]); s.commit()
    s.add(Review(user_id=u.id, product_id=p.id, rating=4)); s.commit()
try:
    with Session(engine) as s:
        s.add(Review(user_id=1, product_id=1, rating=2)); s.commit()
    raise AssertionError('Duplicate review should fail')
except IntegrityError:
    pass
print('REVIEW_UNIQUE_OK')
\"" "review_unique_constraint_missing"

  # 14. OrderItem cascade delete works (delete order removes items)
  check "py_check \"
from models import Base, User, Product, Order, OrderItem
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    u = User(username='buyer', email='buy@x.com', password_hash='h')
    p = Product(name='Gizmo', price=5.00, stock_quantity=10)
    s.add_all([u, p]); s.commit()
    o = Order(user_id=u.id, status='$FIRST_STATUS', total_amount=5.00)
    s.add(o); s.commit()
    oi = OrderItem(order_id=o.id, product_id=p.id, quantity=1, unit_price=5.00)
    s.add(oi); s.commit()
    oi_id = oi.id
    s.delete(o); s.commit()
result = None
with Session(engine) as s:
    result = s.get(OrderItem, oi_id)
assert result is None, 'OrderItem should be cascade-deleted with Order'
print('CASCADE_DELETE_OK')
\"" "order_item_cascade_delete_missing"

elif [ "$DOMAIN" = "hospital" ]; then

  FIRST_SPEC=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(sorted(e['specializations'])[0])" 2>/dev/null || echo "cardiology")
  DURATION_MIN=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['duration_min'])" 2>/dev/null || echo "15")
  FIRST_STATUS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['appt_statuses'][0])" 2>/dev/null || echo "scheduled")

  # 3. All entity classes importable
  check "py_check \"
from models import Base, Patient, Doctor, Appointment, MedicalRecord
assert Base is not None
print('IMPORT_OK')
\"" "entities_not_importable"

  # 4. All tables creatable
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
tables = set(insp.get_table_names())
required = {'patients', 'doctors', 'appointments', 'medical_records'}
missing = required - tables
assert not missing, f'Missing tables: {missing}'
print('TABLES_OK')
\"" "tables_not_created"

  # 5. Patient columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('patients')}
required = {'id', 'first_name', 'last_name', 'date_of_birth', 'email'}
missing = required - cols
assert not missing, f'Missing Patient columns: {missing}'
print('PATIENT_COLS_OK')
\"" "patient_columns_missing"

  # 6. Doctor columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('doctors')}
required = {'id', 'first_name', 'last_name', 'specialization', 'license_number', 'email'}
missing = required - cols
assert not missing, f'Missing Doctor columns: {missing}'
print('DOCTOR_COLS_OK')
\"" "doctor_columns_missing"

  # 7. Appointment columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('appointments')}
required = {'id', 'patient_id', 'doctor_id', 'scheduled_at', 'duration_minutes', 'status'}
missing = required - cols
assert not missing, f'Missing Appointment columns: {missing}'
print('APPT_COLS_OK')
\"" "appointment_columns_missing"

  # 8. MedicalRecord columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('medical_records')}
required = {'id', 'patient_id', 'appointment_id', 'diagnosis'}
missing = required - cols
assert not missing, f'Missing MedicalRecord columns: {missing}'
print('RECORD_COLS_OK')
\"" "medical_record_columns_missing"

  # 9. FK: Appointment → Patient and Doctor
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('appointments')
fk_cols = {fk['constrained_columns'][0] for fk in fks}
assert 'patient_id' in fk_cols and 'doctor_id' in fk_cols, f'Missing FKs: {fk_cols}'
print('APPT_FK_OK')
\"" "appointment_fk_missing"

  # 10. FK: MedicalRecord → Patient and Appointment
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('medical_records')
fk_cols = {fk['constrained_columns'][0] for fk in fks}
assert 'patient_id' in fk_cols and 'appointment_id' in fk_cols, f'Missing FKs: {fk_cols}'
print('RECORD_FK_OK')
\"" "medical_record_fk_missing"

  # 11. Doctor unique constraint on license_number
  check "py_check \"
from models import Base, Doctor
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    s.add(Doctor(first_name='A', last_name='B', specialization='$FIRST_SPEC',
                 license_number='LIC-999', email='a@b.com'))
    s.commit()
try:
    with Session(engine) as s:
        s.add(Doctor(first_name='C', last_name='D', specialization='$FIRST_SPEC',
                     license_number='LIC-999', email='c@d.com'))
        s.commit()
    raise AssertionError('Duplicate license_number should fail')
except IntegrityError:
    pass
print('DOCTOR_UNIQUE_OK')
\"" "doctor_unique_constraint_missing"

  # 12. MedicalRecord unique constraint on appointment_id (one-to-one)
  check "py_check \"
import datetime
from models import Base, Patient, Doctor, Appointment, MedicalRecord
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    p = Patient(first_name='X', last_name='Y', date_of_birth=datetime.date(1990,1,1), email='x@y.com')
    d = Doctor(first_name='Dr', last_name='Z', specialization='$FIRST_SPEC',
               license_number='LIC-100', email='dr@z.com')
    s.add_all([p, d]); s.commit()
    a = Appointment(patient_id=p.id, doctor_id=d.id,
                    scheduled_at=datetime.datetime(2025,6,1,10,0),
                    duration_minutes=$DURATION_MIN, status='$FIRST_STATUS')
    s.add(a); s.commit()
    s.add(MedicalRecord(patient_id=p.id, appointment_id=a.id, diagnosis='Flu')); s.commit()
try:
    with Session(engine) as s:
        s.add(MedicalRecord(patient_id=1, appointment_id=1, diagnosis='Cold')); s.commit()
    raise AssertionError('Duplicate MedicalRecord for same appointment should fail')
except IntegrityError:
    pass
print('RECORD_UNIQUE_OK')
\"" "medical_record_unique_constraint_missing"

  # 13. Patient unique constraint on email
  check "py_check \"
import datetime
from models import Base, Patient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    s.add(Patient(first_name='A', last_name='B',
                  date_of_birth=datetime.date(1980,1,1), email='dup@x.com'))
    s.commit()
try:
    with Session(engine) as s:
        s.add(Patient(first_name='C', last_name='D',
                      date_of_birth=datetime.date(1990,1,1), email='dup@x.com'))
        s.commit()
    raise AssertionError('Duplicate patient email should fail')
except IntegrityError:
    pass
print('PATIENT_UNIQUE_OK')
\"" "patient_email_unique_missing"

  # 14. MedicalRecord cascade delete when appointment deleted
  check "py_check \"
import datetime
from models import Base, Patient, Doctor, Appointment, MedicalRecord
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    p = Patient(first_name='P', last_name='Q', date_of_birth=datetime.date(1975,3,3), email='p@q.com')
    d = Doctor(first_name='R', last_name='S', specialization='$FIRST_SPEC',
               license_number='LIC-200', email='r@s.com')
    s.add_all([p, d]); s.commit()
    a = Appointment(patient_id=p.id, doctor_id=d.id,
                    scheduled_at=datetime.datetime(2025,7,1,9,0),
                    duration_minutes=$DURATION_MIN, status='$FIRST_STATUS')
    s.add(a); s.commit()
    rec = MedicalRecord(patient_id=p.id, appointment_id=a.id, diagnosis='Test')
    s.add(rec); s.commit()
    rec_id = rec.id
    s.delete(a); s.commit()
with Session(engine) as s:
    result = s.get(MedicalRecord, rec_id)
    assert result is None, 'MedicalRecord should be cascade-deleted with Appointment'
print('CASCADE_OK')
\"" "medical_record_cascade_missing"

elif [ "$DOMAIN" = "school" ]; then

  FIRST_DEPT=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(sorted(e['departments'])[0])" 2>/dev/null || echo "Mathematics")
  GRADE_SCALE=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['grade_scale'])" 2>/dev/null || echo "letter")
  MAX_CREDITS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_credits'])" 2>/dev/null || echo "3")
  MAX_CAPACITY=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['max_capacity'])" 2>/dev/null || echo "30")
  FIRST_STATUS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['grade_statuses'][0])" 2>/dev/null || echo "enrolled")

  # 3. All entity classes importable
  check "py_check \"
from models import Base, Student, Course, Enrollment, Grade
assert Base is not None
print('IMPORT_OK')
\"" "entities_not_importable"

  # 4. All tables creatable
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
tables = set(insp.get_table_names())
required = {'students', 'courses', 'enrollments', 'grades'}
missing = required - tables
assert not missing, f'Missing tables: {missing}'
print('TABLES_OK')
\"" "tables_not_created"

  # 5. Student columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('students')}
required = {'id', 'first_name', 'last_name', 'student_id', 'email'}
missing = required - cols
assert not missing, f'Missing Student cols: {missing}'
print('STUDENT_COLS_OK')
\"" "student_columns_missing"

  # 6. Course columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('courses')}
required = {'id', 'course_code', 'title', 'credits', 'capacity', 'department'}
missing = required - cols
assert not missing, f'Missing Course cols: {missing}'
print('COURSE_COLS_OK')
\"" "course_columns_missing"

  # 7. Enrollment columns with FK columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('enrollments')}
required = {'id', 'student_id', 'course_id', 'status'}
missing = required - cols
assert not missing, f'Missing Enrollment cols: {missing}'
print('ENROLLMENT_COLS_OK')
\"" "enrollment_columns_missing"

  # 8. Grade table has enrollment_id
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('grades')}
assert 'enrollment_id' in cols, f'Missing enrollment_id in grades, got: {cols}'
print('GRADE_COLS_OK')
\"" "grade_columns_missing"

  # 9. FK: Enrollment → Student and Course
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('enrollments')
fk_cols = {fk['constrained_columns'][0] for fk in fks}
assert 'student_id' in fk_cols and 'course_id' in fk_cols, f'Missing Enrollment FKs: {fk_cols}'
print('ENROLLMENT_FK_OK')
\"" "enrollment_fk_missing"

  # 10. FK: Grade → Enrollment
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('grades')
fk_cols = {fk['constrained_columns'][0] for fk in fks}
assert 'enrollment_id' in fk_cols, f'Missing Grade FK: {fk_cols}'
print('GRADE_FK_OK')
\"" "grade_fk_missing"

  # 11. Student unique constraint on student_id
  check "py_check \"
from models import Base, Student
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    s.add(Student(first_name='A', last_name='B', student_id='S999', email='a@school.edu'))
    s.commit()
try:
    with Session(engine) as s:
        s.add(Student(first_name='C', last_name='D', student_id='S999', email='c@school.edu'))
        s.commit()
    raise AssertionError('Duplicate student_id should fail')
except IntegrityError:
    pass
print('STUDENT_UNIQUE_OK')
\"" "student_id_unique_missing"

  # 12. Enrollment unique constraint (student_id, course_id)
  check "py_check \"
from models import Base, Student, Course, Enrollment
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    st = Student(first_name='E', last_name='F', student_id='S001', email='e@school.edu')
    co = Course(course_code='CS101', title='Intro', credits=3, capacity=30, department='$FIRST_DEPT')
    s.add_all([st, co]); s.commit()
    s.add(Enrollment(student_id=st.id, course_id=co.id, status='$FIRST_STATUS')); s.commit()
try:
    with Session(engine) as s:
        s.add(Enrollment(student_id=1, course_id=1, status='$FIRST_STATUS')); s.commit()
    raise AssertionError('Duplicate enrollment should fail')
except IntegrityError:
    pass
print('ENROLLMENT_UNIQUE_OK')
\"" "enrollment_unique_constraint_missing"

  # 13. Grade unique constraint on enrollment_id (one-to-one)
  check "py_check \"
from models import Base, Student, Course, Enrollment, Grade
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    st = Student(first_name='G', last_name='H', student_id='S002', email='g@school.edu')
    co = Course(course_code='MATH101', title='Calc', credits=3, capacity=25, department='$FIRST_DEPT')
    s.add_all([st, co]); s.commit()
    enr = Enrollment(student_id=st.id, course_id=co.id, status='$FIRST_STATUS')
    s.add(enr); s.commit()
    s.add(Grade(enrollment_id=enr.id)); s.commit()
try:
    with Session(engine) as s:
        s.add(Grade(enrollment_id=1)); s.commit()
    raise AssertionError('Duplicate grade for same enrollment should fail')
except IntegrityError:
    pass
print('GRADE_UNIQUE_OK')
\"" "grade_unique_constraint_missing"

  # 14. Cascade delete: deleting Enrollment removes Grade
  check "py_check \"
from models import Base, Student, Course, Enrollment, Grade
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    st = Student(first_name='I', last_name='J', student_id='S003', email='i@school.edu')
    co = Course(course_code='PHY101', title='Physics', credits=3, capacity=20, department='$FIRST_DEPT')
    s.add_all([st, co]); s.commit()
    enr = Enrollment(student_id=st.id, course_id=co.id, status='$FIRST_STATUS')
    s.add(enr); s.commit()
    g = Grade(enrollment_id=enr.id)
    s.add(g); s.commit()
    grade_id = g.id
    s.delete(enr); s.commit()
with Session(engine) as s:
    result = s.get(Grade, grade_id)
    assert result is None, 'Grade should be cascade-deleted with Enrollment'
print('CASCADE_OK')
\"" "grade_cascade_missing"

elif [ "$DOMAIN" = "project_mgmt" ]; then

  FIRST_STATUS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['project_statuses'][0])" 2>/dev/null || echo "active")
  FIRST_PRIORITY=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['priorities'][0])" 2>/dev/null || echo "low")
  FIRST_TASK_STATUS=$(python3 -c "import json; e=json.load(open('$EXPECTED')); print(e['task_statuses'][0])" 2>/dev/null || echo "todo")

  # 3. All entity classes importable
  check "py_check \"
from models import Base, User, Project, Task, Comment
assert Base is not None
print('IMPORT_OK')
\"" "entities_not_importable"

  # 4. All tables creatable
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
tables = set(insp.get_table_names())
required = {'users', 'projects', 'tasks', 'comments'}
missing = required - tables
assert not missing, f'Missing tables: {missing}'
print('TABLES_OK')
\"" "tables_not_created"

  # 5. User columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('users')}
required = {'id', 'username', 'email', 'password_hash'}
missing = required - cols
assert not missing, f'Missing User cols: {missing}'
print('USER_COLS_OK')
\"" "user_columns_missing"

  # 6. Project columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('projects')}
required = {'id', 'name', 'owner_id', 'status'}
missing = required - cols
assert not missing, f'Missing Project cols: {missing}'
print('PROJECT_COLS_OK')
\"" "project_columns_missing"

  # 7. Task columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('tasks')}
required = {'id', 'title', 'project_id', 'priority', 'status'}
missing = required - cols
assert not missing, f'Missing Task cols: {missing}'
print('TASK_COLS_OK')
\"" "task_columns_missing"

  # 8. Comment columns
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
cols = {c['name'] for c in insp.get_columns('comments')}
required = {'id', 'task_id', 'author_id', 'body'}
missing = required - cols
assert not missing, f'Missing Comment cols: {missing}'
print('COMMENT_COLS_OK')
\"" "comment_columns_missing"

  # 9. FK: Project → User (owner_id)
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('projects')
fk_cols = {fk['constrained_columns'][0] for fk in fks}
assert 'owner_id' in fk_cols, f'Missing project FK: {fk_cols}'
print('PROJECT_FK_OK')
\"" "project_owner_fk_missing"

  # 10. FK: Task → Project (project_id)
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('tasks')
fk_cols = {fk['constrained_columns'][0] for fk in fks}
assert 'project_id' in fk_cols, f'Missing task project FK: {fk_cols}'
print('TASK_FK_OK')
\"" "task_project_fk_missing"

  # 11. FK: Comment → Task and User
  check "py_check \"
from models import Base
from sqlalchemy import create_engine, inspect as sqlinspect
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
insp = sqlinspect(engine)
fks = insp.get_foreign_keys('comments')
fk_cols = {fk['constrained_columns'][0] for fk in fks}
assert 'task_id' in fk_cols and 'author_id' in fk_cols, f'Missing Comment FKs: {fk_cols}'
print('COMMENT_FK_OK')
\"" "comment_fk_missing"

  # 12. User unique constraints on username and email
  check "py_check \"
from models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    s.add(User(username='devA', email='a@dev.com', password_hash='h')); s.commit()
try:
    with Session(engine) as s:
        s.add(User(username='devA', email='b@dev.com', password_hash='h')); s.commit()
    raise AssertionError('Duplicate username should fail')
except IntegrityError:
    pass
print('USER_UNIQUE_OK')
\"" "user_unique_constraint_missing"

  # 13. Project unique constraint on name
  check "py_check \"
from models import Base, User, Project
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    u = User(username='owner1', email='o1@x.com', password_hash='h'); s.add(u); s.commit()
    s.add(Project(name='Alpha', owner_id=u.id, status='$FIRST_STATUS')); s.commit()
try:
    with Session(engine) as s:
        s.add(Project(name='Alpha', owner_id=1, status='$FIRST_STATUS')); s.commit()
    raise AssertionError('Duplicate project name should fail')
except IntegrityError:
    pass
print('PROJECT_UNIQUE_OK')
\"" "project_name_unique_missing"

  # 14. Cascade delete: deleting Task removes Comments
  check "py_check \"
from models import Base, User, Project, Task, Comment
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
with Session(engine) as s:
    u = User(username='cm', email='cm@x.com', password_hash='h'); s.add(u); s.commit()
    p = Project(name='Delta', owner_id=u.id, status='$FIRST_STATUS'); s.add(p); s.commit()
    t = Task(title='Do it', project_id=p.id,
             priority='$FIRST_PRIORITY', status='$FIRST_TASK_STATUS')
    s.add(t); s.commit()
    c = Comment(task_id=t.id, author_id=u.id, body='Good work'); s.add(c); s.commit()
    comment_id = c.id
    s.delete(t); s.commit()
with Session(engine) as s:
    result = s.get(Comment, comment_id)
    assert result is None, 'Comment should be cascade-deleted with Task'
print('CASCADE_OK')
\"" "comment_cascade_missing"

fi

# ── Final scoring ─────────────────────────────────────────────────────────────
SCORE=$(python3 -c "print(round($PASSED / max($CHECKS, 1), 3))")

cat > "$REPORTS/result.json" <<EOF
{
  "checks": $CHECKS,
  "passed": $PASSED,
  "score": $SCORE,
  "failures": "$FAILURES",
  "domain": "$DOMAIN"
}
EOF

echo "SPEC3_data_model | domain=$DOMAIN | $PASSED/$CHECKS checks passed | score=$SCORE"
if [ -n "$FAILURES" ]; then
  echo "Failed checks: $FAILURES"
fi

[ "$PASSED" -eq "$CHECKS" ]
