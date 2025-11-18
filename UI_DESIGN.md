# UI/UX Design Specifications

## Overview

This document outlines the user interface and user experience design for the n8n Model Orchestration Platform. The UI is designed to be intuitive, powerful, and accessible to both ML engineers and business users.

## Design Principles

### 1. Clarity Over Complexity
- Clear visual hierarchy
- Progressive disclosure of advanced features
- Contextual help and tooltips
- Plain language over jargon

### 2. Efficiency First
- Quick actions accessible within 2 clicks
- Keyboard shortcuts for power users
- Bulk operations support
- Smart defaults

### 3. Transparency
- Real-time status updates
- Clear cost implications
- Visible system state
- Informative error messages

### 4. Responsiveness
- Works on desktop, tablet, and mobile
- Fast loading times (<2s initial load)
- Optimistic UI updates
- Real-time data streaming

## Technology Stack

### Frontend Framework
```json
{
  "framework": "React 18.2+",
  "language": "TypeScript 5.0+",
  "styling": "TailwindCSS 3.3+",
  "components": "shadcn/ui",
  "charts": "Recharts",
  "forms": "React Hook Form + Zod",
  "state": "TanStack Query (React Query)",
  "routing": "React Router v6",
  "websockets": "Socket.io Client",
  "animations": "Framer Motion",
  "icons": "Lucide React"
}
```

## Layout Structure

### Main Layout

```
┌────────────────────────────────────────────────────────────┐
│  Header (64px)                                             │
│  [Logo] [Navigation] [Search] [Notifications] [User Menu] │
├────────────────────────────────────────────────────────────┤
│ Side │                                                     │
│ Nav  │         Main Content Area                          │
│ 240px│                                                     │
│      │                                                     │
│      │                                                     │
│      │                                                     │
└──────┴─────────────────────────────────────────────────────┘
```

### Color Palette

```css
/* Primary Colors */
--primary-500: #6366f1;      /* Indigo - Primary actions */
--primary-600: #4f46e5;      /* Hover states */
--primary-700: #4338ca;      /* Active states */

/* Semantic Colors */
--success-500: #10b981;      /* Success states, running jobs */
--warning-500: #f59e0b;      /* Warnings, budget alerts */
--error-500: #ef4444;        /* Errors, failed jobs */
--info-500: #3b82f6;         /* Information */

/* Neutral Colors */
--gray-50: #f9fafb;          /* Background */
--gray-100: #f3f4f6;         /* Secondary background */
--gray-200: #e5e7eb;         /* Borders */
--gray-600: #4b5563;         /* Secondary text */
--gray-900: #111827;         /* Primary text */

/* Dark Mode */
--dark-bg: #0f172a;          /* Dark background */
--dark-surface: #1e293b;     /* Dark cards */
--dark-border: #334155;      /* Dark borders */
```

### Typography

```css
/* Font Family */
--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', monospace;

/* Font Sizes */
--text-xs: 0.75rem;     /* 12px */
--text-sm: 0.875rem;    /* 14px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.125rem;    /* 18px */
--text-xl: 1.25rem;     /* 20px */
--text-2xl: 1.5rem;     /* 24px */
--text-3xl: 1.875rem;   /* 30px */
--text-4xl: 2.25rem;    /* 36px */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

## Pages & Views

### 1. Dashboard (Home)

**Purpose**: Overview of system status, active jobs, and key metrics

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Dashboard                                 [Date Range Picker]│
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│ │ Active Jobs  │ │ Total Spend  │ │ Budget Left  │        │
│ │     12       │ │   $456.78    │ │   $543.22    │        │
│ │              │ │              │ │              │        │
│ │ +2 vs last hr│ │ +$12.34/hr   │ │ 54% remaining│        │
│ └──────────────┘ └──────────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────────────┤
│ Running Jobs                              [View All →]      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ llama-2-7b-finetuning                                   │ │
│ │ Status: Training • Progress: 65% • Cost: $12.45        │ │
│ │ GPU: 4x A100 (RunPod) • Started: 2h 15m ago            │ │
│ │ [View] [Stop] [Logs]                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ gpt-neo-1.3b-custom                                     │ │
│ │ Status: Initializing • Progress: 5% • Cost: $1.23      │ │
│ │ GPU: 1x RTX 4090 (Vast.ai) • Started: 12m ago          │ │
│ │ [View] [Stop] [Logs]                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Cost Trends (Last 7 Days)                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │        [Line Chart: Daily Cost]                         │ │
│ │    $                                                     │ │
│ │    │     ╱╲                                             │ │
│ │    │   ╱    ╲    ╱                                      │ │
│ │    │ ╱        ╲╱                                        │ │
│ │    └─────────────────────────────────────               │ │
│ │      Mon  Tue  Wed  Thu  Fri  Sat  Sun                 │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Provider Usage                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ RunPod      ████████████░░░░░░░░  60% ($276.45)        │ │
│ │ Vast.ai     ██████░░░░░░░░░░░░░░  30% ($138.22)        │ │
│ │ Lambda Labs ██░░░░░░░░░░░░░░░░░░  10% ($45.89)         │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Key Features**:
- Real-time metrics with auto-refresh
- Quick access to running jobs
- Cost visualization
- Provider distribution
- Recent activity feed

**Components**:
```tsx
// Dashboard.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LineChart, BarChart } from "recharts"

