---
description: Generate synthetic data for fine-tuning or evaluation
icon: robot
---

# Synthetic Data Generation

Anyone can create thousands of synthetic data samples in just a few minutes using our interactive UI.

## Use Cases

Synthetic data is helpful for many reasons:

* **Evals:** Generate data for custom evals of your task performance
* **Fine-tuning:** Generate fine-tuning datasets
* **Built-in Templates:** Use our built-in data-gen templates like 'Jailbreak' or 'Bias' to check your system for common issues (curated evals)
* **Addressing Bugs / Issues:** generate targeted data to reproduce a bug/issue, which can be used for training a fix, evaluating a fix, and backtesting
* **Prompting:** Generate examples to be used for few-shot or multi-shot prompting

## How It Works

Kiln doesn't require you to write complex custom synthetic data gen prompts. Since you've already defined a goal when setting up your task, Kiln can do this for you. It will infer the type of data needed from the system prompt, adapt it to your data-gen goal, and create synthetic data gen prompts without any manual prompting.

Kiln offers two ways to build the dataset itself:

* **[Kiln Pro Batch Planning](synthetic-data-generation.md#kiln-pro-plan-the-batch):** describe the dataset you want and Kiln plans the whole batch for you, writing one tailored prompt per sample to cover your task's use cases and edge cases.
* **[Manual Generation](synthetic-data-generation.md#manual-build-a-topic-tree):** plan the coverage yourself by building a tree of topics for breadth.

Both flows start the same way: choose a goal, optionally set up a Data Guide, then pick how to build the dataset. Only the first build step differs (planning vs topics); from there both generate inputs and outputs and save into your dataset.

## Choose A Goal

First select a goal for your dataset generation: **Evals** or **Fine-Tuning**. This is an important step as you need different data for different goals:

* **Fine-Tuning**: generate high quality outputs across a broad range of possible inputs, to help your model learn how to respond to a range of requests. This can include generating inputs that commonly produce issues, and outputs that avoid that issue.
* **Evals**: Intentionally generate a mix of good and bad inputs and outputs. We'll use the bad outputs to ensure the judge model can properly assess failures, and we'll use the bad inputs to ensure your task no longer has the issue.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.15.49 AM.png" alt="" width="375"><figcaption><p>Select a Goal</p></figcaption></figure>

Selecting the goal will set up two properties:

* **Template:** A starting point for the generation guidance, chosen from your goal. For Fine-Tuning it's the built-in fine-tuning template; for Evals, Kiln matches the eval you're generating for. In manual mode you can switch or edit it (see [Templates and Custom Guidance](synthetic-data-generation.md#templates-and-custom-guidance)); in Kiln Pro it prefills the batch [Guidance box](synthetic-data-generation.md#kiln-pro-plan-the-batch).
* **Tag Assignments:** which dataset tags will be assigned to generated data. This could be a single tag like `fine_tuning_data` or a randomly assigned split like `eval_data: 80%, golden_data: 20%`.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.21.14 AM.png" alt="" width="375"><figcaption><p>Goals drive the template and tag assignments</p></figcaption></figure>

## Set Up A Data Guide

A Data Guide is a per-task prompt that tells Kiln what realistic **inputs** to your task look like: their structure, style, terminology, and value ranges. Without one, the data gen model has to guess what your domain looks like from the system prompt alone. With one, generated topics and inputs are shaped to your actual data.

<!-- TODO IMAGE: The "Create a Data Guide" intro card on the Synthetic Data Generation page, showing the "Set Up Data Guide" and "Continue Without Data Guide" buttons. -->

Most tasks benefit from a Data Guide, especially when:

* Your inputs have a specific structure (forms, JSON, transcripts, tickets, code) the model would otherwise have to invent
* Your domain uses terminology or value ranges a generic model wouldn't know
* The default synthetic data looks plausible but not quite like production
* You already have real examples (documents, past runs, or a spreadsheet of inputs) and want generation grounded in them

The first time you open Synthetic Data Generation for a task, Kiln offers to set up a Data Guide. Click **Set Up Data Guide** and Kiln will ask how you'd like to build it: **Manually**, or with **Kiln Pro**.

<table><thead><tr><th valign="middle"></th><th valign="middle">Manual</th><th valign="middle">Kiln Pro</th><th data-hidden></th></tr></thead><tbody><tr><td valign="middle"><strong>AI Guided Authoring</strong></td><td valign="middle">Manual</td><td valign="middle">Automatic</td><td></td></tr><tr><td valign="middle"><strong>Style &#x26; Constraints Discovery</strong></td><td valign="middle">Manual</td><td valign="middle">Automatic</td><td></td></tr><tr><td valign="middle"><strong>Learn From Documents</strong></td><td valign="middle">—</td><td valign="middle">✅</td><td></td></tr><tr><td valign="middle"><strong>Approx. Effort</strong></td><td valign="middle">~15 mins</td><td valign="middle">~5 mins</td><td></td></tr><tr><td valign="middle"><strong>Kiln Account</strong></td><td valign="middle">Optional</td><td valign="middle">Required</td><td></td></tr></tbody></table>

Both paths end in the same place: a saved guide you've reviewed and refined. The difference is how the first draft gets written.

### Kiln Pro Data Guides

With Kiln Pro, you hand Kiln a pile of real example inputs and it analyzes them into a complete draft guide for you. It's the fastest path, and the only one that can learn directly from documents.

**1. Connect Kiln Pro** (if you haven't already).

**2. Add example inputs.** Click **Add Inputs** and pick a source: upload documents from your computer or reuse them from your [Document Library](documents-and-search-rag.md) (plaintext tasks only; Kiln converts them to text with an [extractor](documents-and-search-rag.md)), pull inputs from real past runs in your [dataset](organizing-datasets.md), bulk-import from a CSV (plaintext tasks only), or write one by hand (structured tasks only). You can mix sources and add more later.

{% hint style="info" %}
Real data works best. A Data Guide is only as realistic as the examples it's built from, so prefer real inputs over synthetic ones.
{% endhint %}

**3. Check your generation settings.** Use the **Generation Settings** card to pick the model that generates your preview inputs ([which model?](synthetic-data-generation.md#choose-a-data-gen-model)).

**4. Click Continue.** Kiln analyzes your examples and drafts your guide, then generates preview inputs and drops you into [Review and Refine](synthetic-data-generation.md#review-and-refine).

### Manual Data Guides

Manual guides need no Kiln account. You write the starting examples yourself and let the refine cycle do the rest.

1. **Add example inputs:** provide at least one real input, either typed in or picked from your existing task runs. Your examples are treated as ground truth and preserved verbatim in the guide throughout refinement.
2. **Check your generation settings:** use the **Generation Settings** card to pick the model that generates your preview inputs ([which model?](synthetic-data-generation.md#choose-a-data-gen-model)).
3. **Generate a preview:** Kiln produces a set of synthetic inputs from your guide so far, and you refine from there.

### Review and Refine

Both paths converge here. Kiln generates synthetic inputs from your guide and asks whether input generation is working as expected. Rate each one **Realistic** or **Needs Work**, and for anything you flag, add a short note on what's off (e.g. "inputs are missing the patient ID field" or "these are far shorter than our real tickets").

Click **Continue** and Kiln refines the guide with your feedback, then generates fresh inputs so you can see whether the change took effect. Repeat until they all look realistic, then click **Save Data Guide**.

You can also expand **Preview Data Guide** to read or hand-edit the guide directly; after an edit, choose **Verify Edit** to regenerate inputs against it, or **Save Without Refining Further** to keep it as-is.

### Using A Saved Data Guide

Once saved, Kiln applies your guide automatically when generating inputs for your task. A **Use Data Guide** toggle lets you turn it off for individual runs.

If you're also using template guidance from an eval, that guidance takes priority over the Data Guide where the two conflict.

To view, edit, or delete a saved guide, use the **Data Guide** button on the Synthetic Data Generation page. Clicking **Edit** offers two options:

* **Edit Manually:** edit the guide text directly, then verify your changes or save without verifying.
* **Review & Refine:** generate fresh example inputs from your guide to re-check quality, and refine it if any need work.

## Choose A Data Gen Model

{% hint style="info" %}
**TL;DR:** Choose a high quality model like GPT-5 or Claude Opus 4.8 for synthetic data gen. Synthetic data gen is complex, and benefits from larger models.
{% endhint %}

We highly recommend choosing a large capable model for data gen. While your task may work on smaller models, data gen is more complex. It requires reasoning about a range of possible inputs, probing edge cases, and more. It benefits from a large model with a long context.

<!-- TODO IMAGE: The data-gen model dropdown, with recommended models tagged. -->

If generating content to evaluate how your model responds to inappropriate requests (bias, jailbreaking, maliciousness, etc.), choose an uncensored model like Grok or Dolphin. Censored models like GPT-5 will refuse to generate some types of content.

## Building The Dataset

With your goal and Data Guide in place, Kiln asks how you want to build the dataset: **Manually**, or with **Kiln Pro**.

<table><thead><tr><th valign="middle"></th><th valign="middle">Manual</th><th valign="middle">Kiln Pro</th><th data-hidden></th></tr></thead><tbody><tr><td valign="middle"><strong>Effort</strong></td><td valign="middle">~15 min</td><td valign="middle">~5 min</td><td></td></tr><tr><td valign="middle"><strong>Use Case Coverage</strong></td><td valign="middle">Manual</td><td valign="middle">AI Planned</td><td></td></tr><tr><td valign="middle"><strong>Edge Case Coverage</strong></td><td valign="middle">Manual</td><td valign="middle">AI Planned</td><td></td></tr><tr><td valign="middle"><strong>Kiln Account</strong></td><td valign="middle">Optional</td><td valign="middle">Required</td><td></td></tr></tbody></table>

Choose **Kiln Pro** when you want a dataset that covers your task's use cases and edge cases without designing that coverage yourself. Choose **Manual** when you want to shape the dataset topic by topic.

Both flows generate synthetic data in the same four stages, and you curate at each one. Only the **first** stage differs between them:

1. **Plan or Topics:** Kiln Pro [**plans the whole batch**](synthetic-data-generation.md#kiln-pro-plan-the-batch) up front; manual mode [**builds a topic tree**](synthetic-data-generation.md#manual-build-a-topic-tree) for breadth.
2. [**Inputs**](synthetic-data-generation.md#generate-inputs): generate synthetic model inputs (the user message).
3. [**Outputs**](synthetic-data-generation.md#generate-outputs): run your task on the inputs to generate synthetic outputs.
4. [**Save Data**](synthetic-data-generation.md#save-your-data): save your curated data into your dataset for use in evals and fine-tuning.

Whichever way you build the dataset, generation is interactive. Be critical of the generated data and use the UI to make great quality data: remove anything that doesn't match your goals, add guidance to steer the content, and iterate until you're happy with the results.

### Kiln Pro: Plan the Batch

Both modes produce a batch of data. The difference is the planning. Instead of building a topic tree, you describe the dataset you want and Kiln plans the whole batch up front, writing one tailored prompt per sample so every sample has a distinct purpose. The plan is what covers your use cases and edge cases and gives the batch its diversity (the job a topic tree does in manual mode), and it's yours to review and edit in a single scannable overview before anything is generated. It's a streamlined, single-step path from idea to dataset.

**1. Connect Kiln Pro** (if you haven't already).

**2. Describe the batch you want.** The **Generate Synthetic Data Batch** page has three controls:

* **Sample Count:** how many samples to plan.
* **Guidance:** free text describing the dataset you want, e.g. _"10% of the dataset should be in Spanish."_ Kiln prefills this from your goal: a representative training set with ~20% edge cases for **Fine-Tuning**, or a batch that exercises the measured behavior (embedding the eval's definition) for **Evals**. Edit it however you like.
* **Use Data Guide:** include your task's [Data Guide](synthetic-data-generation.md#set-up-a-data-guide), so both the plan and the generated inputs match the shape of your real data.

This single **Guidance** box is where you steer the whole batch; unlike manual mode, there's no separate per-stage guidance.

<!-- TODO IMAGE: The "Generate Synthetic Data Batch" form, showing Sample Count, Guidance, and the Use Data Guide toggle. -->

**3. Review the batch plan.** Click **Generate Batch** and Kiln drafts a **Batch Plan** showing what it intends to generate, before it generates anything:

* **Batch Overview:** a short summary of what the batch covers and how it's distributed.
* **All Dataset Items:** expand this to read every planned prompt, one per sample. Remove any you don't want from the row's "..." menu.

<!-- TODO IMAGE: The "Batch Plan" page, showing the Batch Overview summary and the expanded "All Dataset Items" table. -->

### Manual: Build a Topic Tree

Manual refers to how coverage is decided: you shape it by building a topic tree, rather than having Kiln plan the batch for you. Even that is AI-assisted: Kiln can generate the topic tree for you, and the guidance templates help at every stage. Your job is to drive and curate.

{% hint style="info" %}
This video walks through the manual flow and predates Kiln Pro batch planning. The UI has changed since recording, but the manual topics → inputs → outputs steps are the same.
{% endhint %}

{% embed url="https://vimeo.com/1088940292" %}
Synthetic Data Generation Walkthrough
{% endembed %}

A common issue with synthetic data generation is that if you ask a model to generate synthetic data 1000 times, you get 1000 very similar outputs. Kiln addresses this by first generating a tree of diverse topics, then generating data targeting individual topics.

<figure><img src="../.gitbook/assets/Screenshot 2025-01-05 at 12.06.43 PM.png" alt="" width="302"><figcaption><p>Example Topic Tree for a "Newspaper Headline" Task</p></figcaption></figure>

Kiln can use AI models to generate a topic tree for you from your task's prompt. It uses the prompt to ensure the topics are relevant to your goal. See the example above: the model knew it was building topics for newspaper headlines and generated appropriate topics. To generate topics, click **Add Topics**:

<figure><img src="../.gitbook/assets/Screenshot 2025-09-11 at 1.45.58 PM.png" alt="" width="375"><figcaption><p>Generate Topics Dialog</p></figcaption></figure>

You can nest sub-topics under any topic, forming the tree. Adding layers allows you to quickly generate a significant amount of diverse data. Open any topic's "..." menu to expose an **Add Subtopics** button:

<figure><img src="../.gitbook/assets/Screenshot 2025-09-22 at 7.17.28 PM.png" alt="" width="219"><figcaption><p>"Add Subtopics" from ... menu</p></figcaption></figure>

You can manually add topics instead of using synthetic topic generation. Select the "or manually add topics" option at the bottom of the "Generate Topics" dialog.

Topics are strongly recommended, but are optional. You can skip topics and add model inputs without topics by continuing to the **Generate Inputs** step.

### Generate Inputs

Model inputs are the data passed into your task. When normally running your task, these would likely come from a human. However, in synthetic data generation we use AI models to generate them.

In manual mode, click **Generate Inputs** to produce inputs in your data table (under each topic, if you're using them). In Kiln Pro, click **Generate Batch** on your reviewed plan and Kiln generates every sample's input in parallel.

<figure><img src="../.gitbook/assets/Screenshot 2025-09-11 at 1.37.16 PM.png" alt="" width="375"><figcaption><p>Generate Model Inputs Dialog</p></figcaption></figure>

<figure><img src="../.gitbook/assets/Screenshot 2025-09-22 at 7.19.49 PM.png" alt="" width="375"><figcaption><p>Generated model inputs for the "Joke Generator" task</p></figcaption></figure>

Review the quality of inputs and ensure you're happy with them before proceeding. You can remove individual inputs for manual curation or reset the session to change the guidance and generate again to get better quality data.

### Generate Outputs

Once you have generated all of the inputs you want, click **Generate Outputs** to run your task on each input:

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.56.16 AM.png" alt="" width="375"><figcaption></figcaption></figure>

Generating will result in an output for each input:

<figure><img src="../.gitbook/assets/Screenshot 2025-09-22 at 7.21.43 PM.png" alt="" width="375"><figcaption><p>Synthetic Input/Output pairs under a topic</p></figcaption></figure>

Review the quality of outputs and ensure you're happy with them before proceeding. You can remove individual outputs for manual curation or reset the session to change the guidance and generate again to get better quality data.

### Save Your Data

Use the Kiln synthetic data UI to review your data. Once you're happy with the data, click **Save All** to save it into your dataset for use in evals and fine-tuning.

<figure><img src="../.gitbook/assets/Screenshot 2025-09-22 at 7.27.27 PM.png" alt="" width="375"><figcaption><p>Saving All Data</p></figcaption></figure>

The data will automatically be tagged with appropriate tags, based on the goal you selected ([see details](synthetic-data-generation.md#tagging)):

<figure><img src="../.gitbook/assets/Screenshot 2025-09-11 at 1.41.25 PM.png" alt=""><figcaption><p>The tags which will be assigned are shown in the UI</p></figcaption></figure>

Once saved, you can view all of your saved data in the Dataset tab.

### Templates and Custom Guidance

In manual mode, you steer each stage with its own **Guidance**: separate instructions for topic, input, and output generation. Kiln starts each from a template chosen from your goal (or the eval you came from), so you don't have to write a data-gen prompt from scratch. Switch templates or write custom guidance before running any stage.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.42.02 AM.png" alt="" width="375"><figcaption><p>Selecting a Template</p></figcaption></figure>

The guidance dropdown offers a few families:

* **Built-in templates:** ready-made guidance for common goals like **Fine Tuning**, **Toxicity**, **Bias**, **Maliciousness**, **Jailbreak**, and **Factual Correctness**. Use these to probe your system for common issues (curated evals).
* **Eval template:** when you start data gen from a specific [eval](evals-and-specs/evaluations.md), Kiln auto-selects the template that matches that eval's type, so the data targets exactly what the eval measures. Depending on the eval you'll see one of **Requirements Eval**, **Desired Behaviour Eval**, **Appropriate Tool Use**, or **Issue Eval** (legacy evals). Only the one matching your eval is shown.
* **Custom:** write your own guidance from scratch.

These templates are a starting point. Edit one before running a stage, or write your own guidance from scratch, to get exactly the data you want.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.48.14 AM.png" alt="" width="375"><figcaption><p>Editing a template</p></figcaption></figure>

Some examples of custom guidance:

* Generate content for global topics, not only US-centric
* Generate examples in Spanish
* The model is having trouble classifying sentiment of sarcastic messages. Generate sarcastic messages.

{% hint style="info" %}
Often custom guidance is used for producing adversarial content: poor quality or inappropriate content. This is done to ensure an [evaluation](evals-and-specs/evaluations.md) can detect and fail this sort of content.

However, LLMs will often do their best to avoid producing poor or inappropriate content, even when asked for it. If you find that's the case, use an uncensored and unaligned model like Dolphin or Grok. These models will follow instructions more closely, and do not attempt to censor their content.
{% endhint %}

{% hint style="info" %}
Kiln Pro works differently: it plans the whole batch from a single prefilled **Guidance** box, with no template dropdown or per-stage guidance. See [Kiln Pro: Plan the Batch](synthetic-data-generation.md#kiln-pro-plan-the-batch).
{% endhint %}

## Structured Data (JSON, Tool Calling)

If your task requires structured input and/or output, your synthetic data generation will automatically follow the schemas you defined. All values are validated against the schemas you define, and nothing will be saved into your dataset if they don't comply.

You can define the schema in our task definition UI for a visual schema builder. Alternatively you can directly set a JSON Schema in the task via our python library or a text editor.

Under the hood we attempt to use tool calling when the model supports it, but will fallback to JSON parsing if not.

## Tagging

All synthetic data will be assigned a series of [tags](organizing-datasets.md#using-tags-to-organize-your-dataset):

* The tag `synthetic` (manual and imported runs have their own tags)
* A unique tag to identify the data session (e.g. `synthetic_session_12345`)
* Custom tags. These are set up automatically when you select a goal, but you can edit them before generating data:

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 11.13.57 AM.png" alt="" width="375"><figcaption><p>Editing Tag Assignments</p></figcaption></figure>

## Resolving Bugs & Issues with Synthetic Data

Synthetic data is a great tool for resolving bugs and issues in AI systems.

Follow these steps:

1. Create an eval that targets the issue (for example, an eval that describes the failing behavior, optionally with examples).
2. Use synthetic data generation, selecting that eval as the goal. Generate data that reproduces the issue, then return to evals and verify you now have an eval Judge + eval dataset that can detect the issue reliably.
3. Iterate on different approaches to solving the problem (adjust prompt, model, temperature), using your eval judge to check if the solution works.
4. Optionally use synthetic data and fine-tuning to fix the issue (for difficult issues where prompting doesn't work). Select the issue as the goal, but modify the tag assignment to `fine_tune_data`, generate problematic inputs with successful outputs, and add these pairs to your fine tuning dataset.
