---
description: Build fine-tuned models for calling a set of tools, like MCP
---

# Fine Tuning for Tool Use

{% hint style="warning" %}
**Coming soon**

This feature will be in our next release. To use it today, download a daily build.
{% endhint %}

Kiln can fine-tune a model for calling a specific set of tools. The fine-tuned models can improve over the base model by:

* Learning when to call each tool, and when not to
* Learning when to choose one tool over another
* Learning how to format tool calls and tool call parameters. This greatly reduces error rates over the base model, making smaller and faster models viable.

Together, this means you can improve agent performance and lower costs.

#### Building a Fine-Tuning Training Dataset for Tool Calling

To create a fine-tune targeting tool calling, you must generate a training set specifically for tool calling.&#x20;

{% hint style="info" %}
The tool set available during training data generation must exactly match the tool set your fine-tune targets.

Kiln disallows training on samples that don't have a matching toolset. We don't want to train on these as the fine-tuned model would improperly learn to not call a tool, even when a tool call would have been appropriate.

This doesn’t mean every tool needs to be called in every training sample. Only that every tool was available to be called.
{% endhint %}

Kiln makes building a tool-calling training dataset easy:

1. Open Fine-Tune Tab.
2. Click “Create Fine Tune”.
3.  Select the set of tools which the model should learn to call.

    <figure><img src="../../.gitbook/assets/Screenshot 2026-01-08 at 8.07.16 PM (2).png" alt="" width="375"><figcaption><p>Selecting tools available to the fine-tuned model</p></figcaption></figure>


4.  Click “Add Fine-Tuning Data” to launch Kiln's synthetic data generation tool.

    <figure><img src="../../.gitbook/assets/image.png" alt="" width="375"><figcaption></figcaption></figure>


5. Generate synthetic training data.&#x20;

{% hint style="info" %}
When generating your training data, you typically want to use a larger model and/or a longer prompt with additional guidance about tool use.&#x20;

The improvements from these techniques will be reflected in your training set, which can then be learned by the fine-tuned model.
{% endhint %}

#### Create a Tool Calling Fine-Tune

Once you’ve created a training set, return to the “Create a Fine Tune” screen to start training. Select a base model, the tools you want, and the dataset you’ve created to start training. See our [fine-tuning guide](fine-tuning-guide.md) for additional details.

<figure><img src="../../.gitbook/assets/Screenshot 2026-01-08 at 9.01.36 PM.png" alt="" width="375"><figcaption></figcaption></figure>

{% hint style="info" %}
You must select a base model which supports tool calling. Kiln will disable tool calling training if the selected base model was not trained for tool calling.
{% endhint %}

{% hint style="success" %}
Kiln will convert your training data into the base-model's tool calling format automatically.
{% endhint %}

#### Running a Tool Calling Fine-Tune

When running a Tool Calling Fine-Tune in Kiln, we’ll automatically populate the same set of tools it was trained on.&#x20;

Adding or removing tools will show a warning, as this model is unlikely to perform well with tools which were not in its training dataset.&#x20;

{% hint style="info" %}
If deploying a fine-tune created in Kiln, always provide the same tools as it was trained to use.
{% endhint %}

#### Evaluating Tool Use

Kiln has a custom eval for [evaluating appropriate tool use](../evaluations/evaluate-appropriate-tool-use.md). We suggest using it to compare the base model to your fine-tune, to confirm performance is improving.
