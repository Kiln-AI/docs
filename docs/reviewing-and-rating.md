---
description: Ratings help multi-shot prompting, fine-tuning, evals, and more
icon: star
---

# Reviewing and Rating

Kiln includes a rating interface for rating dataset entries. This can be used to score the quality of the generated data, or to evaluate the quality of a model.

<figure><img src="../.gitbook/assets/Screenshot 2025-01-05 at 12.12.38 PM (1).png" alt="" width="341"><figcaption><p>Rating UI in Kiln Desktop</p></figcaption></figure>

### Requirements: Defining Rating Options

Your rating requirements are defined as part of your task definition, in the requirements section. You can  add or edit requirements in **Settings > Edit Task**.&#x20;

* Name: the name of the requirement, which will appear in the rating UI. Limited in length to fit in the UI, but you can add more content in the instructions field below.
* Instructions: more details about the requirement. These will be available to reviewers in the UI (under the ![](<../.gitbook/assets/Screenshot 2025-01-05 at 12.18.52 PM (1).png>) icon).
* Rating Type: one of 5-star, pass/fail, pass/fail/critical.
* Priority: how important this criteria is to the task.

{% hint style="info" %}
An "Overall" rating is always available, even if your task has zero requirements
{% endhint %}

### How Ratings are Used

Kiln uses ratings in a variety of ways:

* In our automatic multi-shot prompting only highly rated examples are used. The generated prompt will filters to examples 4+ stars, and prefers 5-star ratings if available.
* When creating a fine-tuning dataset, you may optionally filter the training data to highly rated content.
* When using the python library, you can access ratings.

### Rating Types:

* **5-star**: a 1-5 star rating.
* **Pass/Fail**: A binary pass/fail rating.
* **Pass/Fail/Critical**: A ternary pass/fail/critical rating. It can be useful to add the "critical" level when there are criteria where some failures are exceptionally important to avoid. For example, a customer service bot could have a "tone" criteria, where casual/slang language would be a failure, but profanity or insulting the user would be critical.
* **Custom**: you can define a custom rating scale when using python library. However, you won't be able to use custom ratings in the Kiln UI.

## Use Ratings to Improve your Quality

Once you have ratings, Kiln offers a number of ways to use human ratings to improve task performance and quality:

* [Create fine-tuned models](fine-tuning-guide.md), filtering the training set to only high quality training data
* [Optimize an evaluator](evaluations.md#finding-the-ideal-eval-method) by finding the eval method with the highest correlation to human preferences. An optimized evaluator is necessary to find the optimal method of running your task.
