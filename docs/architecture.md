# Architecture Overview

This document provides a comprehensive overview of the ADR FastAPI microservice architecture, design decisions, and system components.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend UI   │    │  Other Services │    │   Admin Tools   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │ UI API               │ Internal API         │ Internal API
          │ (v1alpha1)           │ (v1alpha1)           │ (v1alpha1)
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────────────────┐
                    │     ADR FastAPI         │
                    │     Microservice        │
                    │                         │
                    │  ┌─────────────────┐   │
                    │  │  Route Manager  │   │
                    │  │   (API Mode)    │   │
                    │  └─────────────────┘   │
                    │                         │
                    │  ┌─────────────────┐   │
                    │  │   Core Logic    │   │
                    │  └─────────────────┘   │
                    │                         │
                    │  ┌─────────────────┐   │
                    │  │  Data Access    │   │
                    │  │     Layer       │   │
                    │  └─────────────────┘   │
                    └─────────────────────────┘
                                 │
                    ┌─────────────────────────┐
                    │      Database           │
                    │   (Future Component)    │
                    └─────────────────────────┘
```

### Service Boundaries

The ADR microservice is designed with clear boundaries:

1. **API Layer**: Handles HTTP requests, validation, and response formatting
2. **Core Layer**: Contains business logic and domain-specific operations
3. **Data Access Layer**: Manages data persistence and retrieval
4. **Configuration Layer**: Handles environment-specific settings

## Component Architecture

### 1. API Layer (`app/api/`)

The API layer is organized into distinct modules:

```
api/
├── route_management.py    # Dynamic route configuration
├── tags.py               # API categorization and metadata
├── constants.py          # API-specific constants
├── healthz.py            # Health check endpoint
├── readyz.py             # Readiness probe endpoint
├── ui_api/               # UI-specific endpoints
│   └── v1alpha1/
│       ├── abend.py
│       └── sop.py
└── internal_api/         # Internal service endpoints
    └── v1alpha1/
        ├── abend.py
        └── sop.py
```

**Design Principles:**
- **Shallow API Handlers**: API endpoints contain minimal logic
- **Version Separation**: Each API version in its own directory
- **Consumer-Based Separation**: UI and Internal APIs serve different consumers
- **Dynamic Routing**: Routes are configured based on operational mode

### 2. Core Layer (`app/core/`)

The core layer contains business logic and cross-cutting concerns:

```
core/
├── config.py             # Application configuration
└── logger/
    └── struct_logger.py  # Structured logging setup
```

**Responsibilities:**
- Business logic implementation
- Configuration management
- Logging setup and context management
- Utility functions and helpers

### 3. Data Layer (`app/dal/`, `app/models/`, `app/schema/`)

```
dal/                      # Data Access Layer (future implementation)
models/                   # Pydantic data models
├── abend.py
├── sop.py
└── generic_responses.py
schema/                   # Database schema definitions
└── README.md
```

**Design Pattern:**
- **Repository Pattern**: Planned for data access abstraction
- **Domain Models**: Pydantic models for type safety and validation
- **Schema Separation**: Database schema separate from API models

## Design Patterns

### 1. Modular API Design

The service implements a modular API design with the following characteristics:

- **Consumer-Driven**: Separate APIs for UI and internal consumption
- **Version Isolation**: Each API version is independently deployable
- **Feature Toggling**: API modes allow enabling/disabling endpoint groups

### 2. Configuration Management

```python
class Settings:
    # Static configuration
    APP_NAME: str = "adr"
    APP_SERVICE_NAME: str = "adr-svc"
    
    # Dynamic configuration based on environment
    @property
    def is_dev_env(self):
        return bool(os.environ.get("POD_NAMESPACE"))
    
    @property
    def log_level(self):
        return "DEBUG" if self.is_dev_env else "INFO"
```

**Benefits:**
- Environment-agnostic deployment
- No magic values in code
- Runtime configuration detection

### 3. Structured Logging

The service uses structured logging with context preservation:

```python
# Log with structured context
logger.info("Processing request", 
           request_id="abc123", 
           user_id="user456",
           endpoint="/adr/ui/v1alpha1/abend/1")
