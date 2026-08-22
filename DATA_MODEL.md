# Data Model Reference

Auto-generated from the SQLAlchemy models in `backend/app/models/`.

## Conventions

- **PK** = primary key, **FK** = foreign key, **UQ** = unique, **IX** = indexed.
- All UUID PKs use the Postgres `UUID` type.
- `created_at` / timestamp columns with `server_default=func.now()` default to the DB time at insert.
- Column types shown are the SQLAlchemy types; they map to Postgres (e.g. `String(n)` → `VARCHAR(n)`, `JSONB` → `JSONB`, `Text` → `TEXT`).
- Enums are stored as Postgres enum types via `SQLEnum(Enum, name="<pg_enum_name>")`.

---

## Table: `applicants` — `Applicant`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `applicant_id` | `UUID` | no | — | PK | |
| `campus_id` | `String(9)` | no | — | UQ, IX | |
| `employee_id` | `String(7)` | no | — | UQ, IX | Generated alongside campus ID |
| `first_name` | `String(255)` | no | — | | |
| `last_name` | `String(255)` | no | — | | |
| `sex` | `String(255)` | no | — | | Author note: possibly should be an enum |
| `cell_phone` | `String(255)` | no | — | UQ | |
| `home_phone` | `String(255)` | no | — | UQ | |
| `email` | `String(255)` | no | — | UQ | |
| `population_group` | `String(15)` | no | — | | |
| `birth_date` | `Date` | no | — | | |
| `citizenship_residency` | `String(255)` | no | — | | Author note: possibly should be an enum |
| `non_sa_citizenship` | `String(3)` | no | — | IX | Indexed for citizenship filtering |
| `created_at` | `DateTime(tz)` | no | `func.now()` | | |

**Relationships**: `applications`, `applicant_marks`, `notes` (all `cascade="all, delete-orphan"`), `motivation` (one-to-one).

---

## Table: `applications` — `Application`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `application_id` | `UUID` | no | — | PK | |
| `application_number` | `String(8)` | no | — | UQ, IX | |
| `campus_id` | `String` | no | — | FK → `applicants.campus_id`, IX | |
| `academic_program_code` | `String(10)` | no | — | | |
| `academic_plan1` | `String(255)` | no | — | | |
| `academic_plan2` | `String(255)` | yes | — | | Author note: may be removable |
| `choice` | `SQLEnum(Choice, name="choice")` | no | — | IX | Enum: `first`, `second` |
| `admit_type` | `SQLEnum(AdmitType, name="admit_types")` | yes | — | | Enum: `new`, `npg`, `uct`, `con`, `rem`, `rad` |
| `semester` | `SQLEnum(Semester, name="semester")` | no | — | | Enum: `first`, `second` |
| `application_date` | `DateTime(tz)` | yes | — | IX | No default |
| `effective_date` | `DateTime(tz)` | yes | — | IX | No default |
| `application_status` | `SQLEnum(ApplicationStatus, name="application_status")` | no | — | IX | Enum: `applied`, `reviewed`, `conditionally accepted`, `accepted`, `ready to register`, `firm offer`, `deny: requirements not met`, `deny: not competitive`, `deny: requirements not met (duplicate application)` |
| `last_registration` | `DateTime(tz)` | yes | — | | |
| `application_term` | `DateTime(tz)` | no | — | | |
| `previous_application_term` | `DateTime(tz)` | yes | — | | |
| `import_run_id` | `UUID` | no | — | FK → `import_runs.import_run_id` | |
| `created_at` | `DateTime(tz)` | no | `func.now()` | | |

**Relationships**: `applicant` (many-to-one), `votes` (`cascade="all, delete-orphan"`).

---

## Table: `users` — `User`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `user_id` | `UUID` | no | — | PK | |
| `employee_id` | `String(7)` | no | — | UQ, IX | |
| `first_name` | `String(255)` | no | — | | |
| `last_name` | `String(255)` | no | — | | |
| `email` | `String(255)` | no | — | UQ | |
| `role` | `String(255)` | yes | — | | Null = awaiting approval (see `RoleEnum`) |
| `approved_at` | `DateTime(tz)` | yes | `func.now()` (on update) | | `onupdate=func.now()` |
| `approved_by` | `String` | yes | — | FK → `users.employee_id` | |
| `created_at` | `DateTime(tz)` | no | `func.now()` | | |

