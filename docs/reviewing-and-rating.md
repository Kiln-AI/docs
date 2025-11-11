---
description: Ratings help multi-shot prompting, fine-tuning, evals, and more
icon: star
---

# Reviewing and Rating

Kiln includes a rating interface for rating dataset entries. This can be used to score the quality of the generated data, or to evaluate the quality of a model.

<figure><img src="../.gitbook/assets/Screenshot 2025-01-05 at 12.12.38 PM (1).png" alt="" width="341"><figcaption><p>Rating UI in Kiln Desktop</p></figcaption></figure>

### Defining Rating Options

There are two methods of defining rating options:

* Adding requirements to your task definition in **Settings > Edit Task** will add a rating option to every sample in your dataset
* After creating an [Eval](evaluations/), each output score will be available as a rating option for every sample in its golden dataset.

### Rating Option Parameters

Each rating option has a number of parameters:

* Name: the name of the requirement, which will appear in the rating UI. Limited in length to fit in the UI, but you can add more content in the instructions field below.
* Instructions: more details about the requirement. These will be available to reviewers in the UI (under the ![](<../.gitbook/assets/Screenshot 2025-01-05 at 12.18.52 PM (1).png>) icon).
* Rating Type: one of 5-star, pass/fail, pass/fail/critical.
* Priority: how important this criteria is to the task.

{% hint style="info" %}
An "Overall" rating is always available, even if your task has zero requirements
{% endhint %}

### Rating Types:

* **5-star**: a 1-5 star rating.
* **Pass/Fail**: A binary pass/fail rating.
* **Pass/Fail/Critical**: A ternary pass/fail/critical rating. It can be useful to add the "critical" level when there are criteria where some failures are exceptionally important to avoid. For example, a customer service bot could have a "tone" criteria, where casual/slang language would be a failure, but profanity or insulting the user would be critical.
* **Custom**: you can define a custom rating scale when using python library. However, you won't be able to use custom ratings in the Kiln UI.

### How Ratings are Used

Kiln uses ratings in a variety of ways:

* In evals, ratings of your golden dataset are used to benchmark and compare judges for evaluating your task. This helps you find the [ideal judge](evaluations/#finding-the-ideal-judge).
* Kiln's [automatic prompt generators](prompts.md#prompt-generators) may incorporate highly rated samples into a prompt. For example, multi-shot or few-shot prompts will automatically incorporate highly rated samples. These filters to examples 4+ stars, and prefers 5-star ratings if available.
* When creating a [fine-tuning dataset](fine-tuning/fine-tuning-guide.md), you may optionally filter the training data to highly rated content.
* When using the [python library](../developers/python-library-quickstart.md), you can access ratings.
