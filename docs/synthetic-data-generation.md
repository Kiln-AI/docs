---
description: Generate synthetic data for fine-tuning or evaluation
icon: robot
---

# Synthetic Data Generation

Anyone can create thousands of synthetic data samples in just a few minutes using our interactive UI.

### Use Cases

Synthetic data is helpful for many reasons:

* **Evals:** Generate data for custom evals of your task performance
* **Fine-tuning:** Generate fine-tuning datasets
* **Built-in Templates:** Using our built in data-gen templates like 'Jailbreaking' or 'Bias' to check your system for common issues (curated evals)
* **Addressing Bugs / Issues:** generate targeted data to reproduce a bug/issue, which can be used for training a fix, evaluating a fix, and backtesting
* **Prompting:** Generate examples to be used for few-shot or multi-shot prompting

### Video Walkthrough

{% hint style="info" %}
Kiln's UI has been improved since this video was recorded. You may notice small differences in the UI, but the overall flows are the same.
{% endhint %}

{% embed url="https://vimeo.com/1088940292" %}
Synthetic Data Generation Walkthrough
{% endembed %}

### How It Works

#### Automatic Synthetic Data Gen Prompting

Kiln doesn't require you to write complex custom synthetic data gen prompts. Since you've already defined a goal when setting up your task, Kiln can do this for you. It will infer the type of data needed from the system prompt, adapt it to your data-gen goal, and create synthetic data gen prompts without any manual prompting.

