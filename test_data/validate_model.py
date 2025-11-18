#!/usr/bin/env python3
"""
Model Validation Script for Domain Q&A Test

This script tests both baseline and fine-tuned models on the domain Q&A dataset
and generates a comprehensive evaluation report.

Usage:
    python validate_model.py --base_model mistralai/Mistral-7B-v0.1 \
                             --finetuned_model ./output/mistral-platform-qa \
                             --output_file results/test_run_2024-11-18.json
"""

import json
import argparse
from typing import List, Dict, Tuple
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


# Test questions organized by phase
TEST_QUESTIONS = {
    "phase1_direct": [
        {
            "question": "What is the n8n Model Orchestration Platform?",
            "key_facts": ["orchestrating fine-tuning", "open-source language models", "private data", "multiple VPS providers", "cost tracking"]
        },
        {
            "question": "Which VPS providers are supported by the platform?",
            "key_facts": ["RunPod", "Vast.ai", "Lambda Labs", "Modal", "TensorDock", "CoreWeave"]
        },
        {
            "question": "How does the cost tracking system work?",
            "key_facts": ["30 seconds", "TimescaleDB", "ML-based forecasting", "budget", "80%"]
        },
        {
            "question": "How much does it cost to fine-tune Llama 2 7B with LoRA?",
            "key_facts": ["4-6 hours", "A100", "$16", "$22", "provider"]
        },
        {
            "question": "What technology stack powers the backend?",
            "key_facts": ["Python 3.11", "FastAPI", "PostgreSQL", "TimescaleDB", "Redis", "n8n", "MinIO"]
        },
        {
            "question": "How does automatic failover work?",
            "key_facts": ["checkpoint", "alternative provider", "resume training", "n8n workflows"]
        },
        {
            "question": "What GPU types are available across providers?",
            "key_facts": ["RTX 3090", "RTX 4090", "A100", "H100", "40GB", "80GB"]
        },
        {
            "question": "How does budget management prevent overspending?",
            "key_facts": ["budget limit", "80%", "alert", "hard limit", "automatically stop"]
        },
        {
            "question": "What React components are included in the UI library?",
            "key_facts": ["MetricCard", "JobStatusBadge", "CostDisplay", "ProgressBar", "TypeScript", "TailwindCSS"]
        },
        {
            "question": "How does spot instance support work?",
            "key_facts": ["50-80%", "savings", "checkpointing", "15 minutes", "interruption", "automatic resume"]
        }
    ],

    "phase2_paraphrased": [
        {
            "question": "Tell me about the n8n orchestration system for ML models",
            "key_facts": ["fine-tuning", "language models", "VPS providers", "cost management"]
        },
        {
            "question": "What cloud GPU providers can I use?",
            "key_facts": ["RunPod", "Vast.ai", "Lambda", "Modal"]
        },
        {
            "question": "How often does the system check my spending?",
            "key_facts": ["30 seconds"]
        },
        {
            "question": "What's the price range for fine-tuning a Llama model with LoRA?",
            "key_facts": ["$16", "$22", "4-6 hours"]
        },
        {
            "question": "Which database technologies does the backend use?",
            "key_facts": ["PostgreSQL", "TimescaleDB", "Redis"]
        },
        {
            "question": "What happens if my GPU provider goes down during training?",
            "key_facts": ["checkpoint", "failover", "alternative provider", "resume"]
        },
        {
            "question": "Can I use consumer GPUs like RTX 3090?",
            "key_facts": ["yes", "RTX 3090", "RunPod", "Vast.ai"]
        },
        {
            "question": "How do I make sure I don't overspend?",
            "key_facts": ["budget", "limit", "alert", "80%"]
        },
        {
            "question": "What UI components help me display costs?",
            "key_facts": ["CostDisplay", "CostChart", "BudgetGauge"]
        },
        {
            "question": "Is it cheaper to use spot instances?",
            "key_facts": ["50-80%", "savings", "interruption"]
        }
    ],

    "phase3_reasoning": [
        {
            "question": "If I have a $1000 monthly budget and want to fine-tune 3 Llama 2 7B models, will I stay within budget?",
            "key_facts": ["$20", "3", "$60", "within budget", "yes"],
            "reasoning": True
        },
        {
            "question": "Which provider would you recommend for a 6-hour training job if I want the lowest cost?",
            "key_facts": ["Vast.ai", "$16"],
            "reasoning": True
        },
        {
            "question": "What happens if I'm at 85% of my budget and submit a job estimated at $25?",
            "key_facts": ["alert", "80%", "allowed", "hard limit"],
            "reasoning": True
        },
        {
            "question": "If a provider fails after 2 hours of a 4-hour job, how much training time is lost?",
            "key_facts": ["checkpoint", "minimal", "15 minutes", "resume"],
            "reasoning": True
        },
        {
            "question": "What's the total cost if I run 10 jobs per month averaging $18 each?",
            "key_facts": ["10", "$18", "$180"],
            "reasoning": True
        }
    ]
}


