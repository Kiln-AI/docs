---
description: Find the best prompt for your task, automatically.
---

# Automatic Prompt Optimizer

{% hint style="warning" %}
**Coming Soon**

Kiln Prompt Optimizer will be in our next release!
{% endhint %}

{% hint style="warning" %}
**Kiln Prompt Optimizer Requires a Kiln Copilot Enterprise Plan**

The Kiln Prompt Optimizer runs on Kiln's servers, and consumes millions of tokens each run. Due to the high cost of running the optimizer, the prompt optimizer is a paid feature.

[Contact us](mailto:support@kiln.tech) to discuss an enterprise plan.
{% endhint %}

Kiln’s Prompt Optimizer automatically finds high-performing prompts for your task. It often beats manual prompt engineering by double-digit gains on evals.

### How It Works

To find the optimal prompt, Kiln Prompt Optimizer combines [Kiln Specs & Evals](../evals-and-specs/), synthetic training dataset generation, and algorithmic reflective prompt evolution.

Instead of human trial-and-error, Kiln will run thousands of automated experiments and iteratively find an optimal prompt for a given model and task.

#### Kiln Specs & Evals Drive Quality

We can't optimize something unless we can measure it, so the heart of our prompt optimizer is [Kiln Specs & Evals](../evals-and-specs/).&#x20;

Follow our guides to create evals that measure your task's quality. The better your evals are at assessing quality, the better the prompt optimizer will work. Some guidance:

* [Create many small evals](https://kiln.tech/blog/you_need_many_small_evals_for_ai_products): it's typically easier to create several small evals focused on one area, than to try to create an all-encompassing eval
* Use [Kiln Specs](../evals-and-specs/specifications.md) to make better evals: our specs system uses AI to refine your LLM-as-Judge for better alignment to human preference

#### Synthetic Training Data and Withheld Eval Data

When you create a Kiln Spec, we generate two separate datasets: **training** and **eval**. During optimization, we keep eval data withheld from training so results stay unbiased.

{% hint style="info" %}
**Legacy Evals May be Missing Training Data**

If you have an eval created before Kiln Spec was added, it may not have a training dataset. You'll need to use [synthetic data generation](../synthetic-data-generation.md) to generate a training dataset, [tag the results](../organizing-datasets.md#using-tags-to-organize-your-dataset), and save the tag as your eval's training dataset tag.
{% endhint %}

#### Reflective Prompt Evolution

Kiln’s Prompt Optimizer is powered by reflective prompt evolution (inspired by [GEPA](https://arxiv.org/abs/2507.19457), with additional optimizations).

At a high level, we start from your prompt as a baseline, then run **hundreds of iterative prompt mutations**. Each iteration is scored using evals to verify that changes improve performance, and to catch regressions early.

The process is conceptually similar to fine-tuning, but instead of updating model weights, it focuses entirely on improving the prompt.

### Guide

1. **Create one or more** [**specs or evals**](../evals-and-specs/) that define the desired behaviour of your product.
2. **Choose a base model** that performs reasonably well on your task. If it can perform well on a naive prompt, it's more likely to improve with prompt optimization. The prompt we produce will be optimized for this specific model, and may not work as well on other models.
3. **Run the Prompt Optimizer** to evolve and validate improved prompts. Simply select "Create Prompt" in the UI and follow the steps.

### **Fine Tuning vs Prompt Optimization**

Prompt optimization is typically **faster and easier** than fine-tuning. We generally recommend optimizing your prompt first, because it:

* Produces strong results quickly
* Requires no hyperparameter tuning or data-science skills
* Makes overfitting easier to avoid and detect
* Is easier to deploy (just update your prompt)

|                         | Fine Tuning               | Prompt Optimization          |
| ----------------------- | ------------------------- | ---------------------------- |
| **Effort**              | High                      | Low                          |
| **Optimization Target** | Supervised Training Data  | Evals                        |
| **Time**                | 20m to 1 day              | \~1 hour                     |
| **Interpretability**    | Can't interpret changes   | Easy: read your new prompt   |
| **Deployment Effort**   | High: host a custom model | Low: just change your prompt |

