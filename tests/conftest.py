# SPDX-License-Identifier: MIT
"""The markers that split the tests into the sets CI runs apart.

- ``models``: a test that reads a board model (``tests/test_board_model_legends.py``),
  run when a model's inputs change;
- ``selftest``: a checker's own test, planting defects it must catch, or a
  fixture rebuilt from its sources; slow, run when a checker or its fixtures
  change, weekly and on demand.

``.github/workflows/check.yml`` selects them with ``-m``; ``docs/models-and-drawings.md``,
"Tests and CI", says which job runs which.
"""
from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "models: reads a board model; run when a model's inputs change")
    config.addinivalue_line("markers", "selftest: a checker's planted-defect selftest or a fixture "
                                       "rebuild; slow, run when a checker or its fixtures change")
