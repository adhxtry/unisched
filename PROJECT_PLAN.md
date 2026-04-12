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
2. **`unisched.core`**: Handles app-level flow. It runs scheduling steps, connects optimizers, checks scheduling constraints, and exposes a clean API.
3. **`unisched.io`**: Handles input/output. Reads files (CSV, Excel, etc.), normalizes schema, and converts data to/from pandas `DataFrame`.
4. **`unisched.gui`**: The UI layer (MVVM). It only handles interaction and display, and calls `core` for scheduling logic.

### Simple Dependency Rule
The dependency direction is:
- `domain` depends on nothing else.
- `core` depends on `domain`.
- `io` and `gui` depend on `core`.
- `io` may map file data into domain models before handing it to `core`.
- Models and scheduling rules stay in `domain`, app flow stays in `core`, and file/UI concerns stay in `io`/`gui`.
- `io` handles file/schema validation, while `core` and `domain` handle scheduling checks.

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
    gui --> io : invokes
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

### API Usage Flow
The library API should feel simple to use. First, the user gives the data to `io`, then `core` prepares the schedule using the chosen optimizer, and finally the result comes back as a schedule or a clash report. The API should hide the internal steps so the user only sees a clear start point and a clear output.

Example flow:
- load exam and student data
- normalize the input into a common format
- choose an optimizer
- generate the schedule
- check the result and return it

```mermaid
sequenceDiagram
    actor User
    participant API as Library API
    participant IO as io layer
    participant CORE as core layer
    participant DOMAIN as domain layer

    User->>API: Give input files and settings
    API->>IO: Read and normalize data
    IO-->>API: Clean data
    API->>CORE: Start scheduling step
    CORE->>DOMAIN: Check rules and constraints
    DOMAIN-->>CORE: Valid rules / conflict details
    CORE-->>API: Schedule result
    API-->>User: Return schedule or clash report
```


### Interactive GUI
The GUI should also be able to make small updates after a schedule is already built. For example, the user may move one exam to a new date or switch it to another hall. The core part of the library should then recheck the schedule, fix any clash if possible, and return the updated result.

Possible actions:
- move one course to a new date
- change the hall for one exam
- recheck clashes after each change
- return either an updated schedule or a problem report

```mermaid
sequenceDiagram
    actor User
    participant GUI as GUI
    participant API as Library API
    participant CORE as core layer
    participant DOMAIN as domain layer

    User->>GUI: Open the current schedule
    GUI->>API: Ask for a change
    API->>CORE: Send the change request
    CORE->>DOMAIN: Check rules and clashes
    DOMAIN-->>CORE: Valid result or conflict details
    CORE-->>API: Updated schedule or report
    API-->>GUI: Show the result

    alt not_resolvable
        API-->>GUI: Show the issue
        GUI-->>User: Ask for another choice
    else success
        API-->>GUI: Show the updated schedule
        GUI-->>User: Refresh the view
    end
```

## Goals

### Logging
- Implement a logging system to track the scheduling process and any issues that arise.

### Foundation & Data Pipeline
- Define main entities and rules in `domain`.
- Implement the `io` module to read various formats and normalize into `pandas.DataFrame`.
- Support csv, Excel and ODS input formats.
- Implement schema validation and structural boundaries.

### Optimizer Framework & Graph Coloring
- Create the `BaseOptimizer` interface in `core`.
- Implement the `GraphColoringOptimizer` as the first concrete algorithm (adapting the logic from my old project with Dr. Prafullkumar Tale but in the new structure).
- Implement the baseline hall allocation algorithm.

### Advanced Optimizers & Hall Allocation
- Add `SimulatedAnnealingOptimizer` and `ILPOptimizer`.
- Refine the optimal hall allotting algorithm for better utilization and less fragmentation.

### Core Services for Interactivity
- Implement `core` scheduling steps for manual changes.
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
