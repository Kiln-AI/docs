---
description: Create an eval, its eval dataset and an aligned judge from a plain-language description
---

# Eval Builder

<figure><img src="../../.gitbook/assets/specs img (1).png" alt="" width="375"><figcaption></figcaption></figure>

Describe what an eval should check in plain language, and the Eval Builder creates it for you: an LLM judge, an eval dataset, and a golden dataset where you've checked the judge against your own review. It works with single-turn and [multi-turn tasks](../multi-turn-tasks.md).

{% hint style="info" %}
**Note:** The Eval Builder requires a Kiln Pro account. Registration is free and easy inside the Kiln app.
{% endhint %}

{% hint style="info" %}
The Eval Builder currently only supports the creation of LLM as Judge evals. For a programmatic check instead, pick one under **Programmatic Checks** on the **Create Eval** page (click **Set Up Manually** first if Kiln Pro isn't connected). See [Judge Types](judge-types.md).
{% endhint %}

### Getting Started

1. Open your task, click **Evals** in the sidebar, then click **Create Eval**.
2. If Kiln Pro isn't connected, click **Use Kiln Pro** and sign in. You return to the **Create Eval** page.
3. Under **LLM Judge Assistant**, type what the eval should check into **What should this eval check?** and click **Write My Eval**.
4. In **Choose Run Config**, pick the run config this eval is for and click **Continue**. The builder runs this config to create the eval data, and writes the questions and judge around its tools and skills.

The builder opens at Step 2, since your description is already filled in. The run config must run a model in Kiln: a run config that calls an [MCP tool](../tools-and-mcp/connect-to-existing-agents.md) can't create eval data.

### Step 1: Describe Your Eval

This holds the description you typed on the **Create Eval** page, so the builder normally skips it. Use your browser's Back button to return to it and change the description. Clicking **Continue** with a new description brings new clarifying questions.

### Step 2: Clarify Eval

Kiln Pro asks clarifying questions about your description. Pick an answer for each, or choose **Other** to write your own, then click **Continue**.

### Step 3: Review Updated Eval

Kiln Pro rewrites your description using your answers. Check the suggested **Eval Name** (max 32 characters) and the **Issue Description**, edit either one, then click **Continue**.

Every eval the builder makes is an [Issue](../issues.md) eval, so the description says what your agent must avoid doing.

### Step 4: Create Eval Dataset

For a single-turn task with no [Data Guide](../synthetic-data-generation/synthetic-data-guides.md), Kiln first offers to create one: **Set Up Data Guide** or **Continue Without Data Guide**.

Kiln Pro then drafts an **Eval Dataset Proposal**: a mix of items your agent should pass and items designed to tempt it into failing. Expand **All Items (N)** and click **Remove** on any item you don't want.

#### Dataset Size

Click **Refine Plan** to change the **Dataset Size**, or to add **Guidance** for the planner (for example, "10% of the dataset should be in Spanish."). The new plan replaces the current one, including any items already created.

| Dataset Size | Items |
| --- | --- |
| **Standard** (Recommended) | 60 items across train, val and test |
| **Deep** | 120 items across train, val and test |
| **Smoke Test** | 20 items, all in the test set. Can't be used for auto-optimize. |
| **Custom** | 35 to 120 items, set with **Item Count** |

Every plan adds 6 more items for you to review in Step 5, so a Standard plan lists 66 items.

#### Generation Settings

Click **Generate Dataset (N items)**. In **Generation Settings**, pick the **Input Generation Model**, which writes each item's input, and the **Judge Model**, then click **Generate Dataset (N items)** again.

Kiln writes the judge, makes a test call to each model, creates the inputs, then runs your task on each one and judges the result.

#### If Something Fails

* **A model fails its test call**: a banner names the model before anything else runs on your API keys. Check your [AI providers](../models-and-ai-providers.md) or your run config, then try again.
* **Some items fail**: click **Continue With N** to keep the items that worked, or **Re-run Batch**. A re-run fills in only the missing items, as long as you haven't changed the plan or **Generation Settings**.

### Step 5: Validate the Judge

Click **Start**. Kiln shows up to 6 cases, about half that the judge passed and half that it failed. For each case:

* Read the **Overview**. **Full Trace** and the numbered citations open the trace it describes.
* Click **Agree** or **Disagree** on each **Claim from Judge**. Each disagreement needs a reason: what should the judge have done instead?
* The last claim is the judge's verdict, starting "It passes" or "It fails". Disagreeing with it flips the rating saved for that case.

#### Improve Judge with Feedback

If you disagreed with anything, clicking **Next** on the last case opens **Improve Judge with Feedback?**. Choose **Improve Judge** and Kiln rewrites the judge from your feedback, re-checks every item with it, and starts a new review round that includes the cases you disagreed with. Or choose **Save Without Improving**.

With no disagreements, the eval saves right away.

### What Gets Saved

When you see **Eval Created**, click **View Eval**. The builder saves:

* **An eval** with a pass/fail score. Its judge reads the full conversation, including tool calls.
* **A judge** using your **Judge Model** and the final judge prompt, set as the eval's default.
* **A golden dataset**: the cases from your last review round, with your pass/fail ratings and feedback.
* **An eval dataset**: every other item, split evenly into test, train and val. Smoke Test puts them all in test.

The eval page can't add data to a builder eval, so build another eval to cover new cases. To score run configs, click **Run All Evals** under **Compare Run Configurations** on the eval page. See [Finding the Ideal Run Method](evaluations.md#finding-the-ideal-run-method).

### Multi-turn Tasks

On a [multi-turn task](../multi-turn-tasks.md), the builder tests your agent with simulated conversations:

* There's no Data Guide offer. Each planned item is a conversation scenario.
* **Generation Settings** asks for the **Model that writes the user's messages** and **Max turns per conversation** (1 to 20, default 5). A conversation can end sooner once the simulated user has what it came for.
* Kiln Pro creates a simulated user for each scenario, then your run config holds a conversation with it.
* The judge scores each whole conversation, and in Step 5 you review conversations.
* When you compare run configs, each one holds its own conversation with every simulated user. Each run config you add costs calls to your agent, the simulated user and the judge. Run configs you compare must also run a model in Kiln.

### Kiln Pro and Your API Keys

Kiln Pro writes the clarifying questions, the updated description and name, the plan, the judge prompt, the simulated users, the review claims and each improved judge.

Everything else runs on your own provider API keys: model test calls, creating inputs, running your task, simulated conversations, judging, re-checking, and later eval runs.

### Drafts and Reset

* The builder saves your progress as a draft in your browser. While it exists, the **Evals** page button reads **Continue Eval Draft**.
* Each task holds one draft, so finish it or click **Reset** before starting a different eval. **Reset** is also how you change the run config.
* Clarifying answers, results and review progress aren't saved. After a reload, the builder reopens at the step you'd reached, up to the plan. **Generate Dataset (N items)** then runs your task and the judge again, reusing the inputs it already created.