def load_model(model_path: str, is_peft: bool = False, base_model_path: str = None):
    """Load model and tokenizer"""
    print(f"Loading model from {model_path}...")

    tokenizer = AutoTokenizer.from_pretrained(
        base_model_path if is_peft else model_path,
        trust_remote_code=True
    )

    if not tokenizer.pad_token:
        tokenizer.pad_token = tokenizer.eos_token

    if is_peft:
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        model = PeftModel.from_pretrained(base_model, model_path)
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )

    model.eval()
    print("Model loaded successfully")
    return model, tokenizer


def generate_answer(model, tokenizer, question: str, max_length: int = 512) -> str:
    """Generate answer for a question"""
    prompt = f"Question: {question}\nAnswer:"

    inputs = tokenizer(prompt, return_tensors="pt", padding=True)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            num_return_sequences=1,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )

    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Extract only the answer part (after "Answer:")
    if "Answer:" in answer:
        answer = answer.split("Answer:", 1)[1].strip()

    return answer


def evaluate_answer(question: str, answer: str, key_facts: List[str], is_reasoning: bool = False) -> Dict:
    """
    Evaluate answer quality based on factual accuracy, completeness, and relevance
    Returns scores and detailed breakdown
    """
    answer_lower = answer.lower()

    # 1. Factual Accuracy - check for key facts
    facts_found = sum(1 for fact in key_facts if fact.lower() in answer_lower)
    factual_score = facts_found / len(key_facts) if key_facts else 0.0

    # 2. Completeness - based on answer length and fact coverage
    min_length = 50 if not is_reasoning else 30
    length_ok = len(answer) >= min_length
    completeness_score = 1.0 if (factual_score >= 0.7 and length_ok) else \
                         0.7 if factual_score >= 0.5 else \
                         0.4 if factual_score >= 0.3 else 0.0

    # 3. Relevance - check if answer addresses the question
    question_keywords = set(word.lower() for word in question.split() if len(word) > 3)
    answer_keywords = set(word.lower() for word in answer.split() if len(word) > 3)
    keyword_overlap = len(question_keywords & answer_keywords) / max(len(question_keywords), 1)
    relevance_score = 1.0 if keyword_overlap >= 0.3 else \
                      0.7 if keyword_overlap >= 0.15 else \
                      0.4 if keyword_overlap >= 0.05 else 0.0

    # Combined score with weights
    combined_score = (factual_score * 0.5) + (completeness_score * 0.3) + (relevance_score * 0.2)

    return {
        "factual_score": round(factual_score, 3),
        "facts_found": facts_found,
        "total_facts": len(key_facts),
        "completeness_score": round(completeness_score, 3),
        "relevance_score": round(relevance_score, 3),
        "combined_score": round(combined_score, 3),
        "answer_length": len(answer),
        "is_correct": combined_score >= 0.75
    }


