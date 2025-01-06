---
icon: crystal-ball
description: GPT, Llama, and Qwen - oh my!
---

# Models and AI Providers

Kiln can use essentially any LLM model from a number of providers:

* Run locally with Ollama
* Connect a cloud provider like OpenAI, Groq, OpenRouter, AWS, Fireworks and more. You provide your own API keys and we never have access to your dataset.
* Connect to any OpenAI compatible server, like LiteLLM for vLLM

<figure><img src="../.gitbook/assets/Models (1).png" alt=""><figcaption></figcaption></figure>

## Connecting AI Providers

When you first run Kiln, the app will prompt you to setup one or more AI providers. You need at least one for the core features of Kiln to function.

If you want to add providers after initial setup, open **Settings > AI Providers & Models.**

If you want to remove a provider, edit your `~/.kiln_ai/settings.yaml` and remove the provider's config.

## Understanding and Adding Models

Models come in a range of flavours, from very easy to use, to advanced methods for expert users

* [Included models](models-and-ai-providers.md#included-models-recommended)
* [Custom Ollama models](models-and-ai-providers.md#custom-ollama-models)
* [Custom models from existing providers](models-and-ai-providers.md#custom-models-from-existing-providers)
* [Custom OpenAI compatible servers](models-and-ai-providers.md#custom-openai-compatible-servers)
  * [LiteLLM](models-and-ai-providers.md#litellm) - Anthropic, Huggingface, VertexAI, TogetherAI, and more.

### Included models \[Recommended]

These are models that have been tested to work with Kiln's various features. These are the easiest to use, and generally won't result in errors.

To get access to these models, simply connect any AI provider (in the Settings page). We suggest OpenRouter as it has the widest selection of models. Once connected, you can select the model you want to use in the model dropdown.

Note: some models may only work with unstructured output, or may not support data generation. The dropdown will warn if you try to use a model that doesn't support a feature.

Included models include common models like Claude, GPT-4, Llama, and many more. The complete list is available in the [Kiln Models](https://github.com/Kiln-AI/Kiln/blob/main/libs/core/kiln_ai/adapters/ml_model_list.py) guide.

### Custom Ollama Models

Any Ollama model you have installed on your server will be available to use in Kiln. To add models, simply install them with the Ollama CLI `ollama pull <model_name>`.

Some Ollama models are included/tested, and will automatically appear in the model dropdown. Any untested Ollama models will still appear in the dropdown, but in the "Untested" section.

### Custom Models from Existing Providers

If you want to use a model that is not in the list but is supported by one of our AI providers, you can use a custom model.

To use a custom model, click "Add Model" in the "AI Providers & Models" section of Settings.

These will appear in the "untested" section of the model dropdown.

### Custom OpenAI Compatible Servers

If you have an OpenAI compatible server (LiteLLM, vLLM, etc.), you can use it in Kiln.

To do this, add a "Custom API" in the "AI Providers & Models" section of Settings.

All models supported by this API will appear in the "untested" section of the model dropdown.

Notes:

* The API must support the `/v1/models` endpoint, so Kiln can access the list of models.
* Many Kiln tasks require structured (JSON) output. These can be hard to get working on custom servers, as each server/model pair usually needs some configuration to reliably produce structured output (tools vs json\_mode vs json parsing, schema format, etc).

#### LiteLLM

Kiln works with [LiteLLM](https://github.com/BerriAI/litellm), an open source proxy which exposes an OpenAI compatible API to over 100 model providers. If your preferred provider isn't built in, try LiteLLM! Simply add your LiteLLM URL in the "Custom API" section of Settings.
