---
icon: pen-to-square
description: How Kiln generates prompts
---

# Prompts

Once you define a task, Kiln can generate many prompt styles without any manual prompt management. This guide explains how the process works.

{% hint style="info" %}
Kiln prompts are data-driven, meaning the prompts automatically improve as you run your task and collect more examples of good responses (and mistakes!).&#x20;
{% endhint %}

<figure><img src="../.gitbook/assets/Prompts.png" alt=""><figcaption></figcaption></figure>

### Base Prompt Inputs

When you create a Kiln task you specify several fields which are used when generating prompts:

* Instructions: The core of your prompt. Describe the task as you would in a standard LLM prompt.
* Requirements: A list of requirements you want the LLM to adhere to (e.g. "Use professional tone"). These are used in 2 places: 1) they are included in the prompt text sent to the LLM, and 2) they available as rating criteria on any run response.
* Thinking Instructions: This field allows you to specify a portion of the prompt, which is only used when you select a "chain of thought" prompt template. If omitted, the default is "Think step by step, explaining your reasoning.".&#x20;

### Adding Content for Multi-Shot Prompts

Multi-shot prompting is when you provide several examples in the prompt, and has been shown to greatly improve output quality.

In order to use multi-shot prompting in Kiln, we need some correct example content to use. Kiln makes this easy! Simply run your task in the Run tab of the UI, and rate the output. As you collect more 4 and 5 star responses, the set of available content for multi-shot prompting increases.

Kiln will automatically select content for multi-shot prompts using your dataset, using the following priority:

* 5-star repairs: where a human has given feedback, repaired the response, and rated the repair 5-stars
* 5-star responses
* 4-star response

### Viewing Prompts

The "Prompts" tab in the UI lets you quickly preview what each prompt builder generates.

### Prompt Builders / Prompt Styles

Once you've setup your task and added some example content, you'll have a number of prompt styles to choose from:

* **Basic (Zero Shot)**: a prompt template that will only use your task definition (instructions and requirements). This is completely deterministic, and won't change until you edit your task.
* **Few Shot**: a mult-shot prompt that will include the 4 best examples from your dataset, on top of the basic prompt.
* **Many Shot**: a mult-shot prompt that will include the 25 best examples from your dataset, on top of the basic prompt.
* **Repair Multi Shot**:  a mult-shot prompt that will include the 25 best examples from your dataset, on top of the basic prompt. Unlike the basic "Many Shot" which only includes the 5-star content, this prompt will use repaired examples to show 1) the generated content which had issues, 2) the human feedback about what was incorrect, 3) the corrected 5-star content. This gives the LLM examples of common errors to avoid.
* **Basic Chain of Though**: a chain of thought prompt template that will only use your task definition (instructions, requirements, and thinking instructions). The LLM will return in 2 stages, 1) thinking stage, 2) response stage. Both are stored in the dataset, but typically only stage 2 is used in the app. This is completely deterministic, and won't change until you edit your task.
* **Chain of Thought - Few Shot**: a prompt that applies both the few shot template (4 examples), and chain-of-thought thinking instructions.
* **Chain of Thought - Many Shot**: a prompt that applies both the many shot template (25 examples), and chain-of-thought thinking instructions.

### When to Use Each Style

Ultimately it's up to you when to use each style. The best approach varies from task to task, and model to model. It's worth evaluating a range of prompt/model pairs to find one that works best for your task, while considering speed/cost tradeoffs of longer prompts and larger models.

However, if fine-tuning we generally suggest a tiered approach:

* For generating training data: use a long/powerful prompt like "Chain of Though - Few Shot", on a powerful model (GPT, Claude)&#x20;
* When building fine-tunes, try a range of included prompts, including the original prompt used when generating training data, the "Basic (Zero Shot)", and an even shorter custom fine-tune prompt.
* Evaluate the resulting models. See if the longer prompts are necessary. It's possible the very short prompts will perform well after fine-tuning, which improves speed and lowers costs.

