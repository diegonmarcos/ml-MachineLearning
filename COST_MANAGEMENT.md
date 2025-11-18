# Cost Management & Tracking System

## Overview

The cost management system provides comprehensive tracking, forecasting, and optimization of training costs across multiple VPS providers. This system ensures budget compliance, provides cost visibility, and enables data-driven decisions for resource allocation.

## Architecture

### Cost Tracking Components

```
┌──────────────────────────────────────────────────────────────┐
│                    Cost Management Layer                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │   Cost     │  │   Budget   │  │   Cost     │            │
│  │  Tracker   │  │  Manager   │  │ Optimizer  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                     Data Collection Layer                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Provider  │  │  Instance  │  │  Resource  │            │
│  │    APIs    │  │  Metrics   │  │   Usage    │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    Storage & Analytics Layer                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ PostgreSQL │  │ TimescaleDB│  │ ClickHouse │            │
│  │  (Metadata)│  │(Time Series)│  │ (Analytics)│            │
│  └────────────┘  └────────────┘  └────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

## Database Schema

### Tables Structure

```sql
-- Cost tracking table (TimescaleDB hypertable)
CREATE TABLE cost_tracking (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    job_id UUID NOT NULL,
    instance_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    cost_usd DECIMAL(10, 4) NOT NULL,
    cost_type VARCHAR(20) NOT NULL, -- 'compute', 'storage', 'network', 'data_transfer'
    gpu_type VARCHAR(50),
    gpu_count INTEGER,
    duration_seconds INTEGER,
    status VARCHAR(20) -- 'running', 'completed', 'failed'
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('cost_tracking', 'timestamp');

-- Create continuous aggregates for fast queries
CREATE MATERIALIZED VIEW cost_by_hour
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    job_id,
    provider,
    SUM(cost_usd) as total_cost,
    AVG(cost_usd) as avg_cost,
    COUNT(*) as data_points
FROM cost_tracking
GROUP BY hour, job_id, provider;

-- Budget management
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    project_id UUID,
    budget_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly', 'per_job'
    limit_usd DECIMAL(10, 2) NOT NULL,
    current_spend DECIMAL(10, 2) DEFAULT 0,
    alert_threshold DECIMAL(3, 2) DEFAULT 0.80, -- Alert at 80%
    hard_limit BOOLEAN DEFAULT false,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Cost forecasting
CREATE TABLE cost_forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    estimated_duration_seconds INTEGER NOT NULL,
    estimated_cost_usd DECIMAL(10, 4) NOT NULL,
    confidence_level DECIMAL(3, 2), -- 0.00 to 1.00
    actual_cost_usd DECIMAL(10, 4),
    accuracy_score DECIMAL(3, 2) -- Calculated post-job
);

-- Provider pricing history
CREATE TABLE provider_pricing (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    provider VARCHAR(50) NOT NULL,
    instance_type VARCHAR(100) NOT NULL,
    gpu_type VARCHAR(50),
    price_per_hour DECIMAL(10, 6) NOT NULL,
    price_per_second DECIMAL(10, 8),
    availability_zone VARCHAR(50),
    spot_instance BOOLEAN DEFAULT false
);

SELECT create_hypertable('provider_pricing', 'timestamp');

-- Cost anomalies
CREATE TABLE cost_anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    job_id UUID NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL, -- 'spike', 'prolonged_high', 'unexpected_charge'
    expected_cost DECIMAL(10, 4),
    actual_cost DECIMAL(10, 4),
    deviation_percent DECIMAL(5, 2),
    severity VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    resolved BOOLEAN DEFAULT false,
    resolution_note TEXT
);

-- Cost optimization recommendations
CREATE TABLE cost_optimizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    job_id UUID,
    recommendation_type VARCHAR(50) NOT NULL,
    current_cost DECIMAL(10, 4),
    optimized_cost DECIMAL(10, 4),
    potential_savings DECIMAL(10, 4),
    confidence_score DECIMAL(3, 2),
    details JSONB,
    applied BOOLEAN DEFAULT false,
    applied_at TIMESTAMPTZ
);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    total_cost DECIMAL(10, 2) NOT NULL,
    breakdown JSONB NOT NULL, -- Detailed cost breakdown
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'issued', 'paid'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);
```

## Cost Tracking Implementation

### Real-Time Cost Tracker

```python
# cost_tracker.py
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
from decimal import Decimal

