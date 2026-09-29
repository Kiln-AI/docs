---
description: Chat-style tasks, where the user and the model take turns in one conversation
icon: comments
---

# Multi-turn Tasks

A multi-turn task is a back-and-forth conversation: the user sends a message, the model replies, and the conversation continues. You chat with it on the **Run** page, keep each conversation in your **Dataset**, and evaluate it with the [Eval Builder](evals-and-specs/specifications.md).

### Creating a Multi-turn Task

When you create a task, pick **Multi-turn** under **Part 2: Task Type**.

* Multi-turn tasks are plain text, so there's no input or output schema.
* The task type can't be changed after the task is created. To switch, open **Edit Current Task** in Settings, click **Clone Task** and pick the other type. The clone starts with no data.

### Chatting with Your Task

1. Click **Run** in the sidebar. You'll see **Start a conversation**.
2. Pick the model, prompt and tools under **Options**.
3. Type a message and click **Send**.

After the first reply, the conversation opens on its **Dataset Run** page. Type in the box under the last reply to add more turns.

* You can change the model or tools in **Options** between turns. The prompt stays as it was on the first turn.
* Hover a reply and click **Usage** for that turn's cost and tokens. **Total Usage** in the sidebar covers the whole conversation.
* Click **New Chat** to start another conversation.

### Conversations in Your Dataset

Each turn is saved as its own run, linked to the turn before it. The **Dataset** page shows one row per conversation, previewing its latest message and reply.

* **Rating and Feedback** and **Tags** attach to the turn you're viewing, normally the latest one. A new turn starts unrated and doesn't carry over the tags of earlier turns.
* **Parent ID** under **Properties** opens the previous turn.
* Deleting a conversation also deletes its earlier turns, unless another branch shares them.

#### Forking a Conversation

Hover an earlier reply and click **Fork**, then send a new message. This starts a new branch from that point. The original conversation stays unchanged, and each branch is its own row in the **Dataset**.

### Importing Conversations

On the **Dataset** page, click **Add Data** (**Manually Add Data** if the dataset is empty), then **Add CSV**. The **Add Multiturn CSV to Dataset** dialog takes one conversation per row:

* `trace`: required. A JSON list of OpenAI chat messages that alternate user and assistant, starting with user and ending with assistant. Assistant messages may include `reasoning_content`.
* `tags`: optional, comma-separated.

System messages and tool calls aren't supported. Set the system prompt on the task instead. **Download sample CSV** in the dialog has examples. One row from it:

```csv
trace,tags
"[{""role"":""user"",""content"":""What is 2+2?""},{""role"":""assistant"",""content"":""4"",""reasoning_content"":""The user is asking a basic arithmetic question. 2 plus 2 equals 4.""},{""role"":""user"",""content"":""And 3+3?""},{""role"":""assistant"",""content"":""6""}]",math
```

### Evaluating

Use the [Eval Builder](evals-and-specs/specifications.md#multi-turn-tasks) to evaluate a multi-turn task. It creates simulated users and a judge that scores each whole conversation, and every run config you compare holds its own conversation with each simulated user. Conversations stored in your dataset can't be re-run for a run config.

### Not Supported for Multi-turn Tasks

These pages show a message instead of their usual options:

| Feature | Message |
| --- | --- |
| [Synthetic Data Generation](synthetic-data-generation/) | "Synthetic data generation is not supported for multi-turn tasks." |
| [Automatic Prompt Optimizer](prompts/automatic-prompt-optimizer.md) | "Prompt optimization is not supported for multi-turn tasks." |
| [Fine Tuning](fine-tuning/) | "Fine-tuning is not supported for multi-turn tasks." |

To generate multi-turn test data, use the Eval Builder. [Repairs](repairing-responses.md) are also single-turn only.

### Python Library

* Set `turn_mode=TurnMode.multiturn` when you create a `Task`. Import `TurnMode` from `kiln_ai.datamodel.datamodel_enums`. It can't be changed later.
* Each turn is a `TaskRun`. Its `parent_task_run_id` is the ID of the previous turn's run, and its `trace` holds the whole conversation so far.
* `task.runs()` returns the latest turn of each conversation. Pass `include_intermediate_runs=True` to get every turn.
* To add a turn, get an adapter from `adapter_for_task` in `kiln_ai.adapters.adapter_registry`, then call `await adapter.invoke(message, prior_trace=parent_run.trace, parent_task_run=parent_run)`. The parent run must be saved first.

See [Python Library Setup](../developers/python-library-quickstart.md) to get started.
