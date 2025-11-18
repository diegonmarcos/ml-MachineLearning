# Quick Start - Get Running in 30 Minutes

## Prerequisites Checklist

Before you begin, make sure you have:

- [ ] **Docker** 24.0+ installed (`docker --version`)
- [ ] **Docker Compose** 2.20+ installed (`docker-compose --version`)
- [ ] **Git** installed
- [ ] At least **one VPS provider account** (RunPod, Vast.ai, or Lambda Labs recommended)
- [ ] **20GB free disk space**
- [ ] **Internet connection** (for pulling Docker images)

## Step 1: Get VPS Provider API Keys (10 minutes)

You need at least ONE provider to start. Here's how to get API keys:

### Option A: RunPod (Recommended - Easiest)

1. Go to https://www.runpod.io/
2. Sign up for an account (use GitHub OAuth for quick signup)
3. Add $10-20 credit to your account
4. Go to Settings → API Keys
5. Click "Create API Key"
6. Copy the key (starts with `runpod_`)
7. **Save it**: You'll need this for `.env` file

**Cost**: ~$21.60 for 4 hours on 4x A100 (our test)

### Option B: Vast.ai (Cheapest)

1. Go to https://vast.ai/
2. Sign up and verify email
3. Add $10-15 credit
4. Go to Account → API Keys
5. Create new API key
6. **Save it**: You'll need this for `.env` file

**Cost**: ~$16.20 for 4 hours on 4x A100 (our test)

### Option C: Lambda Labs (Most Reliable)

1. Go to https://lambdalabs.com/service/gpu-cloud
2. Sign up for cloud access
3. Add $20 credit
4. Go to API Keys section
5. Generate API key
6. **Save it**: You'll need this for `.env` file

**Cost**: ~$17.60 for 4 hours on 4x A100 (our test)

## Step 2: Clone and Configure (5 minutes)

```bash
# Clone the repository
git clone https://github.com/diegonmarcos/ml-MachineLearning.git
cd ml-MachineLearning

# Checkout the feature branch
git checkout claude/n8n-model-orchestration-013H2LUqzcYqLcbzw8ZX5nW2

# Create environment file
cp .env.example .env
```

## Step 3: Configure Environment Variables (5 minutes)

Edit `.env` file with your settings:

```bash
# Open in your favorite editor
nano .env
# or
vim .env
# or
code .env
```

**Minimal Configuration** (change only these):

```bash
# === REQUIRED: Change These ===

# Generate a secure random key (run: openssl rand -hex 32)
API_SECRET_KEY=your-generated-secret-key-here
JWT_SECRET=your-generated-jwt-secret-here

# Change default passwords
POSTGRES_PASSWORD=choose-secure-password
REDIS_PASSWORD=choose-secure-password
N8N_BASIC_AUTH_PASSWORD=choose-secure-password
GRAFANA_ADMIN_PASSWORD=choose-secure-password
MINIO_ROOT_PASSWORD=choose-secure-password

# === VPS Provider API Keys ===
# Add at least ONE of these (the one you set up in Step 1)

# If you chose RunPod:
RUNPOD_API_KEY=your-runpod-key-here

# If you chose Vast.ai:
VAST_API_KEY=your-vast-key-here

# If you chose Lambda Labs:
LAMBDA_API_KEY=your-lambda-key-here

# === OPTIONAL: Leave defaults for now ===
# (You can configure these later)

# Email (for notifications - optional)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password

# Slack (for cost alerts - optional)
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Quick Commands to Generate Secrets

```bash
# Generate API_SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET
openssl rand -hex 32

# Generate N8N_ENCRYPTION_KEY
openssl rand -hex 32
```

## Step 4: Start the Platform (5 minutes)

```bash
# Start all services
docker-compose up -d

# This will download and start:
# - PostgreSQL (database)
# - TimescaleDB (metrics)
# - Redis (cache)
# - MinIO (storage)
# - n8n (workflows)
# - API backend
# - React frontend
# - Prometheus (monitoring)
# - Grafana (dashboards)

# Wait for services to start (about 2-3 minutes)
# Watch the logs:
docker-compose logs -f
```

**Look for these success messages:**
```
api_1      | INFO: Application startup complete
frontend_1 | webpack compiled successfully
n8n_1      | Editor is now accessible via: http://localhost:5678
```

Press `Ctrl+C` to stop watching logs (services keep running)

## Step 5: Verify Everything Works (5 minutes)

### Check Service Health

```bash
# Check all services are running
docker-compose ps

