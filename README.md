# ADR FastAPI Microservice

A production-ready FastAPI microservice for managing ABEND  records and SOPs (Standard Operating Procedures) with modular architecture, structured logging, and flexible deployment options.

## Features

- **Modular API Design**: Separate UI and Internal APIs with versioned endpoints
- **Flexible Route Management**: Configurable API modes (UI, Internal, or All)
- **Health Monitoring**: Built-in health and readiness probes for Kubernetes
- **Structured Logging**: JSON-structured logging with context preservation
- **Production Ready**: Docker containerization with multi-stage builds
- **Environment Agnostic**: Configurable for development, staging, and production

## Quick Start

### Prerequisites

- Python 3.11+ 
- Docker (optional, for containerized deployment)
- uv package manager (recommended) or pip

### Installation

Install the project with development dependencies:

```bash
# Using uv (recommended)
uv sync --group dev

# Or using pip
pip install -e ".[dev]"

# For auto-fix tools specifically
pip install autoflake autopep8
```

### Running Locally

1. **Clone and navigate to the repository**
   ```bash
   cd /path/to/sample
   ```

2. **Start the application**
   ```bash
   ./scripts/start.sh
   ```
   
   Or with specific options:
   ```bash
   ./scripts/start.sh --api-mode UI --port 8080
   ```

3. **Access the application**
   - API: http://localhost:8000
   - Swagger Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/healthz

### Running with Docker

```bash
# Build the image
docker build -f docker/Dockerfile -t adr-service .

# Run the container
docker run -p 8000:8000 -e API_MODE=ALL adr-service
```

## API Modes

The service supports three operational modes:

- **UI**: Only UI-specific endpoints (`/adr/ui/v1alpha1/*`)
- **INTERNAL**: Only internal endpoints (`/adr/internal/v1alpha1/*`) plus health checks
- **ALL**: All endpoints (default)

Set via environment variable: `API_MODE=UI|INTERNAL|ALL`

## Codebase Structure

This repository follows a specific structure to maintain clarity and organization:

```
sample/
├── app/                    # Core application logic
│   ├── api/               # API layer (shallow, business logic in core/)
│   │   ├── ui_api/        # UI-specific API endpoints
│   │   ├── internal_api/  # Internal API endpoints
│   │   ├── route_management.py  # Dynamic route configuration
│   │   ├── tags.py        # API tagging and categorization
│   │   ├── healthz.py     # Health check endpoint
│   │   └── readyz.py      # Readiness probe endpoint
│   ├── core/              # Core business logic and utilities
│   │   ├── config.py      # Application configuration
│   │   └── logger/        # Structured logging setup
│   ├── dal/               # Data Access Layer (database interactions)
│   ├── models/            # Pydantic data models
│   ├── schema/            # Database schema definitions
│   └── main.py            # FastAPI application factory
├── docker/                # Docker containerization files
├── docs/                  # Project documentation
├── scripts/               # Utility scripts
├── common/                # Temporary shared resources (certs, etc.)
└── deploy/                # Deployment configurations
```

### Design Principles

- **Separation of Concerns**: API layer handles HTTP concerns, core handles business logic
- **Modular APIs**: Separate UI and Internal APIs with independent versioning
- **Configuration Management**: All config in `app/core/config.py`, no magic values in code
- **Environment Flexibility**: Same code works across dev/staging/production
- **Structured Logging**: Consistent JSON logging with context preservation

## Configuration

### Environment Setup

The application uses environment-specific configuration files. Templates are provided for easy setup:

```bash
# Quick setup for development
./scripts/setup-env.sh setup-dev

# Quick setup for production  
./scripts/setup-env.sh setup-prod

# Manual setup
cp .env.dev.template .env.dev     # Edit with your values
cp .env.prod.template .env.prod   # Edit with your values
```

See [ENVIRONMENT_README.md](ENVIRONMENT_README.md) for detailed configuration guide.

### Configuration Management

All application configuration is centralized in `app/core/config.py`:

- **Environment Detection**: Automatic dev/prod environment detection via `POD_NAMESPACE`
- **Configuration Sources**: Environment variables in dev, secrets manager in production
- **No Magic Values**: All constants externalized to config or constants files

### Key Configuration Properties

```python
class Settings:
    APP_NAME: str = "adr"                    # Application name
    APP_SERVICE_NAME: str = "adr-svc"        # Service name for logging
    
    @property
    def is_dev_env(self):                    # Environment detection
        return bool(os.environ.get("POD_NAMESPACE"))
    
    @property
    def log_level(self):                     # Dynamic log level
        return "DEBUG" if self.is_dev_env else "INFO"
    
    @property
    def port(self):                          # Service port
        return 8000
```

### Environment Variables

Key environment variables supported:

| Variable | Development | Production | Description |
|----------|-------------|------------|-------------|
| `APP_NAME` | BAM | BAM | Application identifier |
| `ENVIRONMENT` | development | production | Runtime environment |
| `DEBUG` | true | false | Debug mode |
| `AWS_REGION` | us-east-1 | us-east-1 | AWS region |
| `DYNAMODB_ENDPOINT` | http://localhost:4566 | (empty) | Local DynamoDB |
| `S3_ENDPOINT` | http://localhost:4566 | (empty) | Local S3 |
| `LOG_LEVEL` | DEBUG | INFO | Logging level |

## API Documentation

### Endpoints Overview