export function Dashboard() {
  const { data: metrics } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: fetchDashboardMetrics,
    refetchInterval: 30000 // 30 seconds
  })

  return (
    <div className="p-6 space-y-6">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MetricCard
          title="Active Jobs"
          value={metrics.activeJobs}
          change={metrics.jobsChange}
          icon={<Activity />}
        />
        <MetricCard
          title="Total Spend"
          value={formatCurrency(metrics.totalSpend)}
          change={metrics.spendChange}
          icon={<DollarSign />}
        />
        <MetricCard
          title="Budget Remaining"
          value={formatCurrency(metrics.budgetRemaining)}
          percent={metrics.budgetPercent}
          icon={<Wallet />}
        />
      </div>

      {/* Running Jobs */}
      <Card>
        <CardHeader>
          <CardTitle>Running Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          <JobList jobs={metrics.runningJobs} />
        </CardContent>
      </Card>

      {/* Cost Trends */}
      <Card>
        <CardHeader>
          <CardTitle>Cost Trends</CardTitle>
        </CardHeader>
        <CardContent>
          <CostChart data={metrics.costTrends} />
        </CardContent>
      </Card>
    </div>
  )
}
```

---

### 2. Training Jobs Page

**Purpose**: Manage all training jobs (create, view, monitor, stop)

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Training Jobs                         [+ New Training Job]   │
├─────────────────────────────────────────────────────────────┤
│ [Search...] [Filter: All ▼] [Status: All ▼] [Provider: All ▼]│
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Job Name        Status      GPU Type   Cost    Actions  │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ llama-2-7b...   🟢 Running  4x A100   $12.45  [···]    │ │
│ │ gpt-neo-1.3b... 🟡 Queue    1x 4090   $0.00   [···]    │ │
│ │ mistral-7b...   ✅ Complete  2x A100   $45.67  [···]    │ │
│ │ falcon-40b...   ❌ Failed    8x A100   $23.12  [···]    │ │
│ │ bloom-560m...   🟢 Running  1x 3090   $3.45   [···]    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                       [< Prev] [1 2 3] [Next >]│
└─────────────────────────────────────────────────────────────┘
```

**Job Detail Modal**:
```
┌─────────────────────────────────────────────────────────────┐
│ llama-2-7b-finetuning                              [× Close] │
├─────────────────────────────────────────────────────────────┤
│ [Overview] [Metrics] [Logs] [Checkpoints] [Cost]            │
├─────────────────────────────────────────────────────────────┤
│ Status: 🟢 Training                                          │
│ Progress: ████████████████████░░░░░░░░ 65%                 │
│                                                              │
│ Details:                                                     │
│ • Model: meta-llama/Llama-2-7b-hf                          │
│ • Dataset: custom-dataset-v2 (50,000 samples)              │
│ • Provider: RunPod                                          │
│ • GPU: 4x NVIDIA A100 40GB                                 │
│ • Region: US-West                                           │
│ • Started: 2024-11-18 10:23 AM (2h 15m ago)               │
│                                                              │
│ Cost Information:                                            │
│ • Current Cost: $12.45                                      │
│ • Estimated Total: $18.50 - $22.00                         │
│ • Rate: $5.40/hour                                          │
│                                                              │
│ Training Metrics:                                            │
│ • Epoch: 3/10                                               │
│ • Training Loss: 0.342                                      │
│ • Validation Loss: 0.387                                    │
│ • Learning Rate: 2.5e-5                                     │
│ • Tokens/sec: 1,245                                         │
│                                                              │
│                           [Stop Training] [View Full Logs]  │
└─────────────────────────────────────────────────────────────┘
```