# Expected output: All services should show "Up" status
#   postgres        Up (healthy)
#   timescaledb     Up
#   redis           Up (healthy)
#   minio           Up (healthy)
#   n8n             Up
#   api             Up
#   frontend        Up
#   prometheus      Up
#   grafana         Up
```

### Access the Services

Open in your browser:

1. **Frontend Dashboard**: http://localhost:3000
   - Should show login page or dashboard

2. **API Documentation**: http://localhost:8000/docs
   - Should show interactive API docs (Swagger UI)

3. **n8n Workflows**: http://localhost:5678
   - Login: `admin` / `your-n8n-password`
   - Should show workflow editor

4. **MinIO Console**: http://localhost:9001
   - Login: `minioadmin` / `your-minio-password`
   - Should show storage buckets

5. **Grafana Dashboards**: http://localhost:3001
   - Login: `admin` / `your-grafana-password`
   - Should show monitoring dashboards

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"2024-11-18T..."}
```

## Step 6: Initialize Database (2 minutes)

```bash
# Run database migrations
docker-compose exec api alembic upgrade head

# Expected output:
# INFO [alembic.runtime.migration] Running upgrade -> abc123
# INFO [alembic.runtime.migration] Running upgrade abc123 -> def456
```

## Step 7: Create Your First User (3 minutes)

```bash
# Create admin user
docker-compose exec api python scripts/create_user.py \
  --email your-email@example.com \
  --password your-secure-password \
  --role admin

# Expected output:
# ✓ User created successfully
# Email: your-email@example.com
# Role: admin
# API Token: eyJhbGci...
```

**Save the API Token** - you'll need it for API requests!

## Step 8: Run Your First Test! (Now!)

Now you're ready to run the Domain Q&A test:

```bash
# Set your API token
export API_TOKEN="your-token-from-step-7"

# 1. Upload the test dataset
curl -X POST http://localhost:8000/v1/datasets \
  -H "Authorization: Bearer $API_TOKEN" \
  -F "name=domain_qa_dataset" \
  -F "type=jsonl" \
  -F "file=@test_data/domain_qa_dataset.jsonl" \
  -F "description=Platform Q&A test data" \
  -F "visibility=private"

# Expected response:
# {
#   "id": "ds_abc123",
#   "name": "domain_qa_dataset",
#   "status": "processing"
# }

# 2. Submit fine-tuning job
curl -X POST http://localhost:8000/v1/jobs \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mistral-7b-platform-qa-test",
    "model_name": "mistralai/Mistral-7B-v0.1",
    "dataset_id": "ds_abc123",
    "training_config": {
      "training_type": "lora",
      "epochs": 3,
      "batch_size": 4,
      "learning_rate": 2e-4,
      "lora_r": 16,
      "lora_alpha": 32
    },
    "hardware_requirements": {
      "gpu_type": "A100",
      "gpu_count": 4,
      "min_vram_gb": 40
    },
    "max_cost": 25.00
  }'

# Expected response:
# {
#   "id": "job_xyz789",
#   "status": "queued",
#   "estimated_cost": 18.50,
#   "selected_provider": "vast",
#   "estimated_duration_hours": 4
# }

# 3. Monitor the job
curl http://localhost:8000/v1/jobs/job_xyz789 \
  -H "Authorization: Bearer $API_TOKEN"
```

## Step 9: Watch Your Job Run (Monitor)

### Via Dashboard
1. Go to http://localhost:3000
2. Log in with your email/password
3. Click "Training Jobs"
4. See your job in the list with real-time updates!

### Via API (command line)
```bash
# Watch job progress
watch -n 5 'curl -s http://localhost:8000/v1/jobs/job_xyz789 \
  -H "Authorization: Bearer $API_TOKEN" | jq .progress'

# Watch cost tracking
watch -n 10 'curl -s http://localhost:8000/v1/jobs/job_xyz789 \
  -H "Authorization: Bearer $API_TOKEN" | jq .current_cost'

# View logs (last 50 lines)
curl http://localhost:8000/v1/jobs/job_xyz789/logs?tail=50 \
  -H "Authorization: Bearer $API_TOKEN"
```

### Via n8n (see the orchestration)
1. Go to http://localhost:5678
2. Log in with `admin` / `your-n8n-password`
3. Click "Executions" to see workflows running
4. Watch the "Training Job Orchestration" workflow in action!

## Expected Timeline

| Time | Event | What's Happening |
|------|-------|------------------|
| 0:00 | Job submitted | API validates request |
| 0:05 | Provider selected | Algorithm picks cheapest available (likely Vast.ai) |
| 0:30 | GPU provisioned | Instance starting on provider |
| 1:00 | Data uploaded | Dataset transferred to instance |
| 1:15 | Training starts | Model begins fine-tuning |
| 2:00 | Checkpoint 1 | Progress: ~33%, Cost: ~$5.40 |
| 3:00 | Checkpoint 2 | Progress: ~66%, Cost: ~$10.80 |
| 4:00 | Checkpoint 3 | Progress: 100%, Cost: ~$16.20 |
| 4:15 | Job completes | Model saved, instance cleaned up |