| Endpoint | Method | Description | API Mode |
|----------|--------|-------------|----------|
| `/healthz` | GET | Health check probe | ALL |
| `/readyz` | GET | Readiness probe | ALL |
| `/adr/ui/v1alpha1/abend/{abend_id}` | GET | Get ABEND details for UI | UI, ALL |
| `/adr/ui/v1alpha1/sop/{sop_id}` | GET | Get SOP details for UI | UI, ALL |
| `/adr/internal/v1alpha1/abend/{abend_id}` | GET | Get ABEND record by ID | INTERNAL, ALL |
| `/adr/internal/v1alpha1/sop/` | GET | List all SOPs | INTERNAL, ALL |

### API Versioning

- **Current Version**: `v1alpha1` 
- **Versioning Strategy**: Semantic versioning with alpha/beta/stable tracks
- **Version Support**: Multiple versions can coexist

### Authentication & Authorization

*Note: Authentication and authorization mechanisms are not yet implemented. This is planned for future iterations.*

## Development

### Adding New Endpoints

1. **Create the endpoint handler** in appropriate API directory:
   - UI endpoints: `app/api/ui_api/v1alpha1/`
   - Internal endpoints: `app/api/internal_api/v1alpha1/`

2. **Define data models** in `app/models/`

3. **Add business logic** in `app/core/`

4. **Register routes** in `app/api/route_management.py`

5. **Add API tags** in `app/api/tags.py` if needed

### Testing

*Testing framework setup is planned for future iterations.*

### Code Quality and Formatting

The project includes comprehensive code quality tools and auto-fixing capabilities.

#### Available Commands

The project includes predefined scripts in `pyproject.toml` under `[tool.scripts]` for common development tasks:

**Basic Commands:**
```bash
# Format code with Black and sort imports with isort
black app && isort app

# Check linting with proper line length
flake8 app --max-line-length=88

# Type checking
mypy app

# Run tests with coverage
pytest --cov=app --cov-report=term-missing
```

**Auto-fix Commands:**
```bash
# Remove unused imports and variables
autoflake --in-place --remove-all-unused-imports --remove-unused-variables app

# Fix PEP8 style issues automatically
autopep8 --in-place --max-line-length=88 --aggressive --aggressive app

# Combined format and import cleanup
black app && isort app && autoflake --in-place --remove-all-unused-imports --remove-unused-variables app
```

**Combined Workflows:**
```bash
# Complete formatting and auto-fix workflow  
black app && isort app && autoflake --in-place --remove-all-unused-imports --remove-unused-variables app && autopep8 --in-place --max-line-length=88 --aggressive --aggressive app

# Check all issues after fixes
flake8 app --max-line-length=88 && mypy app

# Full development workflow (fix + check + test)
black app && isort app && autoflake --in-place --remove-all-unused-imports --remove-unused-variables app && flake8 app --max-line-length=88 && mypy app && pytest --cov=app --cov-report=term-missing
```

**For Individual Files:**
```bash
# Format a specific file
black [filename] && isort [filename]

# Fix a specific file
black [filename] && isort [filename] && autoflake --in-place --remove-all-unused-imports [filename]
```

#### Tool Configuration

All tools are configured in `pyproject.toml`:
- **Black**: 88 character line length, Python 3.11+ target
- **isort**: Black-compatible import sorting
- **flake8**: 88 character line length, specific error codes
- **mypy**: Strict type checking with AWS library stubs

#### Development Workflow

1. **Before committing:**
   ```bash
   # Auto-fix common issues
   black app && isort app && autoflake --in-place --remove-all-unused-imports --remove-unused-variables app
   
   # Check remaining issues  
   flake8 app --max-line-length=88
   mypy app
   ```

2. **Quick fixes for specific issues:**
   - Line length violations: `autopep8 --in-place --max-line-length=88 --aggressive --aggressive [file]`
   - Unused imports: `autoflake --in-place --remove-all-unused-imports [file]`
   - Format single file: `black [file] && isort [file]`

3. **Run tests:**
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```

### Logging

The application uses structured JSON logging with context preservation:

```python
from structlog import get_logger
logger = get_logger()
logger.info("Processing request", user_id="123", request_id="abc")
```

## Deployment

### Local Development

Use the provided startup script:
```bash
./scripts/start.sh --api-mode ALL --port 8000
```

### Container Deployment

The application includes a multi-stage Dockerfile optimized for production:

```bash
# Build
docker build -f docker/Dockerfile -t adr-service .

# Run
docker run -p 8000:8000 \
  -e API_MODE=ALL \
  -e POD_NAMESPACE=production \
  adr-service
```

### Kubernetes Deployment

*Kubernetes manifests are planned for the deploy/ directory.*

## Monitoring & Observability

### Health Checks

- **Liveness Probe**: `/healthz` - Verifies service is running
- **Readiness Probe**: `/readyz` - Verifies service is ready to receive traffic

### Logging

- **Format**: Structured JSON with timestamps
- **Context**: Request correlation, user context preservation
- **Levels**: DEBUG (dev), INFO (prod)

### Metrics

*Application metrics integration is planned for future iterations.*

## Security

### Current Status

- ✅ Non-root container execution
- ✅ Minimal container attack surface
- ✅ Custom certificate support
- ⏳ Authentication/Authorization (planned)
- ⏳ Input validation (basic, needs enhancement)
- ⏳ Rate limiting (planned)

## Contributing

1. Follow the established directory structure
2. Add business logic to `core/`, not in API handlers
3. Use structured logging throughout
4. Update documentation for any API changes
5. Add appropriate error handling and validation

## License

*License information to be added.*