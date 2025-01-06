---
icon: tag
description: Tag, Filter, Sort, Freeze and Split
layout:
  title:
    visible: true
  description:
    visible: true
  tableOfContents:
    visible: true
  outline:
    visible: true
  pagination:
    visible: true
---

# Organizing Datasets

<figure><img src="../.gitbook/assets/dataset-2 (1).png" alt=""><figcaption></figcaption></figure>

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

### Sort and Filter

The dataset view offers a number of tools that make working with large datasets easier:

* Filter: Tap the filter button (![](<../.gitbook/assets/filter 2.png>)) to filter to specific tags
* Sort: You can sort by any column by clicking its header
* Multi-select: you can enter "selection" mode by clicking the select button
  * Select any row by clicking it
  * Select a range of rows by clicking the first, then holding shift while clicking the last

### Batch Editing

Once you have selected rows you can perform a number of batch actions:

* Add tags
* Remove tags
* Delete dataset items

### Dataset Splits

When creating a fine-tune, you can define a "dataset split". This is a frozen subset of your data.

* Dataset splits may be broken into sub-sets like "train", "validation" and "test" which are useful for systematically training and evaluating models.
* Dataset splits will randomly assign items between sub-sets (train/test/val), but the assignment is static. Items do not shift between subsets once the dataset split is created.
* Dataset splits to not grow/change when you add new data. They are frozen at the point in time when they are created. This makes it easier to run multiple experiments (fine-tunes, evals, etc) on exactly the same training/eval datasets.

