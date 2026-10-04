# Domain Q&A Test Plan

## Overview

This test validates the n8n Model Orchestration Platform using a real-world scenario: fine-tuning a language model on domain-specific knowledge about the platform itself.

## Objective

**Prove that a fine-tuned model can learn and accurately recall specific domain knowledge that was not in its original training data.**

## Test Dataset

**File**: `domain_qa_dataset.jsonl`
**Format**: JSONL (JSON Lines)
**Size**: 50 Q&A pairs
**Domain**: n8n Model Orchestration Platform technical documentation
**Total Tokens**: ~15,000 tokens

### Dataset Structure

```json
{
  "prompt": "Question about the platform",
  "response": "Detailed answer with specific facts, numbers, and technical details"
}
```

### Knowledge Categories

1. **Architecture** (8 pairs) - System design, components, technology stack
2. **Cost Management** (10 pairs) - Pricing, budgets, forecasting, optimization
3. **Provider Integration** (8 pairs) - VPS providers, selection, failover
4. **Workflows** (7 pairs) - n8n automation, schedules, error handling
5. **API & Integration** (6 pairs) - Endpoints, WebSocket, authentication
6. **Deployment** (5 pairs) - Kubernetes, CI/CD, monitoring
7. **Security** (6 pairs) - Encryption, credentials, compliance

## Test Model Selection

### Recommended: Mistral 7B

**Why Mistral 7B?**
- **Size**: 7B parameters - perfect for domain Q&A
- **Performance**: Excellent at instruction following
- **Cost**: ~$18 for fine-tuning (4 hours on 4x A100)
- **Memory**: Fits comfortably in 24GB VRAM with LoRA
- **Speed**: Fast inference for validation tests

### Alternative: Llama 2 7B Chat

- Slightly more expensive (~$22)
- Excellent chat capabilities
- Well-tested for Q&A tasks

## Training Configuration

### LoRA Fine-tuning (Recommended)

```json
{
  "model_name": "mistralai/Mistral-7B-v0.1",
  "dataset_id": "domain_qa_dataset",
  "training_config": {
    "training_type": "lora",
    "epochs": 3,
    "batch_size": 4,
    "learning_rate": 2e-4,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "warmup_steps": 10,
    "max_seq_length": 2048
  },
  "hardware_requirements": {
    "gpu_type": "A100",
    "gpu_count": 4,
    "min_vram_gb": 40,
    "storage_gb": 50
  }
}
```

### Expected Training Metrics

- **Duration**: 3-4 hours
- **Final Training Loss**: < 0.5
- **Final Validation Loss**: < 0.6
- **Cost**: $16-22 depending on provider

## Validation Strategy

### Phase 1: Direct Recall (Easy)

Test if the model can answer questions exactly as they appear in the training data.

**Test Questions** (10 from training set):

1. "What is the n8n Model Orchestration Platform?"
2. "Which VPS providers are supported by the platform?"
3. "How does the cost tracking system work?"
4. "How much does it cost to fine-tune Llama 2 7B with LoRA?"
5. "What technology stack powers the backend?"
6. "How does automatic failover work?"
7. "What GPU types are available across providers?"
8. "How does budget management prevent overspending?"
9. "What React components are included in the UI library?"
10. "How does spot instance support work?"

**Success Criteria**: Model should answer 9/10 correctly with factually accurate responses.

---

### Phase 2: Paraphrased Questions (Medium)

Test if the model understands concepts and can answer rephrased questions.

**Test Questions** (20 new phrasings):

1. "Tell me about the n8n orchestration system for ML models"
   - *Expected*: Should describe the platform's core functionality

2. "What cloud GPU providers can I use?"
   - *Expected*: Should list RunPod, Vast.ai, Lambda Labs, Modal, TensorDock, CoreWeave

3. "How often does the system check my spending?"
   - *Expected*: Should mention 30-second intervals

4. "What's the price range for fine-tuning a Llama model with LoRA?"
   - *Expected*: Should mention $16-22, 4-6 hours, provider differences

5. "Which database technologies does the backend use?"
   - *Expected*: PostgreSQL, TimescaleDB, Redis

6. "What happens if my GPU provider goes down during training?"
   - *Expected*: Explain checkpoint saving, provider switching, job resume

7. "Can I use consumer GPUs like RTX 3090?"
   - *Expected*: Yes, available on RunPod and Vast.ai

8. "How do I make sure I don't overspend?"
   - *Expected*: Budget limits, alert thresholds, hard limits

