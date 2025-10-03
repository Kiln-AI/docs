---
description: Building Agentic AI systems has never been easier
icon: circle-nodes
---

# Agents

{% hint style="warning" %}
You're here early! Multi-actor agents are launching next week
{% endhint %}

Ah "agents", the move overloaded term in AI! The word "Agents" means different things to different people, but the good news is Kiln supports all the patterns typically associated with "agentic systems". Let's break down the common agent features, and how to build them in Kiln!

* [Tool Use](agents.md#tool-use)
* [Multi-Actor Interaction (aka sub-tasks)](agents.md#multi-actor-interaction-aka-sub-tasks)
* [Goal Directed, Autonomous Looping & Reasoning](agents.md#goal-directed-autonomy-and-reasoning)
* [State & Memory](agents.md#state-and-memory)

### Tool Use

Almost every definition of agents includes tool use. This is some way for the agent to interact with the outside world, such as calling a database, calling an API, or even sending an email.

Kiln has full support for adding tools to your Kiln tasks. Tools can be added to Kiln via [MCP servers](tools-and-mcp.md#connecting-tools) or [Kiln Search Tools (RAG)](documents-and-search-rag.md). See the [Tools & MCP](tools-and-mcp.md) docs for details.

### Multi-Actor Interaction (aka sub-tasks)

Agentic systems often involve an AI agent delegating/coordinating other agents. There are many variants of this pattern with names like orchestrators, supervisors, directors, executors, and experts/assistant.&#x20;

Kiln has full support for this pattern via Kiln Task as Tools:

#### Kiln Tasks as Tools

In Kiln you can make any Kiln Task into a tool which other tasks can then call. This gives you the flexibility to create multi-actor patterns by organizing a heiarachy of tasks:

<figure><img src="../.gitbook/assets/Screenshot 2025-10-03 at 1.31.54 PM.png" alt="" width="375"><figcaption><p>A Kiln task, able to other Kiln tasks as tools</p></figcaption></figure>

To create a Kiln Task as Tool follow these steps:

**Step 1: Create a Kiln Task**

First create a new task. Select "New Task" in the project menu in the sidebar, and fill out the form with a name and prompt.

<figure><img src="../.gitbook/assets/new task.png" alt="" width="275"><figcaption></figcaption></figure>

**Step 2: Add Tools**

If you haven't already and this task requires tools, add tools to your project following the instructions in our [Tools & MCP docs](tools-and-mcp.md).

**Step 2: Create a Run Configuration**

Each Kiln task is run with a "run configuration" which specified which model is used, which prompt is used, which tools are allowed, and more. Since you want your tool calls to be completely consistent, you must first create and save a run configuration.

The easiest way to create a run configuration is from the "Run" tab in Kiln. You can tweak every parameters, run the task to ensure it works, then save it when you're happy.

<figure><img src="../.gitbook/assets/Screenshot 2025-10-03 at 1.48.21 PM.png" alt="" width="375"><figcaption><p>Creating a run configuration in the "Run" tab</p></figcaption></figure>

**Step 3: Create a Kiln Task as Tool**

To turn your task and run config into a tool other tasks can call, open "Settings" > "Manage Tools" > "Add Tools" > "Kiln Task as Tool".&#x20;

When creating you'll be asked to provide a number of options

* Kiln task: which task this tool will call
* Run configuration: which model to use, and which tools to allow this sub-task to call
* Tool name: the name of the tool, which the calling task will see
* Tool description: the description of the tool, which the calling task will see

{% hint style="warning" %}
You’ll be asked to provide a tool name and description. These are very important as the model will read them to decide if and when to use your this sub-task / agent.

For example:

* **Poor:** search - “Search for information” (where will is search?, what information?)
* **Better:** web\_search - “Search the web for information”
* **Best:** web\_researcher - "This tool can search and scape the web for information. Ask it a question and will research using the web, and reply with a summarized answer."
{% endhint %}

<figure><img src="../.gitbook/assets/Screenshot 2025-10-03 at 1.58.39 PM.png" alt="" width="375"><figcaption><p>Creating a Kiln Task as Tool</p></figcaption></figure>

**Step 4: Use Your Task as Tool**

To use your new sub-task, simply select it from the "Tools & Search" dropdown on the Run tab.

<figure><img src="../.gitbook/assets/Screenshot 2025-10-03 at 2.10.42 PM.png" alt="" width="375"><figcaption><p>Adding a Kiln task as tool sub-task</p></figcaption></figure>

If you always want this task to have access to this tool, use the "Save current options" and "Set as task default" links to create a default run configuration inlcuding this task.

**Step 5: Viewing Tool Calls**

When you run a task that has access to sub-tasks, you're able to view the tool/task invocations in the "All Messages" list. Click the "Messages" link to see the sub-tasks message list.

<figure><img src="../.gitbook/assets/Screenshot 2025-10-03 at 2.16.13 PM.png" alt="" width="375"><figcaption></figcaption></figure>

#### Context Manament&#x20;

A common issue with agentic systems is that the context window (chat history) gets very long. This can cause several major issues:

* Running out of room in the context window — the max context size of the model — causing a error/failure
* Degraded quality: a large context window can degrade the quality of newly generated content, especially if some of the messages are no longer relevant.
* Increased costs: each new message still has to pay for processing the entire chat history.&#x20;

Using sub-tasks is the easiest way to solve context management issues. Let's look a a visual example of an agent which requires many web-searches to build a final answer:

* Without Sub-Agents: the context becomes very large very quickly. Entire webpages are loaded into context and stay there. Data we don't need, like web pages that didn't yield useful information, keep taking context room forever. Later calls need to process a large number of tokens to generate the next new token (increasing cost).
* With Sub-Agents: each web-research task is performed in its own sub-agent. The results of the webpages are summarized and only the important details are returned to the main task. The context of the main task stays focused and small. Each sub-task is also smaller and more focused. Irrelevant data is dropped when the subtask ends. Costs are lower by approximately a factor of 4.

<figure><img src="../.gitbook/assets/context mgmt.png" alt=""><figcaption></figcaption></figure>

### Goal Directed, Autonomy, & Reasoning

Agents typically achieve aim to achieve a specific goal, and are given the ability to run over time to achieve that goal.&#x20;

* **Goal-directed**: acts to achieve objectives rather than just replying
* **Planning & reasoning:** agents can break problems into steps, decide what to do next, and reason between tool calls
* **Autonomy / Looping**: the agent can choose how to achieve the goal, calling any tool in any order. They can loop, mixing thinking/reasoning and tool calls until their task is complete.

Kiln tasks support all of these:

* **Goal directed**: you define the agent's goal when you create the task prompt, and when you pass the user input
* **Planning & Reasoning**: All agent loops plan internally. You can tell your tasks to perform additional reasoning by either 1) selecting a reasoning model, 2) selecting a "Chain of Thought" prompt which will explicit ask the model to reason during the run loop.
* **Autonomy / Looping**: Every Kiln task can loop, making many tool calls until deciding to return a final result. The task has autonomy to decide which tools to call, in which order.

{% hint style="success" %}
**Advanced Users: ReAct in Kiln**

A common agent pattern is called "ReAct". I was defined in the paper by [Yao et al](https://arxiv.org/abs/2210.03629).

While we don't use the name ReAct in the Kiln app, a Kiln task with a chain-of-thought prompt has the same  reasoning+acting steps as described in the ReAct paper.&#x20;
{% endhint %}

### State & Memory

Agents maintain state over steps, letting them make progress towards their goals.

Currently Kiln maintains memory simply through the message history. See the [context mangement](agents.md#context-manament) section above for how to use Kiln sub-tasks to compressing memory, summarizing of many sub-task messages into a shorter message in the main-task history.

We're exploring additional memory management options in Kiln. If you have requests, please let us know on the [Discord](https://kiln.tech/discord)!

