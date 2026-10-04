# VPS Provider Integration Specifications

## Overview

This document outlines the integration specifications for various VPS/GPU providers, their APIs, pricing models, and implementation details for the n8n orchestration system.

## Provider Abstraction Layer

### Unified Provider Interface

```typescript
interface IComputeProvider {
  // Provider identification
  name: string;
  id: string;

  // Authentication
  authenticate(credentials: ProviderCredentials): Promise<boolean>;

  // Resource discovery
  listAvailableInstances(): Promise<InstanceType[]>;
  getInstancePricing(instanceType: string): Promise<PricingInfo>;

  // Instance management
  createInstance(config: InstanceConfig): Promise<Instance>;
  terminateInstance(instanceId: string): Promise<boolean>;
  getInstanceStatus(instanceId: string): Promise<InstanceStatus>;

  // Data transfer
  uploadData(instanceId: string, data: Buffer | Stream): Promise<string>;
  downloadResults(instanceId: string, path: string): Promise<Buffer>;

  // Monitoring
  getInstanceMetrics(instanceId: string): Promise<Metrics>;
  streamLogs(instanceId: string): AsyncIterator<LogEntry>;

  // Cost tracking
  getCurrentCost(instanceId: string): Promise<number>;
  getEstimatedCost(config: InstanceConfig, duration: number): Promise<number>;
}
```

## Provider Implementations

### 1. RunPod

**Overview:**
- GPU marketplace with pay-per-second billing
- Wide selection of consumer and enterprise GPUs
- Docker-based deployments
- REST API with Python SDK

**API Details:**
- **Base URL**: `https://api.runpod.io/v2`
- **Authentication**: API Key (Bearer token)
- **Rate Limit**: 100 requests/minute

**Pricing Model:**
- Pay-per-second billing
- Price varies by GPU type and availability
- Spot instances available at 50-80% discount

**Instance Types:**
```json
{
  "instances": [
    {
      "gpu": "RTX 3090",
      "vram": "24GB",
      "price_per_hour": "$0.39",
      "price_per_second": "$0.000108",
      "availability": "high"
    },
    {
      "gpu": "RTX 4090",
      "vram": "24GB",
      "price_per_hour": "$0.69",
      "price_per_second": "$0.000192",
      "availability": "medium"
    },
    {
      "gpu": "A100 40GB",
      "vram": "40GB",
      "price_per_hour": "$1.89",
      "price_per_second": "$0.000525",
      "availability": "medium"
    },
    {
      "gpu": "A100 80GB",
      "vram": "80GB",
      "price_per_hour": "$2.49",
      "price_per_second": "$0.000692",
      "availability": "low"
    },
    {
      "gpu": "H100",
      "vram": "80GB",
      "price_per_hour": "$4.99",
      "price_per_second": "$0.001386",
      "availability": "low"
    }
  ]
}
```

**API Implementation:**

```python
# runpod_provider.py
import runpod
from typing import Dict, List

class RunPodProvider(IComputeProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        runpod.api_key = api_key

    async def create_instance(self, config: InstanceConfig) -> Instance:
        """Create a new RunPod instance"""
        pod = runpod.create_pod(
            name=config.name,
            image_name=config.docker_image,
            gpu_type_id=config.gpu_type,
            cloud_type="SECURE",  # or "COMMUNITY"
            volume_in_gb=config.storage_gb,
            ports=config.ports,
            env=config.environment_vars
        )

        return Instance(
            id=pod['id'],
            provider='runpod',
            status='starting',
            gpu_type=config.gpu_type,
            created_at=datetime.now()
        )

    async def get_instance_status(self, instance_id: str) -> InstanceStatus:
        """Get current status of instance"""
        pod = runpod.get_pod(instance_id)

        return InstanceStatus(
            state=pod['runtime']['state'],
            uptime=pod['runtime']['uptimeInSeconds'],
            gpu_utilization=pod['runtime'].get('gpuUtilization', 0),
            cost_so_far=pod['runtime'].get('costSoFar', 0)
        )

    async def get_current_cost(self, instance_id: str) -> float:
        """Get current accumulated cost"""
        pod = runpod.get_pod(instance_id)
        return float(pod['runtime'].get('costSoFar', 0))
```

**n8n Integration:**
```json
{
  "name": "RunPod - Create Instance",
  "nodes": [
    {
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://api.runpod.io/v2/pods",
        "method": "POST",
        "authentication": "headerAuth",
        "headerAuth": {
          "name": "Authorization",
          "value": "Bearer {{$credentials.runpodApiKey}}"
        },
        "body": {
          "cloudType": "SECURE",
          "gpuTypeId": "{{$json.gpuType}}",
          "name": "{{$json.jobName}}",
          "imageName": "{{$json.dockerImage}}",
          "volumeInGb": "{{$json.storageGb}}",
          "env": "{{$json.envVars}}"
        }
      }
    }
  ]
}
```

