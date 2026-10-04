# n8n Workflow Designs

## Overview

This document defines the core n8n workflows that orchestrate the entire model fine-tuning platform. These workflows handle job submission, provider selection, cost tracking, monitoring, and notifications.

## Workflow Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Core Workflows                          │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Training  │  │  Provider   │  │    Cost     │      │
│  │    Jobs     │  │ Management  │  │  Tracking   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │    Data     │  │   Monitor   │  │   Alert     │      │
│  │  Pipeline   │  │  & Health   │  │  & Notify   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└────────────────────────────────────────────────────────────┘
```

## Core Workflows

### 1. Training Job Orchestration

**Purpose**: End-to-end orchestration of model fine-tuning jobs

**Trigger**: Webhook (from API when user submits job)

**Workflow Steps**:

```json
{
  "name": "Training Job Orchestration",
  "nodes": [
    {
      "name": "Webhook - Job Submitted",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "training-job-submitted",
        "method": "POST",
        "responseMode": "responseNode"
      },
      "position": [250, 300]
    },
    {
      "name": "Validate Job Configuration",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "mode": "runOnceForAllItems",
        "jsCode": "const job = $input.first().json;\n\n// Validate required fields\nconst required = ['model_name', 'dataset_id', 'user_id'];\nconst missing = required.filter(field => !job[field]);\n\nif (missing.length > 0) {\n  throw new Error(`Missing required fields: ${missing.join(', ')}`);\n}\n\n// Validate model exists\nconst models = await $http.get(`${process.env.API_URL}/models/${job.model_name}`);\n\nif (!models.ok) {\n  throw new Error('Model not found');\n}\n\n// Validate dataset exists\nconst dataset = await $http.get(`${process.env.API_URL}/datasets/${job.dataset_id}`);\n\nif (!dataset.ok) {\n  throw new Error('Dataset not found');\n}\n\nreturn { json: { ...job, validated: true } };"
      },
      "position": [450, 300]
    },
    {
      "name": "Check User Budget",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT * FROM budgets WHERE user_id = '{{$json.user_id}}' AND active = true",
        "additionalFields": {}
      },
      "position": [650, 300]
    },
    {
      "name": "Estimate Job Cost",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "{{$env.API_URL}}/cost/estimate",
        "method": "POST",
        "body": {
          "model_size": "={{$json.model_size}}",
          "dataset_size": "={{$json.dataset_size}}",
          "gpu_type": "={{$json.gpu_type}}"
        },
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth"
      },
      "position": [850, 300]
    },
    {
      "name": "Budget Check Decision",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$json.estimated_cost}}",
              "operation": "smaller",
              "value2": "={{$json.budget_remaining}}"
            }
          ]
        }
      },
      "position": [1050, 300]
    },
    {
      "name": "Reject - Budget Exceeded",
      "type": "n8n-nodes-base.respondToWebhook",
      "parameters": {
        "responseBody": {
          "status": "rejected",
          "reason": "budget_exceeded",
          "message": "Insufficient budget for this job"
        },
        "options": {
          "responseCode": 402
        }
      },
      "position": [1050, 100]
    },
    {
      "name": "Select Optimal Provider",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "mode": "runOnceForAllItems",
        "jsCode": "// Get available providers\nconst providers = ['runpod', 'vast', 'lambda', 'modal'];\nconst requirements = $input.first().json;\n\nconst scores = [];\n\n// Check each provider\nfor (const provider of providers) {\n  try {\n    const response = await $http.get(\n      `${process.env.API_URL}/providers/${provider}/availability`,\n      {\n        params: {\n          gpu_type: requirements.gpu_type,\n          gpu_count: requirements.gpu_count\n        }\n      }\n    );\n\n    if (response.ok && response.data.available) {\n      // Calculate score based on cost, reliability, performance\n      const costScore = 1.0 - (response.data.price_per_hour / 10); // Normalize\n      const reliabilityScore = response.data.reliability_rating / 10;\n      const availabilityScore = response.data.available ? 1.0 : 0.0;\n\n      const totalScore = (\n        0.4 * costScore +\n        0.3 * reliabilityScore +\n        0.3 * availabilityScore\n      );\n\n      scores.push({\n        provider,\n        score: totalScore,\n        price_per_hour: response.data.price_per_hour,\n        instance_type: response.data.instance_type\n      });\n    }\n  } catch (error) {\n    console.error(`Error checking provider ${provider}:`, error);\n  }\n}\n\n// Sort by score\nscores.sort((a, b) => b.score - a.score);\n\n// Return best provider\nreturn {\n  json: {\n    ...requirements,\n    selected_provider: scores[0].provider,\n    provider_score: scores[0].score,\n    price_per_hour: scores[0].price_per_hour,\n    instance_type: scores[0].instance_type,\n    alternative_providers: scores.slice(1, 3)\n  }\n};"
      },
      "position": [1250, 300]
    },
    {
      "name": "Create Job Record",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "schema": "public",
        "table": "training_jobs",
        "columns": "id,user_id,model_name,dataset_id,provider,gpu_type,status,created_at",
        "returnFields": "*"
      },
      "position": [1450, 300]
    },
    {
      "name": "Provision Instance",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/providers/{{$json.selected_provider}}/instances",
        "method": "POST",
        "body": {
          "gpu_type": "={{$json.gpu_type}}",
          "gpu_count": "={{$json.gpu_count}}",
          "docker_image": "={{$json.docker_image}}",
          "storage_gb": "={{$json.storage_gb}}",
          "env_vars": "={{$json.env_vars}}"
        }
      },
      "position": [1650, 300]
    },
    {
      "name": "Update Job with Instance ID",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "update",
        "table": "training_jobs",
        "updateKey": "id",
        "columns": "instance_id,status,started_at"
      },
      "position": [1850, 300]
    },
    {
      "name": "Upload Dataset to Instance",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/data/transfer",
        "method": "POST",
        "body": {
          "instance_id": "={{$json.instance_id}}",
          "dataset_id": "={{$json.dataset_id}}",
          "target_path": "/data/training"
        }
      },
      "position": [2050, 300]
    },
    {
      "name": "Start Training",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/training/start",
        "method": "POST",
        "body": {
          "instance_id": "={{$json.instance_id}}",
          "job_id": "={{$json.id}}",
          "training_config": "={{$json.training_config}}"
        }
      },
      "position": [2250, 300]
    },
    {
      "name": "Start Cost Tracking",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/cost/start-tracking",
        "method": "POST",
        "body": {
          "job_id": "={{$json.id}}",
          "instance_id": "={{$json.instance_id}}",
          "provider": "={{$json.selected_provider}}"
        }
      },
      "position": [2250, 500]
    },
    {
      "name": "Respond - Job Started",
      "type": "n8n-nodes-base.respondToWebhook",
      "parameters": {
        "responseBody": {
          "status": "started",
          "job_id": "={{$json.id}}",
          "instance_id": "={{$json.instance_id}}",
          "provider": "={{$json.selected_provider}}",
          "estimated_cost": "={{$json.estimated_cost}}"
        },
        "options": {
          "responseCode": 200
        }
      },
      "position": [2450, 300]
    },
    {
      "name": "Error Handler",
      "type": "n8n-nodes-base.noOp",
      "parameters": {},
      "position": [1250, 100],
      "onError": "continueErrorOutput"
    },
    {
      "name": "Send Error Response",
      "type": "n8n-nodes-base.respondToWebhook",
      "parameters": {
        "responseBody": {
          "status": "error",
          "message": "={{$json.error}}"
        },
        "options": {
          "responseCode": 500
        }
      },
      "position": [1450, 100]
    }
  ],
  "connections": {
    "Webhook - Job Submitted": {
      "main": [[{ "node": "Validate Job Configuration", "type": "main", "index": 0 }]]
    },
    "Validate Job Configuration": {
      "main": [[{ "node": "Check User Budget", "type": "main", "index": 0 }]]
    },
    "Check User Budget": {
      "main": [[{ "node": "Estimate Job Cost", "type": "main", "index": 0 }]]
    },
    "Estimate Job Cost": {
      "main": [[{ "node": "Budget Check Decision", "type": "main", "index": 0 }]]
    },
    "Budget Check Decision": {
      "main": [
        [{ "node": "Select Optimal Provider", "type": "main", "index": 0 }],
        [{ "node": "Reject - Budget Exceeded", "type": "main", "index": 0 }]
      ]
    },
    "Select Optimal Provider": {
      "main": [[{ "node": "Create Job Record", "type": "main", "index": 0 }]]
    },
    "Create Job Record": {
      "main": [[{ "node": "Provision Instance", "type": "main", "index": 0 }]]
    },
    "Provision Instance": {
      "main": [[{ "node": "Update Job with Instance ID", "type": "main", "index": 0 }]]
    },
    "Update Job with Instance ID": {
      "main": [[{ "node": "Upload Dataset to Instance", "type": "main", "index": 0 }]]
    },
    "Upload Dataset to Instance": {
      "main": [[{ "node": "Start Training", "type": "main", "index": 0 }]]
    },
    "Start Training": {
      "main": [
        [
          { "node": "Start Cost Tracking", "type": "main", "index": 0 },
          { "node": "Respond - Job Started", "type": "main", "index": 0 }
        ]
      ]
    }
  }
}
```

---

### 2. Cost Tracking Workflow

**Purpose**: Continuously track costs for all running jobs

**Trigger**: Schedule (every 30 seconds)

**Workflow**:

```json
{
  "name": "Cost Tracking Workflow",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "seconds",
              "secondsInterval": 30
            }
          ]
        }
      },
      "position": [250, 300]
    },
    {
      "name": "Get Active Jobs",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT j.*, j.instance_id, j.provider FROM training_jobs j WHERE j.status = 'running'"
      },
      "position": [450, 300]
    },
    {
      "name": "Split Into Batches",
      "type": "n8n-nodes-base.splitInBatches",
      "parameters": {
        "batchSize": 1,
        "options": {}
      },
      "position": [650, 300]
    },
    {
      "name": "Get Current Cost from Provider",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/providers/{{$json.provider}}/cost/{{$json.instance_id}}",
        "method": "GET",
        "authentication": "genericCredentialType"
      },
      "position": [850, 300]
    },
    {
      "name": "Calculate Incremental Cost",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const currentCost = $input.first().json.current_cost;\nconst lastRecordedCost = $input.first().json.last_recorded_cost || 0;\nconst incrementalCost = currentCost - lastRecordedCost;\n\nreturn {\n  json: {\n    ...$input.first().json,\n    incremental_cost: incrementalCost,\n    timestamp: new Date().toISOString()\n  }\n};"
      },
      "position": [1050, 300]
    },
    {
      "name": "Record Cost Entry",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "cost_tracking",
        "columns": "job_id,instance_id,provider,cost_usd,cost_type,timestamp,status"
      },
      "position": [1250, 300]
    },
    {
      "name": "Check Budget Limits",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Get job total cost\nconst jobId = $input.first().json.job_id;\nconst currentTotalCost = $input.first().json.total_cost;\n\n// Get user budget\nconst budget = await $http.get(\n  `${process.env.API_URL}/budgets/user/${$input.first().json.user_id}`\n);\n\nconst budgetLimit = budget.data.limit_usd;\nconst alertThreshold = budget.data.alert_threshold;\n\n// Calculate usage\nconst usagePercent = currentTotalCost / budgetLimit;\n\n// Check if alert needed\nconst shouldAlert = usagePercent >= alertThreshold;\nconst shouldStop = budget.data.hard_limit && usagePercent >= 1.0;\n\nreturn {\n  json: {\n    ...$input.first().json,\n    should_alert: shouldAlert,\n    should_stop: shouldStop,\n    usage_percent: usagePercent * 100\n  }\n};"
      },
      "position": [1450, 300]
    },
    {
      "name": "Budget Decision",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$json.should_stop}}",
              "value2": true
            }
          ]
        }
      },
      "position": [1650, 300]
    },
    {
      "name": "Stop Job - Budget Exceeded",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/training/stop",
        "method": "POST",
        "body": {
          "job_id": "={{$json.job_id}}",
          "reason": "budget_exceeded"
        }
      },
      "position": [1850, 200]
    },
    {
      "name": "Send Budget Alert",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$json.should_alert}}",
              "value2": true
            }
          ]
        }
      },
      "position": [1850, 400]
    },
    {
      "name": "Trigger Alert Workflow",
      "type": "n8n-nodes-base.executeWorkflow",
      "parameters": {
        "workflowId": "={{$workflow.id('Budget Alert Notification')}}",
        "passData": true
      },
      "position": [2050, 400]
    },
    {
      "name": "Loop Back",
      "type": "n8n-nodes-base.noOp",
      "parameters": {},
      "position": [2250, 300]
    }
  ],
  "connections": {
    "Schedule Trigger": {
      "main": [[{ "node": "Get Active Jobs", "type": "main", "index": 0 }]]
    },
    "Get Active Jobs": {
      "main": [[{ "node": "Split Into Batches", "type": "main", "index": 0 }]]
    },
    "Split Into Batches": {
      "main": [[{ "node": "Get Current Cost from Provider", "type": "main", "index": 0 }]]
    },
    "Get Current Cost from Provider": {
      "main": [[{ "node": "Calculate Incremental Cost", "type": "main", "index": 0 }]]
    },
    "Calculate Incremental Cost": {
      "main": [[{ "node": "Record Cost Entry", "type": "main", "index": 0 }]]
    },
    "Record Cost Entry": {
      "main": [[{ "node": "Check Budget Limits", "type": "main", "index": 0 }]]
    },
    "Check Budget Limits": {
      "main": [[{ "node": "Budget Decision", "type": "main", "index": 0 }]]
    },
    "Budget Decision": {
      "main": [
        [{ "node": "Stop Job - Budget Exceeded", "type": "main", "index": 0 }],
        [{ "node": "Send Budget Alert", "type": "main", "index": 0 }]
      ]
    },
    "Send Budget Alert": {
      "main": [
        [{ "node": "Trigger Alert Workflow", "type": "main", "index": 0 }],
        [{ "node": "Loop Back", "type": "main", "index": 0 }]
      ]
    },
    "Loop Back": {
      "main": [[{ "node": "Split Into Batches", "type": "main", "index": 0 }]]
    }
  }
}
```

---

### 3. Job Monitoring & Completion

**Purpose**: Monitor training progress and handle completion

**Trigger**: Schedule (every 60 seconds)

**Workflow**:

```json
{
  "name": "Job Monitoring Workflow",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "seconds",
              "secondsInterval": 60
            }
          ]
        }
      }
    },
    {
      "name": "Get Running Jobs",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT * FROM training_jobs WHERE status IN ('running', 'initializing')"
      }
    },
    {
      "name": "For Each Job",
      "type": "n8n-nodes-base.splitInBatches"
    },
    {
      "name": "Get Job Status",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/training/status/{{$json.job_id}}"
      }
    },
    {
      "name": "Get Training Metrics",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/training/metrics/{{$json.job_id}}"
      }
    },
    {
      "name": "Update Job Status",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "update",
        "table": "training_jobs",
        "updateKey": "id",
        "columns": "status,progress,current_epoch,training_loss,validation_loss,updated_at"
      }
    },
    {
      "name": "Check If Completed",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.status}}",
              "operation": "equals",
              "value2": "completed"
            }
          ]
        }
      }
    },
    {
      "name": "Handle Completion",
      "type": "n8n-nodes-base.executeWorkflow",
      "parameters": {
        "workflowId": "={{$workflow.id('Job Completion Handler')}}"
      }
    },
    {
      "name": "Check If Failed",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{$json.status}}",
              "operation": "equals",
              "value2": "failed"
            }
          ]
        }
      }
    },
    {
      "name": "Handle Failure",
      "type": "n8n-nodes-base.executeWorkflow",
      "parameters": {
        "workflowId": "={{$workflow.id('Job Failure Handler')}}"
      }
    },
    {
      "name": "Broadcast Status Update",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/websocket/broadcast",
        "method": "POST",
        "body": {
          "event": "job:status",
          "data": "={{$json}}"
        }
      }
    }
  ]
}
```

---

### 4. Job Completion Handler

**Purpose**: Handle successful job completion

**Trigger**: Called from Job Monitoring workflow

**Steps**:
1. Download trained model from instance
2. Upload model to storage
3. Create model version record
4. Finalize cost calculation
5. Cleanup instance
6. Send completion notification
7. Update forecast accuracy

---

### 5. Provider Health Monitoring

**Purpose**: Monitor health and availability of all providers

**Trigger**: Schedule (every 5 minutes)

**Workflow**:

```json
{
  "name": "Provider Health Monitoring",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "minutes",
              "minutesInterval": 5
            }
          ]
        }
      }
    },
    {
      "name": "Get All Providers",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT * FROM providers WHERE enabled = true"
      }
    },
    {
      "name": "For Each Provider",
      "type": "n8n-nodes-base.splitInBatches"
    },
    {
      "name": "Health Check API",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/providers/{{$json.name}}/health",
        "timeout": 5000
      }
    },
    {
      "name": "Check Available Instances",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.API_URL}}/providers/{{$json.name}}/instances"
      }
    },
    {
      "name": "Calculate Health Score",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const health = $input.first().json.health;\nconst instances = $input.first().json.instances;\n\nconst apiHealthy = health.status === 'ok';\nconst responseTime = health.response_time_ms;\nconst availableGPUs = instances.filter(i => i.available).length;\n\n// Calculate score\nlet score = 0;\nif (apiHealthy) score += 40;\nif (responseTime < 500) score += 30;\nif (availableGPUs > 0) score += 30;\n\nreturn {\n  json: {\n    provider: $input.first().json.name,\n    healthy: apiHealthy,\n    score: score,\n    response_time_ms: responseTime,\n    available_gpus: availableGPUs,\n    checked_at: new Date().toISOString()\n  }\n};"
      }
    },
    {
      "name": "Update Provider Status",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "update",
        "table": "provider_health",
        "updateKey": "provider_name"
      }
    },
    {
      "name": "Check If Unhealthy",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$json.healthy}}",
              "value2": false
            }
          ]
        }
      }
    },
    {
      "name": "Send Alert - Provider Down",
      "type": "n8n-nodes-base.executeWorkflow",
      "parameters": {
        "workflowId": "={{$workflow.id('Provider Alert')}}"
      }
    }
  ]
}
```

---

### 6. Daily Cost Report

**Purpose**: Generate and send daily cost reports

**Trigger**: Schedule (daily at 9:00 AM)

**Workflow**:

```json
{
  "name": "Daily Cost Report",
  "nodes": [
    {
      "name": "Daily Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {
          "interval": [
            {
              "field": "hours",
              "hoursInterval": 24,
              "triggerAtHour": 9
            }
          ]
        }
      }
    },
    {
      "name": "Get Yesterday's Costs",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT provider, SUM(cost_usd) as total_cost, COUNT(DISTINCT job_id) as job_count FROM cost_tracking WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day' AND timestamp < CURRENT_DATE GROUP BY provider"
      }
    },
    {
      "name": "Get Top Expensive Jobs",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT j.name, j.user_id, SUM(c.cost_usd) as total_cost FROM training_jobs j JOIN cost_tracking c ON c.job_id = j.id WHERE c.timestamp >= CURRENT_DATE - INTERVAL '1 day' GROUP BY j.id ORDER BY total_cost DESC LIMIT 5"
      }
    },
    {
      "name": "Calculate Totals",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const costs = $input.first().json;\nconst jobs = $input.item(1).json;\n\nconst totalCost = costs.reduce((sum, c) => sum + parseFloat(c.total_cost), 0);\nconst totalJobs = costs.reduce((sum, c) => sum + c.job_count, 0);\n\nreturn {\n  json: {\n    date: new Date(Date.now() - 86400000).toISOString().split('T')[0],\n    total_cost: totalCost.toFixed(2),\n    total_jobs: totalJobs,\n    by_provider: costs,\n    top_jobs: jobs\n  }\n};"
      }
    },
    {
      "name": "Generate HTML Report",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const data = $input.first().json;\n\nconst html = `\n<html>\n<head>\n  <style>\n    body { font-family: Arial, sans-serif; }\n    .header { background: #4f46e5; color: white; padding: 20px; }\n    .metric { display: inline-block; margin: 20px; }\n    .metric-value { font-size: 32px; font-weight: bold; }\n    .metric-label { font-size: 14px; color: #666; }\n    table { width: 100%; border-collapse: collapse; }\n    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }\n  </style>\n</head>\n<body>\n  <div class=\"header\">\n    <h1>Daily Cost Report - ${data.date}</h1>\n  </div>\n  \n  <div class=\"metrics\">\n    <div class=\"metric\">\n      <div class=\"metric-value\">$${data.total_cost}</div>\n      <div class=\"metric-label\">Total Spend</div>\n    </div>\n    <div class=\"metric\">\n      <div class=\"metric-value\">${data.total_jobs}</div>\n      <div class=\"metric-label\">Training Jobs</div>\n    </div>\n  </div>\n  \n  <h2>Cost by Provider</h2>\n  <table>\n    <tr><th>Provider</th><th>Cost</th><th>Jobs</th></tr>\n    ${data.by_provider.map(p => `\n      <tr>\n        <td>${p.provider}</td>\n        <td>$${p.total_cost}</td>\n        <td>${p.job_count}</td>\n      </tr>\n    `).join('')}\n  </table>\n  \n  <h2>Top 5 Most Expensive Jobs</h2>\n  <table>\n    <tr><th>Job Name</th><th>User</th><th>Cost</th></tr>\n    ${data.top_jobs.map(j => `\n      <tr>\n        <td>${j.name}</td>\n        <td>${j.user_id}</td>\n        <td>$${j.total_cost}</td>\n      </tr>\n    `).join('')}\n  </table>\n</body>\n</html>\n`;\n\nreturn { json: { ...data, html_report: html } };"
      }
    },
    {
      "name": "Send Email Report",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "fromEmail": "reports@mlplatform.com",
        "toEmail": "team@company.com",
        "subject": "Daily Cost Report - {{$json.date}}",
        "emailFormat": "html",
        "text": "={{$json.html_report}}"
      }
    },
    {
      "name": "Post to Slack",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#ml-costs",
        "text": "📊 Daily Cost Report for {{$json.date}}\n\nTotal Spend: ${{$json.total_cost}}\nTotal Jobs: {{$json.total_jobs}}\n\nSee full report in your email."
      }
    }
  ]
}
```

---

### 7. Notification Workflow

**Purpose**: Send notifications via multiple channels

**Trigger**: Called from other workflows

**Channels**:
- Email
- Slack
- Discord
- Webhooks
- In-app notifications

---

### 8. Data Pipeline Workflow

**Purpose**: Preprocess and validate datasets before training

**Steps**:
1. Download dataset from storage
2. Validate format and schema
3. Clean and preprocess
4. Split train/val/test
5. Generate statistics
6. Upload processed dataset

---

### 9. Cost Optimization Workflow

**Purpose**: Analyze jobs and recommend cost optimizations

**Trigger**: Schedule (daily)

**Steps**:
1. Get completed jobs from last week
2. Analyze provider costs
3. Identify spot instance opportunities
4. Check for cheaper alternatives
5. Generate recommendations
6. Store in database
7. Send to users

---

### 10. Automatic Failover Workflow

**Purpose**: Handle provider failures and automatically failover

**Trigger**: Provider health check failure

**Steps**:
1. Detect provider failure
2. Get affected jobs
3. Find alternative provider
4. Save checkpoint from failing instance
5. Provision new instance
6. Restore checkpoint
7. Resume training
8. Notify user

---

## Workflow Best Practices

### Error Handling

```json
{
  "name": "Error Handler",
  "type": "n8n-nodes-base.code",
  "parameters": {
    "mode": "runOnceForAllItems",
    "jsCode": "try {\n  // Main logic\n  return { json: result };\n} catch (error) {\n  // Log error\n  await $http.post(`${process.env.API_URL}/errors/log`, {\n    workflow: $workflow.name,\n    node: $node.name,\n    error: error.message,\n    stack: error.stack,\n    input: $input.all()\n  });\n  \n  // Send alert\n  await $http.post(`${process.env.API_URL}/alerts/send`, {\n    severity: 'high',\n    message: `Workflow error: ${error.message}`\n  });\n  \n  throw error;\n}"
  }
}
```

### Retry Logic

```json
{
  "name": "HTTP Request with Retry",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "={{$json.url}}",
    "options": {
      "retry": {
        "maxTries": 3,
        "waitBetweenTries": 1000
      },
      "timeout": 10000
    }
  }
}
```

### Logging

```json
{
  "name": "Log Execution",
  "type": "n8n-nodes-base.code",
  "parameters": {
    "jsCode": "await $http.post(`${process.env.API_URL}/logs`, {\n  workflow: $workflow.name,\n  execution_id: $execution.id,\n  node: $node.name,\n  data: $input.first().json,\n  timestamp: new Date().toISOString()\n});\n\nreturn $input.all();"
  }
}
```

## Workflow Monitoring

### Metrics to Track
- Execution time
- Success rate
- Error rate
- Resource usage
- API calls made
- Cost per execution

### Alerting Rules
- Workflow failures > 5% in 1 hour
- Execution time > 5 minutes
- Error spike detected
- Provider unreachable
- Budget threshold reached

## Summary

These n8n workflows provide:

- **Complete Orchestration**: End-to-end job management
- **Cost Control**: Real-time tracking and budget enforcement
- **High Availability**: Automatic failover and retry logic
- **Monitoring**: Comprehensive health checks and metrics
- **Notifications**: Multi-channel alerts and reports
- **Automation**: Hands-off operation with manual override

All workflows are designed to be modular, reusable, and maintainable, following n8n best practices.
