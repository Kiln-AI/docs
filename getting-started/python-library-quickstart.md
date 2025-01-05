---
icon: python
description: pip install kiln_ai
---

# Python Library Quickstart

Our open source [python library](https://pypi.org/project/kiln-ai/) allows you to use Kiln from your codebase. The can be as simple as accessing a Kiln dataset from a notebook, or as advanced as running any of our features from code.

[![PyPI - Version](https://img.shields.io/pypi/v/kiln-ai.svg?logo=pypi\&label=PyPI\&logoColor=gold)](https://pypi.org/project/kiln-ai/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/kiln-ai.svg?logo=python\&label=Python\&logoColor=gold)](https://pypi.org/project/kiln-ai/) [![Docs](https://img.shields.io/badge/docs-pdoc-blue)](https://kiln-ai.github.io/Kiln/kiln_core_docs/index.html)&#x20;

### Installation

To install Kiln, run the following command:

```bash
pip install kiln-ai
```

### Library Docs & Examples

Our [library docs](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html) provide include an API reference for all of the libraries features. Use the sidebar to navigate.

The docs include several quick-start examples to quickly get up and running:

* [Using the Kiln Data Model](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#using-the-kiln-data-model)
  * [Understanding the Kiln Data Model](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#understanding-the-kiln-data-model)
  * [Datamodel Overview](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#datamodel-overview)
  * [Load a Project](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#load-a-project)
  * [Load an Existing Dataset into a Kiln Task Dataset](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#load-an-existing-dataset-into-a-kiln-task-dataset)
  * [Using your Kiln Dataset in a Notebook or Project](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#using-your-kiln-dataset-in-a-notebook-or-project)
  * [Using Kiln Dataset in Pandas](https://kiln-ai.github.io/Kiln/kiln_core_docs/kiln_ai.html#using-kiln-dataset-in-pandas)

### Web/Rest API

[![PyPI - Version](https://camo.githubusercontent.com/19c9f20a780df4b52075029b50e4ec314b83d20e626eb2bee5ab5e7cac8dc937/68747470733a2f2f696d672e736869656c64732e696f2f707970692f762f6b696c6e2d7365727665722e7376673f6c6f676f3d70797069266c6162656c3d50795049266c6f676f436f6c6f723d676f6c64)](https://pypi.org/project/kiln-server/) [![Docs](https://camo.githubusercontent.com/c60086f2069661becba8f0466057804ae55ace5a870d151681539e6ee77c3f55/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f646f63732d4f70656e4150492d626c7565)](https://kiln-ai.github.io/Kiln/kiln_server_openapi_docs/index.html)

We also offer a self-hostable REST API for Kiln, based on [FastAPI](https://fastapi.tiangolo.com).&#x20;

To install the Kiln rest API, run the following command:

```bash
pip install kiln_server
```

The[ rest-API docs](https://kiln-ai.github.io/Kiln/kiln_server_openapi_docs/index.html) explain the endpoints, parameters, response format, and errors.

The REST API supports OpenAPI, so you can generate typed client libraries for almost [any](https://github.com/swagger-api/swagger-codegen) [language](https://openapi-generator.tech/docs/generators).