**Create Job Form**:
```
┌─────────────────────────────────────────────────────────────┐
│ Create Training Job                           [1/4 Basic]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Job Name *                                                   │
│ [llama-2-7b-finetuning                    ]                 │
│                                                              │
│ Model Selection *                                            │
│ [Search models...                          ▼]               │
│ ┌──────────────────────────────────────────────────┐        │
│ │ 📊 meta-llama/Llama-2-7b-hf                      │        │
│ │    7B parameters • Recommended                   │        │
│ │                                                  │        │
│ │ 📊 meta-llama/Llama-2-13b-hf                     │        │
│ │    13B parameters                                │        │
│ └──────────────────────────────────────────────────┘        │
│                                                              │
│ Dataset *                                                    │
│ [Select dataset...                         ▼]               │
│                                                              │
│ Training Type *                                              │
│ ○ Full Fine-tuning                                          │
│ ● LoRA (Low-Rank Adaptation) - Recommended                 │
│ ○ QLoRA (Quantized LoRA)                                    │
│                                                              │
│                                    [Cancel] [Next: Hardware →]│
└─────────────────────────────────────────────────────────────┘
```

---

### 3. Models Page

**Purpose**: Browse, search, and manage model library

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Models                               [Upload Model] [Import] │
├─────────────────────────────────────────────────────────────┤
│ [Search models...] [Category: All ▼] [Size: All ▼]          │
│                                                              │
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│
│ │ 🦙        │ │ 🤖        │ │ 🦅        │ │ 🔮        ││
│ │ Llama 2   │ │ GPT-Neo   │ │ Falcon    │ │ Mistral   ││
│ │ 7B        │ │ 1.3B      │ │ 7B        │ │ 7B        ││
│ │           │ │           │ │           │ │           ││
│ │ Popular   │ │ Fast      │ │ Efficient │ │ New       ││
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘│
│                                                              │
│ Recent Models                                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ meta-llama/Llama-2-7b-hf                                │ │
│ │ 7B parameters • Last used: 2 hours ago                  │ │
│ │ [Train] [View Details]                                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ Custom Models                                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ my-custom-llama-v2                                      │ │
│ │ Fine-tuned from Llama-2-7b • Created: Nov 15, 2024     │ │
│ │ [Deploy] [Train More] [Share]                           │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. Datasets Page

**Purpose**: Upload, manage, and version training datasets

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Datasets                             [Upload Dataset] [Import]│
├─────────────────────────────────────────────────────────────┤
│ [Search...] [Type: All ▼] [Sort: Recent ▼]                  │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📊 customer-support-conversations                       │ │
│ │ JSONL • 50,000 samples • 125 MB • Updated 2h ago       │ │
│ │ v2.1 (3 versions) • Private                            │ │
│ │ [Preview] [Use in Training] [Version History] [···]    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 📊 code-generation-dataset                              │ │
│ │ Parquet • 100,000 samples • 450 MB • Updated 1d ago    │ │
│ │ v1.0 • Public                                           │ │
│ │ [Preview] [Use in Training] [Version History] [···]    │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Dataset Preview Modal**:
```
┌─────────────────────────────────────────────────────────────┐
│ customer-support-conversations                     [× Close] │
├─────────────────────────────────────────────────────────────┤
│ [Overview] [Schema] [Samples] [Statistics]                  │
├─────────────────────────────────────────────────────────────┤
│ Dataset Information:                                         │
│ • Format: JSONL                                             │
│ • Samples: 50,000                                           │
│ • Size: 125 MB                                              │
│ • Created: Nov 15, 2024                                     │
│ • Updated: Nov 18, 2024                                     │
│                                                              │
│ Schema:                                                      │
│ {                                                            │
│   "prompt": "string",                                       │
│   "response": "string",                                     │
│   "category": "string",                                     │
│   "rating": "number"                                        │
│ }                                                            │
│                                                              │
│ Sample Data:                                                 │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ {                                                    │   │
│ │   "prompt": "How do I reset my password?",          │   │
│ │   "response": "To reset your password, click...",   │   │
│ │   "category": "account",                            │   │
│ │   "rating": 4.5                                     │   │
│ │ }                                                    │   │
│ └──────────────────────────────────────────────────────┘   │
│                                  [Use in Training] [Download]│
└─────────────────────────────────────────────────────────────┘
```