---

### 2. Lambda Labs

**Overview:**
- Dedicated GPU cloud for ML/AI workloads
- Pay-per-minute billing
- Pre-configured ML environments
- SSH and API access

**API Details:**
- **Base URL**: `https://cloud.lambdalabs.com/api/v1`
- **Authentication**: API Key (Bearer token)
- **Rate Limit**: 60 requests/minute

**Pricing Model:**
- Pay-per-minute billing
- Fixed pricing per GPU type
- No spot instances

**Instance Types:**
```json
{
  "instances": [
    {
      "gpu": "RTX 6000 Ada",
      "gpu_count": 1,
      "vram_total": "48GB",
      "price_per_hour": "$0.60",
      "ram": "200GB",
      "vcpus": 30
    },
    {
      "gpu": "A100 40GB",
      "gpu_count": 1,
      "vram_total": "40GB",
      "price_per_hour": "$1.10",
      "ram": "200GB",
      "vcpus": 30
    },
    {
      "gpu": "A100 40GB",
      "gpu_count": 8,
      "vram_total": "320GB",
      "price_per_hour": "$8.80",
      "ram": "1600GB",
      "vcpus": 240
    },
    {
      "gpu": "H100",
      "gpu_count": 8,
      "vram_total": "640GB",
      "price_per_hour": "$13.20",
      "ram": "1920GB",
      "vcpus": 296
    }
  ]
}
```

**API Implementation:**

```python
# lambda_provider.py
import httpx
from typing import Dict, List

class LambdaLabsProvider(IComputeProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def list_available_instances(self) -> List[InstanceType]:
        """List available instance types"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/instance-types",
                headers=self.headers
            )
            data = response.json()

            return [
                InstanceType(
                    id=it['instance_type_name'],
                    gpu_type=it['description'],
                    price_per_hour=float(it['price_cents_per_hour']) / 100,
                    available=len(it['regions_with_capacity_available']) > 0
                )
                for it in data['data']
            ]

    async def create_instance(self, config: InstanceConfig) -> Instance:
        """Launch a new instance"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/instance-operations/launch",
                headers=self.headers,
                json={
                    "region_name": config.region,
                    "instance_type_name": config.instance_type,
                    "ssh_key_names": config.ssh_keys,
                    "file_system_names": config.filesystems,
                    "quantity": 1
                }
            )
            data = response.json()

            return Instance(
                id=data['data']['instance_ids'][0],
                provider='lambda',
                status='booting',
                instance_type=config.instance_type
            )
```

---

### 3. Vast.ai

**Overview:**
- GPU rental marketplace
- Competitive pricing with community providers
- Flexible instance configuration
- Docker-based deployments

**API Details:**
- **Base URL**: `https://console.vast.ai/api/v0`
- **Authentication**: API Key (header)
- **Rate Limit**: 120 requests/minute

**Pricing Model:**
- Pay-per-hour billing
- Prices vary by host and availability
- Spot and on-demand instances
- Pricing ranges from $0.10/hr to $5.00/hr depending on GPU

**Instance Types:**
- Dynamic marketplace (prices vary)
- Search by GPU model, VRAM, bandwidth
- User-rated hosts

**API Implementation:**

```python
# vast_provider.py
import httpx
from typing import Dict, List

class VastAIProvider(IComputeProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://console.vast.ai/api/v0"

    async def search_offers(self, requirements: Dict) -> List[Offer]:
        """Search for available offers matching requirements"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/bundles/",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={
                    "q": json.dumps({
                        "gpu_name": requirements.get("gpu_model"),
                        "gpu_ram": requirements.get("vram_gb"),
                        "verified": True,
                        "rentable": True
                    })
                }
            )

            offers = response.json()['offers']
            return [
                Offer(
                    id=offer['id'],
                    gpu_name=offer['gpu_name'],
                    price_per_hour=offer['dph_total'],
                    available=offer['rentable'],
                    reliability_score=offer.get('reliability2', 0)
                )
                for offer in sorted(offers, key=lambda x: x['dph_total'])
            ]

    async def create_instance(self, offer_id: int, config: InstanceConfig) -> Instance:
        """Rent an instance from an offer"""
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/asks/{offer_id}/",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "client_id": "me",
                    "image": config.docker_image,
                    "disk": config.storage_gb,
                    "env": config.environment_vars,
                    "onstart": config.startup_script
                }
            )

            data = response.json()
            return Instance(
                id=data['new_contract'],
                provider='vast',
                status='starting'
            )
```

---

### 4. Modal