```

**Features:**
- JSON format for machine readability
- Context preservation across request lifecycle
- Configurable log levels per environment

### 4. Dependency Injection

FastAPI's built-in dependency injection is used for:
- Configuration injection
- Database session management (planned)
- Authentication/authorization (planned)

## Data Flow

### Request Processing Flow

```
1. HTTP Request → FastAPI Router
2. Route Matching → API Mode Check
3. Endpoint Handler → Validation
4. Business Logic → Core Layer
5. Data Access → DAL (future)
6. Response Formation → Pydantic Model
7. HTTP Response → Client
```

### Logging Flow

```
1. Request Received → Context Setup
2. Processing → Structured Logging
3. Response Sent → Context Cleanup
4. Log Aggregation → External Systems
```

## Scalability Considerations

### Horizontal Scaling

The service is designed for horizontal scaling:

- **Stateless Design**: No server-side session state
- **Health Checks**: Kubernetes-compatible probes
- **Configuration Externalization**: Environment-based configuration

### Performance Optimization

- **Async/Await**: Non-blocking I/O operations
- **Connection Pooling**: Database connection management (planned)
- **Caching**: Response caching strategies (planned)

### Resource Management

- **Multi-worker Support**: Uvicorn worker configuration
- **Memory Efficiency**: Minimal container footprint
- **CPU Optimization**: Efficient request processing

## Security Architecture

### Current Security Measures

1. **Container Security**:
   - Non-root user execution
   - Minimal base image
   - Multi-stage builds

2. **Network Security**:
   - Custom certificate support
   - HTTPS termination (at load balancer)

3. **Input Validation**:
   - Pydantic model validation
   - Path parameter validation

### Planned Security Enhancements

1. **Authentication & Authorization**:
   - JWT token validation
   - Role-based access control
   - API key management

2. **Rate Limiting**:
   - Request throttling
   - IP-based limits
   - User-based quotas

3. **Security Headers**:
   - CORS configuration
   - Security headers middleware
   - Content Security Policy

## Monitoring & Observability

### Health Monitoring

```python
# Health check implementation
@router.get("/healthz")
def healthz():
    return {"message": "OK"}

# Readiness check with dependency validation
@router.get("/readyz")
def readyz():
    # TODO: Check database connectivity
    # TODO: Check external service dependencies
    return {"message": "OK"}
```

### Logging Strategy

- **Structured Logs**: JSON format with consistent fields
- **Context Correlation**: Request tracing across service calls
- **Log Levels**: Environment-appropriate verbosity

### Metrics (Planned)

- **Application Metrics**: Request rates, response times, error rates
- **Business Metrics**: ABEND processing rates, SOP access patterns
- **Infrastructure Metrics**: CPU, memory, network utilization

## Technology Stack

### Core Technologies

- **FastAPI**: Modern, fast web framework for building APIs
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server implementation
- **Structlog**: Structured logging library

### Development Tools

- **UV**: Fast Python package manager
- **Docker**: Containerization platform
- **Python 3.11+**: Runtime environment

### Infrastructure (Planned)

- **Kubernetes**: Container orchestration
- **PostgreSQL**: Primary database
- **Redis**: Caching layer
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

## Deployment Architecture

### Container Strategy

```dockerfile
# Multi-stage build for optimization
FROM python:3.12-slim as builder
# Dependency installation

FROM python:3.12-slim as production
# Runtime environment
```

**Benefits:**
- Minimal production image
- Fast build times
- Security optimization

### Environment Management

- **Development**: Local with hot reload
- **Staging**: Container-based with production-like config
- **Production**: Kubernetes deployment with horizontal scaling

## Future Enhancements

### Planned Features

1. **Database Integration**: PostgreSQL with SQLAlchemy
2. **Authentication**: JWT-based auth with role management
3. **Caching**: Redis integration for performance
4. **Message Queue**: Async processing capabilities
5. **API Gateway**: Centralized routing and security
6. **Service Mesh**: Inter-service communication

### Architecture Evolution

The current architecture provides a solid foundation for future enhancements while maintaining:
- **Backward Compatibility**: API versioning strategy
- **Incremental Adoption**: Feature flags and gradual rollouts
- **Operational Simplicity**: Minimal complexity for maximum reliability