9. "What UI components help me display costs?"
   - *Expected*: CostDisplay, CostChart, BudgetGauge components

10. "Is it cheaper to use spot instances?"
    - *Expected*: 50-80% savings, with interruption risk

11. "How does the platform pick which provider to use?"
    - *Expected*: Scoring algorithm with cost, reliability, performance, availability weights

12. "What programming languages are used?"
    - *Expected*: Python 3.11+ backend, TypeScript/React frontend

13. "How long does it take to start a training job?"
    - *Expected*: Under 5 seconds for submission, 30-60 seconds to start training

14. "What are the main sections of the web interface?"
    - *Expected*: 8 pages - Dashboard, Jobs, Models, Datasets, Cost, Providers, Workflows, Settings

15. "How is my private data kept secure?"
    - *Expected*: AES-256 encryption, TLS 1.3, secure transfer, auto-deletion

16. "How accurate is the cost prediction?"
    - *Expected*: 85% confidence level using ML-based forecasting

17. "What automated workflows run in the background?"
    - *Expected*: List n8n workflows like cost tracking, health monitoring, job orchestration

18. "How does the system know when to alert me about costs?"
    - *Expected*: Alert threshold (default 80%), hard limit option

19. "What container orchestration is used in production?"
    - *Expected*: Kubernetes with Docker containers

20. "How much memory do different services need?"
    - *Expected*: API 512Mi-2Gi, Frontend 256Mi-512Mi, PostgreSQL 4Gi-16Gi

**Success Criteria**: Model should answer 15/20 correctly (75% accuracy).

---

### Phase 3: Reasoning Questions (Hard)

Test if the model can combine knowledge and make inferences.

**Test Questions** (15 analytical):

1. "If I have a $1000 monthly budget and want to fine-tune 3 Llama 2 7B models, will I stay within budget?"
   - *Expected*: Calculate ~$20 per job × 3 = $60, well within $1000 budget

2. "Which provider would you recommend for a 6-hour training job if I want the lowest cost?"
   - *Expected*: Vast.ai at $16.20 for 4 hours, or explain need to check current pricing

3. "What happens if I'm at 85% of my budget and submit a job estimated at $25?"
   - *Expected*: Alert triggered at 80%, but job allowed unless hard limit enabled

4. "How much GPU memory do I need to fine-tune a 13B parameter model with QLoRA?"
   - *Expected*: Inference from text - QLoRA reduces memory, 40GB+ recommended

5. "If a provider fails after 2 hours of a 4-hour job, how much training time is lost?"
   - *Expected*: Minimal loss due to checkpointing, resume from last checkpoint (likely <15 min lost)

6. "What's the total cost if I run 10 jobs per month averaging $18 each?"
   - *Expected*: 10 × $18 = $180/month

7. "Can I train a Falcon 180B model on RTX 3090 GPUs?"
   - *Expected*: No, insufficient VRAM; need A100 or H100

8. "How long would it take to fine-tune 5 models sequentially vs in parallel?"
   - *Expected*: Sequential: 5 × 4 hours = 20 hours; Parallel: 4 hours (if providers available)

9. "If my API response time is 300ms, is the system performing well?"
   - *Expected*: No, target is <200ms at p95

10. "What's the difference in cost between using spot instances and on-demand?"
    - *Expected*: 50-80% savings with spot, but interruption risk

11. "How many API replicas do I need for 1000 requests per minute?"
    - *Expected*: 3+ replicas recommended based on resource limits

12. "If health monitoring shows a provider at 30% score, will jobs use it?"
    - *Expected*: No, below 40 threshold, provider removed from selection

13. "Can I deploy the platform on a single server?"
    - *Expected*: Yes for development with Docker Compose, but Kubernetes recommended for production

14. "What happens if my PostgreSQL database fills up?"
    - *Expected*: Need to increase storage (100Gi+ recommended), implement retention policies

15. "How much would it cost to fine-tune 100 models per month?"
    - *Expected*: ~$1,800-2,200 (100 × $18-22), need to plan budget accordingly

**Success Criteria**: Model should answer 10/15 correctly (67% accuracy) with reasonable inference.

---

## Comparison Testing

### Baseline Model (No Fine-tuning)

First, test the **base Mistral 7B** model on the same questions to establish a baseline.

**Expected Results**:
- Phase 1 (Direct Recall): 0-1/10 correct (model has no knowledge of our platform)
- Phase 2 (Paraphrased): 0-2/20 correct (may hallucinate generic answers)
- Phase 3 (Reasoning): 0-1/15 correct (no domain knowledge to reason with)

### Fine-tuned Model

**Expected Results**:
- Phase 1 (Direct Recall): 9/10 correct (90%)
- Phase 2 (Paraphrased): 15/20 correct (75%)
- Phase 3 (Reasoning): 10/15 correct (67%)

### Success Threshold

**Minimum Acceptable**: 75% improvement over baseline
**Target**: 85% accuracy on Phase 1, 70% on Phase 2, 60% on Phase 3

---

## Evaluation Metrics

### 1. Factual Accuracy

Score each answer on factual correctness:

- **Correct (1.0)**: Answer is factually accurate with correct numbers/details
- **Mostly Correct (0.7)**: Minor errors but core facts correct
- **Partially Correct (0.4)**: Some correct information, significant errors
- **Incorrect (0.0)**: Wrong or hallucinated information

### 2. Completeness

Does the answer cover all key points?

- **Complete (1.0)**: All important points mentioned
- **Partial (0.5)**: Some points missing
- **Incomplete (0.0)**: Majority of information missing

### 3. Relevance

Is the answer on-topic and relevant?

- **Relevant (1.0)**: Directly answers the question
- **Somewhat Relevant (0.5)**: Related but not directly answering
- **Irrelevant (0.0)**: Off-topic or doesn't address question

### Combined Score

`Final Score = (Factual Accuracy × 0.5) + (Completeness × 0.3) + (Relevance × 0.2)`

**Success Threshold**: Average score ≥ 0.75 across all test questions

---

## Execution Steps

### Step 1: Upload Dataset

```bash
# Upload via API
curl -X POST http://localhost:8000/v1/datasets \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=domain_qa_dataset" \
  -F "type=jsonl" \
  -F "file=@test_data/domain_qa_dataset.jsonl" \
  -F "description=Platform knowledge for Q&A testing" \
  -F "visibility=private"
```

### Step 2: Create Training Job

```bash
# Submit fine-tuning job
curl -X POST http://localhost:8000/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mistral-7b-platform-qa",
    "model_name": "mistralai/Mistral-7B-v0.1",
    "dataset_id": "domain_qa_dataset",
    "training_config": {
      "training_type": "lora",
      "epochs": 3,
      "batch_size": 4,
      "learning_rate": 2e-4,
      "lora_r": 16,
      "lora_alpha": 32,
      "lora_dropout": 0.05
    },
    "hardware_requirements": {
      "gpu_type": "A100",
      "gpu_count": 4,
      "min_vram_gb": 40
    }
  }'
```

### Step 3: Monitor Training

Watch the job via UI or API:

```bash
# Check status
curl http://localhost:8000/v1/jobs/{job_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# Stream metrics
curl http://localhost:8000/v1/jobs/{job_id}/metrics \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 4: Test Base Model (Baseline)

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

# Load base model
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1")
model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1")

# Test questions
questions = [
    "What is the n8n Model Orchestration Platform?",
    "Which VPS providers are supported by the platform?",
    # ... add all test questions
]

results = []
for question in questions:
    prompt = f"Question: {question}\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=512)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    results.append({"question": question, "answer": answer})
```

### Step 5: Test Fine-tuned Model

```python
from peft import PeftModel

# Load fine-tuned model with LoRA adapters
base_model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-v0.1")
model = PeftModel.from_pretrained(base_model, "path/to/lora/adapters")

# Run same test questions
finetuned_results = []
for question in questions:
    prompt = f"Question: {question}\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=512)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    finetuned_results.append({"question": question, "answer": answer})
```

### Step 6: Evaluate Results

```python
def evaluate_answer(question, answer, expected_facts):
    """
    Evaluate answer quality
    Returns: (factual_score, completeness_score, relevance_score)
    """
    # Check if key facts are present
    factual_score = sum(1 for fact in expected_facts if fact.lower() in answer.lower()) / len(expected_facts)

    # Check completeness
    completeness_score = 1.0 if len(answer) > 100 else 0.5

    # Check relevance (basic keyword matching)
    relevance_score = 1.0 if any(keyword in answer.lower() for keyword in question.lower().split()) else 0.5

    return factual_score, completeness_score, relevance_score

# Calculate scores
baseline_scores = []
finetuned_scores = []

for i, question in enumerate(questions):
    base_answer = results[i]['answer']
    ft_answer = finetuned_results[i]['answer']

    base_score = evaluate_answer(question, base_answer, expected_facts[i])
    ft_score = evaluate_answer(question, ft_answer, expected_facts[i])

    baseline_scores.append(base_score)
    finetuned_scores.append(ft_score)

# Calculate averages
print(f"Baseline Average: {sum(baseline_scores)/len(baseline_scores):.2f}")
print(f"Fine-tuned Average: {sum(finetuned_scores)/len(finetuned_scores):.2f}")
print(f"Improvement: {((sum(finetuned_scores) - sum(baseline_scores)) / sum(baseline_scores) * 100):.1f}%")
```

