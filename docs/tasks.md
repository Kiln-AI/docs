---
description: What a task is, how to create one, and when to use single-turn or multi-turn
icon: clipboard-list
---

# Tasks

A task is a single goal for a model to accomplish, such as answering customer questions or extracting fields from an invoice. Prompts, datasets, evals and fine-tunes all belong to a task.

### Creating a Task

The app walks you through your first task when you set up a project. To add another, open Settings, then **Manage Projects**, and choose **Add Task** from the project's menu. The form asks for a name, the task's instructions (its [prompt](prompts.md)), the task type, and, for single-turn tasks, optional [input and output schemas](structured-data-json.md).

### Single-turn or Multi-turn

Pick the type under **Part 2: Task Type** when you create a task. It can't be changed later: to switch, open **Edit Current Task** in Settings, click **Clone Task** and pick the other type. The clone starts with no data.

|  | Single-turn | Multi-turn |
| --- | --- | --- |
| **Shape** | One user message and one response | A back-and-forth conversation |
| **Examples** | Classify a support ticket, extract fields from an invoice, summarize a document, write a product description | A customer support chatbot, a tutor, an intake assistant that asks follow-up questions, a coding assistant you refine answers with |
| **Input and output** | Plain text or [structured JSON](structured-data-json.md) | Plain text |
| **[Synthetic Data Generation](synthetic-data-generation/), [Prompt Optimizer](prompts/automatic-prompt-optimizer.md), [Fine Tuning](fine-tuning/)** | ✅ | Not supported |
| **[Eval Builder](evals-and-specs/specifications.md)** | ✅ | ✅, with a simulated user |

If the model needs earlier messages from the same conversation to reply, use multi-turn. Otherwise, use single-turn. One turn can include many tool calls, so an agent that handles each request on its own is still single-turn.

### Multi-turn Tasks

#### Chatting and Your Dataset

Send a first message from the **Run** tab. The conversation then continues on its **Dataset Run** page, where you can:

* Change the model or tools in **Options** between turns. The prompt stays as it was on the first turn.
* Hover an earlier reply and click **Fork** to start a new branch from that point. The original stays unchanged.
* Rate the conversation. Ratings and tags attach to the turn you're viewing, and a new turn starts unrated.

The **Dataset** tab shows one row per conversation, with each fork as its own row.

#### Importing Conversations

On the **Dataset** tab, click **Add Data** (**Manually Add Data** if the dataset is empty), then **Add CSV**. Each row holds one conversation in a `trace` column, and the dialog explains the format and has a sample CSV.

#### Evaluating

Use the [Eval Builder](evals-and-specs/specifications.md) to evaluate a multi-turn task: it creates simulated users and a judge that scores each whole conversation. Every run configuration you compare holds its own conversation with each simulated user. Conversations stored in your dataset can't be re-run for a run configuration.

#### Python Library

* Set `turn_mode=TurnMode.multiturn` (from `kiln_ai.datamodel.datamodel_enums`) when you create a `Task`.
* Each turn is a `TaskRun`. Its `parent_task_run_id` is the ID of the previous turn's run, and its `trace` holds the conversation so far.
* `task.runs()` returns the latest turn of each conversation. Pass `include_intermediate_runs=True` for every turn.
