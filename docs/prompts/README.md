---
description: How to use our prompt optimizer, prompt generators, or create your own prompt
icon: pen-to-square
---

# Prompts

Kiln offers several methods to build an manage prompts

* [Automatic Prompt Generator](automatic-prompt-optimizer.md): Our state-of-the-art automatic prompt optimizer. We run iterative experiments and use evals to pinpoint and fix failure modes — **no manual prompting required**.
* [Prompt Generators](./#prompt-generators): Kiln can automatically generate many popular prompt styles from your task and dataset (few-shot, many-shot, chain of thought, chain of thought multi-shot, and more). The more you use your task, and rate the results, the richer your prompts become.
* [Custom Prompts](./#custom-prompts): manuall create, save and share any prompt.

<figure><img src="../../.gitbook/assets/Prompts.png" alt=""><figcaption></figcaption></figure>

## Custom Prompts / Saved Prompts

You can create and share custom prompts inside Kiln. Simply open the "Prompts" tab on the left of the UI. Anyone you [collaborate](../collaboration.md) with will have access to these prompts as well.

Custom prompts include several fields:

* Name: a name for you and your team to identify this prompt. Not used by the model.
* Prompt (aka System Message): The core of your prompt. Will be passed to the model as a system message before any user data is sent.
* Chain of thought instructions: if provided, using this prompt will add an extra "thinking"/reasoning phase to its execution. These instructions guide how the model should "think" about the problem before answering. See [COT docs](../reasoning-and-chain-of-thought.md#chain-of-thought-call-flow-non-reasoning-model) for details.

## Viewing Prompts

The "Prompts" tab in the UI lets you quickly preview what each prompt builder generates, or review your saved custom prompts

## Using Prompts

You can select any available prompt from the prompt dropdown:

<figure><img src="../../.gitbook/assets/Screenshot 2025-01-09 at 6.27.57 PM.png" alt="" width="310"><figcaption><p>Select a Prompt</p></figcaption></figure>

## When to Use Each Type of Prompt

Ultimately it's up to you when to use each style. The best approach varies from task to task, and model to model. It's worth evaluating a range of prompt/model pairs to find one that works best for your task, while considering speed/cost tradeoffs of longer prompts and larger models.

However, if fine-tuning we generally suggest a tiered approach:

* For generating training data: use a long/powerful prompt like "Chain of Though - Few Shot", on a powerful model (GPT, Claude, R1)
* Try our [prompt optimizer](automatic-prompt-optimizer.md) to find the best prompt for your task using evals. It works like a human refining a prompt would, but running thousands of tests to optimize and refine.
* When building fine-tunes, try a range of included prompts, including the original prompt used when generating training data, the "Basic (Zero Shot)", and an even shorter custom fine-tune prompt. Also include a range of models and model sizes in your search (llama 1b, 3b, 8b, 70b, etc).
* Evaluate the resulting models. See if the longer prompts are necessary. It's possible the very short prompts will perform well after fine-tuning, which improves speed and lowers costs.
* Read more guidance from [OpenAI](https://platform.openai.com/docs/guides/fine-tuning#crafting-prompts)