---

## Expected Outcomes

### Training Phase

- **Training Loss**: Should decrease from ~2.5 to <0.5 over 3 epochs
- **Validation Loss**: Should follow training loss, final <0.6
- **GPU Utilization**: 85-95% on all 4 A100 GPUs
- **Training Speed**: ~1200-1500 tokens/sec
- **Cost**: $16-22 depending on provider (platform should select cheapest)

### Validation Phase

**Base Model (Mistral 7B) - Baseline**:
- Phase 1: 0-10% accuracy (no platform knowledge)
- Phase 2: 0-10% accuracy (may hallucinate)
- Phase 3: 0-7% accuracy (no reasoning base)
- **Overall**: <10% accuracy

**Fine-tuned Model**:
- Phase 1: 85-95% accuracy (direct recall)
- Phase 2: 70-80% accuracy (understanding)
- Phase 3: 60-70% accuracy (reasoning)
- **Overall**: 70-80% accuracy

**Improvement**: 700-800% increase in accuracy

---

## Success Criteria

✅ **PASS**: Fine-tuned model scores ≥75% overall with ≥600% improvement over baseline

⚠️ **PARTIAL PASS**: Fine-tuned model scores 60-74% with ≥400% improvement

❌ **FAIL**: Fine-tuned model scores <60% or improvement <400%

---

## Cost Analysis

### Platform Cost Tracking Test

This test also validates the cost management system:

1. **Forecast Accuracy**: Compare predicted cost ($18-22) vs actual cost
2. **Real-time Tracking**: Verify cost updates every 30 seconds
3. **Budget Alerts**: If budget set, ensure alerts trigger at 80%
4. **Provider Selection**: Confirm platform selected cheapest available provider
5. **Final Cost Breakdown**: Validate cost calculation and invoice generation

**Success**: Cost forecast within 15% of actual, all tracking events recorded

---

## Troubleshooting

### Issue: Training loss not decreasing

**Possible causes**:
- Learning rate too high (reduce to 1e-4)
- Batch size too large (reduce to 2)
- Dataset issues (check formatting)

### Issue: Model gives generic answers

**Possible causes**:
- Not enough training epochs (increase to 5)
- LoRA rank too low (increase to 32)
- Need more training data (add more Q&A pairs)

### Issue: High validation loss (>1.0)

**Possible causes**:
- Overfitting (reduce epochs to 2)
- Add dropout regularization
- Increase training data diversity

---

## Alternative Models to Try

If Mistral 7B doesn't work well:

1. **Llama 2 7B Chat**: Better instruction following, slightly more expensive
2. **Qwen 7B**: Excellent for technical Q&A, multilingual
3. **Zephyr 7B**: Fine-tuned Mistral variant, good for chat
4. **Falcon 7B**: Efficient architecture, fast inference

---

## Next Steps After Successful Test

1. **Expand Dataset**: Add 100-200 more Q&A pairs for broader coverage
2. **Multi-turn Conversations**: Test follow-up questions and context
3. **Production Deployment**: Deploy fine-tuned model with inference API
4. **User Testing**: Have team members ask questions and rate answers
5. **Continuous Improvement**: Collect incorrect answers and retrain

---

## Documentation of Results

Create a results document with:

1. Training metrics (loss curves, timing, cost)
2. Test scores (all 3 phases, baseline vs fine-tuned)
3. Example Q&A outputs (good and bad)
4. Cost analysis (predicted vs actual)
5. Lessons learned and recommendations

Save results in: `test_data/results/test_run_YYYY-MM-DD.md`

---

## Conclusion

This test plan validates:

✅ The platform can orchestrate fine-tuning successfully
✅ Cost tracking and provider selection work correctly
✅ Fine-tuned models learn domain-specific knowledge
✅ The complete system operates end-to-end

**Success = Functional platform + Knowledgeable fine-tuned model**
