---
description: Tag, Filter and Sort
icon: tag
---

# Organizing Datasets

### Using Tags to Organize Your Dataset

Kiln uses tags to organize your dataset. You can add tags to any run/sample, and then filter by tag. This is a great way to organize your dataset and find specific runs.

Some examples of how you might use tags within a team:

* Working with eval teams:
  * Add the "needs\_review" tag when data is ready for review by a human eval team
  * Ask a human eval team to review the new batch of synthetic data. New synth data is automatically tagged with "synthetic" and "synthetic\_session\_id".
* Defining a "golden" dataset: Have QA tag a "golden" data reserved for evals
* Bug resolution: QA can tag examples of a common issue with a tag (e.g. "issue\_unprofessional\_tone"). Data scientists can run evals of different methods of fixing the issue.
* Regression Testing: tag important customer use cases with a tag ("customer\_use\_case") and run evals to ensure the model doesn't regress on them prior to a new release.
* Fine-tuning: exclude tags from fine-tuning datasets (golden, customer\_use\_case, etc), to prevent contamination.

### Sort and Filter&#x20;

The dataset view offers a number of tools that make working with large datasets easier:

* Filter: Tap the filter button (![](<../.gitbook/assets/filter 2.png>)) to filter to specific tags
* Sort: You can sort by any column by clicking it's header
* Multi-select: you can enter "selection" mode by clicking the select button
  * Select any row by clicking it
  * Select a range of rows by clicking the first, then holding shift while clicking the last

### Batch Editing

Once you have selected rows youn can perform a number of batch actions:

* Add tags
* Remove Tags
* Delete
