---
description: >-
  Score your evals with LLM judges, or with fast deterministic checks that cost
  nothing to run
---

# Judge Types

A judge is a method of running an eval: it takes the output of a task run, and produces scores. Every eval in Kiln can have many judges, and each judge has a type.

Kiln offers two families of judge types:

* **LLM Judges**: a model reads the output and grades it against criteria you write. Best for subjective qualities like tone, helpfulness, toxicity, etc.
* **Programmatic Judges**: code inspects the output or the trace and returns a pass/fail. No model call, so they're fast, free, and return the same answer every time. Best for anything you can state as a rule.

{% hint style="success" %}
**Prefer a programmatic judge when one fits.**

An LLM judge that decides "did the agent call `get_weather` before answering?" costs money on every run and can change its mind. A [Tool Call Check](judge-types.md#tool-call-check) answers the same question for free, identically, every time.

Save LLM judges for the questions that genuinely require subjective judgement.
{% endhint %}

### The Judge Types

| Judge Type | Family | What it scores |
| ---------- | ------ | -------------- |
| [LLM as Judge](judge-types.md#llm-as-judge) | LLM Judge | A model grades the output against a rubric you write |
| [Code](judge-types.md#code-beta) | Programmatic Judge | A custom Python `score()` function you write |
| [Tool Call Check](judge-types.md#tool-call-check) | Programmatic Judge | The agent called the right tools, in the right order, with the right arguments |
| [Exact Match](judge-types.md#exact-match) | Programmatic Judge | The output equals an expected value |
| [Pattern Match](judge-types.md#pattern-match) | Programmatic Judge | The output matches (or doesn't match) a regular expression |
| [Contains](judge-types.md#contains) | Programmatic Judge | The output contains (or omits) a substring |
| [Set Check](judge-types.md#set-check) | Programmatic Judge | A set of values from the output matches an expected set |
| [Step Count Check](judge-types.md#step-count-check) | Programmatic Judge | The agent finished within an expected number of steps |

To add a judge, open your eval and create a new judge, or pick a type directly from the "Select an Eval Type" screen when creating a new eval. Programmatic judges are listed under the "Programmatic Judges" heading.

### Choosing a Judge Type

Work down this list and stop at the first one that fits:

1. **Is there exactly one right answer?** Use [Exact Match](judge-types.md#exact-match) (or [Set Check](judge-types.md#set-check) if the answer is a set of values).
2. **Can you state the rule as text matching?** Use [Contains](judge-types.md#contains) or [Pattern Match](judge-types.md#pattern-match). Good for format rules ("always ends with a citation", "never mentions a competitor").
3. **Is it about what the agent did, not what it said?** Use [Tool Call Check](judge-types.md#tool-call-check) for which tools ran, or [Step Count Check](judge-types.md#step-count-check) for how many steps it took.
4. **Is the rule real, but too complex for the above?** Use a [Code](judge-types.md#code-beta) judge. It can also call an LLM for the subjective part, so you can filter a huge trace down in code and only pay for a judgement on what's left. See [Code Judges](code-judges.md).
5. **Otherwise, use an** [**LLM as Judge**](judge-types.md#llm-as-judge). Subjective quality needs a model.

{% hint style="info" %}
A single eval can have judges of different types, and Kiln will show their scores side by side. A "helpfulness" eval can pair an LLM judge for tone with a Pattern Match that catches a formatting bug — you don't need to pick just one.
{% endhint %}

### Output to Check

The Exact Match, Pattern Match, Contains and Set Check types ask which part of the run they should look at:

* **Final Message**: the model's final output. The default, and what you want most of the time.
* **Entire Trace**: the whole conversation, including tool calls, as JSON.
* **Custom (Jinja)**: extract part of the output or trace using a Jinja expression.

Custom expressions are useful for structured outputs and agent traces. Some examples:

| Goal | Expression |
| ---- | ---------- |
| Extract a field from JSON output | `(final_message \| fromjson).user.status` |
| Truncate a long output | `final_message \| truncate(200)` |
| Last message in the trace | `trace[-1].content` |
| Count messages in the trace | `trace \| length` |
| Name of a tool called in the trace | `trace[-1].tool_calls[0].function.name` |

Tool Call Check and Step Count Check always read the trace, so they don't offer this option. [Code](judge-types.md#code-beta) judges receive the output and trace directly, and pick out what they need in Python.

### LLM as Judge

A model reads the output and grades it against criteria you write, producing a score for each of your eval's output scores.

Configure it with:

* **Model and provider**: we suggest larger, higher quality models for judges. You're trusting their results to make product decisions, and evals run far less often than your task.
* **Judge prompt**: pre-populated from your eval's task description and evaluation steps, and editable at creation time.
* **G-Eval** (optional): an enhanced form of LLM as Judge which looks at token output probabilities (logprobs) to produce a weighted score. If the model had a 51% chance of passing an item and 49% chance of failing it, G-Eval gives the more nuanced score of 0.51, where LLM as Judge would simply pass it (1.0). The [G-Eval paper (Liu et al)](https://arxiv.org/abs/2303.16634) shows it can outperform alternatives like BLEU, ROUGE and embedding distance scores across a range of eval tasks.

{% hint style="info" %}
G-Eval requires logprobs, which only a limited set of models support — currently it works best with OpenAI models like GPT-4o and GPT 4.1. The option only appears when you select a supported model and provider.

Unfortunately [Ollama doesn't support logprobs yet](https://github.com/ollama/ollama/issues/2415).
{% endhint %}

For guidance on judge prompts, evaluation steps, and picking a judge model, see [Add a Judge to your Eval](evaluations.md#add-a-judge-to-your-eval).

### Programmatic Judges

#### Exact Match

Passes when the output equals an expected value.

* **Expected Value**: the value the output should equal.
* **Case Sensitive**: on by default.
* **Output to Check**: see [above](judge-types.md#output-to-check).

Best for tasks with a single correct answer: classification labels, yes/no answers, extracted IDs.

#### Pattern Match

Passes when the output matches a regular expression — or when it doesn't, if you set the mode to "must not match".

* **Pattern**: any Python regular expression.
* **Mode**: must match, or must not match.

Best for format rules. A "must not match" pattern is a cheap way to catch an output that keeps leaking something it shouldn't, like a placeholder string or an internal ID format.

#### Contains

Passes when the output contains a substring — or when it doesn't, if you set the mode to "must not contain".

* **Substring**: the text to look for.
* **Case Sensitive**: on by default.
* **Mode**: must contain, or must not contain.

Simpler than Pattern Match, and usually clearer to a teammate reading your eval later. Reach for Pattern Match only when a plain substring won't do.

#### Set Check

Parses a set of values from the output and compares it to an expected set.

* **Expected Set**: the values to compare against.
* **Mode**: `subset` (everything found must be in the expected set), `superset` (everything expected must be found), or `equal` (exactly the same values).

Best for multi-label classification, tag extraction, or any task where the output is a list and the order doesn't matter.

#### Tool Call Check

Inspects the agent's trace to check it called the tools you expected.

* **Expected Tools**: one or more tools, each optionally with expected arguments. Each argument can be matched exactly, by substring, or by regular expression.
* **Match Mode**:
  * `all`: every expected tool was called
  * `any`: at least one expected tool was called
  * `ordered`: the expected tools were called, in the order listed
  * `never`: none of the listed tools were called
* **Unexpected Tools**: ignore other tool calls, or fail the check if the agent calls anything not on your list.

This is the deterministic way to test tool use. It answers "did the agent do the right thing?" for free, where an LLM judge would need to read the whole trace and form an opinion. See [Evaluate Appropriate Tool Use](evaluate-appropriate-tool-use.md) for the full workflow, including when you still want an LLM judge.

#### Step Count Check

Counts steps in the agent's trace and passes when the count is within bounds you set.

* **Count Type**: tool calls, model responses, or conversation turns.
* **Min Count / Max Count**: at least one is required.

Best for agent efficiency. Cap an agent at 5 tool calls to catch runaway loops, or require at least 1 to confirm it actually used a tool instead of answering from memory.

#### Code (Beta)

Write a custom Python `score()` function. It can read the output, the full trace, and the task input, and it can call other tools — including built-in tools that call an LLM.

See the [Code Judges](code-judges.md) guide for details.

### Judges and Human Ratings

Kiln's [judge comparison](evaluations.md#finding-the-ideal-judge) tools measure how closely a judge's scores match human ratings from your golden dataset. This is essential for LLM judges: an LLM judge is an approximation of human preference, and you need to know how good the approximation is.

Programmatic judges are a different kind of thing. They don't approximate anything — a Pattern Match either encodes the rule you meant or it doesn't, and it will return the same answer forever. You generally don't need a golden set or human ratings to trust one.

Running judge comparison on a programmatic judge is still allowed, and there's one case where it's genuinely useful: confirming that the rule you wrote actually captures what humans care about. If your Tool Call Check passes items your subject matter expert would fail, the check is wrong, not the human — and comparison will show you that.

{% hint style="success" %}
If your eval only uses programmatic judges, you can skip the golden dataset and human rating steps entirely, and go straight to [comparing run methods](evaluations.md#finding-the-ideal-run-method).
{% endhint %}
