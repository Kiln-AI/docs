---
title: "Code Tools"
description: "Write a Python function that runs as a tool, and can call other tools"
---
Code tools let you write Python that runs as a tool inside your agent, without leaving Kiln. They're stored in your project like any other artifact, and appear in the tools dropdown alongside your MCP servers and search tools.

### Why Code Tools

Agents rarely fail because the model is bad at reasoning. They fail because the interface they're given is messy:

* **N+1 tool loops**: an API with no batch endpoint forces the agent to call `get_user` fifty times, one per turn, burning context and time.
* **Context floods**: a tool returns a 40KB JSON blob when the agent needed three fields from it.
* **Missing operations**: the thing the agent actually needs is two API calls and a join, and no single tool does it.

You can try to fix these in the prompt, and the model will get it right most of the time. A code tool fixes them in code, once, and gets it right every time. A batch wrapper, a result filter, or a purpose-built endpoint is a durable artifact — it doesn't drift when you change models.

:::note
Code tools run inside the Kiln desktop app, on your machine. They aren't available to server-side deployments.
:::

### Creating a Code Tool

Open "Tools" > "Add Tools" > "Code Tool", and Kiln will walk you through two steps.

#### Step 1: Define the Tool

* **Display Name**: the name you and your team see in Kiln. For example "User Lookup".
* **Tool Name**: the function name exposed to the model. Lowercase with underscores, for example `get_user`.
* **Description**: shown to the model. Describe what the tool does and when to use it — this is what the model reads when deciding whether to call it.
* **Parameters**: the arguments the model passes to your tool, defined with the same schema builder used for task inputs and outputs.

:::caution
**Write the description for the model, not for yourself.**

