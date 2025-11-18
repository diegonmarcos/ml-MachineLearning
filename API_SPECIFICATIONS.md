# API Specifications

## Overview

This document defines the RESTful API for the n8n Model Orchestration Platform. The API provides comprehensive access to all platform features including training jobs, datasets, models, cost tracking, and provider management.

## Base URL

```
Production: https://api.mlplatform.com/v1
Staging: https://api-staging.mlplatform.com/v1
Development: http://localhost:8000/v1
```

## Authentication

### JWT Bearer Token

All API requests require authentication using JWT tokens in the Authorization header.

```http
Authorization: Bearer <access_token>
```

### Obtaining Tokens

**POST /auth/login**

```json
Request:
{
  "email": "user@example.com",
  "password": "securepassword"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

**POST /auth/refresh**

```json
Request:
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

## API Endpoints

### Training Jobs

#### GET /jobs

List all training jobs

```http
GET /jobs?status=running&limit=20&offset=0&sort=-created_at

Response 200:
{
  "data": [
    {
      "id": "job_123abc",
      "name": "llama-2-7b-finetuning",
      "status": "running",
      "model_name": "meta-llama/Llama-2-7b-hf",
      "dataset_id": "ds_456def",
      "provider": "runpod",
      "gpu_type": "A100",
      "gpu_count": 4,
      "progress": 65,
      "current_cost": 12.45,
      "estimated_cost": 18.50,
      "started_at": "2024-11-18T10:23:00Z",
      "created_at": "2024-11-18T10:20:00Z",
      "updated_at": "2024-11-18T12:38:15Z"
    }
  ],
  "pagination": {
    "total": 156,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

#### POST /jobs

Create a new training job

```http
POST /jobs

Request:
{
  "name": "llama-2-7b-custom",
  "model_name": "meta-llama/Llama-2-7b-hf",
  "dataset_id": "ds_456def",
  "training_config": {
    "training_type": "lora",
    "epochs": 10,
    "batch_size": 4,
    "learning_rate": 2e-5,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05
  },
  "hardware_requirements": {
    "gpu_type": "A100",
    "gpu_count": 4,
    "min_vram_gb": 40,
    "storage_gb": 100
  },
  "provider_preference": "auto",
  "max_cost": 50.00
}

Response 201:
{
  "id": "job_789ghi",
  "status": "queued",
  "estimated_cost": 22.50,
  "selected_provider": "runpod",
  "message": "Job queued successfully"
}
```

#### GET /jobs/{job_id}

Get job details

```http
GET /jobs/job_123abc

Response 200:
{
  "id": "job_123abc",
  "name": "llama-2-7b-finetuning",
  "status": "running",
  "model_name": "meta-llama/Llama-2-7b-hf",
  "dataset_id": "ds_456def",
  "provider": "runpod",
  "instance_id": "inst_xyz123",
  "gpu_type": "A100",
  "gpu_count": 4,
  "progress": 65,
  "current_epoch": 7,
  "total_epochs": 10,
  "training_loss": 0.342,
  "validation_loss": 0.387,
  "learning_rate": 2.5e-5,
  "tokens_per_second": 1245,
  "current_cost": 12.45,
  "estimated_cost": 18.50,
  "started_at": "2024-11-18T10:23:00Z",
  "estimated_completion": "2024-11-18T14:30:00Z",
  "training_config": {
    "training_type": "lora",
    "epochs": 10,
    "batch_size": 4,
    "learning_rate": 2e-5
  },
  "checkpoints": [
    {
      "epoch": 5,
      "timestamp": "2024-11-18T11:45:00Z",
      "loss": 0.412,
      "size_mb": 256
    }
  ]
}
```

#### POST /jobs/{job_id}/stop

Stop a running job

```http
POST /jobs/job_123abc/stop

Request:
{
  "reason": "user_requested",
  "save_checkpoint": true
}

Response 200:
{
  "status": "stopped",
  "final_cost": 12.45,
  "checkpoint_saved": true,
  "checkpoint_id": "ckpt_abc123"
}
```

#### GET /jobs/{job_id}/logs

Get job logs

```http
GET /jobs/job_123abc/logs?tail=100&follow=true

