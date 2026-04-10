# Unisched Implementation Project Plan

## Objective and Scope

The goal of this project is to create a university exam scheduler framework in a highly structured, scalable, and modern Python library and application. The project strictly adheres to Object-Oriented Programming (OOP) principles, emphasizing modularity, extensibility, and maintainability.

### Core Features
- **Generic Data Pipeline**: Standardized file reading, bringing all inputs into a single format (pandas `DataFrame` instead of raw graph structures for data handling) utilized by the entire library.
- **Pluggable Optimizer Architecture**: An extensible approach utilizing inheritance to support multiple scheduling algorithms.
- **Advanced Hall Allocation**: Dedicated algorithms to optimally assign lecture halls.
- **Stable Public API**: A well-documented interface for advanced users to leverage the package programmatically.
- **Modern Responsive GUI**: A clean, MVVM-based graphical interface with real-time interactive scheduling adjustments supported by the core library.

## Architectural Design

I want to use a simple layered architecture. The idea is to separate data models, application flow, file handling, and UI so each part is easy to understand, test, and change.

### Core Modules
1. **`unisched.domain`**: Contains the main exam scheduling concepts and rules. This includes models like `Course`, `Student`, `ExamHall`, `TimeSlot`, `Schedule`, and `Constraint`.
2. **`unisched.core`**: Handles app-level flow. It runs scheduling steps, connects optimizers, validates data, and exposes a clean API.
3. **`unisched.io`**: Handles input/output. Reads files (CSV, Excel, etc.), normalizes schema, and converts data to/from pandas `DataFrame`.
4. **`unisched.gui`**: The UI layer (MVVM). It only handles interaction and display, and calls `core` for scheduling logic.

### Simple Dependency Rule
The dependency direction is:
- `domain` depends on nothing else.
- `core` depends on `domain`.
- `io` and `gui` depend on `core`.
- Models and validation rules stay in `domain`, app flow stays in `core`, and file/UI concerns stay in `io`/`gui`.

```mermaid
classDiagram
    class domain {
        +Entities
        +ValueObjects
        +ValidationRules
        +Constraints
    }

    class core {
        +Optimizers
        +SchedulingCoordinator
    }

    class io {
        +FileReaders
        +SchemaNormalization
        +DataFrameMappers
    }

    class gui {
        +Model
        +UiAction
        +View
        +ViewModel
    }

    core --> domain : uses
    io --> core : invokes
    gui --> core : invokes
    io --> domain : maps
```

### Optimizer Architecture (OOP)
A base `BaseOptimizer` class will define the interface for all scheduling algorithms. This ensures extensibility.

* **BaseOptimizer** (Abstract Base Class)
    * `GraphColoringOptimizer`
    * `SimulatedAnnealingOptimizer`
    * `ILPOptimizer` (Integer Linear Programming)

```mermaid
classDiagram
    class BaseOptimizer {
        <<abstract>>
        +schedule(data: DataFrame) Schedule
    }

    class GraphColoringOptimizer {
        +schedule(data: DataFrame) Schedule
    }
    class SimulatedAnnealingOptimizer {
        +schedule(data: DataFrame) Schedule
    }
    class ILPOptimizer {
        +schedule(data: DataFrame) Schedule
    }

    BaseOptimizer <|-- GraphColoringOptimizer
    BaseOptimizer <|-- SimulatedAnnealingOptimizer
    BaseOptimizer <|-- ILPOptimizer
```


### Interactive GUI and Core Support
To support on-the-fly updates, the core library will provide specific service methods:
- `move_course_and_resolve(course_id, new_date)`: Moves a course and attempts to rearrange others to resolve student clashes.
- `reassign_hall_and_resolve(course_id, new_hall_id)`: Changes a hall and rearranges to resolve hall capacity/overlap clashes.

```mermaid
sequenceDiagram
    actor User
    participant GUI as GUI (View/Controller)
    participant API as Core Library API
    participant Engine as Optimization Engine

    User->>GUI: Select Registration file, define schema
    GUI->>API: load_data(file_path, schema)
    User->>GUI: Setup constraints and preferences
    GUI->>API: set_constraints(constraints)
    API->>Engine: apply_constraints(constraints)
    Engine-->>API: Ready for Scheduling
    User->>GUI: Select Optimizer, Trigger Schedule Generation
    GUI->>API: generate_schedule(optimizer_type)
    API->>Engine: run_optimizer(optimizer_type)
    Engine-->>API: Generated Schedule + Conflict Report
    API-->>GUI: Render Schedule + Conflict Details

    User->>GUI: Move Course to New Date
    GUI->>API: update_schedule(course_id, new_date)
    API->>Engine: resolve_student_clashes(course_id)
    Engine-->>API: Updated Schedule / Conflicts

    alt not_resolvable
        API-->>GUI: Reject + Diagnostic Details
        GUI-->>User: Prompt for resolution/Undo
    else success
        API-->>GUI: Updated Schedule
        GUI-->>User: Render Updated Schedule
    end
```

## Goals

### Foundation & Data Pipeline
- Define main entities and rules in `domain`.
- Implement the `io` module to read various formats and normalize into `pandas.DataFrame`.
- Implement schema validation and structural boundaries.

### Optimizer Framework & Graph Coloring
- Create the `BaseOptimizer` interface in `core`.
- Implement the `GraphColoringOptimizer` as the first concrete algorithm (adapting the logic from my old project with Dr. Prafullkumar Tale but in the new structure).
- Implement the baseline hall allocation algorithm.

### Advanced Optimizers & Hall Allocation
- Add `SimulatedAnnealingOptimizer` and `ILPOptimizer`.
- Refine the optimal hall allotting algorithm for better utilization and less fragmentation.

### Core Services for Interactivity
- Implement `core` use-cases for manual changes.
- Implement clash detection and automatic localized conflict resolution (`move_course_and_resolve`).

### Stable API & Documentation
- Define and expose the public API for the library.
- Add comprehensive docstrings and type hinting.
- Ensure the library operates smoothly head-less (without GUI).

### Modern GUI Implementation
- Set up the MVVM architecture for the `gui` module.
- Build a responsive interface (e.g., using PyQt6/PySide6, CustomTkinter, or a web-based UI).
- Integrate the GUI with the core API to support visualization and drag-and-drop/on-the-fly updates.


## Final Note
All the functions are just for demonstration purposes and are not actual implementations. The project will be developed iteratively, with continuous testing and refactoring to ensure a robust and maintainable codebase.
