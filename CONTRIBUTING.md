# Contributing

Thanks for your interest in contributing to llm-markdown-tools.

## Ways to contribute

- report bugs
- suggest features or UX improvements
- improve documentation
- submit fixes and tests
- help review pull requests

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
```

## Running tests

```bash
pytest
```

## Code style

- keep changes focused and small
- prefer clear function and variable names
- add or update tests for behavior changes
- do not add network calls in unit tests

## Pull request checklist

- tests pass locally
- documentation updated if behavior changes
- changelog entry added if relevant
- no secrets or personal environment values committed

## Reporting issues

Please include:

- steps to reproduce
- expected behavior
- actual behavior
- relevant environment details
- any sample input/output that is safe to share

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
