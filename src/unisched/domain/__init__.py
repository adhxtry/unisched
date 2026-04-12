"""
Domain layer for exam scheduling entities, value objects, and rule semantics.

This package should remain pure business logic and should not depend on `core`,
`io`, or `gui`.

Planned files and responsibilities:
- `course.py`
    - `Course` entity and course-level metadata used in exam planning.
- `student.py`
    - `Student` entity and registration relationships.
- `exam_hall.py`
    - `ExamHall` entity with capacity and hall constraints.
- `timeslot.py`
    - `TimeSlot` value object and temporal validation rules.
- `exam.py`
    - `Exam` aggregate linking course, slot, and hall assignment.
- `schedule.py`
    - `Schedule` aggregate and convenience query/update operations.
- `constraints.py`
    - Constraint abstractions and concrete rule definitions.
- `conflicts.py`
    - Conflict descriptors and clash report models.

Planned main classes:
- `Course`
- `Student`
- `ExamHall`
- `TimeSlot`
- `Exam`
- `Schedule`
- `Constraint` (base abstraction)
- Domain-specific conflict/result models
"""
