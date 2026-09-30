---
description: >-
  The Kiln Eval Builder combines evals, synthetic data generation, automatic judge prompt creation,
  and judge alignment into one easy to use feature
---

# Eval Builder

{% hint style="info" %}
**Note:** The Eval Builder requires a Kiln Pro account. Registration is free and easy inside the Kiln app.
{% endhint %}

{% hint style="info" %}
The Eval Builder currently only supports the creation of LLM as Judge evals. For programmatic checks, see [Judge Types](judge-types.md).
{% endhint %}

### What is the Kiln Eval Builder?&#x20;

<figure><img src="../../.gitbook/assets/specs img (1).png" alt="" width="375"><figcaption></figcaption></figure>

The Kiln Eval Builder combines Kiln’s best features into one interactive tool: evals, synthetic data generation, automatic judge prompt creation, and judge alignment. Together they go beyond making an eval manually in several ways:

* **Identify Gaps with AI**: Describe what to check in plain language. Kiln asks clarifying questions where your description could use more clarity, then rewrites it into an eval you review and edit.
* **Uses Your Tools and Skills**: you pick the run config to evaluate. Kiln uses its tools and skills to write the clarifying questions and the judge, then runs that config to create the eval data.
* **Interactive Human Alignment & Accuracy**: Building a LLM-as-Judge as good as a human isn’t easy. Human judges make subtle and subjective decisions, and have a hard time articulating their judgement process in a way LLMs can duplicate. You review a sample of the judge's results and agree or disagree with each claim it makes. Kiln uses your feedback to improve the judge and re-check your data, and you can repeat until your judge is aligned to your preference.
* **Dataset Planning**: Kiln drafts a plan for your eval dataset that mixes items your agent should pass with items designed to tempt it into failing. Before your task runs, you can remove items, or refine the plan with your own guidance or a different size, from a 20-item Smoke Test to a 120-item Deep dataset.
* **Automatic Synthetic Data**: Kiln generates each planned item, then runs your task and the judge on it with your own API keys. By the time you save your eval you'll have datasets for evals and training, plus a golden dataset you've reviewed.
* **Multi-turn Tasks**: for [multi-turn tasks](../multi-turn-tasks.md), a simulated user holds each test conversation with your agent, up to a turn limit you set, and the judge scores the whole conversation.
* **Judge Meta-prompting**: Humans often struggle at writing effective eval judge prompts. Our judge meta-prompting takes your issues and concerns in human terms, and turns them into accurate and judge-able evals.
* **Easy to Use**: Subject matter experts can easily create accurate evals, without a lengthy iteration loop with data scientists. The Eval Builder will walk you through all the steps of defining your judge, creating synthetic data, golden dataset, aligning your judge, and creating training datasets. You get the same rigorous process, without managing each step.

### How to Get Started

Getting started is easy:

* Open the Kiln App to any task
* Click "Evals" in the sidebar
* Click "Create Eval"
* Connect Kiln Pro account (if you haven’t already)
* Describe what the eval should check, click "Write My Eval", and pick the run config to evaluate
* Follow the interactive steps until complete!

