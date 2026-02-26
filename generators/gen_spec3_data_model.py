"""
Parameterized generator for SPEC3: Data Model from ERD.

Each seed selects a different domain and produces:
  - models.py: Empty file (agent must create all entity classes)
  - test_models.py: Skeleton with basic import checks and partial tests
  - requirements.txt: sqlalchemy pytest
  - spec.md: Complete ERD with entities, relationships, cardinality, constraints, index requirements
  - brief.md: Vague — "Implement the data model. The Planner has the detailed schema."
  - expected.json: Seed-aware ground-truth for the grader

TNI driver: brief.md is vague; spec.md has the complete ERD including:
  - All entity class names and their fields with types
  - NOT NULL / UNIQUE / CHECK constraints
  - FK references with ON DELETE behavior
  - Cardinality (one-to-many, many-to-many via join table)
  - Required CREATE TABLE order (parent before child)
  - Index requirements

Seed → domain mapping:
  0 mod 4 → ecommerce      (users / products / orders / order_items / reviews)
  1 mod 4 → hospital       (patients / doctors / appointments / medical_records)
  2 mod 4 → school         (students / courses / enrollments / grades)
  3 mod 4 → project_mgmt   (users / projects / tasks / comments)
"""
from __future__ import annotations

import textwrap

from generators.base import TaskGenerator, GeneratedTask
from generators.primitives import SeededRandom

DOMAINS = [
    "ecommerce",
    "hospital",
    "school",
    "project_mgmt",
]


