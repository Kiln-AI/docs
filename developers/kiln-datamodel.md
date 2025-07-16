---
icon: database
description: How Kiln projects are structured
---

# Kiln Data Model

### Understanding the Kiln Data Model

Kiln projects are simply a directory of files (mostly JSON files with the extension `.kiln`) that describe your project, including tasks, runs, ratings, fine-tunes and other data.

This dataset design was chosen for several reasons:

* Git compatibility: Kiln project folders are easy to collaborate on with Git (or a shared drive). See our [collaboration guide](../docs/collaboration.md#technical-collaboration-architecture) for additional details of how we avoid conflicts and format to support diff tools.
* JSON allows you to easily load and manipulate the data using standard tools (pandas, polars, etc.).

### Data Model Overview

Here's a high level overview of the Kiln datamodel. A project folder will reflect this nested structure:

* Project: a Kiln Project that contains related tasks.
  * Task: a specific task including prompt instructions, input/output schemas, and requirements.
    * TaskRun: a sample (run) of a task including input, output, and human rating information.
    * [Finetune](../docs/fine-tuning-guide.md): a model for fine-tuning jobs. Includes configuration, status tracking, and data necessary to call the deployed fine-tuned model.
    * [Prompts](../docs/prompts.md): a custom prompt for this task. See our [prompts docs](../docs/prompts.md) for details.
    * DatasetSplit: a frozen collection of task runs divided into train/test/validation splits.
    * [Task Run Config](../docs/evaluations.md#finding-the-ideal-run-method): a specific method of running this task, including a prompt and model.
    * [Eval](../docs/evaluations.md): an evaluation of this task, including output score definitions and datasets to run this eval on
      * [Judge](../docs/evaluations.md#finding-the-ideal-judge): a method of running this eval, including instructions and model.
      * Eval Runs: the results of running this eval, including scoring.

See the [python library datamodel docs](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai/datamodel.html) for detailed descriptions of classes, fields and validations.

### Python Library

If you want to access the data model via code, check out our [python library](python-library-quickstart.md). The library offers iterators, typed classes, pydantic validation, and more. It's the easiest way to read and mutate a Kiln dataset.

### Direct Access

You can load Kiln project files using any tool which supports JSON, including polars and pandas. See the [example](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#using-kiln-dataset-in-pandas) in our library docs.

{% hint style="warning" %}
We highly recommend the Kiln python library for any writes to `.kiln` files. It will run validators which catch issues which could break your project.
{% endhint %}