Response 200:
{
  "logs": [
    {
      "timestamp": "2024-11-18T12:38:15Z",
      "level": "info",
      "message": "Epoch 7/10 - Step 450/650 - Loss: 0.342"
    }
  ],
  "has_more": false
}
```

#### GET /jobs/{job_id}/metrics

Get training metrics

```http
GET /jobs/job_123abc/metrics?interval=1m

Response 200:
{
  "metrics": [
    {
      "timestamp": "2024-11-18T12:38:00Z",
      "training_loss": 0.342,
      "validation_loss": 0.387,
      "learning_rate": 2.5e-5,
      "gpu_utilization": 95,
      "memory_used_gb": 38,
      "tokens_per_second": 1245
    }
  ]
}
```

### Datasets

#### GET /datasets

List datasets

```http
GET /datasets?type=jsonl&limit=20

Response 200:
{
  "data": [
    {
      "id": "ds_456def",
      "name": "customer-support-conversations",
      "type": "jsonl",
      "samples": 50000,
      "size_bytes": 131072000,
      "visibility": "private",
      "version": "2.1",
      "created_at": "2024-11-15T08:00:00Z",
      "updated_at": "2024-11-18T10:15:00Z"
    }
  ],
  "pagination": {
    "total": 12,
    "limit": 20,
    "offset": 0
  }
}
```

#### POST /datasets

Upload new dataset

```http
POST /datasets
Content-Type: multipart/form-data

Form Data:
- name: "my-custom-dataset"
- type: "jsonl"
- file: <binary file data>
- description: "Custom dataset for fine-tuning"
- visibility: "private"

Response 201:
{
  "id": "ds_new123",
  "name": "my-custom-dataset",
  "status": "processing",
  "upload_url": null,
  "message": "Dataset uploaded successfully"
}
```

#### GET /datasets/{dataset_id}

Get dataset details

```http
GET /datasets/ds_456def

Response 200:
{
  "id": "ds_456def",
  "name": "customer-support-conversations",
  "type": "jsonl",
  "samples": 50000,
  "size_bytes": 131072000,
  "visibility": "private",
  "version": "2.1",
  "schema": {
    "prompt": "string",
    "response": "string",
    "category": "string",
    "rating": "number"
  },
  "statistics": {
    "avg_prompt_length": 45,
    "avg_response_length": 120,
    "categories": ["account", "billing", "technical", "general"]
  },
  "versions": [
    {"version": "2.1", "created_at": "2024-11-18T10:15:00Z"},
    {"version": "2.0", "created_at": "2024-11-15T08:00:00Z"}
  ],
  "created_at": "2024-11-15T08:00:00Z"
}
```

#### GET /datasets/{dataset_id}/preview

Preview dataset samples

```http
GET /datasets/ds_456def/preview?limit=5

Response 200:
{
  "samples": [
    {
      "prompt": "How do I reset my password?",
      "response": "To reset your password, click on...",
      "category": "account",
      "rating": 4.5
    }
  ]
}
```

### Models

#### GET /models

List available models

```http
GET /models?category=llm&size=7b

Response 200:
{
  "data": [
    {
      "id": "meta-llama/Llama-2-7b-hf",
      "name": "Llama 2 7B",
      "size": "7B",
      "parameters": 7000000000,
      "type": "llm",
      "architecture": "transformer",
      "context_length": 4096,
      "license": "llama2",
      "downloads": 1234567,
      "recommended": true
    }
  ]
}
```

#### POST /models/custom

Register custom model

```http
POST /models/custom

Request:
{
  "name": "my-custom-llama-v2",
  "base_model": "meta-llama/Llama-2-7b-hf",
  "source_job_id": "job_123abc",
  "description": "Fine-tuned for customer support",
  "visibility": "private"
}