**Overview:**
- Serverless compute for ML
- Python-native interface
- Automatic scaling
- Pay-per-compute billing

**API Details:**
- **SDK**: Python-native (`modal` package)
- **Authentication**: Token-based
- **Deployment**: Code-as-configuration

**Pricing Model:**
- Pay per second of compute
- Separate pricing for CPU and GPU
- Free tier available
- GPU pricing: $0.00003/sec (A100) to $0.00006/sec (H100)

**Implementation:**

```python
# modal_provider.py
import modal
from modal import Image, Stub, gpu, Secret

class ModalProvider(IComputeProvider):
    def __init__(self, token: str):
        self.token = token
        modal.config._profile._token = token

    def create_training_function(self, config: InstanceConfig):
        """Create a Modal function for training"""
        stub = Stub(config.name)

        image = (
            Image.from_registry(config.docker_image)
            .pip_install(config.requirements)
        )

        @stub.function(
            gpu=gpu.A100(count=config.gpu_count),
            image=image,
            secrets=[Secret.from_name("huggingface")],
            timeout=config.timeout_hours * 3600,
            volumes={"/data": modal.Volume.from_name("training-data")}
        )
        async def train(model_config: Dict):
            # Training code here
            pass

        return train

    async def execute_training(self, function, config: Dict) -> str:
        """Execute training job"""
        with stub.run():
            result = await function.remote.aio(config)
            return result
```

---

### 5. TensorDock

**Overview:**
- GPU cloud platform
- Pay-per-hour billing
- Web-based and API access
- Competitive pricing

**API Details:**
- **Base URL**: `https://marketplace.tensordock.com/api/v0`
- **Authentication**: Token and Secret
- **Rate Limit**: 100 requests/minute

**Pricing Model:**
- Pay-per-hour billing
- GPU prices range from $0.19/hr (RTX 3060) to $2.39/hr (A100)

**Instance Types:**
```json
{
  "instances": [
    {
      "gpu": "RTX 3060",
      "vram": "12GB",
      "price_per_hour": "$0.19"
    },
    {
      "gpu": "RTX 3080",
      "vram": "10GB",
      "price_per_hour": "$0.29"
    },
    {
      "gpu": "RTX 3090",
      "vram": "24GB",
      "price_per_hour": "$0.39"
    },
    {
      "gpu": "A100 40GB",
      "vram": "40GB",
      "price_per_hour": "$1.39"
    }
  ]
}
```

---

### 6. Coreweave

**Overview:**
- Enterprise-grade GPU cloud
- Kubernetes-native
- High-performance networking
- Volume pricing available

**API Details:**
- **Interface**: Kubernetes API
- **Authentication**: Kubernetes credentials
- **Management**: kubectl, Helm, or Terraform

**Pricing Model:**
- Pay-per-hour billing
- Committed use discounts available
- Enterprise contracts

**Implementation:**

```python
# coreweave_provider.py
from kubernetes import client, config

class CoreweaveProvider(IComputeProvider):
    def __init__(self, kubeconfig_path: str):
        config.load_kube_config(kubeconfig_path)
        self.api = client.CoreV1Api()
        self.batch_api = client.BatchV1Api()

    async def create_training_job(self, config: InstanceConfig) -> Instance:
        """Create Kubernetes job for training"""
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=config.name),
            spec=client.V1JobSpec(
                template=client.V1PodTemplateSpec(
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="trainer",
                                image=config.docker_image,
                                resources=client.V1ResourceRequirements(
                                    requests={
                                        "nvidia.com/gpu": str(config.gpu_count)
                                    },
                                    limits={
                                        "nvidia.com/gpu": str(config.gpu_count)
                                    }
                                ),
                                env=[
                                    client.V1EnvVar(name=k, value=v)
                                    for k, v in config.environment_vars.items()
                                ]
                            )
                        ],
                        restart_policy="Never",
                        node_selector={
                            "gpu.nvidia.com/class": config.gpu_type
                        }
                    )
                )
            )
        )

        result = self.batch_api.create_namespaced_job(
            namespace="default",
            body=job
        )

        return Instance(
            id=result.metadata.name,
            provider='coreweave',
            status='pending'
        )
```

---

## Provider Selection Algorithm

### Decision Factors

1. **Availability**: Is the required GPU type available?
2. **Cost**: What is the total estimated cost?
3. **Reliability**: Historical success rate
4. **Performance**: Network speed, storage I/O
5. **Region**: Data locality and latency

### Selection Logic

