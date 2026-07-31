---
description: Improve evals or fine-tuning with synthetic data
---

# Generating Synthetic Data

<figure><img src="../../.gitbook/assets/synth_data-2 (1).png" alt=""><figcaption></figcaption></figure>

## How It Works

Kiln doesn't require you to write complex custom synthetic data gen prompts. Since you've already defined a goal when setting up your task, Kiln can do this for you. It will infer the type of data needed from the system prompt, adapt it to your data-gen goal, and create synthetic data gen prompts without any manual prompting.

Kiln offers two ways to build the dataset itself:

* [**Kiln Pro Batch Planning**](generating-synthetic-data.md#kiln-pro-plan-the-batch)**:** describe the dataset you want and Kiln plans the whole dataset for you, writing one tailored prompt per sample to cover your task's use cases and edge cases.
* [**Manual Generation**](generating-synthetic-data.md#manual-build-a-topic-tree)**:** plan the coverage yourself by building a tree of topics for breadth.

Both flows start the same way: choose a goal, optionally set up a Data Guide, then pick how to build the dataset.&#x20;

## Choose A Goal

First select a goal for your dataset generation: **Evals** or **Fine-Tuning**. This is an important step as you need different data for different goals:

* **Fine-Tuning**: generate high quality outputs across a broad range of possible inputs, to help your model learn how to respond to a range of requests. This can include generating inputs that commonly produce issues, and outputs that avoid that issue.
* **Evals**: Intentionally generate a mix of good and bad inputs and outputs. We'll use the bad outputs to ensure the judge model can properly assess failures, and we'll use the bad inputs to ensure your task no longer has the issue.

Selecting the goal will set up two properties:

* **Template:** targets the data generation to the use case you selected above. Use our built in templates for fine-tuning or evals, or generate your own custom guidance.
* **Tag Assignments:** which dataset tags will be assigned to generated data. This could be a single tag like `fine_tuning_data` or a randomly assigned split like `eval_data: 80%, golden_data: 20%`. These will be pre-filled based on your selected goal.

## Choose A Data Gen Model

{% hint style="info" %}
**TL;DR:** Choose a high quality model like the latest GPT or Claude model for synthetic data gen. Synthetic data gen is complex, and benefits from larger models.
{% endhint %}

We highly recommend choosing a large capable model for data gen. While your task may work on smaller models, data gen is more complex. It requires reasoning about a range of possible inputs, probing edge cases, and more. It benefits from a large model with a long context.

If generating content to evaluate how your model responds to inappropriate requests (bias, jailbreaking, maliciousness, etc.), choose an uncensored model like Grok or Dolphin. Censored models like GPT will refuse to generate some types of sensitive content.

## Building The Dataset

With your goal and Data Guide in place, Kiln asks how you want to build the dataset: **Manually**, or with **Kiln Pro**.

<table><thead><tr><th valign="middle"></th><th valign="middle">Manual</th><th valign="middle">Kiln Pro</th><th data-hidden></th></tr></thead><tbody><tr><td valign="middle"><strong>Effort</strong></td><td valign="middle">~15 min</td><td valign="middle">~5 min</td><td></td></tr><tr><td valign="middle"><strong>Use Case Coverage</strong></td><td valign="middle">Manual</td><td valign="middle">AI Planned</td><td></td></tr><tr><td valign="middle"><strong>Edge Case Coverage</strong></td><td valign="middle">Manual</td><td valign="middle">AI Planned</td><td></td></tr><tr><td valign="middle"><strong>Kiln Account</strong></td><td valign="middle">Optional</td><td valign="middle">Required</td><td></td></tr></tbody></table>

Choose **Kiln Pro** when you want a dataset that covers your task's use cases and edge cases without designing that coverage yourself. Choose **Manual** when you want to shape the dataset topic by topic.

Both flows generate synthetic data in the same four stages, and you curate at each one. Only the **first** stage differs between them:

1. **Plan or Topics:** Kiln Pro [**plans the whole batch**](generating-synthetic-data.md#kiln-pro-plan-the-batch) up front; manual mode [**builds a topic tree**](generating-synthetic-data.md#manual-build-a-topic-tree) for breadth.
2. [**Inputs**](generating-synthetic-data.md#generate-inputs): generate synthetic model inputs (the user message).
3. [**Outputs**](generating-synthetic-data.md#generate-outputs): run your task on the inputs to generate synthetic outputs.
4. [**Save Data**](generating-synthetic-data.md#save-your-data): save your curated data into your dataset for use in evals and fine-tuning.

Whichever way you build the dataset, generation is interactive. Be critical of the generated data and use the UI to make great quality data: remove anything that doesn't match your goals, add guidance to steer the content, and iterate until you're happy with the results.

### Dataset Planning

A common issue with synthetic data generation is that if you ask a model to generate synthetic data 1000 times, you get 1000 very similar outputs. They are too uniform to be useful for fine tuning or evals.

The solution is to design your entire dataset to ensure breadth and coverage.

Kiln offers 2 ways to plan entire deadsets: [Kiln Pro Batch Planning](generating-synthetic-data.md#kiln-pro-plan-the-batch) and [Manual Topic Trees](generating-synthetic-data.md#manual-build-a-topic-tree).

#### Kiln Pro: Plan the Batch

Both modes produce a batch of data. The difference is the planning. Instead of building a topic tree, you describe the dataset you want and Kiln plans the whole batch up front, writing one tailored prompt per sample so every sample has a distinct purpose. The plan is what covers your use cases and edge cases and gives the batch its diversity (the job a topic tree does in manual mode), and it's yours to review and edit in a single scannable overview before anything is generated. It's a streamlined, single-step path from idea to dataset.

**1. Connect Kiln Pro** (if you haven't already).

**2. Describe the batch you want.** The **Generate Synthetic Data Batch** page has three controls:

* **Sample Count:** how many samples to plan.
* **Guidance:** free text describing the dataset you want, e.g. _"10% of the dataset should be in Spanish. 30% should hit edge case X."._ Kiln will prefill this from your goal. This single Guidance box is where you steer the whole batch; unlike manual mode, there's no separate per-stage guidance.
* **Use Data Guide:** include your task's [Data Guide](generating-synthetic-data.md#set-up-a-data-guide), so both the plan and the generated inputs match the shape of your real data.

**3. Review the batch plan.** Click **Generate Batch** and Kiln drafts a **Batch Plan** showing what it intends to generate, before it generates anything:

* **Batch Overview:** a short summary of what the batch covers and how it's distributed.
* **All Dataset Items:** expand this to read every planned prompt, one per sample. Remove any you don't want from the row's "..." menu.

#### Manual: Build a Topic Tree

In manual synthetic data generation, you shape the dataset by building a topic tree: a hierarchy of topic nodes to generate data samples for. You can use the topics and sub-topics to control the distribution of data in your dataset.

{% hint style="info" %}
This video walks through the manual flow and predates Kiln Pro batch planning. The UI has changed since recording, but the steps are similar.
{% endhint %}

{% embed url="https://vimeo.com/1088940292" %}
Synthetic Data Generation Walkthrough
{% endembed %}



Kiln can use AI models to generate a topic tree for you from your task's prompt. It uses the prompt to ensure the topics are relevant to your goal. See the example above: the model knew it was building topics for newspaper headlines and generated appropriate topics. To generate topics, click **Add Topics**:

You can nest sub-topics under any topic, forming the tree. Adding layers allows you to quickly generate a significant amount of diverse data. Open any topic's "..." menu to expose an **Add Subtopics** button:

You can manually add topics instead of using synthetic topic generation. Select the "or manually add topics" option at the bottom of the "Generate Topics" dialog.

Topics are strongly recommended, but are optional. You can skip topics and add model inputs without topics by continuing to the **Generate Inputs** step.

### Generate Inputs

Model inputs are the data passed into your task. When normally running your task, these would likely come from a human. However, in synthetic data generation we use AI models to generate them.

In manual mode, click **Generate Inputs** to produce inputs in your data table (under each topic, if you're using them). In Kiln Pro, click **Generate Batch** on your reviewed plan and Kiln generates every sample's input in parallel.

Review the quality of inputs and ensure you're happy with them before proceeding. You can remove individual inputs for manual curation or reset the session to change the guidance and generate again to get better quality data.

### Generate Outputs

Once you have generated all of the inputs you want, click **Generate Outputs** to run your task on each input:

Generating will result in an output for each input:

Review the quality of outputs and ensure you're happy with them before proceeding. You can remove individual outputs for manual curation or reset the session to change the guidance and generate again to get better quality data.

### Save Your Data

Use the Kiln synthetic data UI to review your data. Once you're happy with the data, click **Save All** to save it into your dataset for use in evals and fine-tuning.

The data will automatically be tagged with appropriate tags, based on the goal you selected ([see details](generating-synthetic-data.md#tagging)):

Once saved, you can view all of your saved data in the Dataset tab.

### Templates and Custom Guidance

In manual mode, you steer each stage with its own **Guidance**: separate instructions for topic, input, and output generation. Kiln starts each from a template chosen from your goal (or the eval you came from), so you don't have to write a data-gen prompt from scratch. Switch templates or write custom guidance before running any stage.

The guidance dropdown offers a few families:

* **Built-in templates:** ready-made guidance for common goals like **Fine Tuning**, **Toxicity**, **Bias**, **Maliciousness**, **Jailbreak**, and **Factual Correctness**. Use these to probe your system for common issues (curated evals).
* **Eval template:** when you start data gen from a specific [eval](../evals-and-specs/evaluations.md), Kiln auto-selects the template that matches that eval's type, so the data targets exactly what the eval measures. Depending on the eval you'll see one of **Requirements Eval**, **Desired Behaviour Eval**, **Appropriate Tool Use**, or **Issue Eval** (legacy evals). Only the one matching your eval is shown.
* **Custom:** write your own guidance from scratch.

These templates are a starting point. Edit one before running a stage, or write your own guidance from scratch, to get exactly the data you want.

Some examples of custom guidance:

* Generate content for global topics, not only US-centric
* Generate examples in Spanish
* The model is having trouble classifying sentiment of sarcastic messages. Generate sarcastic messages.

{% hint style="info" %}
Often custom guidance is used for producing adversarial content: poor quality or inappropriate content. This is done to ensure an [evaluation](../evals-and-specs/evaluations.md) can detect and fail this sort of content.

However, LLMs will often do their best to avoid producing poor or inappropriate content, even when asked for it. If you find that's the case, use an uncensored and unaligned model like Dolphin or Grok. These models will follow instructions more closely, and do not attempt to censor their content.
{% endhint %}

{% hint style="info" %}
Kiln Pro works differently: it plans the whole batch from a single prefilled **Guidance** box, with no template dropdown or per-stage guidance. See [Kiln Pro: Plan the Batch](generating-synthetic-data.md#kiln-pro-plan-the-batch).
{% endhint %}

## Structured Data (JSON, Tool Calling)

If your task requires structured input and/or output, your synthetic data generation will automatically follow the schemas you defined. All values are validated against the schemas you define, and nothing will be saved into your dataset if they don't comply.

## Tagging

All synthetic data will be assigned a series of [tags](../organizing-datasets.md#using-tags-to-organize-your-dataset) in the dataset:

* The tag `synthetic` (manual and imported runs have their own tags)
* A unique tag to identify the data session (e.g. `synthetic_session_12345`)
* Custom tags. These are set up automatically when you select a goal, but you can edit them before generating data:
