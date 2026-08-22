---
title: "LLM Judges"
description: "Grade your task's output with a model and a rubric you write"
---
An LLM judge uses a model to grade the output of your task, against criteria you write. It combines a "thinking" stage (chain of thought/reasoning), followed by asking the model to produce scores matching the goals you laid out in your eval.

LLM judges are the right tool for subjective qualities like tone, helpfulness, toxicity, etc. For anything you can state as a rule, a [programmatic judge](/docs/evals-and-specs/judge-types/#programmatic-judges) will be faster, cheaper, and perfectly consistent.

This guide covers the options you'll configure when adding an LLM judge. For the overall eval workflow, see [Evaluations](/docs/evals-and-specs/evaluations/).

### Select a Judge Model & Provider

Select the model you want the judge to use (including which AI provider it should be run on).

:::note
We suggest larger high quality models for judges, as you'll be trusting their results to make product improvements. You can always run a cheaper/smaller model for inference which is where the majority of compute is spent in most projects.
:::

<details>

<summary><strong>Using models to evaluate models? Does that really work?</strong></summary>

Your intuition might be that you can't use LLMs to evaluate LLM tasks. Won't they make the same errors during evaluation that they make running your task?

There's a few reasons this approach actually works quite well:

* You can use better/larger models during evaluations: evals are (typically) run less often than the task itself. You can use larger models during evals, to gain trust in your smaller/faster task model.
* You can use more inference time compute during evaluation. Evals can be run with advanced reasoning models or detailed chain-of-thought instructions during eval, since latency and cost matter less during evals (they are run less often, and your users aren't waiting for an answer). In particular, defining specialized eval prompts covering specific error cases to watch for, multi-shot examples and rating guidance can really help evals outperform the core task model.
* Often we see the best model at evaluating a task is not the best model at running the task. Using the best model for each job can improve your overall system.

</details>

### G-Eval

G-Eval is an enhanced form of LLM as Judge. It looks at token output probabilities (logprobs) to create a weighted score. For example, if the model had a 51% chance of passing an eval and 49% chance of failing it, G-Eval will give the more nuanced score of 0.51, where LLM-as-Judge would simply pass it (1.0). The [G-Eval paper (Liu et al)](https://arxiv.org/abs/2303.16634) compares G-eval to a range of alternatives (BLEU, ROUGE, embedding distance scores), and shows it can outperform them across a range of eval tasks.

:::note
Since G-Eval requires logprobs (individual token probabilities), only a limited set of models and providers work with G-Eval. Currently it only works best with older OpenAI models like GPT 4.1. G-eval is not recommended for reasoning models, as the reasoning colors the probability distribution.

The UI will only show the G-Eval option if you select a supported model + provider.

Unfortunately [Ollama doesn't support logprobs yet](https://github.com/ollama/ollama/issues/2415).
:::

### Evaluation Instructions

LLM judges give the model time to "think" using chain-of-thought/reasoning before generating the output scores. Evaluation instructions are an ordered list of steps, giving the model a process for "thinking through" the eval prior to answering.

This section appears when your judge prompt doesn't already carry its own steps — typically an eval you created without a template. If you created your eval from a template, the steps come from that template, and you edit them in the judge prompt itself (see below).

<details>

<summary>Advanced tactics for defining evaluation instructions</summary>

If you start editing the eval's instructions, here are some advanced tactics/guidance that can help improve your eval performance:

* Include Multi-shot examples: for a step, give examples of different outputs and how they should be scored. Be sure to not include examples in your eval datasets.
* If your eval has multiple output scores, include at least 1 step for each score.
* Consider order of your steps: start with the more independent considerations, before moving to holistic considerations. For example, instructions for generating a final "overall score" should come after all other thinking steps.
* Consider short-circuit exits and limits: for example "If this step results in a failure, always return a 1-star overall score." or "If this step fails, the maximum overall score you should return is 3-stars".
* Consider weighting guidance for overall scores: if you have many steps producing an overall score, tell the LLM which steps matter the most.

</details>

### Advanced: Judge Prompt

The judge prompt is the Jinja2 template Kiln uses to prompt the judge model, and it's what actually carries your rubric. Kiln assembles a default for you from your task's description, the data to evaluate, and your evaluation instructions — so editing it is optional.

Open "Advanced: Judge Prompt" to edit it, or to set a **System Prompt** for the judge model. This is also where you edit template-derived evaluation steps, since those arrive as part of the prompt rather than as a separate list.

:::note
The evaluator model can almost always perform better if it knows what the task was. Kiln includes your task's description in the default judge prompt for exactly this reason — keep that description short and clear, usually a sentence, and your judges benefit along with your task.
:::

### Align your Judge to Human Preference

An LLM judge is an approximation of human preference, so you'll want to know how good the approximation is. Kiln compares your judge's scores against human ratings from your golden dataset, and helps you try several judges to find the one that matches your raters most closely.

See [Finding the Ideal Judge](/docs/evals-and-specs/evaluations/#finding-the-ideal-judge) for that workflow.