---

### 5. Cost Dashboard

**Purpose**: Detailed cost analytics and budget management

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Cost Dashboard                        [Date Range: Last 30d ▼]│
├─────────────────────────────────────────────────────────────┤
│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│
│ │Total Spend │ │ This Month │ │Budget Used │ │Avg Daily   ││
│ │ $1,234.56  │ │  $456.78   │ │    67%     │ │ $15.23     ││
│ └────────────┘ └────────────┘ └────────────┘ └────────────┘│
├─────────────────────────────────────────────────────────────┤
│ Cost Trend                                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │  $                                                       │ │
│ │  │     [Area Chart: Daily Cost Over Time]              │ │
│ │  │       ████                                           │ │
│ │  │     ██░░░░██                                         │ │
│ │  │   ██░░░░░░░░██                                       │ │
│ │  └──────────────────────────────────────────            │ │
│ │    Week 1  Week 2  Week 3  Week 4                      │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Cost Breakdown                                               │
│ ┌────────────────────┐ ┌────────────────────────────────┐  │
│ │  By Provider       │ │  By GPU Type                   │  │
│ │  [Pie Chart]       │ │  A100    ████████ 65% $802.45 │  │
│ │                    │ │  RTX4090 ████░░░░ 25% $308.64 │  │
│ │  RunPod    60%     │ │  RTX3090 ██░░░░░░ 10% $123.47 │  │
│ │  Vast.ai   30%     │ └────────────────────────────────┘  │
│ │  Lambda    10%     │                                     │
│ └────────────────────┘                                     │
├─────────────────────────────────────────────────────────────┤
│ Budget Management                             [Edit Budgets] │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Monthly Budget                                          │ │
│ │ ████████████████████░░░░░░░░░ 67% ($456.78 / $680.00) │ │
│ │ 13 days remaining • On track                           │ │
│ │                                                         │ │
│ │ Daily Budget                                            │ │
│ │ ████████████░░░░░░░░░░░░░░░░░ 45% ($15.23 / $34.00)  │ │
│ │ 8 hours remaining • Under budget ✓                     │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ Cost Optimization Recommendations                            │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 💡 Switch to Vast.ai for RTX 4090 jobs                 │ │
│ │    Potential savings: $45.23/week                       │ │
│ │    [Learn More] [Apply]                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 💡 Use spot instances for fault-tolerant workloads      │ │
│ │    Potential savings: $120.50/month (35%)               │ │
│ │    [Learn More] [Apply]                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

### 6. Providers Page

**Purpose**: Manage VPS provider configurations and monitor health

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Providers                                  [+ Add Provider]  │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🟢 RunPod                                    [Enabled]   │ │
│ │ Status: Healthy • Last checked: 2m ago                  │ │
│ │ Available GPUs: 145 • Avg Response: 245ms              │ │
│ │ Current Jobs: 3 • Total Spent: $276.45                 │ │
│ │ [Configure] [View Instances] [Disable]                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🟢 Vast.ai                                   [Enabled]   │ │
│ │ Status: Healthy • Last checked: 1m ago                  │ │
│ │ Available GPUs: 89 • Avg Response: 312ms               │ │
│ │ Current Jobs: 2 • Total Spent: $138.22                 │ │
│ │ [Configure] [View Instances] [Disable]                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🟢 Lambda Labs                               [Enabled]   │ │
│ │ Status: Healthy • Last checked: 3m ago                  │ │
│ │ Available GPUs: 23 • Avg Response: 189ms               │ │
│ │ Current Jobs: 1 • Total Spent: $45.89                  │ │
│ │ [Configure] [View Instances] [Disable]                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ⚪ Modal                                     [Disabled]  │ │
│ │ Status: Not configured                                  │ │
│ │ [Configure] [Enable]                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Provider Configuration Modal**:
```
┌─────────────────────────────────────────────────────────────┐
│ Configure RunPod                                   [× Close] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ API Key *                                                    │
│ [********************************]                          │
│ [Test Connection]                                           │
│                                                              │
│ Preferences                                                  │
│ ☑ Enable for new jobs                                      │
│ ☑ Allow spot instances                                     │
│ ☐ Preferred provider                                       │
│                                                              │
│ Resource Limits                                              │
│ Max concurrent jobs: [5                ]                    │
│ Max cost per job:    [$100.00          ]                   │
│                                                              │
│ Regions                                                      │
│ ☑ US-West                                                   │
│ ☑ US-East                                                   │
│ ☐ EU-West                                                   │
│ ☐ Asia-Pacific                                              │
│                                                              │
│ Webhooks (Optional)                                          │
│ Webhook URL: [https://...                ]                  │
│                                                              │
│                                   [Cancel] [Save & Test]    │
└─────────────────────────────────────────────────────────────┘
```