class Generator(TaskGenerator):
    task_id = "SPEC3_data_model"
    domain = "specification"
    difficulty = "medium"
    languages = ["python"]

    def generate(self, seed: int) -> GeneratedTask:
        rng = SeededRandom(seed)
        domain = DOMAINS[seed % len(DOMAINS)]

        if domain == "ecommerce":
            return self._gen_ecommerce(seed, rng)
        elif domain == "hospital":
            return self._gen_hospital(seed, rng)
        elif domain == "school":
            return self._gen_school(seed, rng)
        else:
            return self._gen_project_mgmt(seed, rng)

    # -----------------------------------------------------------------------
    # Domain 0: E-Commerce
    # -----------------------------------------------------------------------

    def _gen_ecommerce(self, seed: int, rng: SeededRandom) -> GeneratedTask:
        # Vary constraints per seed
        username_max = rng.choice([30, 50, 80])
        product_name_max = rng.choice([100, 150, 200])
        min_price = rng.choice([0, 1])
        max_rating = rng.choice([5, 10])
        min_stock = rng.choice([0, 1])
        order_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
        selected_statuses = rng.sample(order_statuses, rng.randint(4, 5))
        selected_statuses_sorted = [s for s in order_statuses if s in selected_statuses]

        expected = {
            "domain": "ecommerce",
            "entities": ["User", "Product", "Order", "OrderItem", "Review"],
            "entity_count": 5,
            "relationships": [
                {"from": "Order", "to": "User", "type": "many_to_one"},
                {"from": "OrderItem", "to": "Order", "type": "many_to_one"},
                {"from": "OrderItem", "to": "Product", "type": "many_to_one"},
                {"from": "Review", "to": "User", "type": "many_to_one"},
                {"from": "Review", "to": "Product", "type": "many_to_one"},
            ],
            "username_max": username_max,
            "product_name_max": product_name_max,
            "min_price": min_price,
            "max_rating": max_rating,
            "min_stock": min_stock,
            "order_statuses": selected_statuses_sorted,
            "not_null_fields": {
                "User": ["username", "email", "password_hash"],
                "Product": ["name", "price", "stock_quantity"],
                "Order": ["user_id", "status", "total_amount"],
                "OrderItem": ["order_id", "product_id", "quantity", "unit_price"],
                "Review": ["user_id", "product_id", "rating"],
            },
            "unique_fields": {
                "User": ["username", "email"],
                "Product": ["name"],
                "Review": ["user_id,product_id"],
            },
            "check_constraints": {
                "Product": [f"price >= {min_price}", f"stock_quantity >= {min_stock}"],
                "OrderItem": ["quantity >= 1"],
                "Review": [f"rating >= 1 AND rating <= {max_rating}"],
            },
            "indexes": [
                "orders.user_id",
                "order_items.order_id",
                "order_items.product_id",
                "reviews.product_id",
            ],
            "create_order": ["User", "Product", "Order", "OrderItem", "Review"],
        }

        statuses_str = ", ".join(f"'{s}'" for s in selected_statuses_sorted)

        spec_md = f"""# SPEC3: E-Commerce Data Model — Entity-Relationship Specification

## Overview

Design and implement a relational data model for an e-commerce platform.
Use SQLAlchemy ORM (declarative base). All models must be importable from `models.py`.

## Entities and Attributes

### User
Represents a registered customer.

| Column          | Type         | Constraints                          |
|-----------------|--------------|--------------------------------------|
| id              | Integer      | PRIMARY KEY, auto-increment          |
| username        | String({username_max}) | NOT NULL, UNIQUE               |
| email           | String(255)  | NOT NULL, UNIQUE                     |
| password_hash   | String(255)  | NOT NULL                             |
| created_at      | DateTime     | NOT NULL, default = current UTC time |
| is_active       | Boolean      | NOT NULL, default = True             |

### Product
Represents a product available for purchase.

| Column          | Type         | Constraints                                    |
|-----------------|--------------|------------------------------------------------|
| id              | Integer      | PRIMARY KEY, auto-increment                    |
| name            | String({product_name_max}) | NOT NULL, UNIQUE                 |
| description     | Text         | nullable                                       |
| price           | Numeric(10,2)| NOT NULL, CHECK (price >= {min_price})         |
| stock_quantity  | Integer      | NOT NULL, CHECK (stock_quantity >= {min_stock})|
| category        | String(100)  | nullable                                       |
| created_at      | DateTime     | NOT NULL, default = current UTC time           |

### Order
Represents a purchase order placed by a user.

| Column          | Type         | Constraints                                                    |
|-----------------|--------------|----------------------------------------------------------------|
| id              | Integer      | PRIMARY KEY, auto-increment                                    |
| user_id         | Integer      | NOT NULL, FK → User.id ON DELETE RESTRICT                      |
| status          | String(20)   | NOT NULL, CHECK (status IN ({statuses_str}))                   |
| total_amount    | Numeric(12,2)| NOT NULL                                                       |
| created_at      | DateTime     | NOT NULL, default = current UTC time                           |
| updated_at      | DateTime     | NOT NULL, default = current UTC time, updated on modification  |

### OrderItem
Join entity representing a product line within an order (resolves Order ↔ Product many-to-many).

| Column          | Type         | Constraints                                      |
|-----------------|--------------|--------------------------------------------------|
| id              | Integer      | PRIMARY KEY, auto-increment                      |
| order_id        | Integer      | NOT NULL, FK → Order.id ON DELETE CASCADE        |
| product_id      | Integer      | NOT NULL, FK → Product.id ON DELETE RESTRICT     |
| quantity        | Integer      | NOT NULL, CHECK (quantity >= 1)                  |
| unit_price      | Numeric(10,2)| NOT NULL                                         |

### Review
Represents a user review of a product. One user may review each product at most once.

| Column          | Type         | Constraints                                        |
|-----------------|--------------|-----------------------------------------------------|
| id              | Integer      | PRIMARY KEY, auto-increment                         |
| user_id         | Integer      | NOT NULL, FK → User.id ON DELETE CASCADE            |
| product_id      | Integer      | NOT NULL, FK → Product.id ON DELETE CASCADE         |
| rating          | Integer      | NOT NULL, CHECK (rating >= 1 AND rating <= {max_rating}) |
| comment         | Text         | nullable                                            |
| created_at      | DateTime     | NOT NULL, default = current UTC time                |

**UNIQUE constraint:** (user_id, product_id) — a user may only leave one review per product.

## Relationships

| Relationship              | Cardinality  | Details                                     |
|---------------------------|--------------|---------------------------------------------|
| User → Orders             | One-to-Many  | User.id ← Order.user_id                     |
| Order → OrderItems        | One-to-Many  | Order.id ← OrderItem.order_id               |
| Product → OrderItems      | One-to-Many  | Product.id ← OrderItem.product_id           |
| User → Reviews            | One-to-Many  | User.id ← Review.user_id                    |
| Product → Reviews         | One-to-Many  | Product.id ← Review.product_id              |
| Order ↔ Product (via OrderItem) | Many-to-Many | Resolved through OrderItem join entity |

## Index Requirements

The following columns must have database indexes for query performance:
- `orders.user_id`
- `order_items.order_id`
- `order_items.product_id`
- `reviews.product_id`

## CREATE TABLE Order (FK dependency order)

Tables must be created in this order to satisfy foreign key constraints:
1. `users` (no dependencies)
2. `products` (no dependencies)
3. `orders` (depends on users)
4. `order_items` (depends on orders, products)
5. `reviews` (depends on users, products)

## Implementation Notes

- Use `from sqlalchemy import ...` and `from sqlalchemy.orm import declarative_base`
- Define `Base = declarative_base()` at the top of `models.py`
- Each class must inherit from `Base`
- Use `__tablename__` attribute (snake_case plural: `users`, `products`, `orders`, `order_items`, `reviews`)
- Define `relationship()` back-references where appropriate
- Export `Base`, `User`, `Product`, `Order`, `OrderItem`, `Review` from `models.py`
"""

        brief_md = """# SPEC3: E-Commerce Data Model (Executor Brief)

Implement the data model for the e-commerce application. The Planner has the
detailed schema including all entity definitions, constraints, and relationships.

The workspace contains:
- `models.py` — empty; you must implement all entity classes here
- `test_models.py` — partial test suite (does not cover all constraints)

Install dependencies: `pip install sqlalchemy pytest`

Run tests with: `python -m pytest test_models.py -v`
"""

        models_py = '# models.py — implement the e-commerce data model here\n'

        test_models_py = textwrap.dedent(f"""\
            \"\"\"Partial tests for the e-commerce data model.

            NOTE: These tests check basic structure but do NOT verify all constraints,
            relationships, or indexes. The Planner has the full specification.
            \"\"\"
            import pytest
            from sqlalchemy import create_engine, inspect
            from sqlalchemy.orm import Session


            def get_engine():
                return create_engine("sqlite:///:memory:", echo=False)


            def test_models_importable():
                \"\"\"All entity classes must be importable from models.py.\"\"\"
                from models import Base, User, Product, Order, OrderItem, Review
                assert Base is not None


            def test_tables_creatable():
                \"\"\"All tables must be created without errors.\"\"\"
                from models import Base
                engine = get_engine()
                Base.metadata.create_all(engine)
                insp = inspect(engine)
                tables = set(insp.get_table_names())
                assert "users" in tables
                assert "products" in tables
                assert "orders" in tables


            def test_user_insert():
                \"\"\"User record can be inserted and retrieved.\"\"\"
                from models import Base, User
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    u = User(
                        username="alice",
                        email="alice@example.com",
                        password_hash="hashed",
                    )
                    session.add(u)
                    session.commit()
                    result = session.get(User, u.id)
                    assert result.username == "alice"


            def test_product_insert():
                \"\"\"Product record can be inserted and retrieved.\"\"\"
                from models import Base, Product
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    p = Product(
                        name="Laptop",
                        price=999.99,
                        stock_quantity=10,
                    )
                    session.add(p)
                    session.commit()
                    result = session.get(Product, p.id)
                    assert result.name == "Laptop"


            def test_order_links_to_user():
                \"\"\"Order must have a valid FK to User.\"\"\"
                from models import Base, User, Order
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    u = User(username="bob", email="bob@example.com", password_hash="x")
                    session.add(u)
                    session.commit()
                    o = Order(user_id=u.id, status="{selected_statuses_sorted[0]}", total_amount=50.00)
                    session.add(o)
                    session.commit()
                    assert o.user_id == u.id
        """)

        requirements_txt = "sqlalchemy\npytest\n"

        return GeneratedTask(
            task_id="SPEC3_data_model",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files={
                "models.py": models_py,
                "test_models.py": test_models_py,
                "requirements.txt": requirements_txt,
            },
        )

    # -----------------------------------------------------------------------
    # Domain 1: Hospital
    # -----------------------------------------------------------------------

    def _gen_hospital(self, seed: int, rng: SeededRandom) -> GeneratedTask:
        name_max = rng.choice([100, 150, 200])
        note_max = rng.choice([500, 1000, 2000])
        specializations = ["cardiology", "neurology", "orthopedics", "pediatrics",
                           "oncology", "dermatology", "psychiatry", "radiology"]
        selected_specs = rng.sample(specializations, rng.randint(4, 6))
        appt_statuses = ["scheduled", "completed", "cancelled", "no_show"]
        duration_min = rng.choice([15, 20, 30])
        duration_max = rng.choice([60, 90, 120])

        expected = {
            "domain": "hospital",
            "entities": ["Patient", "Doctor", "Appointment", "MedicalRecord"],
            "entity_count": 4,
            "relationships": [
                {"from": "Appointment", "to": "Patient", "type": "many_to_one"},
                {"from": "Appointment", "to": "Doctor", "type": "many_to_one"},
                {"from": "MedicalRecord", "to": "Patient", "type": "many_to_one"},
                {"from": "MedicalRecord", "to": "Appointment", "type": "one_to_one"},
            ],
            "name_max": name_max,
            "note_max": note_max,
            "specializations": sorted(selected_specs),
            "appt_statuses": appt_statuses,
            "duration_min": duration_min,
            "duration_max": duration_max,
            "not_null_fields": {
                "Patient": ["first_name", "last_name", "date_of_birth", "email"],
                "Doctor": ["first_name", "last_name", "specialization", "license_number"],
                "Appointment": ["patient_id", "doctor_id", "scheduled_at", "duration_minutes", "status"],
                "MedicalRecord": ["patient_id", "appointment_id", "diagnosis"],
            },
            "unique_fields": {
                "Patient": ["email"],
                "Doctor": ["license_number", "email"],
            },
            "check_constraints": {
                "Appointment": [
                    f"duration_minutes >= {duration_min} AND duration_minutes <= {duration_max}",
                    f"status IN ({', '.join(repr(s) for s in appt_statuses)})",
                ],
                "Doctor": [f"specialization IN ({', '.join(repr(s) for s in sorted(selected_specs))})"],
            },
            "indexes": [
                "appointments.patient_id",
                "appointments.doctor_id",
                "appointments.scheduled_at",
                "medical_records.patient_id",
            ],
            "create_order": ["Patient", "Doctor", "Appointment", "MedicalRecord"],
        }

        specs_str = ", ".join(f"'{s}'" for s in sorted(selected_specs))
        statuses_str = ", ".join(f"'{s}'" for s in appt_statuses)

        spec_md = f"""# SPEC3: Hospital Management Data Model — Entity-Relationship Specification

## Overview

Design and implement a relational data model for a hospital management system.
Use SQLAlchemy ORM (declarative base). All models must be importable from `models.py`.

## Entities and Attributes

### Patient
Represents a registered patient.

| Column          | Type          | Constraints                                |
|-----------------|---------------|--------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                |
| first_name      | String({name_max}) | NOT NULL                              |
| last_name       | String({name_max}) | NOT NULL                              |
| date_of_birth   | Date          | NOT NULL                                   |
| email           | String(255)   | NOT NULL, UNIQUE                           |
| phone           | String(20)    | nullable                                   |
| address         | Text          | nullable                                   |
| registered_at   | DateTime      | NOT NULL, default = current UTC time       |

### Doctor
Represents a medical professional.

| Column          | Type          | Constraints                                              |
|-----------------|---------------|----------------------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                              |
| first_name      | String({name_max}) | NOT NULL                                            |
| last_name       | String({name_max}) | NOT NULL                                            |
| specialization  | String(100)   | NOT NULL, CHECK (specialization IN ({specs_str}))        |
| license_number  | String(50)    | NOT NULL, UNIQUE                                         |
| email           | String(255)   | NOT NULL, UNIQUE                                         |
| phone           | String(20)    | nullable                                                 |

### Appointment
Represents a scheduled meeting between a patient and doctor.

| Column             | Type          | Constraints                                                               |
|--------------------|---------------|---------------------------------------------------------------------------|
| id                 | Integer       | PRIMARY KEY, auto-increment                                               |
| patient_id         | Integer       | NOT NULL, FK → Patient.id ON DELETE RESTRICT                              |
| doctor_id          | Integer       | NOT NULL, FK → Doctor.id ON DELETE RESTRICT                               |
| scheduled_at       | DateTime      | NOT NULL                                                                  |
| duration_minutes   | Integer       | NOT NULL, CHECK (duration_minutes >= {duration_min} AND duration_minutes <= {duration_max}) |
| status             | String(20)    | NOT NULL, CHECK (status IN ({statuses_str}))                              |
| notes              | Text          | nullable                                                                  |
| created_at         | DateTime      | NOT NULL, default = current UTC time                                      |

### MedicalRecord
Represents the medical outcome/notes from an appointment. One record per appointment.

| Column          | Type          | Constraints                                          |
|-----------------|---------------|------------------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                          |
| patient_id      | Integer       | NOT NULL, FK → Patient.id ON DELETE RESTRICT         |
| appointment_id  | Integer       | NOT NULL, UNIQUE, FK → Appointment.id ON DELETE CASCADE |
| diagnosis       | Text          | NOT NULL                                             |
| treatment       | Text          | nullable                                             |
| notes           | String({note_max}) | nullable                                        |
| recorded_at     | DateTime      | NOT NULL, default = current UTC time                 |

## Relationships

| Relationship                      | Cardinality  | Details                                               |
|-----------------------------------|--------------|-------------------------------------------------------|
| Patient → Appointments            | One-to-Many  | Patient.id ← Appointment.patient_id                   |
| Doctor → Appointments             | One-to-Many  | Doctor.id ← Appointment.doctor_id                     |
| Patient → MedicalRecords          | One-to-Many  | Patient.id ← MedicalRecord.patient_id                 |
| Appointment → MedicalRecord       | One-to-One   | Appointment.id ← MedicalRecord.appointment_id (UNIQUE)|

## Index Requirements

- `appointments.patient_id`
- `appointments.doctor_id`
- `appointments.scheduled_at`
- `medical_records.patient_id`

## CREATE TABLE Order

1. `patients` (no dependencies)
2. `doctors` (no dependencies)
3. `appointments` (depends on patients, doctors)
4. `medical_records` (depends on patients, appointments)

## Implementation Notes

- Use `from sqlalchemy import ...` and `from sqlalchemy.orm import declarative_base`
- Define `Base = declarative_base()` at the top of `models.py`
- Each class must inherit from `Base`
- Use `__tablename__` (snake_case plural): `patients`, `doctors`, `appointments`, `medical_records`
- Export `Base`, `Patient`, `Doctor`, `Appointment`, `MedicalRecord` from `models.py`
"""

        brief_md = """# SPEC3: Hospital Management Data Model (Executor Brief)

Implement the data model for the hospital management application. The Planner has
the detailed schema including all entity definitions, constraints, and relationships.

The workspace contains:
- `models.py` — empty; you must implement all entity classes here
- `test_models.py` — partial test suite (does not cover all constraints)

Install dependencies: `pip install sqlalchemy pytest`

Run tests with: `python -m pytest test_models.py -v`
"""

        models_py = '# models.py — implement the hospital data model here\n'

        test_models_py = textwrap.dedent(f"""\
            \"\"\"Partial tests for the hospital data model.

            NOTE: These tests check basic structure but do NOT verify all constraints,
            relationships, or indexes. The Planner has the full specification.
            \"\"\"
            import pytest
            from sqlalchemy import create_engine, inspect
            from sqlalchemy.orm import Session


            def get_engine():
                return create_engine("sqlite:///:memory:", echo=False)


            def test_models_importable():
                from models import Base, Patient, Doctor, Appointment, MedicalRecord
                assert Base is not None


            def test_tables_creatable():
                from models import Base
                engine = get_engine()
                Base.metadata.create_all(engine)
                insp = inspect(engine)
                tables = set(insp.get_table_names())
                assert "patients" in tables
                assert "doctors" in tables
                assert "appointments" in tables
                assert "medical_records" in tables


            def test_patient_insert():
                import datetime
                from models import Base, Patient
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    p = Patient(
                        first_name="Jane",
                        last_name="Doe",
                        date_of_birth=datetime.date(1990, 5, 15),
                        email="jane@hospital.com",
                    )
                    session.add(p)
                    session.commit()
                    result = session.get(Patient, p.id)
                    assert result.email == "jane@hospital.com"


            def test_doctor_insert():
                from models import Base, Doctor
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    d = Doctor(
                        first_name="Dr",
                        last_name="Smith",
                        specialization="{sorted(selected_specs)[0]}",
                        license_number="LIC-001",
                        email="smith@hospital.com",
                    )
                    session.add(d)
                    session.commit()
                    result = session.get(Doctor, d.id)
                    assert result.license_number == "LIC-001"


            def test_appointment_links_patient_and_doctor():
                import datetime
                from models import Base, Patient, Doctor, Appointment
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    p = Patient(first_name="A", last_name="B",
                                date_of_birth=datetime.date(1985, 1, 1), email="a@b.com")
                    d = Doctor(first_name="C", last_name="D",
                               specialization="{sorted(selected_specs)[0]}",
                               license_number="LIC-002", email="c@d.com")
                    session.add_all([p, d])
                    session.commit()
                    appt = Appointment(
                        patient_id=p.id,
                        doctor_id=d.id,
                        scheduled_at=datetime.datetime(2025, 6, 1, 10, 0),
                        duration_minutes={duration_min},
                        status="{appt_statuses[0]}",
                    )
                    session.add(appt)
                    session.commit()
                    assert appt.patient_id == p.id
                    assert appt.doctor_id == d.id
        """)

        requirements_txt = "sqlalchemy\npytest\n"

        return GeneratedTask(
            task_id="SPEC3_data_model",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files={
                "models.py": models_py,
                "test_models.py": test_models_py,
                "requirements.txt": requirements_txt,
            },
        )

    # -----------------------------------------------------------------------
    # Domain 2: School
    # -----------------------------------------------------------------------

    def _gen_school(self, seed: int, rng: SeededRandom) -> GeneratedTask:
        name_max = rng.choice([80, 100, 150])
        course_code_max = rng.choice([10, 12, 15])
        max_credits = rng.choice([3, 4, 6])
        max_capacity = rng.choice([30, 50, 100])
        grade_scale = rng.choice(["letter", "percentage"])
        grade_statuses = ["enrolled", "withdrawn", "completed"]
        departments = ["Mathematics", "Physics", "Computer Science", "Chemistry",
                       "Biology", "History", "Literature", "Economics"]
        selected_depts = rng.sample(departments, rng.randint(4, 6))

        if grade_scale == "letter":
            grade_values = ["A", "B", "C", "D", "F"]
            grade_check = "grade IN ('A', 'B', 'C', 'D', 'F')"
        else:
            grade_values = None
            grade_check = "grade_percentage >= 0 AND grade_percentage <= 100"

        expected = {
            "domain": "school",
            "entities": ["Student", "Course", "Enrollment", "Grade"],
            "entity_count": 4,
            "relationships": [
                {"from": "Enrollment", "to": "Student", "type": "many_to_one"},
                {"from": "Enrollment", "to": "Course", "type": "many_to_one"},
                {"from": "Grade", "to": "Enrollment", "type": "one_to_one"},
            ],
            "name_max": name_max,
            "course_code_max": course_code_max,
            "max_credits": max_credits,
            "max_capacity": max_capacity,
            "grade_scale": grade_scale,
            "grade_values": grade_values,
            "grade_check": grade_check,
            "grade_statuses": grade_statuses,
            "departments": sorted(selected_depts),
            "not_null_fields": {
                "Student": ["first_name", "last_name", "student_id", "email"],
                "Course": ["course_code", "title", "credits", "capacity", "department"],
                "Enrollment": ["student_id", "course_id", "enrolled_at", "status"],
                "Grade": ["enrollment_id", "recorded_at"],
            },
            "unique_fields": {
                "Student": ["student_id", "email"],
                "Course": ["course_code"],
                "Enrollment": ["student_id,course_id"],
            },
            "check_constraints": {
                "Course": [f"credits >= 1 AND credits <= {max_credits}",
                           f"capacity >= 1 AND capacity <= {max_capacity}"],
                "Grade": [grade_check],
            },
            "indexes": [
                "enrollments.student_id",
                "enrollments.course_id",
                "grades.enrollment_id",
            ],
            "create_order": ["Student", "Course", "Enrollment", "Grade"],
        }

        depts_str = ", ".join(f"'{d}'" for d in sorted(selected_depts))
        statuses_str = ", ".join(f"'{s}'" for s in grade_statuses)

        if grade_scale == "letter":
            grade_col_block = """\
| grade           | String(2)     | nullable, CHECK (grade IN ('A', 'B', 'C', 'D', 'F'))     |"""
        else:
            grade_col_block = """\
| grade_percentage| Numeric(5,2)  | nullable, CHECK (grade_percentage >= 0 AND grade_percentage <= 100) |"""

        spec_md = f"""# SPEC3: School Management Data Model — Entity-Relationship Specification

## Overview

Design and implement a relational data model for a school management system.
Use SQLAlchemy ORM (declarative base). All models must be importable from `models.py`.

## Entities and Attributes

### Student
Represents a registered student.

| Column          | Type          | Constraints                                |
|-----------------|---------------|--------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                |
| first_name      | String({name_max}) | NOT NULL                              |
| last_name       | String({name_max}) | NOT NULL                              |
| student_id      | String(20)    | NOT NULL, UNIQUE (institutional ID)        |
| email           | String(255)   | NOT NULL, UNIQUE                           |
| date_of_birth   | Date          | nullable                                   |
| enrolled_at     | DateTime      | NOT NULL, default = current UTC time       |

### Course
Represents a course offered by the school.

| Column          | Type          | Constraints                                                          |
|-----------------|---------------|----------------------------------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                                          |
| course_code     | String({course_code_max}) | NOT NULL, UNIQUE (e.g. "CS101")                          |
| title           | String(200)   | NOT NULL                                                             |
| credits         | Integer       | NOT NULL, CHECK (credits >= 1 AND credits <= {max_credits})          |
| capacity        | Integer       | NOT NULL, CHECK (capacity >= 1 AND capacity <= {max_capacity})       |
| department      | String(100)   | NOT NULL, CHECK (department IN ({depts_str}))                        |
| description     | Text          | nullable                                                             |

### Enrollment
Join entity representing a student enrolled in a course. A student may enroll in a given course at most once.

| Column          | Type          | Constraints                                                        |
|-----------------|---------------|--------------------------------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                                        |
| student_id      | Integer       | NOT NULL, FK → Student.id ON DELETE RESTRICT                       |
| course_id       | Integer       | NOT NULL, FK → Course.id ON DELETE RESTRICT                        |
| enrolled_at     | DateTime      | NOT NULL, default = current UTC time                               |
| status          | String(20)    | NOT NULL, CHECK (status IN ({statuses_str}))                       |

**UNIQUE constraint:** (student_id, course_id) — a student may only enroll once per course.

### Grade
Records the academic outcome for an enrollment. One grade record per enrollment.

| Column          | Type          | Constraints                                                     |
|-----------------|---------------|-----------------------------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                                     |
| enrollment_id   | Integer       | NOT NULL, UNIQUE, FK → Enrollment.id ON DELETE CASCADE          |
{grade_col_block}
| remarks         | Text          | nullable                                                        |
| recorded_at     | DateTime      | NOT NULL, default = current UTC time                            |

## Relationships

| Relationship                    | Cardinality  | Details                                          |
|---------------------------------|--------------|--------------------------------------------------|
| Student → Enrollments           | One-to-Many  | Student.id ← Enrollment.student_id               |
| Course → Enrollments            | One-to-Many  | Course.id ← Enrollment.course_id                 |
| Enrollment → Grade              | One-to-One   | Enrollment.id ← Grade.enrollment_id (UNIQUE)     |
| Student ↔ Course (via Enrollment)| Many-to-Many | Resolved through Enrollment join entity          |

## Index Requirements

- `enrollments.student_id`
- `enrollments.course_id`
- `grades.enrollment_id`

## CREATE TABLE Order

1. `students` (no dependencies)
2. `courses` (no dependencies)
3. `enrollments` (depends on students, courses)
4. `grades` (depends on enrollments)

## Implementation Notes

- Use `from sqlalchemy import ...` and `from sqlalchemy.orm import declarative_base`
- Define `Base = declarative_base()` at the top of `models.py`
- Each class must inherit from `Base`
- `__tablename__` values: `students`, `courses`, `enrollments`, `grades`
- Export `Base`, `Student`, `Course`, `Enrollment`, `Grade` from `models.py`
"""

        brief_md = """# SPEC3: School Management Data Model (Executor Brief)

Implement the data model for the school management application. The Planner has
the detailed schema including all entity definitions, constraints, and relationships.

The workspace contains:
- `models.py` — empty; you must implement all entity classes here
- `test_models.py` — partial test suite (does not cover all constraints)

Install dependencies: `pip install sqlalchemy pytest`

Run tests with: `python -m pytest test_models.py -v`
"""

        models_py = '# models.py — implement the school data model here\n'

        if grade_scale == "letter":
            grade_insert = 'g = Grade(enrollment_id=enr.id, grade="B")'
            grade_assert = 'assert result.grade == "B"'
        else:
            grade_insert = 'g = Grade(enrollment_id=enr.id, grade_percentage=85.5)'
            grade_assert = 'assert result.grade_percentage == 85.5'

        test_models_py = textwrap.dedent(f"""\
            \"\"\"Partial tests for the school data model.

            NOTE: These tests check basic structure but do NOT verify all constraints,
            relationships, or indexes. The Planner has the full specification.
            \"\"\"
            import pytest
            from sqlalchemy import create_engine, inspect
            from sqlalchemy.orm import Session
            import datetime


            def get_engine():
                return create_engine("sqlite:///:memory:", echo=False)


            def test_models_importable():
                from models import Base, Student, Course, Enrollment, Grade
                assert Base is not None


            def test_tables_creatable():
                from models import Base
                engine = get_engine()
                Base.metadata.create_all(engine)
                insp = inspect(engine)
                tables = set(insp.get_table_names())
                assert "students" in tables
                assert "courses" in tables
                assert "enrollments" in tables
                assert "grades" in tables


            def test_student_insert():
                from models import Base, Student
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    s = Student(
                        first_name="Alice",
                        last_name="Smith",
                        student_id="S001",
                        email="alice@school.edu",
                    )
                    session.add(s)
                    session.commit()
                    result = session.get(Student, s.id)
                    assert result.student_id == "S001"


            def test_course_insert():
                from models import Base, Course
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    c = Course(
                        course_code="CS101",
                        title="Intro to CS",
                        credits=3,
                        capacity=30,
                        department="{sorted(selected_depts)[0]}",
                    )
                    session.add(c)
                    session.commit()
                    result = session.get(Course, c.id)
                    assert result.course_code == "CS101"


            def test_enrollment_and_grade():
                from models import Base, Student, Course, Enrollment, Grade
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    s = Student(first_name="B", last_name="C",
                                student_id="S002", email="b@school.edu")
                    c = Course(course_code="MATH101", title="Calculus",
                               credits=3, capacity=25, department="{sorted(selected_depts)[0]}")
                    session.add_all([s, c])
                    session.commit()
                    enr = Enrollment(student_id=s.id, course_id=c.id,
                                     enrolled_at=datetime.datetime.utcnow(),
                                     status="{grade_statuses[0]}")
                    session.add(enr)
                    session.commit()
                    {grade_insert}
                    session.add(g)
                    session.commit()
                    result = session.get(Grade, g.id)
                    {grade_assert}
        """)

        requirements_txt = "sqlalchemy\npytest\n"

        return GeneratedTask(
            task_id="SPEC3_data_model",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files={
                "models.py": models_py,
                "test_models.py": test_models_py,
                "requirements.txt": requirements_txt,
            },
        )

    # -----------------------------------------------------------------------
    # Domain 3: Project Management
    # -----------------------------------------------------------------------

    def _gen_project_mgmt(self, seed: int, rng: SeededRandom) -> GeneratedTask:
        username_max = rng.choice([40, 60, 100])
        project_name_max = rng.choice([100, 150, 200])
        task_title_max = rng.choice([100, 200, 300])
        comment_max = rng.choice([500, 1000, 2000])
        priorities = ["low", "medium", "high", "critical"]
        selected_priorities = rng.sample(priorities, rng.randint(3, 4))
        selected_priorities_sorted = [p for p in priorities if p in selected_priorities]
        task_statuses = ["todo", "in_progress", "review", "done", "cancelled"]
        selected_task_statuses = rng.sample(task_statuses, rng.randint(4, 5))
        selected_task_statuses_sorted = [s for s in task_statuses if s in selected_task_statuses]
        project_statuses = ["active", "on_hold", "completed", "archived"]

        expected = {
            "domain": "project_mgmt",
            "entities": ["User", "Project", "Task", "Comment"],
            "entity_count": 4,
            "relationships": [
                {"from": "Project", "to": "User", "type": "many_to_one"},
                {"from": "Task", "to": "Project", "type": "many_to_one"},
                {"from": "Task", "to": "User", "type": "many_to_one"},
                {"from": "Comment", "to": "Task", "type": "many_to_one"},
                {"from": "Comment", "to": "User", "type": "many_to_one"},
            ],
            "username_max": username_max,
            "project_name_max": project_name_max,
            "task_title_max": task_title_max,
            "comment_max": comment_max,
            "priorities": selected_priorities_sorted,
            "task_statuses": selected_task_statuses_sorted,
            "project_statuses": project_statuses,
            "not_null_fields": {
                "User": ["username", "email", "password_hash"],
                "Project": ["name", "owner_id", "status"],
                "Task": ["title", "project_id", "status"],
                "Comment": ["task_id", "author_id", "body"],
            },
            "unique_fields": {
                "User": ["username", "email"],
                "Project": ["name"],
            },
            "check_constraints": {
                "Task": [
                    f"priority IN ({', '.join(repr(p) for p in selected_priorities_sorted)})",
                    f"status IN ({', '.join(repr(s) for s in selected_task_statuses_sorted)})",
                ],
                "Project": [f"status IN ({', '.join(repr(s) for s in project_statuses)})"],
                "Comment": [f"length(body) <= {comment_max}"],
            },
            "indexes": [
                "projects.owner_id",
                "tasks.project_id",
                "tasks.assignee_id",
                "comments.task_id",
            ],
            "create_order": ["User", "Project", "Task", "Comment"],
        }

        priorities_str = ", ".join(f"'{p}'" for p in selected_priorities_sorted)
        task_statuses_str = ", ".join(f"'{s}'" for s in selected_task_statuses_sorted)
        project_statuses_str = ", ".join(f"'{s}'" for s in project_statuses)

        spec_md = f"""# SPEC3: Project Management Data Model — Entity-Relationship Specification

## Overview

Design and implement a relational data model for a project management tool.
Use SQLAlchemy ORM (declarative base). All models must be importable from `models.py`.

## Entities and Attributes

### User
Represents a registered team member.

| Column          | Type          | Constraints                                |
|-----------------|---------------|--------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                |
| username        | String({username_max}) | NOT NULL, UNIQUE                  |
| email           | String(255)   | NOT NULL, UNIQUE                           |
| password_hash   | String(255)   | NOT NULL                                   |
| display_name    | String(100)   | nullable                                   |
| created_at      | DateTime      | NOT NULL, default = current UTC time       |
| is_active       | Boolean       | NOT NULL, default = True                   |

### Project
Represents a project owned by a user.

| Column          | Type          | Constraints                                                     |
|-----------------|---------------|-----------------------------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                                     |
| name            | String({project_name_max}) | NOT NULL, UNIQUE                             |
| description     | Text          | nullable                                                        |
| owner_id        | Integer       | NOT NULL, FK → User.id ON DELETE RESTRICT                       |
| status          | String(20)    | NOT NULL, CHECK (status IN ({project_statuses_str}))            |
| created_at      | DateTime      | NOT NULL, default = current UTC time                            |
| due_date        | Date          | nullable                                                        |

### Task
Represents a work item within a project.

| Column          | Type          | Constraints                                                           |
|-----------------|---------------|-----------------------------------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                                           |
| title           | String({task_title_max}) | NOT NULL                                                 |
| description     | Text          | nullable                                                              |
| project_id      | Integer       | NOT NULL, FK → Project.id ON DELETE CASCADE                           |
| assignee_id     | Integer       | nullable, FK → User.id ON DELETE SET NULL                             |
| priority        | String(20)    | NOT NULL, CHECK (priority IN ({priorities_str})), default = 'medium'  |
| status          | String(20)    | NOT NULL, CHECK (status IN ({task_statuses_str})), default = 'todo'   |
| due_date        | Date          | nullable                                                              |
| created_at      | DateTime      | NOT NULL, default = current UTC time                                  |

### Comment
Represents a comment on a task.

| Column          | Type          | Constraints                                                      |
|-----------------|---------------|------------------------------------------------------------------|
| id              | Integer       | PRIMARY KEY, auto-increment                                      |
| task_id         | Integer       | NOT NULL, FK → Task.id ON DELETE CASCADE                         |
| author_id       | Integer       | NOT NULL, FK → User.id ON DELETE RESTRICT                        |
| body            | Text          | NOT NULL, CHECK (length(body) <= {comment_max})                  |
| created_at      | DateTime      | NOT NULL, default = current UTC time                             |
| updated_at      | DateTime      | NOT NULL, default = current UTC time                             |

## Relationships

| Relationship               | Cardinality  | Details                                        |
|----------------------------|--------------|------------------------------------------------|
| User → Projects (owned)    | One-to-Many  | User.id ← Project.owner_id                     |
| Project → Tasks            | One-to-Many  | Project.id ← Task.project_id                   |
| User → Tasks (assigned)    | One-to-Many  | User.id ← Task.assignee_id (nullable)          |
| Task → Comments            | One-to-Many  | Task.id ← Comment.task_id                      |
| User → Comments (authored) | One-to-Many  | User.id ← Comment.author_id                    |

## Index Requirements

- `projects.owner_id`
- `tasks.project_id`
- `tasks.assignee_id`
- `comments.task_id`

## CREATE TABLE Order

1. `users` (no dependencies)
2. `projects` (depends on users)
3. `tasks` (depends on projects, users)
4. `comments` (depends on tasks, users)

## Implementation Notes

- Use `from sqlalchemy import ...` and `from sqlalchemy.orm import declarative_base`
- Define `Base = declarative_base()` at the top of `models.py`
- Each class must inherit from `Base`
- `__tablename__` values: `users`, `projects`, `tasks`, `comments`
- Export `Base`, `User`, `Project`, `Task`, `Comment` from `models.py`
"""

        brief_md = """# SPEC3: Project Management Data Model (Executor Brief)

Implement the data model for the project management application. The Planner has
the detailed schema including all entity definitions, constraints, and relationships.

The workspace contains:
- `models.py` — empty; you must implement all entity classes here
- `test_models.py` — partial test suite (does not cover all constraints)

Install dependencies: `pip install sqlalchemy pytest`

Run tests with: `python -m pytest test_models.py -v`
"""

        models_py = '# models.py — implement the project management data model here\n'

        test_models_py = textwrap.dedent(f"""\
            \"\"\"Partial tests for the project management data model.

            NOTE: These tests check basic structure but do NOT verify all constraints,
            relationships, or indexes. The Planner has the full specification.
            \"\"\"
            import pytest
            from sqlalchemy import create_engine, inspect
            from sqlalchemy.orm import Session


            def get_engine():
                return create_engine("sqlite:///:memory:", echo=False)


            def test_models_importable():
                from models import Base, User, Project, Task, Comment
                assert Base is not None


            def test_tables_creatable():
                from models import Base
                engine = get_engine()
                Base.metadata.create_all(engine)
                insp = inspect(engine)
                tables = set(insp.get_table_names())
                assert "users" in tables
                assert "projects" in tables
                assert "tasks" in tables
                assert "comments" in tables


            def test_user_insert():
                from models import Base, User
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    u = User(
                        username="devuser",
                        email="dev@example.com",
                        password_hash="hashed_pw",
                    )
                    session.add(u)
                    session.commit()
                    result = session.get(User, u.id)
                    assert result.username == "devuser"


            def test_project_links_to_user():
                from models import Base, User, Project
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    u = User(username="owner", email="owner@x.com", password_hash="pw")
                    session.add(u)
                    session.commit()
                    p = Project(name="Alpha Project", owner_id=u.id, status="{project_statuses[0]}")
                    session.add(p)
                    session.commit()
                    result = session.get(Project, p.id)
                    assert result.owner_id == u.id


            def test_task_links_to_project():
                from models import Base, User, Project, Task
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    u = User(username="tm", email="tm@x.com", password_hash="pw")
                    session.add(u)
                    session.commit()
                    p = Project(name="Beta Project", owner_id=u.id, status="{project_statuses[0]}")
                    session.add(p)
                    session.commit()
                    t = Task(
                        title="Implement feature",
                        project_id=p.id,
                        priority="{selected_priorities_sorted[0]}",
                        status="{selected_task_statuses_sorted[0]}",
                    )
                    session.add(t)
                    session.commit()
                    assert t.project_id == p.id


            def test_comment_links_to_task_and_user():
                from models import Base, User, Project, Task, Comment
                engine = get_engine()
                Base.metadata.create_all(engine)
                with Session(engine) as session:
                    u = User(username="commenter", email="c@x.com", password_hash="pw")
                    session.add(u)
                    session.commit()
                    p = Project(name="Gamma Project", owner_id=u.id, status="{project_statuses[0]}")
                    session.add(p)
                    session.commit()
                    t = Task(title="Do work", project_id=p.id,
                             priority="{selected_priorities_sorted[0]}",
                             status="{selected_task_statuses_sorted[0]}")
                    session.add(t)
                    session.commit()
                    c = Comment(task_id=t.id, author_id=u.id, body="Looks good!")
                    session.add(c)
                    session.commit()
                    result = session.get(Comment, c.id)
                    assert result.body == "Looks good!"
        """)

        requirements_txt = "sqlalchemy\npytest\n"

        return GeneratedTask(
            task_id="SPEC3_data_model",
            seed=seed,
            spec_md=spec_md,
            brief_md=brief_md,
            expected=expected,
            workspace_files={
                "models.py": models_py,
                "test_models.py": test_models_py,
                "requirements.txt": requirements_txt,
            },
        )
