---
description: Evaluate the quality of your models/tasks using state of the art evals
---

# Evaluators

{% hint style="warning" %}
Evals are in beta, and have not been included in a release yet. If you want to preview evals, download a [daily build](https://github.com/Kiln-AI/Kiln/actions/runs/13552265493).
{% endhint %}

### Intro

Kiln includes a complete platform for ensuring your tasks/models are of the highest possible quality. It includes:

* Access multiple SOTA evaluation methods (G-Eval, LLM as Judge)
* Compare and benchmark your eval methods against human evals to find the best possible evaluator for your use case
* Test a variety of different methods of running your task (prompts, models, fine-tunes) to find which perform best
* Easily manage datasets for eval sets, golden sets, human ratings through our intuitive UI
* Generate evaluators automatically. Using your task definition we'll create an evaluator for your task's overall score and task requirements
* Utilize built-in eval templates for toxicity, bias, jailbreaking, and other common eval scenarios
* Integrate evals with the rest of Kiln: use synthetic data generation to build eval sets, or use evals to evaluate fine-tunes

### Concepts Overview

This is a quick summary of all of the concepts in creating evals with Kiln:

* Eval (aka Evaluator): defines an evaluation goal (like "overall score" or "toxicity"), and includes dataset definitions to use for running this eval. You can add many evals to a task, each for different goals.
* Score: an output score for an eval like "overall score", "toxicity" or "helpfulness". An eval can have 1 or more output scores. These have a score type: 1-5 star, pass/fail, or pass/fail/critical.
* Evaluation Methods: a method of running an Eval. An eval method includes an eval algorithm, eval instructions, eval model, and model provider. An eval can have many eval-methods, and Kiln will help you compare them to find which eval-method best correlates to human preferences.
* Task Run Methods: a method of running your task. A task run method includes a prompt, model and model provider. A task can have many run methods. Once you have an Eval, you can use it to find an optimal run-method for your task: the run method which scores the highest, using your eval.

### The Workflow

Working with Evals in Kiln is easy. We'll walk through the flow of creating your first evaluator end to end:

* [Creating an Evaluator](evaluators.md#creating-an-eval)
* [Add an Evaluation Method to your Eval](evaluators.md#add-an-evaluation-method-to-your-eval)
* [Create your Eval Datasets](evaluators.md#create-your-eval-datasets)
* [Finding the Ideal Eval Method](evaluators.md#finding-the-ideal-eval-method)
* [Finding the Ideal Run Method](evaluators.md#finding-the-ideal-run-method)
* [Iterate and Expand](evaluators.md#iterate-and-expand)

### Creating an Eval

From the "Eval" tab in Kiln's UI, you can easily create a new evaluator.

#### Pick a Goal / Select a Template

Kiln has a number of built-in templates to make it easy to get started.

{% hint style="info" %}
We recommend starting with the "Overall Score and Task Requirements" template.
{% endhint %}

* **Overall Score and Task Requirement Scores:** Generate scores for the requirements you setup when you created this task, plus an overall-score. These can be compared to human ratings from the dataset UI.
* **Generalized Templates**: Kiln includes a number of common templates for evaluating AI systems. These include evaluator templates for measuring **toxicity, bias, maliciousness, factual correctness, and jailbreak susceptibility**.
* **Custom Goal and Scores**: If the templates aren't a good fit, feel free to create your own Eval from scratch using the custom option.

Select a template, edit if desired, and save your eval.

### Add an Evaluation Method to your Eval

The Eval you created defines the goal of the eval, but it doesn't include the specifics of how it's run. That's where eval-methods come in — they define the exact approach of running an eval. This includes things like the eval algorithm, the eval model, the model provider, and instructions/prompts.

#### Select an Eval Algorithm

Kiln supports two powerful eval algorithms:

_**LLM as Judge**_

Just like the name says, this approach uses LLMs to judge the output of your task. It combines a "thinking" stage (chain of thought/reasoning), followed by asking the model to produce a score rubric matching the goals you laid out in the eval.

_**G-Eval**_

G-Eval is an enhanced form of LLM as Judge. It looks at token output probabilities (logprobs) to create a weighted score. For example, if the model had a 51% chance of passing an eval and 49% chance of failing it, G-Eval will give the more nuanced score of 0.51, where LLM-as-Judge would simply pass it (1.0). The [G-Eval paper (Liu et al)](https://arxiv.org/abs/2303.16634) compares G-eval to a range of alternatives (BLEU, ROUGE, embedding distance scores), and shows it can outperform them across a range of eval tasks.

{% hint style="warning" %}
Since G-Eval requires logprobs (token probabilities), only a limited set of models work with G-Eval. Currently it only works with GPT-4o, GPT-4o Mini, Llama 3.1 70b on OpenRouter, and Deepseek R1 on Openrouter.&#x20;

Unfortunately [Ollama doesn't support logprobs yet](https://github.com/ollama/ollama/issues/2415).&#x20;

Select LLM as Judge if you want to use Ollama or models other than the ones listed above.
{% endhint %}

<details>

<summary><strong>Using models to evaluate models? Does that really work?</strong></summary>

Your intuition might be that you can't use LLMs to evaluate LLM tasks. Won't they make the same errors during evaluation that they make running your task?

There's a few reasons this approach actually works quite well:

* You can use better/larger models during evaluations: evals are (typically) run less often than the task itself. You can use larger models during evals, to gain trust in your smaller/faster task model.
* You can use more inference time compute during evaluation. Evals can be run with advanced reasoning models or detailed chain-of-thought instructions during eval, since latency and cost matter less during evals (they are run less often, and your users aren't waiting for an answer). In particular, defining specialized eval prompts covering specific error cases to watch for, multi-shot examples and rating guidance can really help evals outperform the core task model.
* Often we see the best model at evaluating a task is not the best model at running the task. Using the best model for each job can improve your overall system.

</details>

#### Add a Task Description

The evaluator model can almost always perform better if you give it a high level summary of the task. Keep this short, usually just one sentence. We'll add more detailed asks of the evaluators in the next section.

#### Add Evaluation Steps

Both Kiln eval algorithms give the model time to "think" using chain-of-thought/reasoning before generating the output scores. Your eval method defines an ordered list of evaluation instructions/steps, giving the model steps for "thinking through" the eval prior to answering. If you selected a template when creating the eval, Kiln will automatically fill in template steps for you. You can edit the templates as much as you wish, adding, removing and editing steps.

<details>

<summary>Advanced tactics for defining eval steps</summary>

If you start editing the eval's steps, here are some advanced tactics/guidance that can help improve your eval performance:

* Include Multi-shot examples: for a step, give examples of different outputs and how they should be scored. Be sure to not include examples in your eval datasets.
* If your eval has multiple output scores, include at least 1 step for each score.
* Consider order of your steps: start with the more independent considerations, before moving to holistic considerations. For example, instructions for generating a final "overall score" should come after all other thinking steps.
* Consider short-circuit exits and limits: for example "If this step results in a failure, always return a 1-star overall score." or "If this step fails, the maximum overall score you should return is 3-stars".
* Consider weighting guidance for overall scores: if you have many steps producing an overalls score, tell the LLM which steps matter the most.

</details>

#### Select an eval method model & provider

Finally, select the model you want the eval method to use (including which AI provider it should be run on).

#### Python Library Usage \[optional]

It's possible to create evals in code as well. Just be aware eval methods are called EvalConfigs in our library.

### Create your Eval Datasets

An eval in Kiln includes two datasets:

* **Eval dataset**: specifies which part of your dataset is used when evaluating different methods of running your task.
* **Eval Method dataset**: specifies which part of your dataset is used when trying to find the best evaluation method for this task.

This section will walk you through populating both of your eval datasets.

#### Defining your Dataset with Tags

When first creating your eval, you will specify a "tag" which defines each eval dataset as a subset of all the items in Kiln's Dataset tab. To add/remove items from your datasets, simply add/remove the corresponding tag. These tags can be added or removed anytime from the "Dataset" tab.

Don't worry if your dataset is empty when creating your eval, we can add data after its creation.

By default, Kiln will suggest appropriate tags and we suggest keeping the defaults. For example, the overall-score template will use the tags "eval\_set" and "golden", while the toxicity template will use the tags "toxicity\_eval\_set" and "toxicity\_golden".

{% hint style="info" %}
"Golden" is a term often used in data science, to describe a "gold standard" dataset, used to compared different methods/approaches.
{% endhint %}

{% hint style="info" %}
If you're creating multiple evals for task, it's usually beneficial to maintain separate datasets for each eval. For example, a "toxicity" eval dataset will likely be filled with negative content you wouldn't want in your overall-score eval. Kiln will suggest goal-specific tags by default.
{% endhint %}

#### Populating the Dataset with Synthetic Data

Most commonly, you'll want to populate the datasets using synthetic data. Follow our synthetic data generation guide to generate data for this eval across a range of topics. We suggest at least 100 data samples per eval.

We suggest using the "topic tree" option in our synthetic data gen tool to ensure your eval dataset is diverse.

For the "overall score" eval template, the default data-gen UX should work well without any custom inputs. However, for more specific evals like bias, toxicity and jailbreaking you'll want to generate data with specific guidance that ensures there are both positive and negative examples in your dataset. The following templates can be added to the "Human Guidance" option in synthetic data gen, to help generate appropriate content.

#### Splitting the Dataset

Once you've generated your data, open the "Dataset" tab in Kiln

1. Filter your dataset to only the content you just generated (they will all be tagged with an auto-generated tag such as synthetic\_session\_12345).
2. Use the "Select" UI to select a portion of your dataset for your eval-dataset. 80% is a good starting point. Add the tag for your eval dataset, which is "eval\_config" if you kept the default tag name.
3. Select only the remaining items, and add the tag for your eval method dataset, which is "golden" if you kept the default tag name.
4. Filter the dataset to both tags (eval\_config and golden) to double check you didn't accidentally add any items to both datasets.

#### Add Human Ratings

Next we'll add human ratings, so we can measure how well our evaluator performs compared to a human. If you have a subject matter expert for your task, get them to perform this step. See our collaboration guide for how to work together on a Kiln project.

Assuming you're working on the "overall score" template: filter your Dataset view to the "golden" tag, click the first item, add ratings, and repeat until all items in your golden dataset are rated. You can use the left/right keyboard keys to quickly move between items. Only the golden dataset needs ratings, not the eval\_set.

If you're working on another template (toxicity, bias, etc) or a custom eval, you need to add each eval-score to your task, or else the rating UI for it won't appear. Open Settings > Edit Task, then add a task requirement with a matching name and type for each of the output scores in your eval. Then proceed with the instructions above (substituting the correct tags).

### Finding the Ideal Eval Method

You added an "eval method" to your eval above. However, we don't actually know how well this eval method works. Kiln includes tools to compare multiple eval methods, and find which one is the closest to a real human evaluator.

It may seem strange, but yes… one of the first steps of building an eval to evaluate evaluation methods. It sounds complicated, but Kiln makes it easy.

#### Run Evals on your Golden Set

Open your eval from the "Evals" tab, then click the "Compare Evaluation Methods" button. From the "Compare Evaluation Methods" screen, click the "Run Eval" button.

This will run your evaluator on the golden dataset, once with each eval method.

Once complete, you'll have a set of metrics about how well the eval method's scoring matched human scores.

#### Add Eval Methods and Compare to Find the Best

One score in isolation isn't helpful. You'll want to add additional eval methods to see which one performs best. Kiln makes it easy to compare eval-methods. We suggest trying a range of options:

* Try both eval methods: G-Eval and LLM as Judge
* Try a range of different models: you may be surprised which model works best as an evaluator for your task. Be sure to try SOTA models, like the latest models from OpenAI and Anthropic. Even if you prefer open models, it can be good to know how far you are from these benchmarks.
* Try custom eval instructions, not just the template contents.

Once you've added multiple eval methods, you can compare scores to find the best evaluator for your task. On this screen you're looking for the **lowest** scores, which mean the least deviation from human scores.

#### Understanding Correlation Scores

There's no benchmark good/bad score for an evaluator; it all depends on your task.

For an easy and highly deterministic task, you might be able to find many eval-methods which achieve near perfect scores, even with smaller eval models.

For a highly subjective task, it's likely no evaluator will perfectly match the human scores, even with SOTA models. It's often the case that two humans can't match each other on subjective tasks. Try a range of eval methods, and pick the one with the best (lowest) score. The more subjective the task, the more beneficial a larger and more diverse golden dataset becomes.

For a technical description of how each score is calculated, see the in-app "Learn about score types" popup in app.

#### Select a Default Eval Method

Once you have a winner, click the "Set as default" button to make this eval-method the default for your eval.

### Finding the Ideal Run Method

Now that we have an evaluator we trust, we can use it to rapidly evaluate a variety of method of running our task. We call this a "Run Method" and it includes the model (including fine-tunes), the model provider, and the prompt.

Return the "Evaluator" screen for your eval, and add a variety run methods you want to compare. We suggest:

* A range of models (SOTA, smaller, open, etc)
* A range of prompts: both Kiln's [auto-generated prompts](prompts.md#prompt-generators), and [custom prompts](prompts.md#custom-prompts-saved-prompts)&#x20;
* Some model fine-tunes of various sizes, created by [Kiln fine tuning](fine-tuning-guide.md)&#x20;

Once you've defined a set of run methods, click "Run Eval" to kick off the eval. Behind the scenes, this is performing the following steps:

* Fetching the input data from your eval dataset (eval\_set tag)
* Generating new output for each input, using each run method you defined for each input
* Running your evaluator on each result, collecting scores

#### Comparing Run Methods

Once done, you'll have results for how each run method performed on the eval.

These results are easy to interpret compared to the eval method comparisons. Each score is simply the average score from that run method. Assuming we want to find the run method that produces the best content, simply find the highest average score.

Congrats! You've used systematic evals to find an optimal method for running your task!

#### Python Library Usage \[optional]

It's possible to create/evaluate task run methods in code as well. Just be aware task run methods are called TaskRunConfigs in our library. See the EvalRunner class for details.

### Iterate and Expand

Congrats, you've found an optimal method of running your task!

However there's always room to improve.

#### Iterate on Methods

You can repeat the processes above to try new eval-methods or run-methods. Through more searching, you may be able to find a better method and improve overall performance.

You can iterate by trying new prompts, more models, building custom fine-tuned models, or trying new state of the art models as they are released.

#### Expand your Dataset

Your understanding of your model/product usually gets better over time. Consider adding data to your dataset over time (both eval\_set and golden). This can come from real users, bug reports, or new synthetic data that comes from a better understanding of the problem. As you add data, re-run both sub-evals (eval-method and run-method) find the best eval-method and run-method for your task.

#### Add New Evals

You can always add additional evals to your Kiln project/task. Try some of our built in templates like bias, toxicity, factual correctness, or jailbreak susceptibility — or create your own from scratch!