class CostTracker:
    """Real-time cost tracking service"""

    def __init__(self, db_pool, provider_manager):
        self.db = db_pool
        self.provider_manager = provider_manager
        self.active_jobs = {}

    async def start_tracking(self, job_id: str, instance_id: str, provider: str):
        """Start tracking costs for a job"""
        tracking_task = asyncio.create_task(
            self._track_job_cost(job_id, instance_id, provider)
        )
        self.active_jobs[job_id] = tracking_task

    async def _track_job_cost(self, job_id: str, instance_id: str, provider: str):
        """Continuously track job costs"""
        start_time = datetime.now()
        last_cost = Decimal('0')

        while job_id in self.active_jobs:
            try:
                # Get current cost from provider
                provider_client = self.provider_manager.get_provider(provider)
                current_cost = await provider_client.get_current_cost(instance_id)

                # Calculate incremental cost
                incremental_cost = current_cost - last_cost

                if incremental_cost > 0:
                    # Record cost entry
                    await self._record_cost_entry(
                        job_id=job_id,
                        instance_id=instance_id,
                        provider=provider,
                        cost=incremental_cost,
                        duration=(datetime.now() - start_time).total_seconds()
                    )

                last_cost = current_cost

                # Check budget limits
                await self._check_budget_limits(job_id, current_cost)

                # Check for anomalies
                await self._detect_cost_anomalies(job_id, current_cost)

                # Wait before next check (every 30 seconds)
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Error tracking cost for job {job_id}: {e}")
                await asyncio.sleep(60)  # Back off on error

    async def _record_cost_entry(
        self,
        job_id: str,
        instance_id: str,
        provider: str,
        cost: Decimal,
        duration: float
    ):
        """Record a cost entry in the database"""
        async with self.db.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO cost_tracking (
                    timestamp, job_id, instance_id, provider,
                    cost_usd, cost_type, duration_seconds, status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                datetime.now(), job_id, instance_id, provider,
                cost, 'compute', int(duration), 'running'
            )

    async def _check_budget_limits(self, job_id: str, current_cost: Decimal):
        """Check if job has exceeded budget limits"""
        async with self.db.acquire() as conn:
            # Get job's budget
            budget = await conn.fetchrow(
                """
                SELECT b.* FROM budgets b
                JOIN training_jobs j ON j.user_id = b.user_id
                WHERE j.id = $1 AND b.active = true
                AND (b.expires_at IS NULL OR b.expires_at > NOW())
                """,
                job_id
            )

            if not budget:
                return

            # Get total spend for budget period
            if budget['budget_type'] == 'daily':
                period_start = datetime.now().replace(hour=0, minute=0, second=0)
            elif budget['budget_type'] == 'weekly':
                period_start = datetime.now() - timedelta(days=datetime.now().weekday())
            elif budget['budget_type'] == 'monthly':
                period_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            else:  # per_job
                period_start = await self._get_job_start_time(job_id)

            total_spend = await conn.fetchval(
                """
                SELECT COALESCE(SUM(cost_usd), 0)
                FROM cost_tracking
                WHERE job_id = $1 AND timestamp >= $2
                """,
                job_id, period_start
            )

            budget_limit = budget['limit_usd']
            usage_percent = float(total_spend / budget_limit)

            # Send alert if threshold exceeded
            if usage_percent >= budget['alert_threshold']:
                await self._send_budget_alert(
                    budget_id=budget['id'],
                    usage_percent=usage_percent,
                    total_spend=total_spend,
                    budget_limit=budget_limit
                )

            # Stop job if hard limit enabled and exceeded
            if budget['hard_limit'] and total_spend >= budget_limit:
                await self._enforce_hard_limit(job_id)

    async def stop_tracking(self, job_id: str):
        """Stop tracking costs for a job"""
        if job_id in self.active_jobs:
            self.active_jobs[job_id].cancel()
            del self.active_jobs[job_id]

            # Mark as completed
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE cost_tracking
                    SET status = 'completed'
                    WHERE job_id = $1
                    """,
                    job_id
                )

    async def get_job_cost_summary(self, job_id: str) -> Dict:
        """Get cost summary for a job"""
        async with self.db.acquire() as conn:
            summary = await conn.fetchrow(
                """
                SELECT
                    SUM(cost_usd) as total_cost,
                    MIN(timestamp) as start_time,
                    MAX(timestamp) as end_time,
                    MAX(duration_seconds) as total_duration,
                    provider,
                    gpu_type,
                    gpu_count
                FROM cost_tracking
                WHERE job_id = $1
                GROUP BY provider, gpu_type, gpu_count
                """,
                job_id
            )

            return dict(summary) if summary else None
```

### Cost Forecasting

```python
# cost_forecaster.py
from typing import Dict, List
from decimal import Decimal
import numpy as np

class CostForecaster:
    """Forecast training costs before job execution"""

    def __init__(self, db_pool):
        self.db = db_pool

    async def forecast_training_cost(
        self,
        model_size: int,
        dataset_size: int,
        gpu_type: str,
        provider: str,
        training_config: Dict
    ) -> Dict:
        """
        Forecast cost based on historical data and job parameters
        """
        # Get historical data for similar jobs
        similar_jobs = await self._get_similar_jobs(
            model_size, dataset_size, gpu_type
        )

        if len(similar_jobs) < 3:
            # Not enough data, use conservative estimate
            return await self._conservative_estimate(
                gpu_type, provider, training_config
            )

        # Calculate average duration and cost
        durations = [job['duration_seconds'] for job in similar_jobs]
        costs = [job['total_cost'] for job in similar_jobs]

        # Use linear regression for better prediction
        X = np.array([[job['model_size'], job['dataset_size']]
                      for job in similar_jobs])
        y_duration = np.array(durations)
        y_cost = np.array(costs)

        # Simple linear regression
        from sklearn.linear_model import LinearRegression

        duration_model = LinearRegression()
        duration_model.fit(X, y_duration)

        cost_model = LinearRegression()
        cost_model.fit(X, y_cost)

        # Predict for current job
        current_job = np.array([[model_size, dataset_size]])
        predicted_duration = duration_model.predict(current_job)[0]
        predicted_cost = cost_model.predict(current_job)[0]

        # Calculate confidence based on variance
        duration_std = np.std(durations)
        cost_std = np.std(costs)

        confidence = 1.0 / (1.0 + (cost_std / np.mean(costs)))

        # Get current provider pricing
        current_price = await self._get_current_pricing(provider, gpu_type)

        # Adjust cost based on current pricing
        avg_historical_price = np.mean([job['price_per_hour']
                                       for job in similar_jobs])
        price_adjustment = current_price / avg_historical_price
        adjusted_cost = predicted_cost * price_adjustment

        # Add buffer for uncertainty
        buffer_percent = 0.15  # 15% buffer
        final_estimate = adjusted_cost * (1 + buffer_percent)

        forecast = {
            'estimated_duration_seconds': int(predicted_duration),
            'estimated_duration_hours': predicted_duration / 3600,
            'estimated_cost_usd': round(Decimal(final_estimate), 4),
            'confidence_level': round(confidence, 2),
            'price_per_hour': current_price,
            'historical_jobs_count': len(similar_jobs),
            'cost_range': {
                'min': round(Decimal(adjusted_cost * 0.85), 4),
                'max': round(Decimal(adjusted_cost * 1.30), 4)
            }
        }

        # Store forecast
        await self._store_forecast(forecast)

        return forecast

    async def _get_similar_jobs(
        self,
        model_size: int,
        dataset_size: int,
        gpu_type: str,
        threshold: float = 0.3
    ) -> List[Dict]:
        """Get historically similar training jobs"""
        async with self.db.acquire() as conn:
            jobs = await conn.fetch(
                """
                SELECT
                    j.id,
                    j.model_size,
                    j.dataset_size,
                    c.gpu_type,
                    SUM(c.cost_usd) as total_cost,
                    MAX(c.duration_seconds) as duration_seconds,
                    AVG(p.price_per_hour) as price_per_hour
                FROM training_jobs j
                JOIN cost_tracking c ON c.job_id = j.id
                JOIN provider_pricing p ON p.provider = c.provider
                    AND p.gpu_type = c.gpu_type
                WHERE c.status = 'completed'
                    AND c.gpu_type = $1
                    AND j.model_size BETWEEN $2 AND $3
                    AND j.dataset_size BETWEEN $4 AND $5
                GROUP BY j.id, j.model_size, j.dataset_size, c.gpu_type
                ORDER BY j.created_at DESC
                LIMIT 20
                """,
                gpu_type,
                int(model_size * (1 - threshold)),
                int(model_size * (1 + threshold)),
                int(dataset_size * (1 - threshold)),
                int(dataset_size * (1 + threshold))
            )

            return [dict(job) for job in jobs]

    async def update_forecast_accuracy(self, job_id: str):
        """Update forecast accuracy after job completion"""
        async with self.db.acquire() as conn:
            # Get forecast and actual cost
            forecast = await conn.fetchrow(
                """
                SELECT * FROM cost_forecasts
                WHERE job_id = $1
                """,
                job_id
            )

            actual_cost = await conn.fetchval(
                """
                SELECT SUM(cost_usd)
                FROM cost_tracking
                WHERE job_id = $1
                """,
                job_id
            )

            if forecast and actual_cost:
                estimated_cost = forecast['estimated_cost_usd']
                accuracy = 1.0 - abs(actual_cost - estimated_cost) / estimated_cost

                await conn.execute(
                    """
                    UPDATE cost_forecasts
                    SET actual_cost_usd = $1,
                        accuracy_score = $2
                    WHERE job_id = $3
                    """,
                    actual_cost, accuracy, job_id
                )
```

### Cost Optimizer

```python
# cost_optimizer.py
from typing import Dict, List
from decimal import Decimal

class CostOptimizer:
    """Recommend cost optimizations for training jobs"""

    def __init__(self, db_pool, provider_manager):
        self.db = db_pool
        self.provider_manager = provider_manager

    async def analyze_job_for_optimization(self, job_id: str) -> List[Dict]:
        """Analyze a job and recommend cost optimizations"""
        recommendations = []

        # Get job details
        async with self.db.acquire() as conn:
            job = await conn.fetchrow(
                """
                SELECT j.*, c.provider, c.gpu_type, c.cost_usd
                FROM training_jobs j
                JOIN cost_tracking c ON c.job_id = j.id
                WHERE j.id = $1
                LIMIT 1
                """,
                job_id
            )

        if not job:
            return recommendations

        # Check alternative providers
        alt_provider_savings = await self._check_alternative_providers(job)
        if alt_provider_savings:
            recommendations.append(alt_provider_savings)

        # Check spot instances
        spot_savings = await self._check_spot_instances(job)
        if spot_savings:
            recommendations.append(spot_savings)

        # Check smaller GPU options
        gpu_downgrade = await self._check_gpu_downgrade(job)
        if gpu_downgrade:
            recommendations.append(gpu_downgrade)

        # Check batch processing opportunities
        batch_savings = await self._check_batch_processing(job)
        if batch_savings:
            recommendations.append(batch_savings)

        # Store recommendations
        for rec in recommendations:
            await self._store_recommendation(job_id, rec)

        return recommendations

    async def _check_alternative_providers(self, job: Dict) -> Dict:
        """Check if alternative providers offer better pricing"""
        current_provider = job['provider']
        current_cost = job['cost_usd']
        gpu_type = job['gpu_type']

        # Get pricing from all providers
        all_pricing = {}
        for provider_name in self.provider_manager.get_all_providers():
            if provider_name == current_provider:
                continue

            pricing = await self.provider_manager.get_pricing(
                provider_name, gpu_type
            )
            if pricing:
                all_pricing[provider_name] = pricing

        # Find cheapest alternative
        if all_pricing:
            cheapest_provider = min(all_pricing, key=lambda k: all_pricing[k]['price_per_hour'])
            cheapest_price = all_pricing[cheapest_provider]['price_per_hour']

            current_price = await self.provider_manager.get_pricing(
                current_provider, gpu_type
            )

            if cheapest_price < current_price['price_per_hour'] * 0.9:  # At least 10% savings
                estimated_savings = (current_price['price_per_hour'] - cheapest_price) * \
                                  (job['duration_seconds'] / 3600)

                return {
                    'type': 'alternative_provider',
                    'title': f'Switch to {cheapest_provider}',
                    'description': f'Save by using {cheapest_provider} instead of {current_provider}',
                    'current_cost': float(current_cost),
                    'optimized_cost': float(current_cost - estimated_savings),
                    'potential_savings': float(estimated_savings),
                    'confidence': 0.85,
                    'details': {
                        'current_provider': current_provider,
                        'recommended_provider': cheapest_provider,
                        'current_price_per_hour': float(current_price['price_per_hour']),
                        'recommended_price_per_hour': float(cheapest_price)
                    }
                }

        return None

    async def _check_spot_instances(self, job: Dict) -> Dict:
        """Check if spot/preemptible instances could reduce costs"""
        provider = job['provider']
        gpu_type = job['gpu_type']

        # Check if provider supports spot instances
        spot_pricing = await self.provider_manager.get_spot_pricing(provider, gpu_type)

        if spot_pricing and spot_pricing['available']:
            savings_percent = (1 - spot_pricing['price_per_hour'] / spot_pricing['on_demand_price']) * 100
            estimated_savings = job['cost_usd'] * (savings_percent / 100)

            return {
                'type': 'spot_instance',
                'title': 'Use Spot/Preemptible Instances',
                'description': f'Save {savings_percent:.0f}% by using spot instances',
                'current_cost': float(job['cost_usd']),
                'optimized_cost': float(job['cost_usd'] - estimated_savings),
                'potential_savings': float(estimated_savings),
                'confidence': 0.70,  # Lower confidence due to interruption risk
                'details': {
                    'interruption_risk': 'medium',
                    'recommended_checkpointing': 'every 15 minutes'
                }
            }

        return None
```

### Budget Management

```python
# budget_manager.py
from datetime import datetime, timedelta
from decimal import Decimal

class BudgetManager:
    """Manage budgets and spending limits"""

    def __init__(self, db_pool, notification_service):
        self.db = db_pool
        self.notifications = notification_service

    async def create_budget(
        self,
        user_id: str,
        budget_type: str,
        limit_usd: Decimal,
        alert_threshold: float = 0.80,
        hard_limit: bool = False
    ) -> str:
        """Create a new budget"""
        async with self.db.acquire() as conn:
            budget_id = await conn.fetchval(
                """
                INSERT INTO budgets (
                    user_id, budget_type, limit_usd,
                    alert_threshold, hard_limit
                )
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                user_id, budget_type, limit_usd, alert_threshold, hard_limit
            )

            return budget_id

    async def check_budget_before_job(
        self,
        user_id: str,
        estimated_cost: Decimal
    ) -> Dict:
        """Check if user has budget for a new job"""
        async with self.db.acquire() as conn:
            # Get active budgets
            budgets = await conn.fetch(
                """
                SELECT * FROM budgets
                WHERE user_id = $1
                    AND active = true
                    AND (expires_at IS NULL OR expires_at > NOW())
                """,
                user_id
            )

            for budget in budgets:
                # Get current spend for budget period
                period_start = self._get_period_start(budget['budget_type'])

                current_spend = await conn.fetchval(
                    """
                    SELECT COALESCE(SUM(cost_usd), 0)
                    FROM cost_tracking ct
                    JOIN training_jobs j ON j.id = ct.job_id
                    WHERE j.user_id = $1
                        AND ct.timestamp >= $2
                    """,
                    user_id, period_start
                )

                remaining = budget['limit_usd'] - current_spend
                projected_spend = current_spend + estimated_cost

                if budget['hard_limit'] and projected_spend > budget['limit_usd']:
                    return {
                        'approved': False,
                        'reason': 'budget_exceeded',
                        'budget_limit': float(budget['limit_usd']),
                        'current_spend': float(current_spend),
                        'estimated_cost': float(estimated_cost),
                        'remaining': float(remaining)
                    }

            return {
                'approved': True,
                'remaining_budget': float(remaining) if budgets else None
            }

    def _get_period_start(self, budget_type: str) -> datetime:
        """Get the start of the budget period"""
        now = datetime.now()

        if budget_type == 'daily':
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif budget_type == 'weekly':
            return now - timedelta(days=now.weekday())
        elif budget_type == 'monthly':
            return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return now  # per_job budget starts with job
