---
description: Score your evals with a custom Python function
---

# Code Judges

{% hint style="info" %}
Code judges are in **beta**. The authoring contract may change in future releases.
{% endhint %}

A code judge scores your eval with a Python function you write, instead of a model or a built-in check. It's the escape hatch for rules that are real and checkable, but too complex for the other [judge types](judge-types.md): scoring against a lookup table, parsing a structured output and validating it, or measuring something specific to your domain.

Code judges are fast and cheap compared to [LLM as Judge](judge-types.md#llm-as-judge), and unlike an LLM judge they return the same score every time.

### Creating a Code Judge

Add a judge to your eval and select the "Code" type. You'll get a Python editor, a tool picker, and a test panel for running your code against real dataset items before you save it.

{% hint style="warning" %}
**Code judges run on your machine, with full access.**

There are no import restrictions or resource limits beyond the timeout. The first time you add or edit code in a project, Kiln asks you to confirm you trust it — that trust gate is the security boundary. See [Code Trust](../tools-and-mcp/code-tools.md#code-trust) for details.
{% endhint %}

### The `score()` Function

Your code must define a function named `score()`. Kiln passes it only the arguments your function actually declares, so declare the ones you need and omit the rest. You must accept at least `output` or `trace`.

| Parameter | What you get |
| --------- | ------------ |
| `output` | The model's final output, as a string |
| `trace` | The full conversation, as a list of message dicts |
| `task_input` | The original task input, as a string |
| `reference_data` | A dict of ground-truth data for this item, or `None` |

`score()` returns a dict, keyed by the JSON key of each of your eval's output scores. A score's JSON key is its display name in lowercase snake\_case: a score named "Exact Match" has the key `exact_match`. Kiln checks the returned keys against exactly this set, so return the JSON keys, not the display names.

```python
def score(output: str) -> dict:
    """Pass when the output is valid JSON with a non-empty summary."""
    import json

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return {"valid_output": 0.0}

    has_summary = bool(parsed.get("summary", "").strip())
    return {"valid_output": 1.0 if has_summary else 0.0}
```

Scores are floats. For a pass/fail score, return `1.0` or `0.0`.

### Calling LLMs from a Code Judge

Code judges can call two built-in tools, selectable from the judge's tool picker like any other tool:

* **`llm`**: a general-purpose model call. Pass a prompt, model and provider. Provide an optional JSON schema to force structured output; without one you get text back.
* **`llm_judge`**: the same, but it automatically applies your eval's own output score schema and returns mapped float scores — so you can return its result directly.

Both run outside the code sandbox, so your API keys are never exposed to your judge's code.

This combination solves the long-trace problem. An agent run can produce a 500k token trace, and handing all of it to an LLM judge is slow and expensive. Instead, filter it down in code to the handful of messages that actually matter, then ask a cheap model about just those:

```python
import json
from kiln import tools


def score(trace: list) -> dict:
    """Judge only the user-facing messages, ignoring tool chatter."""
    user_facing = [
        m["content"]
        for m in trace
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]
    transcript = "\n\n".join(user_facing)

    result = tools.llm_judge(
        prompt=f"Was the assistant helpful in this conversation?\n\n{transcript}",
        model="gpt_4_1_mini",
        provider="openai",
    )
    return json.loads(result)
```

Your judge can call any other tool in its allowlist too, not just the LLM tools. See [Calling Other Tools](../tools-and-mcp/code-tools.md#calling-other-tools) for the full API.

### Advanced Options

* **Timeout**: wall-clock timeout for scoring one item, including any nested tool calls. Defaults to 180 seconds.
* **Tools**: an explicit allowlist of the tools your code may call. Code with no tools selected can't make tool calls at all.

### Your Code is a Real Python File

Kiln stores your judge's source as `scorer.py`, in the eval config's folder next to `eval_config.kiln`:

```
{task}/.../eval_configs/{id} - {name}/
  ├── eval_config.kiln   # metadata (no code)
  └── scorer.py          # your score() source
```

Because it's a plain Python file rather than a string inside JSON, it's importable, lintable, type-checkable, and produces a readable diff when you review changes in [Git](../collaboration/).

### Testing with pytest

You can write standard `pytest` tests against your judge. `score()` takes plain keyword arguments and depends only on the standard library plus `kiln_ai`, so you can import and call it directly — no Kiln-specific test runner.

Create `test_scorer.py` beside `scorer.py`:

```python
from scorer import score


# For an eval whose output score is named "Valid Output" (JSON key: valid_output).
def test_accepts_good_output():
    result = score(output='{"summary": "A real summary."}')
    assert result["valid_output"] == 1.0


def test_rejects_empty_summary():
    result = score(output='{"summary": ""}')
    assert result["valid_output"] == 0.0
```

Then run `pytest` from that folder. Kiln doesn't store, display, or run these tests — they live in a normal Python environment with `kiln_ai` installed.

{% hint style="info" %}
`scorer.py` is a fixed filename, so running `pytest` across several eval config folders at once hits a module name collision. Run `pytest` from inside a single folder, or use `pytest --import-mode=importlib`.
{% endhint %}

### Learn More

* [Judge Types](judge-types.md): all the judge types, and when to use each
* [Code Tools](../tools-and-mcp/code-tools.md): the same Python authoring model, for tools your agents call
* [Code Tools Authoring Guide](https://github.com/Kiln-AI/Kiln/blob/main/docs/code_tools_guide.md): the complete authoring contract, including the tool calling API and testing details
