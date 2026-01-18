# Usage Examples

Concrete, real-world examples of using the uv plugin to manage Python projects.

## Example 1: Create a REST API with FastAPI

**Scenario**: You need to create a new REST API application using FastAPI with proper testing and linting tools.

**Steps**:

1. Initialize a new application project
2. Add FastAPI and dependencies
3. Add development tools
4. Create the application structure
5. Run and test the application

**Commands**:

```bash
# Initialize application
uv init fastapi-demo --app
cd fastapi-demo

# Add production dependencies
uv add fastapi uvicorn 'pydantic>=2.0' sqlalchemy 'python-jose[cryptography]' passlib

# Add development dependencies
uv add --dev pytest pytest-asyncio pytest-cov httpx ruff mypy black

# Sync environment
uv sync

# Run the application
uv run uvicorn main:app --reload --port 8000

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run mypy .
```

**Result**: A fully configured FastAPI application with dependencies locked in `uv.lock`, ready for development with hot reload, testing infrastructure, and code quality tools.

---

## Example 2: Create a Data Analysis Script

**Scenario**: You need to create a portable data analysis script that can be shared with colleagues and run on any machine without environment setup.

**Steps**:

1. Initialize a script with PEP 723 metadata
2. Add data analysis dependencies
3. Write analysis code
4. Lock for reproducibility
5. Make executable

**Commands**:

```bash
# Create script with metadata
uv init --script analyze_sales.py --python 3.11

# Add dependencies
uv add --script analyze_sales.py pandas matplotlib seaborn numpy

# Edit the script
cat > analyze_sales.py << 'EOF'
#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas>=2.0",
#   "matplotlib>=3.7",
#   "seaborn>=0.12",
#   "numpy>=1.24",
# ]
# ///

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv('sales_data.csv')

# Analyze
monthly_sales = df.groupby('month')['revenue'].sum()

# Visualize
plt.figure(figsize=(12, 6))
sns.barplot(x=monthly_sales.index, y=monthly_sales.values)
plt.title('Monthly Sales Revenue')
plt.xlabel('Month')
plt.ylabel('Revenue ($)')
plt.savefig('monthly_sales.png')
print("Analysis complete! Chart saved to monthly_sales.png")
EOF

# Lock for reproducibility
uv lock --script analyze_sales.py

# Make executable
chmod +x analyze_sales.py

# Run
./analyze_sales.py
```

**Result**: A completely portable script that automatically creates its own environment with the correct dependencies. Share the script and the `.lock` file with colleagues - it will run identically on their machines.

---

## Example 3: Migrate an Existing Project from pip

**Scenario**: You have an existing Python project using `requirements.txt` and `requirements-dev.txt`. You want to migrate to uv for faster dependency management.

**Steps**:

1. Initialize uv in the existing project
2. Import existing dependencies
3. Clean up old files
4. Test the migration
5. Update documentation

**Commands**:

```bash
# Navigate to existing project
cd my-existing-project

# Backup existing files
cp requirements.txt requirements.txt.bak
cp requirements-dev.txt requirements-dev.txt.bak

# Initialize uv (creates pyproject.toml)
uv init --bare

# Import dependencies
uv add -r requirements.txt
uv add --dev -r requirements-dev.txt

# Sync environment
uv sync

# Test that everything works
uv run pytest

# If successful, remove old files
rm requirements.txt requirements-dev.txt
rm requirements.txt.bak requirements-dev.txt.bak

# Update README.md with new installation instructions
cat >> README.md << 'EOF'

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install dependencies

```bash
uv sync
```

### Run the application

```bash
uv run python main.py
```
EOF
```

**Result**: Project now uses uv with a `pyproject.toml` and `uv.lock` file. Dependencies are locked for reproducibility and installation is 10-100x faster.

---

## Example 4: Migrate from Poetry

**Scenario**: You have a project using Poetry and want to migrate to uv for better performance and simpler configuration.

**Steps**:

1. Backup existing configuration
2. Use automated migration tool
3. Verify the migration
4. Clean up Poetry files

**Commands**:

```bash
# Navigate to Poetry project
cd my-poetry-project

# Backup poetry files
cp pyproject.toml pyproject.toml.poetry.bak
cp poetry.lock poetry.lock.bak

# Run automated migration (preview first)
uvx migrate-to-uv --dry-run

# If preview looks good, run migration
uvx migrate-to-uv

# Sync environment
uv sync

# Run tests to verify
uv run pytest

# If successful, remove Poetry files
rm poetry.lock poetry.lock.bak
poetry env remove --all  # Clean up poetry virtualenvs

# Update pyproject.toml to remove Poetry-specific sections
# The migrate-to-uv tool handles most of this automatically
```

**Result**: Project converted from Poetry to uv with equivalent dependencies in `uv.lock`. Build configuration, dependency groups, and optional dependencies preserved.

---

## Example 5: Set Up CI/CD Pipeline

**Scenario**: You need to configure GitHub Actions for your Python project to run tests, linting, and type checking on every push and pull request.

**Steps**:

1. Create GitHub Actions workflow
2. Configure caching for speed
3. Set up matrix testing for multiple Python versions
4. Add linting and type checking

**Code**:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
          cache-suffix: python-${{ matrix.python-version }}

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --frozen --all-extras

      - name: Run tests with coverage
        run: |
          uv run pytest --cov=src --cov-report=xml --cov-report=term

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --frozen

      - name: Run ruff
        run: uv run ruff check .

      - name: Run black
        run: uv run black --check .

      - name: Run mypy
        run: uv run mypy src/

      - name: Run pyright
        run: uv run pyright src/
```

**Result**: Automated testing and linting on every push. Matrix testing ensures compatibility across Python versions. Caching makes subsequent runs extremely fast.

---

## Example 6: Create a Command-Line Tool

**Scenario**: You want to create a command-line tool that can be installed globally and used across different projects.

**Steps**:

1. Initialize a library project
2. Add CLI dependencies
3. Configure entry points
4. Install as a tool
5. Use globally

**Commands**:

```bash
# Create library project
uv init mycli --lib --build-backend hatchling
cd mycli

# Add CLI dependencies
uv add click rich

# Create CLI module
mkdir src/mycli
cat > src/mycli/__init__.py << 'EOF'
__version__ = "0.1.0"
EOF

cat > src/mycli/cli.py << 'EOF'
import click
from rich.console import Console

console = Console()

@click.group()
def cli():
    """My awesome CLI tool"""
    pass

@cli.command()
@click.argument('name')
def greet(name):
    """Greet someone"""
    console.print(f"[bold green]Hello, {name}![/bold green]")

if __name__ == '__main__':
    cli()
EOF

# Configure entry point in pyproject.toml
cat >> pyproject.toml << 'EOF'

[project.scripts]
mycli = "mycli.cli:cli"
EOF

# Build the package
uv build

# Install as a tool
uv tool install .

# Use globally
mycli greet World
```

**Result**: A globally installed command-line tool that can be used from any directory. The tool is isolated in its own environment but accessible via PATH.

---

## Example 7: Set Up Docker Container

**Scenario**: You need to containerize your Python application with uv for fast, reproducible builds.

**Steps**:

1. Create optimized Dockerfile
2. Use multi-stage builds
3. Leverage uv's speed
4. Configure for production

**Code**:

```dockerfile
# Dockerfile
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (cached layer)
RUN uv sync --frozen --no-dev --no-install-project

# Copy application
COPY . .

# Install project
RUN uv sync --frozen --no-dev

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application
COPY --from=builder /app /app

# Use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Run application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build and run**:

```bash
# Build image
docker build -t myapp:latest .

# Run container
docker run -p 8000:8000 myapp:latest

# Test
curl http://localhost:8000/
```

**Result**: Optimized Docker image with fast builds thanks to uv's speed. Multi-stage build keeps the final image small. Dependency installation is cached for extremely fast rebuilds.

---

## Example 8: Create a Monorepo Workspace

**Scenario**: You're building a system with multiple related packages that need to be developed together but remain separate.

**Steps**:

1. Create workspace structure
2. Configure workspace members
3. Set up inter-package dependencies
4. Build and test workspace

**Commands**:

```bash
# Create workspace root
mkdir my-workspace
cd my-workspace
uv init --bare

# Configure workspace
cat > pyproject.toml << 'EOF'
[tool.uv.workspace]
members = ["packages/*", "apps/*"]

[tool.uv]
managed = true
EOF

# Create packages
mkdir -p packages apps

# Create shared library
cd packages
uv init shared-lib --lib
cd shared-lib
uv add pydantic
cd ../..

# Create core utilities
cd packages
uv init core-utils --lib
cd core-utils
uv add requests
cd ../..

# Create application
cd apps
uv init webapp --app
cd webapp

# Add workspace dependencies
cat >> pyproject.toml << 'EOF'

[tool.uv.sources]
shared-lib = { workspace = true }
core-utils = { workspace = true }
EOF

uv add fastapi shared-lib core-utils
cd ../..

# Lock workspace (single lockfile)
uv lock

# Build specific package
uv build --package shared-lib

# Run app
uv run --package webapp python main.py
```

**Result**: A monorepo workspace with multiple packages sharing a single lockfile. Workspace members can depend on each other with proper versioning and build isolation.

---

## Example 9: Install and Use Python Tools

**Scenario**: You need various Python tools (ruff, black, pytest) available globally without polluting any project environment.

**Steps**:

1. Install tools globally
2. Configure shell PATH
3. Use tools across projects
4. Update tools regularly

**Commands**:

```bash
# Install common development tools
uv tool install ruff
uv tool install black
uv tool install mypy
uv tool install pytest
uv tool install httpie

# Install mkdocs with plugins
uv tool install mkdocs --with mkdocs-material --with mkdocs-git-revision-date-localized-plugin

# Update shell configuration (adds tools to PATH)
uv tool update-shell

# Restart shell or source config
source ~/.bashrc  # or ~/.zshrc

# Use tools from any directory
cd ~/project1
ruff check .
black .

cd ~/project2
mypy src/
pytest

# List installed tools
uv tool list --show-paths

# Upgrade all tools
uv tool upgrade --all

# Upgrade specific tool
uv tool upgrade ruff

# Run tool once without installing (ephemeral)
uvx pycowsay "Hello from uv!"
uvx --from httpie http GET httpbin.org/json
```

**Result**: Python tools installed globally and available in all projects. Tools are isolated in their own environments, preventing conflicts. Easy to update and manage.

---

## Example 10: Configure Private Package Index

**Scenario**: Your organization has a private PyPI server with internal packages that need to be accessible alongside public packages.

**Steps**:

1. Configure custom index
2. Set up authentication
3. Configure source priority
4. Test package installation

**Configuration**:

```toml
# pyproject.toml
[tool.uv]
index-strategy = "first-index"  # Use first index that has the package

# Custom indexes
[[tool.uv.index]]
name = "private-pypi"
url = "https://pypi.company.internal/simple"
default = false  # Not the default index

[[tool.uv.index]]
name = "public-pypi"
url = "https://pypi.org/simple"
default = true  # Default for most packages

# Configure specific packages to use specific indexes
[tool.uv.sources]
company-core = { index = "private-pypi" }
company-utils = { index = "private-pypi" }
```

**Authentication**:

```bash
# Set authentication via environment variables
export UV_INDEX_PRIVATE_PYPI_USERNAME="myuser"
export UV_INDEX_PRIVATE_PYPI_PASSWORD="mypassword"

# Or use netrc file
cat >> ~/.netrc << 'EOF'
machine pypi.company.internal
login myuser
password mypassword
EOF
chmod 600 ~/.netrc

# Install packages
uv add company-core requests pandas

# company-core comes from private-pypi
# requests and pandas come from public-pypi
```

**Result**: Seamless access to both private and public packages. Authentication handled securely via environment variables or netrc. Package resolution respects index priority configuration.

---

## Summary

These examples demonstrate the full range of uv capabilities:

- **Project initialization** - Web apps, libraries, scripts
- **Migration** - From pip, Poetry, and other tools
- **CI/CD** - Fast, cached, matrix testing
- **Tools** - Global installation and ephemeral execution
- **Docker** - Optimized containerization
- **Workspaces** - Monorepo management
- **Private indexes** - Enterprise package management

Each example is production-ready and can be adapted to your specific needs.
