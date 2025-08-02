# ADR (Abnormal End Records) FastAPI Microservice

A production-ready FastAPI microservice for managing ABEND (Abnormal End) records and SOPs (Standard Operating Procedures) with modular architecture, structured logging, and flexible deployment options.

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