[Learn more below](synthetic-data-generation.md#automatic-templates-and-custom-prompting)

### Walkthrough

#### Choose A Goal To Focus Data Gen

First select a goal for your dataset generation: Evals for Fine-Tuning. This is an important step as you need different data for different goals:

* **Fine-Tuning**: generate high quality outputs across a broad range of possible inputs, to help your model learn how to respond to a range of requests. This can include generating inputs that commonly produce issues, and outputs that avoid that issue.
* **Evals**: Intentionally generate a mix of good and bad inputs and outputs. We'll use the bad outputs to ensure the judge model can properly assess failures, and we'll use the bad inputs to ensure your task no longer has the issue.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.15.49 AM.png" alt="" width="375"><figcaption><p>Select a Goal</p></figcaption></figure>

Selecting the goal will setup two:

* **Template:** A Kiln prompt template to guide the data gen. You can edit this template before running data gen.
* **Tag Assignments:** which dataset tags will be assigned to generated data. This could be a single tag like `fine_tuning_data` or a randomly assigned split like `eval_data: 80%, golden_data: 20%`.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.21.14 AM (1).png" alt="" width="375"><figcaption><p>Goals drive the template and tag assignments</p></figcaption></figure>

#### Choose A Data Gen Model

{% hint style="info" %}
**TL;DR:** Choose a high quality model like GPT 4o or Grok 4 for synthetic data gen. Synthetic data gen is complex, and benefits from larger models.
{% endhint %}

We highly recommend choosing a large capable model for data gen. While your task may work on smaller models, data gen is more complex. It requires reasoning about a range of possible inputs, probing edge cases, and more. It benefits from a large model with a long context.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.38.10 AM.png" alt="" width="375"><figcaption><p>Recommended models are tagged in the dropdown</p></figcaption></figure>

If generating content to evaluate how your model responds to inappropriate requests (bias, jailbreaking, maliciousness, etc.), choose an uncensored model like Grok. Censored models like GPT 4o will refuse to generate some types of content.

#### Interactive Curation UX

Kiln synthetic data generation is designed to be interactive! As you work, be critical of the generated data and use the interactive UI to make great quality data. You can delete topics or examples that don't match your goals, add custom topics manually, update prompts to guide content, and iterate until you're happy with the results.

### 4 Stages of Data Gen: Topics, Inputs, Outputs, Saving

Kiln generates synthetic data in 4 stages:

* [**Topics**](synthetic-data-generation.md#topic-tree-data-generation-for-content-breadth): generate a tree of topics, which allows for breadth
* [**Model Inputs**](synthetic-data-generation.md#generate-model-inputs): generate synthetic model inputs (the user message). Optionally targeting a specific topic. Within each topic, we aim for a range of relevant inputs which are not too similar to each other.
* [**Model Outputs**](synthetic-data-generation.md#generate-model-outputs): generate synthetic model outputs from one of the inputs.
* [**Save Data**](synthetic-data-generation.md#save-synthetic-data-into-dataset): once you're happy with your synthetic data, save it into your dataset for use in evals and fine-tuning.

#### Topic Generation For Content Breadth

A common issue with synthetic data generation is that if you ask a model to generate synthetic data 1000 times, you get 1000 very similar outputs. Kiln addresses this by first generating a tree of diverse topics, then generating data targeting on individual topics.

<figure><img src="../.gitbook/assets/Screenshot 2025-01-05 at 12.06.43 PM.png" alt="" width="302"><figcaption><p>Example Topic Tree for a "Newspaper Headline" Task</p></figcaption></figure>

Kiln can use AI models to generate a topic tree for you from your task's prompt. If uses the prompt to ensure the topics are relevant to your goal. See the example above, the model knew it was building topics for newspaper headlines and generated appropriate topics. To generate topics, click "Add Topics" or "Add Topics":&#x20;

<figure><img src="../.gitbook/assets/Screenshot 2025-09-11 at 1.45.58 PM.png" alt="" width="375"><figcaption><p>Generate Topics Dialog</p></figcaption></figure>

You can nest sub-topics under any topic, forming the tree. Adding layers allows you to quickly generate a significant amount of diverse data. Hover any topic row to expose a "Add Subtopics" link:

<figure><img src="../.gitbook/assets/Screenshot 2025-09-11 at 1.21.32 PM.png" alt="Add Subtopics Button"><figcaption><p>Visible when hovering a topic row</p></figcaption></figure>

You can manually add topics instead of using synthetic topic generation. Select the "or manually add topics" option at the bottom of the "Generate Topics" dialog.

Topics are strongly recommended, but are optional. You skipt topics can add model inputs without topics by clicking "Generate Model Inputs".

#### Generate Model Inputs

Model inputs are the data passed into your task. When normally running your task, these would likley come from a human. However in synthetic data generation we us AI models to generate them.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.54.50 AM.png" alt="" width="375"><figcaption><p>Generated model inputs for the "Joke Generator" task</p></figcaption></figure>

Click "Generate Model Inputs" to generate model inputs using an AI model:

<figure><img src="../.gitbook/assets/Screenshot 2025-09-11 at 1.37.16 PM.png" alt="" width="375"><figcaption><p>Generate Model Inputs Dialog</p></figcaption></figure>

#### Generate Model Outputs

Once you have generated all of the inputs you want, click "Save All Model Outputs" to generate outputs. These won't appear in this UI, but will appear in your dataset with the appropriate tags.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.56.16 AM.png" alt="" width="375"><figcaption></figcaption></figure>

#### Save Synthetic Data into Dataset

Use the Kiln synthetic data UI to review your data. Once you're happy with the data, save it into your dataset for use in evals and fine-tuning. This is currently automatic, as soon as you generate model outputs.

The data will automatically be tagged with appriopiate tags, based on the goal you selected:

<figure><img src="../.gitbook/assets/Screenshot 2025-09-11 at 1.41.25 PM.png" alt=""><figcaption><p>The tags which will be assigned are shown in the UI</p></figcaption></figure>

### Automatic Templates and Custom Prompting

When you select a goal, we'll select the corresponding prompt template. These are built into Kiln and help guide data generation for a variety of tasks.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.42.02 AM.png" alt="" width="375"><figcaption><p>Selecting a Template</p></figcaption></figure>

When creating synthetic data for an eval there are two additional powerful options:

* Kiln Issue Template: When you create an eval using the "Issue" template, data gen will create a template that can help find passing and failing examples for evaluating and resolving the issue.
* Kiln Requirements Template: Generate synthetic data to evaluate overall task rating, and any requirements you added to your task.

{% hint style="info" %}
**You can edit templates or add custom prompts to get the desired behaviour**
{% endhint %}

These templates are a starting point. They may work for you out of the box, or you may want to edit them to get the desired data. You can edit a template before you run data gen to ensure it matches your needs.

Some examples of custom prompts/edit:

* Generate content for global topics, not only US-centric
* Generate examples in Spanish
* The model is having trouble classifying sentiment of sarcastic messages. Generate sarcastic messages.

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 10.48.14 AM.png" alt="" width="375"><figcaption><p>Editing a template</p></figcaption></figure>

{% hint style="info" %}
Often custom guidance is used for producing adversarial content: poor quality or inappropriate content. This is done to ensure an [evaluation](evaluations.md) can detect and fail this sort of content.

However, LLMs will often do their best to avoid producing poor or inappropriate content, even when asked for it. If you find that's the case, use an uncensored and unaligned model like Dolphin 8x22B or Grok. These models will follow instructions more closely, and do not attempt to censor their content.
{% endhint %}

### Structured Data (JSON, tool calling)

If your task requires structured input and/or output, your synthetic data generation will automatically follow the schemas you defined. All values are validated against the schemas you define, and nothing will be saved into your dataset if they don't comply.

You can define the schema in our task definition UI for a visual schema builder. Alternatively you can directly set a JSON Schema in the task via our python library or a text editor.

Under the hood we attempt to use tool calling when the model supports it, but will fallback to JSON parsing if not.

### Resolving Bugs & Issues with Synthetic Data

Synthetic data is a great tool for resolving bugs and issues in AI systems.

Follow these steps:

1. Create an eval using the Issue template, which will ask you to describe the issue and optionally provide examples.
2. Use synthetic data generation, selecting that issue as the goal. Generate data that reproduces that issue, then return to evals and verify you now have an eval Judge + eval dataset that can detect the issue reliably.
3. Iterate on different approaches to solving the problem (adjust prompt, model, temperature), using your eval judge to check if the solution works
4. Optionally use synthetic data and fine-tuning to fix the issue (for difficult issues where prompting doesn't work). Select the issue as the goal, but modify the tag assignment to `fine_tuning_data`, generate problematic inputs with successful outputs, adding these pairs to your fine tuning dataset.

### Tagging

All synthetic data will be assigned a series of [tags](organizing-datasets.md#using-tags-to-organize-your-dataset):

* The tag `synthetic` (manual and imported runs have their own tags)
* A unique tag to identify the date session (e.g. `synthetic_session_12345` )
* Custom tags. These are setup automatically when you select a goal, but you can edit before generating data:

<figure><img src="../.gitbook/assets/Screenshot 2025-07-16 at 11.13.57 AM.png" alt="" width="375"><figcaption><p>Editing Tag Assignments</p></figcaption></figure>