```

## Cost Analytics Dashboard

### Key Metrics

1. **Real-time Spending**
   - Current hourly/daily/monthly spend
   - Running jobs cost
   - Projected end-of-period spend

2. **Cost Breakdown**
   - By provider
   - By GPU type
   - By project/team
   - By user

3. **Cost Trends**
   - Historical spending patterns
   - Cost per model/dataset size
   - Efficiency metrics (cost per epoch, cost per sample)

4. **Budget Health**
   - Budget utilization percentage
   - Days remaining in period
   - Burn rate
   - Projected vs actual spending

5. **Optimization Opportunities**
   - Potential savings identified
   - Applied optimizations impact
   - ROI of optimization actions

## n8n Cost Tracking Workflows

### Workflow 1: Continuous Cost Monitoring

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
              "field": "minutes",
              "minutesInterval": 5
            }
          ]
        }
      }
    },
    {
      "name": "Get Active Jobs",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT * FROM training_jobs WHERE status = 'running'"
      }
    },
    {
      "name": "For Each Job",
      "type": "n8n-nodes-base.splitInBatches"
    },
    {
      "name": "Get Provider Cost",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "{{$json.provider_api_url}}/cost/{{$json.instance_id}}"
      }
    },
    {
      "name": "Record Cost Entry",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "cost_tracking"
      }
    },
    {
      "name": "Check Budget",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Check if budget exceeded"
      }
    },
    {
      "name": "Send Alert If Needed",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#cost-alerts"
      }
    }
  ]
}
```