---

### 7. n8n Workflows Page

**Purpose**: Manage and monitor n8n automation workflows

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Workflows                           [+ Create Workflow]      │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🟢 Auto Fine-Tuning Pipeline                [Active]    │ │
│ │ Executions: 156 • Success Rate: 98.7%                  │ │
│ │ Last run: 15m ago • Next run: 45m                      │ │
│ │ [Edit] [Logs] [Disable]                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🟢 Cost Monitoring & Alerts                 [Active]    │ │
│ │ Executions: 2,341 • Success Rate: 99.9%                │ │
│ │ Last run: 5m ago • Next run: 5m                        │ │
│ │ [Edit] [Logs] [Disable]                                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ⚪ Dataset Preprocessing                    [Inactive]  │ │
│ │ Executions: 45 • Success Rate: 95.6%                   │ │
│ │ Last run: 2d ago                                        │ │
│ │ [Edit] [Logs] [Enable]                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

### 8. Settings Page

**Purpose**: User preferences, API keys, team management

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│ Settings                                                     │
├─────────────────────────────────────────────────────────────┤
│ [Profile] [API Keys] [Notifications] [Team] [Billing]       │
├─────────────────────────────────────────────────────────────┤
│ Profile                                                      │
│                                                              │
│ Name                                                         │
│ [John Doe                          ]                        │
│                                                              │
│ Email                                                        │
│ [john.doe@company.com              ]                        │
│                                                              │
│ Theme                                                        │
│ ○ Light  ● Dark  ○ System                                  │
│                                                              │
│ Timezone                                                     │
│ [UTC-8 (Pacific Time)              ▼]                       │
│                                                              │
│ Language                                                     │
│ [English                           ▼]                       │
│                                                              │
│                                           [Save Changes]     │
└─────────────────────────────────────────────────────────────┘
```

## Component Library

### Core Components

#### 1. MetricCard
```tsx
interface MetricCardProps {
  title: string
  value: string | number
  change?: number
  icon?: React.ReactNode
  trend?: 'up' | 'down' | 'neutral'
}

