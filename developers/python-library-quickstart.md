---
icon: python
description: pip install kiln_ai
---

# Python Library Setup

{% hint style="info" %}
The Python library is completely optional. If you just want to use the app, follow our [Quickstart guide](../docs/quickstart.md).
{% endhint %}

Our open source [python library](https://pypi.org/project/kiln-ai/) allows you to use Kiln from your codebase. This can be as simple as accessing a Kiln dataset from a notebook, or as advanced as running any of our features from code.

[![PyPI - Version](https://img.shields.io/pypi/v/kiln-ai.svg?logo=pypi\&label=PyPI\&logoColor=gold)](https://pypi.org/project/kiln-ai/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kiln-ai.svg?logo=python\&label=Python\&logoColor=gold)](https://pypi.org/project/kiln-ai/) [![Docs](https://img.shields.io/badge/docs-pdoc-blue)](https://kiln-ai.github.io/Kiln/kiln_core_docs/index.html)

### Installation

To install Kiln, run the following command:

```bash
pip install kiln_ai
```

### Library Docs & Examples

Our [library docs](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html) include an API reference for all of the library's features.

The docs include several quick-start examples to get up and running:

* [Using the Kiln Data Model](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#using-the-kiln-data-model)
  * [Understanding the Kiln Data Model](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#understanding-the-kiln-data-model)
  * [Datamodel Overview](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#datamodel-overview)
  * [Load a Project](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#load-a-project)
  * [Load an Existing Dataset into a Kiln Task Dataset](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#load-an-existing-dataset-into-a-kiln-task-dataset)
  * [Using your Kiln Dataset in a Notebook or Project](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#using-your-kiln-dataset-in-a-notebook-or-project)
  * [Using Kiln Dataset in Pandas](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#using-kiln-dataset-in-pandas)

### Web/REST API

We also offer a self-hostable [REST API](rest-api.md) for Kiln, based on FastAPI.
