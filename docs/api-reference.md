# API Reference

This document provides detailed information about all available API endpoints in the ADR FastAPI microservice.

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-production-domain.com`

## API Modes

The service supports three operational modes that determine which endpoints are available:

- **UI Mode**: Only UI-specific endpoints
- **INTERNAL Mode**: Only internal endpoints plus health checks
- **ALL Mode**: All endpoints (default)

Configure via environment variable: `API_MODE=UI|INTERNAL|ALL`

## Authentication

*Currently, no authentication is implemented. This is planned for future versions.*

## Common Response Models

### Message
```json
{
  "message": "string"
}
```

### Error Response
```json
{
  "detail": "Error description"
}
```

## Health & Monitoring Endpoints

### Health Check
**GET** `/healthz`

Returns the health status of the service.

**Response:**
- **200 OK**: Service is healthy
- **500 Internal Server Error**: Service is unhealthy

```json
{
  "message": "OK"
}
```

**Available in modes:** ALL, INTERNAL

---

### Readiness Check
**GET** `/readyz`

Returns the readiness status of the service.

**Response:**
- **200 OK**: Service is ready to receive traffic
- **500 Internal Server Error**: Service is not ready

```json
{
  "message": "OK"
}
```

**Available in modes:** ALL, INTERNAL

## UI API Endpoints (v1alpha1)

UI endpoints are designed for frontend applications and provide comprehensive data for display purposes.

### Get ABEND Details for UI
**GET** `/adr/ui/v1alpha1/abend/{abend_id}`

Retrieves detailed ABEND (Abnormal End) information optimized for UI display.

**Parameters:**
- `abend_id` (path, required): The unique identifier of the ABEND record

**Response Models:**

**Success (200):**
```json
{
  "abendId": "string",
  "name": "string",
  "severity": "string",
  "description": "string"
}
```

**Not Found (404):**
```json
{
  "message": "ABEND record with ID {abend_id} not found"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/adr/ui/v1alpha1/abend/1"
```

**Available in modes:** UI, ALL

---

### Get SOP Details for UI
**GET** `/adr/ui/v1alpha1/sop/{sop_id}`

Retrieves detailed SOP (Standard Operating Procedure) information optimized for UI display.

**Parameters:**
- `sop_id` (path, required): The unique identifier of the SOP

**Response Models:**

**Success (200):**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "version": "string",
  "content": "string",
  "last_updated": "string"
}
```

**Not Found (404):**
```json
{
  "message": "SOP with ID {sop_id} not found"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/adr/ui/v1alpha1/sop/1"
```

**Available in modes:** UI, ALL

## Internal API Endpoints (v1alpha1)

Internal endpoints are designed for service-to-service communication and provide lightweight responses.

### Get ABEND Record by ID
**GET** `/adr/internal/v1alpha1/abend/{abend_id}`

Retrieves a specific ABEND record by its ID for internal service consumption.

**Parameters:**
- `abend_id` (path, required): The unique identifier of the ABEND record

**Response Models:**

**Success (200):**
```json
{
  "abendId": "string",
  "name": "string"
}
```

**Not Found (404):**
```json
{
  "message": "ABEND record with ID {abend_id} not found"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/adr/internal/v1alpha1/abend/1"
```

**Available in modes:** INTERNAL, ALL

---

### List All SOPs
**GET** `/adr/internal/v1alpha1/sop/`

Retrieves a list of all Standard Operating Procedures available in the system.

**Response Models:**

**Success (200):**
```json
[
  {
    "id": "string",
    "name": "string",
    "description": "string"
  }
]
```

**Example:**
```bash
curl -X GET "http://localhost:8000/adr/internal/v1alpha1/sop/"
```

**Available in modes:** INTERNAL, ALL

## Error Handling

The API uses standard HTTP status codes and returns error details in a consistent format.

### Common Error Status Codes

- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error

### Error Response Format

All errors follow this structure:
```json
{
  "detail": "Detailed error message"
}
```

For validation errors:
```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "Error message",
      "type": "error_type"
    }
  ]
}
```

## Rate Limiting

*Rate limiting is not currently implemented but is planned for future versions.*

## Versioning

The API uses semantic versioning with the following pattern:
- `v1alpha1`: Alpha version 1 (current)
- `v1beta1`: Beta version 1 (planned)
- `v1`: Stable version 1 (planned)

Multiple versions can coexist, allowing for gradual migration between versions.

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## SDKs and Client Libraries

*Client libraries are planned for future development.*

## Changelog

### v1alpha1 (Current)
- Initial implementation of ABEND and SOP endpoints
- Health and readiness probes
- UI and Internal API separation
- Basic error handling