def run_evaluation(model, tokenizer, test_questions: Dict, model_name: str) -> Dict:
    """Run full evaluation across all test phases"""
    results = {
        "model_name": model_name,
        "timestamp": datetime.now().isoformat(),
        "phases": {}
    }

    total_score = 0
    total_questions = 0
    total_correct = 0

    for phase_name, questions in test_questions.items():
        print(f"\nEvaluating {phase_name}...")
        phase_results = []
        phase_score = 0
        phase_correct = 0

        for i, q_data in enumerate(questions, 1):
            question = q_data["question"]
            key_facts = q_data["key_facts"]
            is_reasoning = q_data.get("reasoning", False)

            print(f"  Question {i}/{len(questions)}: {question[:60]}...")

            # Generate answer
            answer = generate_answer(model, tokenizer, question)

            # Evaluate
            eval_result = evaluate_answer(question, answer, key_facts, is_reasoning)

            # Store result
            question_result = {
                "question": question,
                "answer": answer,
                "key_facts": key_facts,
                "evaluation": eval_result
            }
            phase_results.append(question_result)

            # Update counters
            phase_score += eval_result["combined_score"]
            if eval_result["is_correct"]:
                phase_correct += 1

            print(f"    Score: {eval_result['combined_score']:.3f} | "
                  f"Facts: {eval_result['facts_found']}/{eval_result['total_facts']}")

        # Calculate phase statistics
        phase_avg_score = phase_score / len(questions)
        phase_accuracy = (phase_correct / len(questions)) * 100

        results["phases"][phase_name] = {
            "questions": phase_results,
            "statistics": {
                "total_questions": len(questions),
                "correct_answers": phase_correct,
                "accuracy": round(phase_accuracy, 2),
                "average_score": round(phase_avg_score, 3)
            }
        }

        print(f"  Phase Results: {phase_correct}/{len(questions)} correct ({phase_accuracy:.1f}%)")
        print(f"  Average Score: {phase_avg_score:.3f}")

        total_score += phase_score
        total_questions += len(questions)
        total_correct += phase_correct

    # Overall statistics
    overall_accuracy = (total_correct / total_questions) * 100
    overall_avg_score = total_score / total_questions

    results["overall"] = {
        "total_questions": total_questions,
        "correct_answers": total_correct,
        "accuracy": round(overall_accuracy, 2),
        "average_score": round(overall_avg_score, 3)
    }

    print(f"\n{'='*60}")
    print(f"OVERALL RESULTS: {total_correct}/{total_questions} correct ({overall_accuracy:.1f}%)")
    print(f"Average Score: {overall_avg_score:.3f}")
    print(f"{'='*60}")

    return results


def generate_comparison_report(baseline_results: Dict, finetuned_results: Dict) -> Dict:
    """Generate comparison report between baseline and fine-tuned models"""
    report = {
        "comparison": {
            "baseline_model": baseline_results["model_name"],
            "finetuned_model": finetuned_results["model_name"],
            "timestamp": datetime.now().isoformat()
        },
        "overall_comparison": {},
        "phase_comparison": {}
    }

    # Overall comparison
    baseline_acc = baseline_results["overall"]["accuracy"]
    finetuned_acc = finetuned_results["overall"]["accuracy"]
    improvement = ((finetuned_acc - baseline_acc) / baseline_acc * 100) if baseline_acc > 0 else float('inf')

    report["overall_comparison"] = {
        "baseline_accuracy": baseline_acc,
        "finetuned_accuracy": finetuned_acc,
        "accuracy_improvement": round(improvement, 2),
        "baseline_avg_score": baseline_results["overall"]["average_score"],
        "finetuned_avg_score": finetuned_results["overall"]["average_score"],
        "test_passed": improvement >= 600  # 600% improvement threshold
    }

    # Phase-by-phase comparison
    for phase_name in baseline_results["phases"].keys():
        baseline_phase = baseline_results["phases"][phase_name]["statistics"]
        finetuned_phase = finetuned_results["phases"][phase_name]["statistics"]

        phase_improvement = ((finetuned_phase["accuracy"] - baseline_phase["accuracy"]) /
                           baseline_phase["accuracy"] * 100) if baseline_phase["accuracy"] > 0 else float('inf')

        report["phase_comparison"][phase_name] = {
            "baseline_accuracy": baseline_phase["accuracy"],
            "finetuned_accuracy": finetuned_phase["accuracy"],
            "improvement": round(phase_improvement, 2),
            "baseline_avg_score": baseline_phase["average_score"],
            "finetuned_avg_score": finetuned_phase["average_score"]
        }

    return report


