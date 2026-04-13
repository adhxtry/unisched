[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/TNdrCHth)

<center>

# Unisched - Extensible University Exam Scheduler

![GUI Image](public/gui.png)

</center>

---

This is my (Adheesh Trivedi's) submission for the course "Advanced Programming".

Unisched is a basic, modular exam scheduling project that currently supports:

- Registration data loading from CSV, Excel, and ODS
- Core scheduling using a graph coloring optimizer (DSatur-based)
- Conflict-aware schedule generation with simple penalty calculation
- A desktop GUI built with PySide6

The project is intentionally minimal and designed to be extended over time.

## Current Architecture

- `unisched.io`: file handling and registration-data loading
- `unisched.domain`: schedule models and conflict/penalty helpers
- `unisched.core`: coordinator and optimizer interfaces/implementations
- `unisched.gui`: desktop user interface

## GUI Screenshot

Add your screenshot here later:

![GUI Screenshot Placeholder](docs/gui-screenshot-placeholder.png)

## Requirements

- Python 3.12
- `uv` package manager

Dependencies used by the project:

- pandas
- PySide6
- openpyxl
- odfpy

## Quick Start

Install dependencies:

```bash
uv sync
```

Run the GUI app:

```bash
uv run python -m unisched
```

## Running Tests

Run all tests:

```bash
uv run pytest
```

## Example Script

Run the sample scheduling script:

```bash
uv run python examples/schedule.py
```

## Notes

- Current optimizer implementation: GraphColoringOptimizer only
- Future optimizers (for later): Simulated Annealing, ILP
- GUI tests are currently not included