**Total time**: ~4 hours
**Total cost**: $16-22 (depending on provider)

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs postgres
docker-compose logs api

# Common fix: restart everything
docker-compose down
docker-compose up -d
```

### "Connection refused" errors

```bash
# Wait for services to fully start (can take 2-3 minutes)
docker-compose logs -f | grep "startup complete"

# Check specific service
docker-compose ps postgres
docker-compose logs postgres
```

### Database migration fails

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
sleep 30
docker-compose exec api alembic upgrade head
```

### API returns "Provider unavailable"

```bash
# Check your API key is correct in .env
docker-compose exec api env | grep API_KEY

# Restart API to reload environment
docker-compose restart api

# Test provider connection manually
docker-compose exec api python scripts/test_provider.py runpod
```

### Job stuck in "queued" status

```bash
# Check n8n is running
docker-compose logs n8n

# Check workflow is active
# Go to http://localhost:5678 and verify "Training Job Orchestration" is enabled

# Manually trigger workflow
curl -X POST http://localhost:5678/webhook/training-job-submitted \
  -H "Content-Type: application/json" \
  -d '{"job_id":"job_xyz789"}'
```

### Out of disk space

```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes
# WARNING: This removes all unused containers, images, and volumes

# Need at least 20GB free for:
# - Docker images: ~10GB
# - Database: ~2GB
# - Models/datasets: ~5GB
# - Logs: ~1GB
```

## Next Steps After First Job Completes

1. **Validate the model** (see test_data/README.md)
   ```bash
   python test_data/validate_model.py \
     --base_model mistralai/Mistral-7B-v0.1 \
     --finetuned_model /path/to/output \
     --output_file results/test_run.json
   ```

2. **Review cost analytics**
   - Go to http://localhost:3000/cost
   - Compare predicted vs actual cost
   - Check provider selection was optimal

3. **Explore the platform**
   - Upload more datasets
   - Try different models (Llama 2, Falcon, etc.)
   - Set up budget limits
   - Configure Slack notifications

4. **Read the docs**
   - [ARCHITECTURE.md](./ARCHITECTURE.md) - understand the system
   - [N8N_WORKFLOWS.md](./N8N_WORKFLOWS.md) - see how orchestration works
   - [COST_MANAGEMENT.md](./COST_MANAGEMENT.md) - optimize spending

## Cost Management Tips

### Set a Budget (Recommended!)

```bash
# Create monthly budget
curl -X POST http://localhost:8000/v1/budgets \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "monthly",
    "limit_usd": 100.00,
    "alert_threshold": 0.80,
    "hard_limit": true
  }'
```

Now you'll get alerts at $80 and jobs will auto-stop at $100!

### Monitor Spending

```bash
# Get current month's spending
curl http://localhost:8000/v1/cost/summary?period=month \
  -H "Authorization: Bearer $API_TOKEN"

# Get cost forecast for a job
curl -X POST http://localhost:8000/v1/cost/forecast \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{
    "model_size": 7000000000,
    "dataset_size": 50000,
    "gpu_type": "A100"
  }'
```

## What You Should See

### Successful Job Output

```json
{
  "id": "job_xyz789",
  "status": "completed",
  "progress": 100,
  "final_cost": 16.20,
  "estimated_cost": 18.50,
  "provider": "vast",
  "training_metrics": {
    "final_training_loss": 0.342,
    "final_validation_loss": 0.387,
    "total_epochs": 3,
    "total_time_seconds": 14256
  },
  "output_model_id": "custom_model_abc123"
}
```

### Cost Breakdown

```json
{
  "job_id": "job_xyz789",
  "total_cost": 16.20,
  "breakdown": {
    "compute": 15.84,
    "storage": 0.24,
    "data_transfer": 0.12
  },
  "provider": "vast",
  "gpu_hours": 4.05,
  "price_per_hour": 3.91
}
```

## Getting Help

If you get stuck:

1. **Check logs**: `docker-compose logs -f api`
2. **Verify configuration**: `docker-compose exec api env`
3. **Test provider**: `docker-compose exec api python scripts/test_provider.py`
4. **Review docs**: Start with [DEPLOYMENT.md](./DEPLOYMENT.md)
5. **Check status**: `curl http://localhost:8000/health`

## Success Checklist

After following this guide, you should have:

- [x] All Docker services running (`docker-compose ps`)
- [x] Database initialized (migrations complete)
- [x] User account created with API token
- [x] At least one VPS provider configured
- [x] Test dataset uploaded
- [x] First training job submitted
- [x] Job running and being monitored
- [x] Real-time cost tracking visible

**Congratulations!** 🎉 Your ML Orchestration Platform is running!

---

**Estimated setup time**: 30 minutes
**Estimated first job time**: 4 hours
**Estimated first job cost**: $16-22

*You're now orchestrating ML training like a pro!* 🚀