def print_comparison_report(report: Dict):
    """Print formatted comparison report"""
    print("\n" + "="*70)
    print("BASELINE vs FINE-TUNED MODEL COMPARISON")
    print("="*70)

    print(f"\nBaseline Model: {report['comparison']['baseline_model']}")
    print(f"Fine-tuned Model: {report['comparison']['finetuned_model']}")

    print("\n" + "-"*70)
    print("OVERALL RESULTS")
    print("-"*70)

    overall = report["overall_comparison"]
    print(f"Baseline Accuracy:     {overall['baseline_accuracy']:>6.2f}%")
    print(f"Fine-tuned Accuracy:   {overall['finetuned_accuracy']:>6.2f}%")
    print(f"Improvement:           {overall['accuracy_improvement']:>6.2f}%")
    print(f"\nBaseline Avg Score:    {overall['baseline_avg_score']:>6.3f}")
    print(f"Fine-tuned Avg Score:  {overall['finetuned_avg_score']:>6.3f}")

    status = "✅ PASSED" if overall["test_passed"] else "❌ FAILED"
    print(f"\nTest Status: {status}")
    print(f"(Requirement: ≥600% improvement)")

    print("\n" + "-"*70)
    print("PHASE-BY-PHASE COMPARISON")
    print("-"*70)

    for phase_name, phase_data in report["phase_comparison"].items():
        print(f"\n{phase_name}:")
        print(f"  Baseline:    {phase_data['baseline_accuracy']:>6.2f}% | Avg Score: {phase_data['baseline_avg_score']:.3f}")
        print(f"  Fine-tuned:  {phase_data['finetuned_accuracy']:>6.2f}% | Avg Score: {phase_data['finetuned_avg_score']:.3f}")
        print(f"  Improvement: {phase_data['improvement']:>6.2f}%")

    print("\n" + "="*70)


def main():
    parser = argparse.ArgumentParser(description="Validate fine-tuned model on domain Q&A")
    parser.add_argument("--base_model", required=True, help="Base model path or HuggingFace ID")
    parser.add_argument("--finetuned_model", help="Fine-tuned model path (LoRA adapters)")
    parser.add_argument("--output_file", default="results/validation_results.json",
                       help="Output file for results")
    parser.add_argument("--skip_baseline", action="store_true",
                       help="Skip baseline evaluation (only test fine-tuned)")

    args = parser.parse_args()

    results = {}

    # Evaluate baseline model
    if not args.skip_baseline:
        print("\n" + "="*70)
        print("EVALUATING BASELINE MODEL")
        print("="*70)
        base_model, base_tokenizer = load_model(args.base_model)
        baseline_results = run_evaluation(base_model, base_tokenizer, TEST_QUESTIONS, args.base_model)
        results["baseline"] = baseline_results

        # Free memory
        del base_model
        del base_tokenizer
        torch.cuda.empty_cache()

    # Evaluate fine-tuned model
    if args.finetuned_model:
        print("\n" + "="*70)
        print("EVALUATING FINE-TUNED MODEL")
        print("="*70)
        ft_model, ft_tokenizer = load_model(
            args.finetuned_model,
            is_peft=True,
            base_model_path=args.base_model
        )
        finetuned_results = run_evaluation(ft_model, ft_tokenizer, TEST_QUESTIONS, args.finetuned_model)
        results["finetuned"] = finetuned_results

    # Generate comparison report
    if "baseline" in results and "finetuned" in results:
        comparison = generate_comparison_report(results["baseline"], results["finetuned"])
        results["comparison"] = comparison
        print_comparison_report(comparison)

    # Save results
    import os
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    with open(args.output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {args.output_file}")


if __name__ == "__main__":
    main()