### Workflow 2: Daily Cost Report

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
              "hoursInterval": 24
            }
          ]
        }
      }
    },
    {
      "name": "Calculate Daily Costs",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "executeQuery",
        "query": "SELECT provider, SUM(cost_usd) FROM cost_tracking WHERE timestamp >= CURRENT_DATE GROUP BY provider"
      }
    },
    {
      "name": "Generate Report",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Generate HTML report"
      }
    },
    {
      "name": "Send Email Report",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "to": "team@company.com",
        "subject": "Daily Cost Report"
      }
    }
  ]
}
```

## Integration with Monitoring Stack

### Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Gauge, Histogram

# Cost metrics
cost_total = Counter(
    'training_cost_total_usd',
    'Total training cost in USD',
    ['provider', 'gpu_type', 'user_id']
)

cost_current = Gauge(
    'training_cost_current_usd',
    'Current cost of running jobs',
    ['job_id', 'provider']
)

cost_forecast_accuracy = Histogram(
    'cost_forecast_accuracy',
    'Accuracy of cost forecasts',
    buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
)

budget_utilization = Gauge(
    'budget_utilization_percent',
    'Budget utilization percentage',
    ['user_id', 'budget_type']
)
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "Training Cost Dashboard",
    "panels": [
      {
        "title": "Current Hourly Spend",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(training_cost_total_usd[1h]))"
          }
        ]
      },
      {
        "title": "Cost by Provider",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (provider) (training_cost_total_usd)"
          }
        ]
      },
      {
        "title": "Budget Utilization",
        "type": "gauge",
        "targets": [
          {
            "expr": "budget_utilization_percent"
          }
        ],
        "thresholds": [
          {"value": 80, "color": "yellow"},
          {"value": 95, "color": "red"}
        ]
      }
    ]
  }
}
```

## Cost Optimization Best Practices

### 1. Provider Selection
- Always compare prices across providers
- Consider spot/preemptible instances for fault-tolerant workloads
- Use provider price history to predict cost trends

### 2. Resource Optimization
- Right-size GPU selection for workload
- Use mixed precision training when possible
- Implement efficient checkpointing
- Clean up resources immediately after completion

### 3. Budget Management
- Set realistic budgets based on historical data
- Use alert thresholds to catch overspending early
- Implement hard limits for non-critical projects
- Review and adjust budgets regularly

### 4. Monitoring & Alerts
- Real-time cost tracking
- Anomaly detection
- Budget breach alerts
- Weekly/monthly cost reviews

## Summary

This cost management system provides:

- **Real-time Tracking**: Per-second cost tracking across all providers
- **Forecasting**: ML-based cost prediction before job execution
- **Budget Management**: Flexible budgeting with alerts and hard limits
- **Optimization**: Automated recommendations for cost reduction
- **Analytics**: Comprehensive dashboards and reports
- **Integration**: Seamless integration with n8n and monitoring stack

The system ensures cost visibility, prevents budget overruns, and enables data-driven decisions for resource allocation.