**Relationships**: `notes`, `votes`.

---

## Table: `notes` — `Note`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `note_id` | `UUID` | no | — | PK | |
| `campus_id` | `String` | no | — | FK → `applicants.campus_id`, IX | |
| `author_id` | `String` | no | — | FK → `users.employee_id` | |
| `content` | `Text` | no | — | | |
| `created_at` | `DateTime(tz)` | yes | `func.now()` | | No `nullable=False` |

**Relationships**: `applicant`, `author`.

---

## Table: `documents` — `Documents`

> Not exported from `app/models/__init__.py`.

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `document_id` | `UUID` | no | — | PK | |
| `applicant_id` | `UUID` | no | — | FK → `applicants.applicant_id`, IX | |
| `storage_key` | `UUID` | no | — | | |
| `orginal_file_name` | `String(255)` | no | — | | Typo in model: `orginal` |
| `content_type` | `String(255)` | no | — | | |
| `sha256_hash` | `String(64)` | no | — | UQ | |
| `uploaded_at` | `DateTime(tz)` | no | `func.now()` | | |

---

## Table: `votes` — `Vote`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `vote_id` | `UUID` | no | — | PK | |
| `application_number` | `String` | no | — | FK → `applications.application_number`, IX | |
| `campus_id` | `String` | no | — | FK → `applicants.campus_id` | |
| `vote` | `SQLEnum(VoteDecision, name="vote_decision")` | no | — | | Placeholder enum: `placeholder` |
| `voter_id` | `String` | no | — | FK → `users.employee_id` | |
| `voted_at` | `DateTime` | no | `func.now()` | | No timezone |

**Relationships**: `application`, `voter`.

---

## Table: `system_logs` — `SystemLog`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `log_id` | `UUID` | no | — | PK | |
| `entity_name` | `String(50)` | no | — | IX | |
| `entity_id` | `UUID` | no | — | | Loose reference (not a FK) |
| `old_data` | `JSONB` | yes | — | | |
| `new_data` | `JSONB` | yes | — | | |
| `changed_by` | `String` | no | — | FK → `users.employee_id` | |
| `changed_at` | `DateTime(tz)` | no | `func.now()` | | |
| `reason` | `SQLEnum(ChangeSource, name="change_source")` | yes | — | | Enum: `import`, `manual_edit`, `merge_resolution`, `rules_calc`, `decision` |
| `import_run_id` | `UUID` | yes | — | | Not a FK |

---

## Table: `staging` — `Staging`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `staging_id` | `UUID` | no | — | PK | |
| `import_run_id` | `UUID` | no | — | FK → `import_runs.import_run_id` | |
| `entity` | `String(50)` | no | — | | Identifies target table for insertion |
| `raw_data` | `JSONB` | no | — | | |
| `normalized_data` | `JSONB` | no | — | | |
| `validation_status` | `SQLEnum(ValidationStatus, name="validation_status")` | no | — | | Enum: `valid`, `rejected` |
| `rejection_reason` | `Text` | yes | — | | |
| `matched_application_id` | `String` | yes | — | FK → `applications.application_number` | |
| `matched_campus_id` | `String` | yes | — | FK → `applicants.campus_id` | |

---

## Table: `motivations` — `Motivation`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `motivation_id` | `UUID` | no | — | PK | |
| `campus_id` | `String` | no | — | FK → `applicants.campus_id`, UQ | |
| `last_name` | `String(255)` | no | — | | |
| `first_name` | `String(255)` | no | — | | |
| `motivation` | `Text` | no | — | | |

**Relationships**: `applicant` (one-to-one).

---

## Table: `matching_reviews` — `MatchingReview`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `match_id` | `UUID` | no | — | PK | |
| `staging_row_id` | `UUID` | no | — | FK → `staging.staging_id` | |
| `candidate_keys` | `JSON` | yes | — | | |
| `match_signals` | `JSON` | yes | — | | What matched |
| `status` | `SQLEnum(MatchStatus, name="match_status")` | no | `MatchStatus.PENDING` | | Enum: `pending`, `resolved` |
| `resolved_by` | `String` | no | — | FK → `users.employee_id` | |
| `resolution` | `SQLEnum(MatchResolution)` | yes | — | | No `name` arg; enum: `merge`, `reject` |
| `reason` | `Text` | yes | — | | |
| `resolved_at` | `DateTime(tz)` | yes | `datetime.now(UTC)` (on update) | | `onupdate=lambda: datetime.now(UTC)` |

