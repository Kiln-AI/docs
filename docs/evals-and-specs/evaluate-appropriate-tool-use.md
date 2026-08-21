---
description: Test your model's ability to appropriately invoke tools
---

# Evaluate Appropriate Tool Use

<figure><img src="../../.gitbook/assets/Repair.png" alt=""><figcaption></figcaption></figure>

{% hint style="success" %}
**It doesn't matter how well a tool works if it isn't invoked when needed.**

Kiln can evaluate your agent's tool use to help find issues early.
{% endhint %}

### **Overview**

Tool use evals measure how well your model decides when to invoke a tool. They check that:

* The tool is called when needed
* The tool isn’t called when it shouldn’t be
* The parameters passed to the tool are correct
* The agent doesn't take an unreasonable number of steps to get there

### Two Ways to Evaluate Tool Use

Most tool use questions have a definite right answer, and Kiln can check those directly in code:

* **[Tool Call Check](judge-types.md#tool-call-check)**: inspects the agent's trace and asserts which tools were called, in what order, and with what arguments. No model call, so it's free, instant, and returns the same answer every time. **Start here.**
* **[Step Count Check](judge-types.md#step-count-check)**: asserts the agent finished within a reasonable number of tool calls or turns. A good companion to a Tool Call Check — "it called the right tool" and "it didn't call it eleven times" are different bugs.
* **[LLM as Judge](judge-types.md#llm-as-judge)**: a model reads the whole trace and forms an opinion. Reach for this only when whether the tool *should* have been called is genuinely a judgement call.

{% hint style="info" %}
The rule of thumb: if you can write down the tool calls you expect, use a Tool Call Check. If deciding whether the agent was right requires reading the user's request and thinking about it, use an LLM judge.
{% endhint %}

### Evaluating Tool Use with a Tool Call Check

#### Creating the Eval

From the "Evals" tab in Kiln's UI, create a new eval and select "Tool Call Check" under "Programmatic Checks".

You'll configure:

* **Expected Tools**: the tools you expect the agent to call. For each one, you can also specify expected arguments, matched exactly, by substring, or by regular expression.
* **Match Mode**:
  * `all`: every expected tool was called
  * `any`: at least one expected tool was called
  * `ordered`: the expected tools were called, in the order you listed them
  * `never`: none of the listed tools were called
* **Unexpected Tools**: ignore any other tool the agent calls, or fail the check if it calls anything not on your list.

Some examples of what these combinations express:

| Goal | Configuration |
| ---- | ------------- |
| The agent must search before answering | `search` with match mode `all` |
| The agent must search, then fetch the page | `search`, `fetch_url` with match mode `ordered` |
| The agent must never email a customer directly | `send_email` with match mode `never` |
| The agent must look up the right user | `get_user` with an expected argument `id` matching your value |
| The agent must stay within its allowed tools | your tool list, with unexpected tools set to fail |

Use the Test Run pane to run your check against a real dataset item before saving. Kiln will pre-select an item that actually has a trace, so there's something for the check to inspect.

#### No Golden Set Required

A Tool Call Check doesn't approximate human judgement, so there's no judge to align: you don't need a golden dataset, human ratings, or the [Compare Judges](evaluations.md#finding-the-ideal-judge) flow. Populate your test dataset and go straight to [comparing run methods](evaluate-appropriate-tool-use.md#finding-the-ideal-run-configuration).

#### Generate Synthetic Test Data

Populate your test dataset using synthetic data generation. Click "Add Eval Data" from the Evals UI and select "Synthetic Data" to launch the generator with the proper eval tags already populated.

{% hint style="info" %}
**Tool-Specific Behaviour**: when generating outputs, the tools available to your task are enabled for this step, ensuring your model has the opportunity to call them when appropriate. The system captures the full conversation trace, including whether the tool was called and what parameters were used.

Synthetic data generation is also aware of your check: for an eval scored by a Tool Call Check, the generator reads the check's definition and creates inputs designed to expose its failures. See our [Synthetic Data Generation docs](../synthetic-data-generation/) for more guidance.
{% endhint %}

### Evaluating Judgement with an LLM Judge

Some tool use questions really are subjective. "Should the agent have searched the web here, or was its own knowledge good enough?" doesn't have one right answer for every input — it depends on the request.

For those, create an eval with the "Desired Behaviour" template and add an [LLM as Judge](judge-types.md#llm-as-judge). Make sure conversation history is included, so the judge examines the full trace rather than only the final response.

#### Describe When the Tool Should be Used

Your judge needs guidelines describing correct usage. These help both the synthetic data generator create relevant test cases and the judge understand what "appropriate" means for your task.

**Web Research** tool examples:

* "Questions requiring current information, recent events, or up-to-date data that may have changed"
* "Questions about specific facts, statistics, or information that may not be in the model's training data"
* "Questions asking for comparisons, reviews, or analysis that benefit from multiple sources"

It's just as useful to describe when the tool should **not** be used. This creates a more comprehensive test dataset that includes clear negative cases.

**Web Research** tool examples:

* "General conversation, greetings, or questions that don't require factual information"
* "Questions about well-established facts, definitions, or concepts that are reliably in the model's training data"
* "Simple calculations, math problems, or questions that can be answered without external information"

#### Add Human Ratings

An LLM judge needs a golden dataset with human ratings, so you can measure how well it matches human preference. When rating for tool use, you'll need to check both the dataset entry and the Message Trace to see if the tool was invoked and with what parameters.

1. Click the `Rate Golden Dataset` button on the eval screen to go to the dataset view filtered to your golden dataset. For general guidance on rating, see [Reviewing and Rating](../reviewing-and-rating.md).
2. **View the Message Trace** for each dataset entry to inspect:
   * Whether the tool was called
   * What parameters were passed to the tool

This allows you to accurately rate whether the tool was called appropriately based on the full conversation context.

For your eval output rating, you should click "Pass" if the model's behaviour was appropriate and "Fail" if not.

**Pass = Appropriate Tool Use**

* The model called the tool with correct parameters at the appropriate time
* The model correctly did not call the tool as it was not needed

**Fail = Inappropriate Tool Use**

* The model should have called the tool but did not
* The model called the tool but shouldn't have, or called it with wrong parameters.

#### Finding the Ideal Judge

For detailed guidance on selecting judge models, customizing evaluation steps, and comparing judges to find the one that best aligns with human preferences, see [Add a Judge to your Eval](evaluations.md#add-a-judge-to-your-eval) and [Finding the Ideal Judge](evaluations.md#finding-the-ideal-judge).

{% hint style="success" %}
You can add both to one eval. A Tool Call Check that asserts the mechanics, plus an LLM judge for the judgement call, gives you a cheap signal that runs on everything and a nuanced one where it matters.
{% endhint %}

### Finding the Ideal Run Configuration

Once your eval is set up, you can evaluate different configurations for running your task. Since tool use evals specifically test your model's tool calling behaviour, you'll want to test configurations such as:

* Different task models (some models are better at tool calling than others)
* Different prompts and system instructions
* Different sets of available tools (testing with varying numbers of tools can help identify optimal tool configurations)

You will also be able to see the tools available to each run configuration. Keep in mind that any run configuration without access to the tool you are evaluating will produce unreliable scores, as the model cannot actually invoke the tool being tested.

<figure><img src="../../.gitbook/assets/Screenshot 2025-11-14 at 1.33.24 PM.png" alt="" width="375"><figcaption><p>Comparing Run Configurations</p></figcaption></figure>

For detailed guidance on selecting and comparing task model options, see [Finding the Ideal Run Method](evaluations.md#finding-the-ideal-run-method).

{% hint style="info" %}
**Already built an "Appropriate Tool Use" eval?**

Earlier versions of Kiln offered an "Appropriate Tool Use" LLM template. Those evals keep working exactly as they did, and there's nothing to migrate. New tool use evals are best built with a Tool Call Check, which is faster, free to run, and perfectly consistent.
{% endhint %}