export function MetricCard({ title, value, change, icon, trend }: MetricCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">{title}</p>
            <p className="text-3xl font-bold mt-2">{value}</p>
            {change && (
              <p className={cn(
                "text-sm mt-2",
                trend === 'up' && "text-green-600",
                trend === 'down' && "text-red-600"
              )}>
                {change > 0 ? '+' : ''}{change}%
              </p>
            )}
          </div>
          {icon && (
            <div className="text-gray-400">
              {icon}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
```

#### 2. JobStatusBadge
```tsx
type JobStatus = 'running' | 'queued' | 'completed' | 'failed' | 'stopped'

interface JobStatusBadgeProps {
  status: JobStatus
}

export function JobStatusBadge({ status }: JobStatusBadgeProps) {
  const config = {
    running: { icon: '🟢', label: 'Running', class: 'bg-green-100 text-green-800' },
    queued: { icon: '🟡', label: 'Queued', class: 'bg-yellow-100 text-yellow-800' },
    completed: { icon: '✅', label: 'Completed', class: 'bg-blue-100 text-blue-800' },
    failed: { icon: '❌', label: 'Failed', class: 'bg-red-100 text-red-800' },
    stopped: { icon: '⏸️', label: 'Stopped', class: 'bg-gray-100 text-gray-800' }
  }

  const { icon, label, class: className } = config[status]

  return (
    <Badge className={className}>
      {icon} {label}
    </Badge>
  )
}
```

#### 3. CostDisplay
```tsx
interface CostDisplayProps {
  amount: number
  period?: 'hour' | 'day' | 'month' | 'total'
  showCurrency?: boolean
}

export function CostDisplay({ amount, period, showCurrency = true }: CostDisplayProps) {
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount)

  return (
    <span className="font-mono">
      {formatted}
      {period && <span className="text-sm text-gray-600">/{period}</span>}
    </span>
  )
}
```

#### 4. ProgressBar
```tsx
interface ProgressBarProps {
  value: number
  max: number
  label?: string
  showPercentage?: boolean
  color?: 'blue' | 'green' | 'yellow' | 'red'
}

export function ProgressBar({
  value,
  max,
  label,
  showPercentage = true,
  color = 'blue'
}: ProgressBarProps) {
  const percentage = (value / max) * 100

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-2">
          <span className="text-sm">{label}</span>
          {showPercentage && (
            <span className="text-sm font-medium">{percentage.toFixed(0)}%</span>
          )}
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className={cn(
            "h-2.5 rounded-full",
            color === 'blue' && "bg-blue-600",
            color === 'green' && "bg-green-600",
            color === 'yellow' && "bg-yellow-600",
            color === 'red' && "bg-red-600"
          )}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}
```

## Real-Time Updates

### WebSocket Integration

```tsx
// useRealtimeUpdates.ts
import { useEffect } from 'react'
import { io, Socket } from 'socket.io-client'
import { useQueryClient } from '@tanstack/react-query'

export function useRealtimeUpdates() {
  const queryClient = useQueryClient()
  const socket: Socket = io(process.env.REACT_APP_WS_URL!)

  useEffect(() => {
    // Job status updates
    socket.on('job:status', (data) => {
      queryClient.invalidateQueries(['jobs', data.jobId])
      queryClient.invalidateQueries(['dashboard-metrics'])
    })

    // Cost updates
    socket.on('cost:update', (data) => {
      queryClient.setQueryData(['job-cost', data.jobId], data.cost)
      queryClient.invalidateQueries(['dashboard-metrics'])
    })

    // Budget alerts
    socket.on('budget:alert', (data) => {
      toast.warning(`Budget alert: ${data.message}`)
    })

    // Provider health
    socket.on('provider:health', (data) => {
      queryClient.invalidateQueries(['providers'])
    })

    return () => {
      socket.disconnect()
    }
  }, [socket, queryClient])
}
```

## Responsive Design

### Breakpoints
```css
/* Mobile: 0-640px */
@media (max-width: 640px) {
  /* Stack cards vertically */
  /* Hide sidebar, show hamburger menu */
  /* Simplified tables */
}

/* Tablet: 641-1024px */
@media (min-width: 641px) and (max-width: 1024px) {
  /* 2-column grid for cards */
  /* Collapsible sidebar */
}

/* Desktop: 1025px+ */
@media (min-width: 1025px) {
  /* Full layout with sidebar */
  /* 3-4 column grids */
}
```

## Accessibility

### WCAG 2.1 AA Compliance
- Color contrast ratio ≥ 4.5:1 for normal text
- Color contrast ratio ≥ 3:1 for large text
- Keyboard navigation support
- Screen reader compatible
- ARIA labels on interactive elements
- Focus indicators
- Alt text for images

### Keyboard Shortcuts
```
Ctrl/Cmd + K      Quick search
Ctrl/Cmd + N      New training job
Ctrl/Cmd + ,      Settings
Esc               Close modals
?                 Show keyboard shortcuts
```

## Performance Optimization

### Code Splitting
```tsx
// Lazy load heavy components
const Dashboard = lazy(() => import('./pages/Dashboard'))
const JobDetail = lazy(() => import('./pages/JobDetail'))
const CostDashboard = lazy(() => import('./pages/CostDashboard'))
```

### Image Optimization
- WebP format with fallbacks
- Lazy loading for images
- Responsive images with srcset
- CDN delivery

### Data Caching
```tsx
// React Query configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // 30 seconds
      cacheTime: 300000, // 5 minutes
      refetchOnWindowFocus: false
    }
  }
})
```

## Summary

This UI design provides:

- **Intuitive Navigation**: Clear hierarchy and easy-to-find features
- **Real-Time Updates**: WebSocket-powered live data
- **Comprehensive Dashboards**: Cost, jobs, models, and providers
- **Responsive Design**: Works on all devices
- **Accessibility**: WCAG 2.1 AA compliant
- **Performance**: Optimized loading and caching
- **Modern Stack**: React 18, TypeScript, TailwindCSS

The design prioritizes clarity, efficiency, and user experience while handling complex ML orchestration workflows.