---

## Table: `academic_plans` — `AcademicPlan`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `academic_plan_id` | `UUID` | no | — | PK | |
| `academic_plan` | `String(5)` | no | — | UQ, IX | |
| `department_code` | `String` | no | — | FK → `department_codes.department_code` | |

---

## Table: `import_runs` — `ImportRun`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `import_run_id` | `UUID` | no | — | PK | |
| `source_type` | `SQLEnum(SourceType, name="source_types")` | no | — | IX | Enum: `asr`, `uct_marks`, `motivations`, `it_transcripts` |
| `uploaded_by` | `String` | no | — | FK → `users.employee_id` | |
| `uploaded_at` | `DateTime(tz)` | no | `func.now()` | | |
| `file_name` | `String(255)` | no | — | | |
| `status` | `SQLEnum(ImportStatus, name="import_status")` | no | `ImportStatus.PENDING` | IX | Enum: `pending`, `processing`, `completed`, `failed` |
| `rows_total` | `Integer` | no | — | | |
| `rows_loaded` | `Integer` | no | `0` | | |
| `rows_rejected` | `Integer` | no | `0` | | |
| `rows_auto_matched` | `Integer` | no | `0` | | |
| `rows_auto_new` | `Integer` | no | `0` | | |
| `rows_flagged` | `Integer` | no | `0` | | |

---

## Table: `courses` — `Course`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `course_id` | `UUID` | no | — | PK | |
| `department_code` | `String(3)` | no | — | IX | |
| `course_code` | `String(8)` | no | — | UQ, IX | |
| `course_name` | `String(255)` | yes | — | | |

> A commented-out `academic_program_code` FK exists in the model source.

---

## Table: `applicant_marks` — `ApplicantMark`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `mark_id` | `UUID` | no | — | PK | |
| `campus_id` | `String` | no | — | FK → `applicants.campus_id` | |
| `course_code` | `String(8)` | no | — | IX | |
| `mark` | `Float` | no | — | | |
| `created_at` | `DateTime(tz)` | no | `func.now()` | IX | |

**Check constraint**: `course_mark_constraint` → `mark >= 0 AND mark <= 100`.

**Relationships**: `applicant`.

---

## Table: `department_codes` — `DepartmentCode`

| Column | Type | Nullable | Default | Key / Index | Notes |
| --- | --- | --- | --- | --- | --- |
| `academic_program_id` | `UUID` | no | — | PK | |
| `academic_program_code` | `String(3)` | no | — | UQ, IX | |
| `academic_program` | `String(255)` | yes | — | | Program name |

---

## Enums Summary

| Python enum | PG type name | Values |
| --- | --- | --- |
| `Choice` | `choice` | `first`, `second` |
| `Semester` | `semester` | `first`, `second` |
| `AdmitType` | `admit_types` | `new`, `npg`, `uct`, `con`, `rem`, `rad` |
| `ApplicationStatus` | `application_status` | `applied`, `reviewed`, `conditionally accepted`, `accepted`, `ready to register`, `firm offer`, `deny: requirements not met`, `deny: not competitive`, `deny: requirements not met (duplicate application)` |
| `RoleEnum` | *(unused — `role` stored as `String`)* | `admin`, `convenor`, `committee` |
| `VoteDecision` | `vote_decision` | `placeholder` |
| `ChangeSource` | `change_source` | `import`, `manual_edit`, `merge_resolution`, `rules_calc`, `decision` |
| `ValidationStatus` | `validation_status` | `valid`, `rejected` |
| `MatchStatus` | `match_status` | `pending`, `resolved` |
| `MatchResolution` | *(no name arg)* | `merge`, `reject` |
| `SourceType` | `source_types` | `asr`, `uct_marks`, `motivations`, `it_transcripts` |
| `ImportStatus` | `import_status` | `pending`, `processing`, `completed`, `failed` |
