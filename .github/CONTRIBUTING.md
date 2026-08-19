# Contributing to CISON CLI

Thank you for contributing to the CISON Command Line Interface. Follow this guide to set up your environment and submit contributions.

## Development Environment Setup

1. **Install `uv`** (Fast Python package manager):
   ```bash
   curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

   ```

2. **Clone and setup virtual environment**:
   ```bash
   git clone git@github.com:CISON-Official/cli.git
   cd cli
   uv sync

   ```


3. **Install editable local build**:
   ```bash
   uv tool install --editable .

   ```



## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name

   ```


2. Verify code quality using `ruff`:
   ```bash
   uv run ruff check .
   uv run ruff format .

   ```


3. Test configuration and local command execution:
   ```bash
   cison configure
   cison config show

   ```


4. Commit changes using structured messages:
* `feat:` for new capabilities
* `fix:` for bug fixes
* `docs:` for documentation updates
* `refactor:` for code restructures


5. Push branch and open a Pull Request against `main`.