Response 201:
{
  "id": "custom_model_xyz",
  "name": "my-custom-llama-v2",
  "status": "active",
  "download_url": "https://storage.mlplatform.com/models/custom_model_xyz"
}
```

### Cost Management

#### GET /cost/summary

Get cost summary

```http
GET /cost/summary?period=month

Response 200:
{
  "period": "2024-11",
  "total_cost": 1234.56,
  "by_provider": {
    "runpod": 740.74,
    "vast": 370.37,
    "lambda": 123.45
  },
  "by_gpu_type": {
    "A100": 802.45,
    "RTX4090": 308.64,
    "RTX3090": 123.47
  },
  "job_count": 45,
  "avg_cost_per_job": 27.43
}
```

#### GET /cost/forecast

Get cost forecast

```http
POST /cost/forecast

Request:
{
  "model_size": 7000000000,
  "dataset_size": 50000,
  "gpu_type": "A100",
  "provider": "runpod",
  "training_config": {
    "epochs": 10,
    "batch_size": 4
  }
}

Response 200:
{
  "estimated_duration_seconds": 14400,
  "estimated_duration_hours": 4,
  "estimated_cost_usd": 21.60,
  "confidence_level": 0.85,
  "price_per_hour": 5.40,
  "cost_range": {
    "min": 18.36,
    "max": 28.08
  }
}
```

#### GET /cost/optimizations

Get cost optimization recommendations

```http
GET /cost/optimizations?job_id=job_123abc

Response 200:
{
  "recommendations": [
    {
      "type": "alternative_provider",
      "title": "Switch to Vast.ai",
      "description": "Save 25% by using Vast.ai instead of RunPod",
      "current_cost": 21.60,
      "optimized_cost": 16.20,
      "potential_savings": 5.40,
      "confidence": 0.85
    }
  ]
}
```

#### GET /budgets

Get user budgets

```http
GET /budgets

Response 200:
{
  "budgets": [
    {
      "id": "budget_123",
      "type": "monthly",
      "limit_usd": 1000.00,
      "current_spend": 456.78,
      "remaining": 543.22,
      "usage_percent": 45.68,
      "alert_threshold": 0.80,
      "hard_limit": false,
      "active": true
    }
  ]
}
```

#### POST /budgets

Create budget

```http
POST /budgets

Request:
{
  "type": "monthly",
  "limit_usd": 1000.00,
  "alert_threshold": 0.80,
  "hard_limit": false
}

Response 201:
{
  "id": "budget_new",
  "status": "active"
}
```

### Providers

#### GET /providers

List all providers

```http
GET /providers

Response 200:
{
  "providers": [
    {
      "name": "runpod",
      "display_name": "RunPod",
      "enabled": true,
      "healthy": true,
      "last_health_check": "2024-11-18T12:35:00Z",
      "available_gpus": 145,
      "current_jobs": 3,
      "total_spent": 276.45,
      "avg_response_time_ms": 245
    }
  ]
}
```

#### GET /providers/{provider}/instances

Get available instances

```http
GET /providers/runpod/instances?gpu_type=A100

Response 200:
{
  "instances": [
    {
      "instance_type": "A100_40GB_x4",
      "gpu_type": "A100",
      "gpu_count": 4,
      "vram_total_gb": 160,
      "price_per_hour": 5.40,
      "available": true,
      "region": "US-West"
    }
  ]
}
```

### Workflows

#### GET /workflows

List n8n workflows

```http
GET /workflows

Response 200:
{
  "workflows": [
    {
      "id": "wf_123",
      "name": "Auto Fine-Tuning Pipeline",
      "active": true,
      "executions": 156,
      "success_rate": 98.7,
      "last_execution": "2024-11-18T12:23:00Z",
      "next_execution": "2024-11-18T13:08:00Z"
    }
  ]
}
```

### WebSocket API

Connect to real-time updates:

```javascript
const socket = io('wss://api.mlplatform.com', {
  auth: {
    token: 'Bearer <access_token>'
  }
});

// Job status updates
socket.on('job:status', (data) => {
  console.log('Job status:', data);
  // { job_id: 'job_123', status: 'running', progress: 65 }
});

