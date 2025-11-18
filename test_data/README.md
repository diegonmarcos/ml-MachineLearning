# Domain Q&A Test Suite

## Quick Start

This test validates the platform by fine-tuning **Mistral 7B** on domain-specific knowledge about the ML Orchestration Platform itself.

### 🎯 Test Objective

Prove that a fine-tuned model can learn unique knowledge that only exists in our platform documentation.

### 📊 What's Included

1. **domain_qa_dataset.jsonl** - 50 Q&A pairs about the platform
2. **TEST_PLAN.md** - Complete test methodology and expectations
3. **validate_model.py** - Automated validation script

## Dataset Overview

**50 Q&A pairs covering:**

- System architecture (8 pairs)
- Cost management (10 pairs)
- VPS provider integration (8 pairs)
- n8n workflows (7 pairs)
- API & WebSocket (6 pairs)
- Deployment & infrastructure (5 pairs)
- Security & compliance (6 pairs)

**Format:**
```json
{"prompt": "Question", "response": "Detailed answer with facts"}
```

**Sample:**
```json
{"prompt": "What is the n8n Model Orchestration Platform?", "response": "The n8n Model Orchestration Platform is a comprehensive system for orchestrating fine-tuning of open-source language models using private data across multiple VPS providers..."}
```

## Quick Test

### Step 1: Upload Dataset

```bash
curl -X POST http://localhost:8000/v1/datasets \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "name=domain_qa_dataset" \
  -F "type=jsonl" \
  -F "file=@domain_qa_dataset.jsonl"
```

### Step 2: Submit Fine-tuning Job

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mistral-platform-qa-test",
    "model_name": "mistralai/Mistral-7B-v0.1",
    "dataset_id": "domain_qa_dataset",
    "training_config": {
      "training_type": "lora",
      "epochs": 3,
      "batch_size": 4,
      "learning_rate": 2e-4
    },
    "hardware_requirements": {
      "gpu_type": "A100",
      "gpu_count": 4
    }
  }'
```

### Step 3: Run Validation

```bash
# Wait for training to complete (3-4 hours)

# Run validation script
python validate_model.py \
  --base_model mistralai/Mistral-7B-v0.1 \
  --finetuned_model ./output/mistral-platform-qa \
  --output_file results/test_run_$(date +%Y-%m-%d).json
```

## Expected Results

### Training
- **Duration**: 3-4 hours
- **Cost**: $16-22 (platform selects cheapest provider)
- **Final Loss**: <0.5

### Validation

| Phase | Baseline | Fine-tuned | Improvement |
|-------|----------|------------|-------------|
| Phase 1: Direct Recall (10q) | <10% | 85-95% | ~900% |
| Phase 2: Paraphrased (20q) | <10% | 70-80% | ~750% |
| Phase 3: Reasoning (15q) | <7% | 60-70% | ~900% |
| **Overall (45q)** | **<10%** | **70-80%** | **~700%** |

### Success Criteria

✅ **PASS**: ≥600% improvement over baseline + ≥75% overall accuracy

## Test Questions Examples

### Phase 1: Direct Recall
- "What is the n8n Model Orchestration Platform?"
- "Which VPS providers are supported?"
- "How does the cost tracking system work?"

### Phase 2: Paraphrased
- "Tell me about the n8n orchestration system for ML models"
- "What cloud GPU providers can I use?"
- "How often does the system check my spending?"

### Phase 3: Reasoning
- "If I have a $1000 monthly budget and want to fine-tune 3 Llama 2 7B models, will I stay within budget?"
- "Which provider would you recommend for a 6-hour training job if I want the lowest cost?"

## Validation Script Usage

### Full Comparison
```bash
python validate_model.py \
  --base_model mistralai/Mistral-7B-v0.1 \
  --finetuned_model ./output/mistral-platform-qa \
  --output_file results/full_comparison.json
```

### Skip Baseline (faster)
```bash
python validate_model.py \
  --base_model mistralai/Mistral-7B-v0.1 \
  --finetuned_model ./output/mistral-platform-qa \
  --skip_baseline \
  --output_file results/finetuned_only.json
