---
description: Built a reasoning model, like o3 or R1, for your use case
icon: person-chalkboard
---

# Guide: Train your own reasoning model

Kiln is a platform that makes building task-specific AI models easy and fast. By creating a fine-tuned model targeted to your  use case, you can produce a model that's higher quality, faster and cheaper that standard foundation models.

In this guide, we'll walk through how to build a reasoning model, like OpenAI o3 or Deepseek R1, for your specific use case. The whole process can be completed in as little as 30 minutes, and does not require coding.

## How to Train a Task Specific Reasoning Model

We already have a [detailed guide on fine-tuning models](fine-tuning-guide.md). This article covers the settings to use throughout that process to ensure the final model you produce is a reasoning model, and not just a standard fine-tune.

### Ensure your training data includes "reasoning"

When developing your training data with our [synthetic data generation](synthetic-data-generation.md) tool, be sure to use either a reasoning model or chain-of-thought prompting. Using either of these will ensure your dataset has reasoning data to learn from. See our [model list](models-and-ai-providers.md#included-models-recommended) for which models have native reasoning support.

See below for [how to choose between reasoning and chain of thought](guide-train-your-own-reasoning-model.md#choosing-between-reasoning-and-chain-of-thought).

<figure><img src="../.gitbook/assets/run method.png" alt="" width="375"><figcaption><p>Synthetic Data Run Options</p></figcaption></figure>

{% hint style="info" %}
If you're using multi-shot prompting, also ensure your prompt examples have appropriate reasoning data. Consider a [custom prompt](prompts.md#custom-prompts-saved-prompts) with examples demonstrating ideal reasoning for your task.
{% endhint %}

### Create a training dataset filtered to samples with reasoning

When creating your training dataset, be sure to filter it to samples with reasoning/thinking as shown here:

<figure><img src="../.gitbook/assets/Screenshot 2025-02-05 at 9.29.09 AM (1).png" alt="" width="188"><figcaption><p>Filtering your training dataset</p></figcaption></figure>

### Choose the correct training strategy

To train your own reasoning mode, you must select the `Final Responses and Intermediate Reasoning` training strategy. This will include the reasoning data in the fine-tune data.

<figure><img src="../.gitbook/assets/Screenshot 2025-02-05 at 9.34.47 AM.png" alt="" width="348"><figcaption><p>Select this on the "Create Fine Tune" screen</p></figcaption></figure>

If you select `Final only` the fine-tune will only learn from the final result, not the reasoning. This is still a valid approach and could produce a viable model for you task. However, it won't produce a model with learned reasoning skills.

### Call your fine-tuned model with the appropriate prompt&#x20;

When you call any fine-tune, we recommend calling it with the same prompt used in training.&#x20;



### Choosing between Reasoning and Chain of Thought

### Technical Notes: Learning Method

Kiln is using supervised fine-tuning for these models.

SFT, not RL, good for use case specific distilling.
