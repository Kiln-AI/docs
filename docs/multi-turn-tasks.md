---
description: Chat-style tasks, where the user and the model take turns in one conversation
icon: comments
---

# Multi-turn Tasks

A multi-turn task is a back-and-forth conversation: the user sends a message, the model replies, and the conversation continues. You chat with it in the **Run** tab and evaluate it with the [Eval Builder](evals-and-specs/specifications.md).

### Creating a Multi-turn Task

When you create a task, pick **Multi-turn** under **Part 2: Task Type**. Multi-turn tasks are plain text, with no [input or output schema](structured-data-json.md). The task type can't be changed later, so clone the task to switch.

### Chatting and Your Dataset

Send a first message from the **Run** tab. The conversation then continues on its **Dataset Run** page, where you can:

* Change the model or tools in **Options** between turns. The prompt stays as it was on the first turn.
* Hover an earlier reply and click **Fork** to start a new branch from that point. The original stays unchanged.
* Rate the conversation. Ratings and tags attach to the turn you're viewing, and a new turn starts unrated.

The **Dataset** tab shows one row per conversation, with each fork as its own row.

### Importing Conversations

Click **Add Data** (**Manually Add Data** if the dataset is empty), then **Add CSV**. Each row holds one conversation in a `trace` column, and the dialog explains the format and has a sample CSV.

### Evaluating

Use the [Eval Builder](evals-and-specs/specifications.md). It creates simulated users and a judge that scores each whole conversation, and every run configuration you compare holds its own conversation with each simulated user. Conversations stored in your dataset can't be re-run for a run configuration.

### Not Supported

[Synthetic Data Generation](synthetic-data-generation/), the [Automatic Prompt Optimizer](prompts/automatic-prompt-optimizer.md) and [Fine Tuning](fine-tuning/) aren't available for multi-turn tasks. To generate test conversations, use the Eval Builder.

### Python Library

* Set `turn_mode=TurnMode.multiturn` (from `kiln_ai.datamodel.datamodel_enums`) when you create a `Task`.
* Each turn is a `TaskRun`. Its `parent_task_run_id` is the ID of the previous turn's run, and its `trace` holds the conversation so far.
* `task.runs()` returns the latest turn of each conversation. Pass `include_intermediate_runs=True` for every turn.
