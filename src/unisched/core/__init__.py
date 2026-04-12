"""
Application core for scheduling orchestration and optimizer execution.

This package is responsible for application flow, not low-level I/O parsing and
not GUI concerns.

Planned files and responsibilities:
- `schema.py`
    - Define canonical tabular schema and normalization helpers used at boundaries.
- `optimizers/base.py`
    - Define `BaseOptimizer` interface: `schedule(data: DataFrame) -> Schedule`.
- `optimizers/graph_coloring.py`
    - First production optimizer adapted from the previous prototype.
- `optimizers/simulated_annealing.py`
    - Metaheuristic optimizer for local/global schedule improvements.
- `optimizers/ilp.py`
    - Integer linear programming optimizer for exact/near-exact solutions.
- `coordinator.py`
    - Scheduling pipeline coordinator: preprocess, optimize, post-validate.
- `constraints_service.py`
    - Cross-cutting rule checks using domain constraints.
- `interactive.py`
    - Manual adjustment handlers such as move-and-resolve operations.
- `hall_allocation.py`
    - Hall assignment algorithms and utilization strategies.

Planned main classes:
- `BaseOptimizer`
- `GraphColoringOptimizer`
- `SimulatedAnnealingOptimizer`
- `ILPOptimizer`
- `SchedulingCoordinator`
"""
