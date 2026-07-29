Run the full Python test suite UNPIPED and report the REAL exit code.

Piping pytest through `tail`/`head`/`|` makes `$?` report the pipe's exit, not
pytest's — this repo has been bitten by that. Never do it. Run directly:

    .venv/Scripts/python.exe -m pytest

Then read the summary line (`N passed` / `N failed`) and report the true
pass/fail counts plus the exit code. If anything failed, list the failing test
node IDs. Do not claim green off a piped exit code.