```python
def select_provider(requirements: JobRequirements) -> Provider:
    """
    Select optimal provider based on requirements and current conditions
    """
    available_providers = []

    for provider in enabled_providers:
        # Check availability
        instances = provider.list_available_instances()
        matching = [i for i in instances if meets_requirements(i, requirements)]

        if not matching:
            continue

        # Calculate score
        score = calculate_provider_score(
            provider=provider,
            instance=matching[0],
            requirements=requirements
        )

        available_providers.append({
            'provider': provider,
            'instance': matching[0],
            'score': score
        })

    # Sort by score (higher is better)
    available_providers.sort(key=lambda x: x['score'], reverse=True)

    # Return top provider
    return available_providers[0]['provider']

def calculate_provider_score(provider, instance, requirements):
    """
    Calculate weighted score for provider selection
    """
    weights = {
        'cost': 0.4,
        'reliability': 0.3,
        'performance': 0.2,
        'availability': 0.1
    }

    # Normalize and calculate sub-scores
    cost_score = 1.0 - (instance.price_per_hour / max_acceptable_price)
    reliability_score = provider.reliability_rating / 10.0
    performance_score = provider.performance_rating / 10.0
    availability_score = 1.0 if instance.available else 0.0

    total_score = (
        weights['cost'] * cost_score +
        weights['reliability'] * reliability_score +
        weights['performance'] * performance_score +
        weights['availability'] * availability_score
    )

    return total_score
```

## Cost Tracking Integration

### Per-Provider Cost Tracking

```python
class CostTracker:
    def __init__(self, db_connection):
        self.db = db_connection

    async def track_instance_cost(self, instance_id: str, provider: str):
        """Continuously track instance cost"""
        provider_client = get_provider_client(provider)

        while True:
            try:
                current_cost = await provider_client.get_current_cost(instance_id)

                await self.db.update_cost(
                    instance_id=instance_id,
                    current_cost=current_cost,
                    timestamp=datetime.now()
                )

                # Check budget limits
                if current_cost > get_budget_limit(instance_id):
                    await self.send_alert(instance_id, "Budget limit exceeded")

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                logger.error(f"Error tracking cost: {e}")
                break
```

## Failover & High Availability

### Automatic Failover Strategy

```python
async def execute_with_failover(job: TrainingJob):
    """Execute job with automatic failover to alternative providers"""
    providers = get_ranked_providers(job.requirements)

    for provider in providers:
        try:
            instance = await provider.create_instance(job.config)
            result = await execute_training(instance, job)

            if result.success:
                return result
            else:
                logger.warning(f"Training failed on {provider.name}")
                await provider.terminate_instance(instance.id)
                continue

        except ProviderError as e:
            logger.error(f"Provider {provider.name} failed: {e}")
            continue

    raise AllProvidersFailedError("All providers failed to complete the job")
```

## Monitoring & Health Checks

### Provider Health Monitoring

```python
async def monitor_provider_health():
    """Continuous health monitoring for all providers"""
    while True:
        for provider in enabled_providers:
            try:
                # Check API availability
                health = await provider.health_check()

                # Check resource availability
                instances = await provider.list_available_instances()

                # Update provider status
                await update_provider_status(
                    provider_id=provider.id,
                    healthy=health.ok,
                    available_gpus=len(instances),
                    last_check=datetime.now()
                )

            except Exception as e:
                logger.error(f"Health check failed for {provider.name}: {e}")
                await update_provider_status(
                    provider_id=provider.id,
                    healthy=False,
                    error=str(e)
                )

        await asyncio.sleep(300)  # Check every 5 minutes
```

## n8n Workflow Integration

### Provider Selection Workflow

```json
{
  "name": "Select Optimal Provider",
  "nodes": [
    {
      "name": "Get Job Requirements",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {
          "gpu_type": "{{$json.gpu_type}}",
          "vram_required": "{{$json.vram_gb}}",
          "max_cost_per_hour": "{{$json.max_cost}}"
        }
      }
    },
    {
      "name": "Check Provider Availability",
      "type": "n8n-nodes-base.splitInBatches",
      "parameters": {
        "batchSize": 1,
        "options": {}
      }
    },
    {
      "name": "Query Provider API",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "{{$json.provider_api_url}}/instances",
        "method": "GET",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth"
      }
    },
    {
      "name": "Calculate Provider Score",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Provider scoring logic"
      }
    },
    {
      "name": "Select Best Provider",
      "type": "n8n-nodes-base.aggregate",
      "parameters": {
        "aggregate": "max",
        "field": "score"
      }
    }
  ]
}
```

## Summary

This provider integration system offers:

- **Unified Interface**: Abstract away provider-specific details
- **Cost Optimization**: Automatic selection based on price and performance
- **High Availability**: Automatic failover between providers
- **Real-time Monitoring**: Continuous cost and performance tracking
- **Flexibility**: Easy to add new providers

All providers are integrated through a common interface, making the system extensible and maintainable.
