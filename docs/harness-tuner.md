---
description: >-
  Automatically tune your agent's harness: tools, prompts, skills, model and
  settings.
icon: sliders
---

# Kiln Harness Tuner

[Kiln Harness Tuner](https://github.com/Kiln-AI/harness-tuner) automatically improves an AI agent by tuning its harness: the tools, prompts, skills, model and settings around the model. It is free, open source, and runs on your machine alongside the Kiln app.

Most optimizers tune only the prompt. Harness Tuner tunes everything around the model, and uses your [Kiln evals](evals-and-specs/) to measure every change.

{% embed url="https://youtu.be/UJfpzHJc0PQ" %}

## What It Tunes

* **Tools:** often the biggest win. It rewrites your tools for the agent: smaller responses, better descriptions, no repeated calls. It doesn't touch your original tools. It writes wrappers as [code tools](tools-and-mcp/code-tools.md).
* **Prompts and skills:** it cuts contradictions, adds the requirements nobody wrote down, and moves long instructions into [skills](skills.md) that load only when needed.
* **Model and settings:** it tunes thinking level, temperature and the rest. It keeps your model by default. Allow other models at start-up, or optimize for speed or cost, and it also searches models and providers.
* **RAG, fine-tunes and sub-agents:** it attaches, swaps or drops the ones in your project.

It tries different methods, not just different words: one big prompt or skills, RAG or a skill, many small tools or one general one.

## How It Works

Harness Tuner runs experiments in a loop. Each experiment builds a new run configuration for your task, and your evals measure it against the current best.

* **You set the goal and steer:** optimize for quality, cost or speed. When it cuts cost or latency, it holds quality. Tell it what to focus on and what not to touch, in plain English.
* **Many goals, not one number:** bring all your evals. It tracks every one, and checks every eval before it promotes a change.
* **Targeted experiments:** each experiment runs only the evals it targets, so trying an idea is cheap.
* **Train, validation and test data, kept apart:** the tuner's agents only see training data. Validation data decides which changes are promoted. Test data is never read, so your test score stays a true measure.
* **Several winners, your pick:** it finds the best quality, the cheapest at good quality, a balanced option and the fastest. Compare them side by side in Kiln.
* **Runs on the coding agent you already use:** Claude Code, Codex or OpenCode, on your existing subscription.

<figure><img src="https://github.com/user-attachments/assets/e93e24f6-d964-4ae8-acaf-015b7de37ac6" alt="The Experiment Graph in Kiln, showing how a tuning run progressed"><figcaption><p>Kiln tracks every experiment and shows how the tuning progressed</p></figcaption></figure>

## What You Need

* **The Kiln app**, running on the same machine. See the [quickstart](quickstart.md).
* **A Kiln task with at least one run configuration.** This is the agent you want to tune, and the starting point for experiments. Single-turn and multi-turn [tasks](tasks.md) are both supported.
* **Evals**, each with a training and a validation dataset. See [Evals Drive Quality](harness-tuner.md#evals-drive-quality) below.
* **A coding agent:** Claude Code (the default), Codex or OpenCode. The tuner's agents run on your subscription.
* **Model provider keys**, [added in Kiln](models-and-ai-providers.md). These run the agent being tuned, and your evals.
* [**uv**](https://docs.astral.sh/uv/), to install it.
* **Linux, or macOS on Apple silicon.** Windows is not supported.

The [install guide](https://github.com/Kiln-AI/harness-tuner/blob/main/docs/install.md) has a check and a fix for each requirement.

## Quickstart

Install Harness Tuner and start it:

```bash
uv tool install harness-tuner
harness-tuner
```

It walks you through the rest: connecting to Kiln, picking the project and task to tune, and setting a goal, a budget and a time limit. It then works until the budget or the time runs out, writes a report, and prints where to find it.

To try it first on a small example, run the demo. It copies a small moderation task into a new Kiln project and tunes it. The demo needs an OpenRouter API key in Kiln, and costs about $2.

```bash
harness-tuner --demo
```

See [tuning your own task](https://github.com/Kiln-AI/harness-tuner/blob/main/docs/your-own-task.md) for a full walkthrough.

## Evals Drive Quality

We can't optimize something unless we can measure it, so the heart of Harness Tuner is [Kiln Evals](evals-and-specs/). The better your evals are at assessing quality, the better the tuner will work. Some guidance:

* [Create many small evals](https://kiln.tech/blog/you_need_many_small_evals_for_ai_products): it's typically easier to create several small evals focused on one area, than to try to create an all-encompassing eval.
* Use the [Kiln Eval Builder](evals-and-specs/specifications.md) to make better evals: it uses AI to refine your LLM-as-Judge for better alignment to human preference.
* Set a default judge on every eval you want measured.

#### Training, Validation and Test Datasets

Each eval the tuner uses needs a **training** dataset and a **validation** dataset, separate from its **test** dataset. See [eval datasets](evals-and-specs/evaluations.md#create-your-eval-datasets) for how to create them.

{% hint style="info" %}
**Older Evals May Be Missing Training or Validation Data**

Harness Tuner does not create these datasets for you. If an eval doesn't have them, use [synthetic data generation](synthetic-data-generation/) to generate more data, [tag the results](organizing-datasets.md#using-tags-to-organize-your-dataset), and set the tags as the eval's training and validation datasets.
{% endhint %}

## Reviewing the Results

Every experiment is saved to your Kiln project as a run configuration, so nothing is lost when a run ends.

* **Compare:** compare the winners against your starting point on evals, cost and speed.
* **Experiment Graph:** see how the tuning progressed, and which experiments each winner came from.
* **Test score:** the tuner never reads your test dataset. Run your evals on it in Kiln to get a final score that the tuner never optimized against.

## Cost

Harness Tuner is free, but it makes LLM API calls. A small agent with a small eval can cost a few dollars. A large agent with hundreds of tools can cost several hundred.

* **Your agent and evals** bill to the provider keys in Kiln. You set a budget for these at start-up, and the tuner starts no new work once it is spent.
* **The tuner's own agents** run on your coding agent subscription. The budget does not count this usage.

See the [cost guide](https://github.com/Kiln-AI/harness-tuner/blob/main/docs/costs.md) to estimate a run before you start it.

## Harness Tuning vs Fine Tuning

We generally recommend tuning your harness before [fine-tuning](fine-tuning/). A tuned harness is:

* Easier to deploy: no GPUs, and it works with off-the-shelf models
* Easier to update when new product requirements come up
* Quicker to move to new model releases: run the tuner again with the new model
* Easier to interpret: you can read every change

|                         | Fine Tuning               | Harness Tuning                                |
| ----------------------- | ------------------------- | --------------------------------------------- |
| **Optimization Target** | Supervised training data  | Evals                                         |
| **What Changes**        | Model weights             | Tools, prompts, skills, model and settings    |
| **Interpretability**    | Can't interpret changes   | Easy: read the new run configuration          |
| **Deployment Effort**   | High: host a custom model | Low: use the new run configuration            |

The two work together. Harness Tuner can use the fine-tuned models in your project.

## Learn More

* [Harness Tuner on GitHub](https://github.com/Kiln-AI/harness-tuner): the README, FAQ and source code.
* [How it works](https://github.com/Kiln-AI/harness-tuner/blob/main/docs/how-it-works.md): the whole loop, with a diagram.
* [Objectives and models](https://github.com/Kiln-AI/harness-tuner/blob/main/docs/objectives.md): what to optimize, and which models it may use.
* [CLI reference](https://github.com/Kiln-AI/harness-tuner/blob/main/docs/cli.md): every command and flag.
* [Limitations](https://github.com/Kiln-AI/harness-tuner/blob/main/docs/limitations.md): what it doesn't do. Read it before planning a long run.