```

## Output Example

```
======================================================================
BASELINE vs FINE-TUNED MODEL COMPARISON
======================================================================

Baseline Model: mistralai/Mistral-7B-v0.1
Fine-tuned Model: ./output/mistral-platform-qa

----------------------------------------------------------------------
OVERALL RESULTS
----------------------------------------------------------------------
Baseline Accuracy:      8.89%
Fine-tuned Accuracy:   77.78%
Improvement:          775.00%

Baseline Avg Score:    0.123
Fine-tuned Avg Score:  0.782

Test Status: ✅ PASSED
(Requirement: ≥600% improvement)

----------------------------------------------------------------------
PHASE-BY-PHASE COMPARISON
----------------------------------------------------------------------

phase1_direct:
  Baseline:     10.00% | Avg Score: 0.145
  Fine-tuned:   90.00% | Avg Score: 0.887
  Improvement: 800.00%

phase2_paraphrased:
  Baseline:      5.00% | Avg Score: 0.089
  Fine-tuned:   75.00% | Avg Score: 0.756
  Improvement: 1400.00%

phase3_reasoning:
  Baseline:     13.33% | Avg Score: 0.167
  Fine-tuned:   66.67% | Avg Score: 0.678
  Improvement: 400.00%

======================================================================
```

## What This Test Validates

This single test validates the **entire platform**:

✅ **Training Orchestration**
- Job submission and validation
- Provider selection algorithm
- GPU provisioning
- Dataset transfer
- Training execution

✅ **Cost Management**
- Real-time cost tracking (30-second intervals)
- Cost forecasting accuracy
- Provider cost comparison
- Budget compliance

✅ **n8n Workflows**
- Training job orchestration
- Cost tracking automation
- Provider health monitoring
- Job completion handling

✅ **Model Quality**
- Fine-tuned model learns domain knowledge
- Accuracy significantly improves over baseline
- Model can recall facts and reason about them

## Troubleshooting

### Training loss not decreasing
- Reduce learning rate to 1e-4
- Reduce batch size to 2
- Check dataset formatting

### Model gives generic answers
- Increase epochs to 5
- Increase LoRA rank to 32
- Add more training data

### High validation loss (>1.0)
- Reduce epochs to 2 (overfitting)
- Add dropout regularization
- Check data quality

## Next Steps After Success

1. **Expand dataset** to 100-200 Q&A pairs
2. **Test multi-turn conversations** with follow-up questions
3. **Deploy model** with inference API
4. **Collect user feedback** and improve
5. **Continuous retraining** with new data

## Files Structure

```
test_data/
├── README.md                    # This file
├── domain_qa_dataset.jsonl      # 50 Q&A pairs
├── TEST_PLAN.md                 # Detailed test methodology
├── validate_model.py            # Validation script
└── results/                     # Test results (created after running)
    └── test_run_YYYY-MM-DD.json
```

## Cost Breakdown

| Item | Cost | Duration |
|------|------|----------|
| Fine-tuning (Mistral 7B LoRA) | $16-22 | 3-4 hours |
| Inference validation (100 queries) | <$1 | 5-10 minutes |
| **Total** | **~$20** | **~4 hours** |

**Note**: Platform automatically selects cheapest available provider (usually Vast.ai)

## Requirements

### Software
- Python 3.11+
- PyTorch 2.0+
- Transformers 4.35+
- PEFT 0.7+
- 1x GPU with 24GB+ VRAM (for validation)

### Platform Access
- API credentials for the ML Orchestration Platform
- VPS provider API keys (RunPod, Vast.ai, Lambda Labs, etc.)
- Budget allocation ($25 recommended for first test)

## Support

For questions or issues:
1. Check TEST_PLAN.md for detailed methodology
2. Review troubleshooting section above
3. Verify dataset format matches schema
4. Check API credentials and budget

---

**This test is the proof-of-concept for the entire platform!** 🚀

*A successful test means the platform works end-to-end and can produce high-quality fine-tuned models.*