Like [skills](/docs/skills/#creating-skills), the description is the model's only signal about when to use this tool. "Look up a user by ID and return their profile" beats "user tool".
:::

#### Step 2: Write the Code

Write a function named `run`. Your parameters arrive as keyword arguments matching the schema you defined:

```python
def run(user_id: str) -> str:
    """Look up a user and return their profile."""
    return f"User {user_id}"
```

Both sync and async forms work — use `async def run(...)` when you want concurrency.

Return values become the tool output the model sees. Strings pass through as-is; dicts, lists, numbers and booleans are JSON-serialized for you.

The right-hand panel of the editor has two things worth using before you save:

* **Tool Access**: an allowlist of the tools your code may call. Code with nothing selected can't make tool calls at all.
* **Test panel**: run your tool against real arguments, calling your real allowlisted tools, and see what comes back.

Under "Advanced Options" you can set the **timeout**: the wall-clock limit for one invocation, including any nested tool calls. Defaults to 60 seconds.

### Calling Other Tools

The most powerful thing a code tool can do is call other tools. Two modules are available in your code:

```python
from kiln import tools          # sync — blocks until the tool returns
from kiln import async_tools    # async — awaitable, concurrent under gather
```

Call an allowlisted tool as an attribute, with keyword arguments:

```python
import json
from kiln import tools


def run(query: str, max_results: int = 10) -> str:
    """Search, then return only the fields the agent actually needs."""
    raw = tools.search(query=query)
    results = json.loads(raw)

    filtered = [
        {"title": r["title"], "url": r["url"]}
        for r in results[:max_results]
        if "title" in r and "url" in r
    ]
    return json.dumps(filtered)
```

A few rules worth knowing up front:

* **Tool calls always return a string** — byte for byte what the model would have seen. Parse it yourself with `json.loads` when the tool returns JSON.
* **Keyword arguments only.** Positional arguments raise an error.
* **Only allowlisted tools resolve.** Calling anything else raises `ToolNotAllowed`, and the error lists what is available.
* **`tools.list_tools()`** returns the tools in your allowlist, with their descriptions and parameter schemas.

For true concurrency, use `async_tools` with `asyncio.gather` — this is the fix for the N+1 loop:

```python
import json
import asyncio
from kiln import async_tools


async def run(user_ids: list[str]) -> str:
    """Fetch many users at once, instead of one agent turn per user."""
    async def fetch(uid):
        return json.loads(await async_tools.get_user(id=uid))

    users = await asyncio.gather(*(fetch(uid) for uid in user_ids))
    return json.dumps(users)
```

Tool calls raise typed exceptions you can catch for retries: `ToolNotAllowed`, `ToolTimeout`, and `ToolCallError`. Import them from `kiln.tools` or `kiln.async_tools`.

:::note
Code tools can call other code tools — they're just tools.
:::

### Code Trust

:::danger
**Code tools run on your machine with full access.**

There is no sandbox: no import restrictions and no resource limits beyond the wall-clock timeout. Code can read your files, make network calls, and anything else Python can do.
:::

The trust gate is the security boundary. Adding or editing code in a project requires confirming that you trust it; running code you've already saved and trusted doesn't prompt you again. Trust is granted for the session, so Kiln asks again after a restart.

This matters most when a project came from somewhere else. Kiln projects are designed to be [shared across teams with Git](/docs/collaboration/), and a project you sync or import may contain code tools written by someone else. Importing a project authored elsewhere requires explicit approval before its code will run — treat that prompt the way you'd treat running an unfamiliar script from the internet, and read the code first.

### Your Code is a Real Python File

Kiln stores your tool's source as `tool.py`, in the tool's folder next to `code_tool.kiln`:

```
{project}/code_tools/{id} - {name}/
  ├── code_tool.kiln   # metadata (no code)
  └── tool.py          # your source — byte-for-byte what runs
```

Because it's a plain Python file rather than a string inside JSON, it's importable, lintable, type-checkable, and produces a readable diff in Git.

### Testing with pytest

Kiln ships a `pytest` plugin, so you can write standard tests against your tool in a normal Python environment. Install `kiln_ai` (`pip install kiln-ai`) and the plugin is auto-discovered: the `from kiln import tools` at the top of your `tool.py` resolves under `pytest`, and a `kiln_tools` fixture becomes available for stubbing tool responses.

Create `test_tool.py` in the same folder as `tool.py`:

```python
import json
import tool  # the artifact's tool.py — imports cleanly under pytest


def test_filters_results(kiln_tools):
    kiln_tools.set("search", json.dumps([
        {"title": "Real", "url": "https://example.com"},
        {"title": "No URL"},
    ]))

    out = json.loads(tool.run(query="anything"))

    assert out == [{"title": "Real", "url": "https://example.com"}]
    assert kiln_tools.calls[0].name == "search"
```

The fixture stubs replies with `kiln_tools.set(name, reply)`, forces errors with `kiln_tools.set_error(name, exc)`, and records every call in `kiln_tools.calls`. It behaves like the real runtime: unregistered tools raise `ToolNotAllowed`, positional arguments raise `ToolCallError`.

Kiln doesn't store, display, or run these tests — the loop lives in your own Python environment.

:::note
`tool.py` is a fixed filename, so running `pytest` across several tool folders at once hits a module name collision. Run `pytest` from inside a single tool folder, or use `pytest --import-mode=importlib`.
:::

### Code Tools vs Other Options

| | Code Tool | MCP Server | Kiln Task as Tool |
| ---- | --------- | ---------- | ----------------- |
| **Best for** | Wrapping, batching and filtering existing tools | Connecting an existing service or third-party integration | Delegating a sub-problem to another agent |
| **Written in** | Python, inside Kiln | Any language, outside Kiln | A Kiln task prompt |
| **Deterministic** | Yes | Depends on the server | No — it's a model call |
| **Setup** | Low | Medium | Medium |

### Learn More

* [Code Tools Authoring Guide](https://github.com/Kiln-AI/Kiln/blob/main/docs/code_tools_guide.md): the complete authoring contract, with more examples of concurrency, retries and error handling
* [Code Judges](/docs/evals-and-specs/code-judges/): the same Python model, used to score evals
