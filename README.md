[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/TNdrCHth)

<center>

# Unisched - Extensible University Exam Scheduler

![GUI Image](public/gui.png)

</center>

---

This is my (Adheesh Trivedi's) submission for the course "Advanced Programming".

**Unisched** is a basic, modular exam scheduling project that currently supports:

- Registration data loading from CSV, Excel and ODS
- Exam hall data loading from CSV, Excel and ODS
- Core scheduling using a graph coloring optimizer (DSatur-based)
- Conflict-aware schedule generation with simple penalty calculation
- A native-desktop GUI built with PySide6

The project is intentionally minimal and designed to be extended over time.

## Installation

### From PyPI

```bash
pip install unisched

# Then run the app
python -m unisched
```

It's recommended to use `pipx` for better dependency resolution:

```bash
pipx install unisched

# Then run the app
unisched
```

### Running from source

- Python 3.12
- [`uv` package manager](https://github.com/astral-sh/uv)

Dependencies used by the project:

- pandas
- PySide6
- openpyxl
- odfpy

Install dependencies:

```bash
uv sync
```

Run the GUI app:

```bash
uv run unisched
```

### Running Tests

Run all tests:

```bash
uv sync --extra dev
uv run pytest
```

### Example Script

Run the sample scheduling script:

```bash
uv sync --extra example
uv run python examples/schedule.py
```

## TODOs

- Current optimizer implementation: GraphColoringOptimizer only
- Future optimizers (for later): Simulated Annealing, ILP
- Needs a cute logo for the GUI :)