// Cost updates
socket.on('cost:update', (data) => {
  console.log('Cost update:', data);
  // { job_id: 'job_123', current_cost: 12.45 }
});

// Budget alerts
socket.on('budget:alert', (data) => {
  console.log('Budget alert:', data);
  // { message: '80% of monthly budget used', usage: 0.80 }
});
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "invalid_request",
    "message": "Invalid training configuration",
    "details": {
      "field": "batch_size",
      "issue": "must be greater than 0"
    },
    "request_id": "req_abc123"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `invalid_request` | 400 | Request validation failed |
| `unauthorized` | 401 | Invalid or missing token |
| `forbidden` | 403 | Insufficient permissions |
| `not_found` | 404 | Resource not found |
| `budget_exceeded` | 402 | Budget limit reached |
| `provider_unavailable` | 503 | No providers available |
| `rate_limit_exceeded` | 429 | Too many requests |
| `internal_error` | 500 | Server error |

## Rate Limiting

```
Rate Limit: 1000 requests per hour per user
Rate Limit Headers:
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 995
  X-RateLimit-Reset: 1700317200
```

## Pagination

```http
GET /jobs?limit=20&offset=40

Response Headers:
  Link: </jobs?limit=20&offset=20>; rel="prev",
        </jobs?limit=20&offset=60>; rel="next"
```

## Webhooks

Configure webhooks to receive event notifications:

```http
POST /webhooks

Request:
{
  "url": "https://yourapp.com/webhooks/training",
  "events": ["job.completed", "job.failed", "budget.alert"],
  "secret": "your_webhook_secret"
}

Response 201:
{
  "id": "webhook_123",
  "status": "active"
}
```

### Webhook Events

- `job.started`
- `job.completed`
- `job.failed`
- `job.stopped`
- `budget.alert`
- `budget.exceeded`
- `provider.unhealthy`

### Webhook Payload

```json
{
  "event": "job.completed",
  "timestamp": "2024-11-18T14:30:00Z",
  "data": {
    "job_id": "job_123abc",
    "status": "completed",
    "final_cost": 18.45,
    "duration_seconds": 14256
  }
}
```

## SDK Examples

### Python SDK

```python
from mlplatform import MLPlatform

client = MLPlatform(api_key="your_api_key")

# Create training job
job = client.jobs.create(
    name="llama-2-7b-custom",
    model="meta-llama/Llama-2-7b-hf",
    dataset="ds_456def",
    training_config={
        "epochs": 10,
        "batch_size": 4
    }
)

# Monitor progress
for update in client.jobs.stream(job.id):
    print(f"Progress: {update.progress}%")
    print(f"Cost: ${update.current_cost}")

# Get results
if job.status == "completed":
    model = client.models.get(job.output_model_id)
    model.download("./my-model")
```

### JavaScript SDK

```javascript
import { MLPlatform } from '@mlplatform/sdk';

const client = new MLPlatform({ apiKey: 'your_api_key' });

// Create training job
const job = await client.jobs.create({
  name: 'llama-2-7b-custom',
  model: 'meta-llama/Llama-2-7b-hf',
  dataset: 'ds_456def',
  trainingConfig: {
    epochs: 10,
    batchSize: 4
  }
});

// Monitor with WebSocket
client.jobs.on('status', (update) => {
  console.log(`Progress: ${update.progress}%`);
  console.log(`Cost: $${update.currentCost}`);
});
```

## API Versioning

- Current version: `v1`
- Version specified in URL: `/v1/jobs`
- Breaking changes require new version
- Old versions supported for 12 months

## Summary

This API provides:

- **Complete Coverage**: All platform features accessible via API
- **RESTful Design**: Standard HTTP methods and status codes
- **Real-time Updates**: WebSocket support for live data
- **Comprehensive Documentation**: Clear request/response examples
- **SDKs Available**: Python and JavaScript SDKs
- **Webhooks**: Event-driven integrations
- **Versioned**: Backward compatibility guaranteed

The API is designed for ease of use, reliability, and scalability.
