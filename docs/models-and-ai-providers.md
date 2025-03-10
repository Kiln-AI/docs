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

When you first run Kiln, the app will prompt you to setup one or more AI providers. You need at least one for the core features of Kiln to function.&#x20;

We currently support the following AI providers: Ollama, OpenRouter, OpenAI, Groq, Fireworks.ai, AWS Bedrock, or any OpenAI compatible endpoing (like LiteLLM, Anthropic, HuggingFace and more).

If you want to add or remove providers after initial setup, open `Settings > AI Providers & Models`.

## Understanding and Adding Models

Models come in several flavours, from very easy to use, to advanced methods for expert users:

* [Included Models - Recommended](models-and-ai-providers.md#included-models-recommended)
* [Custom Ollama models](models-and-ai-providers.md#custom-ollama-models)
* [Custom models from existing providers](models-and-ai-providers.md#custom-models-from-existing-providers)
* Provider Specific Guidance
  * [Azure OpenAI API](models-and-ai-providers.md#azure-openai-api)
  * [Azure AI Foundry / Azure AI Studio](models-and-ai-providers.md#azure-ai-foundry-formerly-azure-ai-studio-microsoft-ai-for-enterprise-360-elite)
* [Custom OpenAI compatible servers](models-and-ai-providers.md#custom-openai-compatible-servers)
  * [LiteLLM](models-and-ai-providers.md#litellm) - Anthropic, Huggingface, VertexAI, TogetherAI, and more.

### Included Models - Recommended

These are models that have been tested to work with Kiln's various features. These are the easiest to use, and generally won't result in errors.

To use these models simply connect any AI provider from the Settings page. Once connected, you can select these model from the model dropdown on the Run screen. The dropdown will warn if you attempt to use a model that doesn't support a feature (like structured output or synthetic data generation).

You can request we add models [here](https://github.com/Kiln-AI/Kiln/issues/29).

| Model Name                    | Providers                                              | Structured Output   | Reasoning | Synthetic Data      | API Fine-Tuneable |
| ----------------------------- | ------------------------------------------------------ | ------------------- | --------- | ------------------- | ----------------- |
| GPT 4o Mini                   | OpenAI, OpenRouter                                     | ✅︎                  |           | ✅︎                  | ✅︎                |
| GPT 4o                        | OpenAI, OpenRouter                                     | ✅︎                  |           | ✅︎                  | ✅︎                |
| Claude 3.5 Haiku              | OpenRouter                                             | ✅︎                  |           | ✅︎                  |                   |
| Claude 3.5 Sonnet             | OpenRouter                                             | ✅︎                  |           | ✅︎                  |                   |
| Claude 3.7 Sonnet             | OpenRouter                                             | ✅︎                  |           | ✅︎                  |                   |
| Claude 3.7 Sonnet Thinking    | OpenRouter                                             | ✅︎                  | ✅︎        | ✅︎                  |                   |
| Gemini 1.5 Pro                | OpenRouter                                             | ✅︎                  |           | ✅︎                  |                   |
| Gemini 1.5 Flash              | OpenRouter                                             | ✅︎                  |           | ✅︎                  |                   |
| Gemini 1.5 Flash 8B           | OpenRouter                                             | ✅︎                  |           |                     |                   |
| Gemini 2.0 Flash              | OpenRouter                                             | ✅︎                  |           | ✅︎                  |                   |
| Nemotron 70B                  | OpenRouter                                             |                     |           |                     |                   |
| Llama 3.1 8B                  | Amazon Bedrock, Fireworks AI, Groq, Ollama, OpenRouter | ✅︎ (some providers) |           | ✅︎ (some providers) | ✅︎                |
| Llama 3.1 70B                 | Amazon Bedrock, Fireworks AI, Ollama, OpenRouter       | ✅︎                  |           | ✅︎ (some providers) | ✅︎                |
| Llama 3.1 405B                | Amazon Bedrock, Fireworks AI, Ollama, OpenRouter       | ✅︎                  |           | ✅︎ (some providers) |                   |
| Mistral Nemo                  | OpenRouter                                             | ✅︎                  |           | ✅︎                  |                   |
| Mistral Large                 | Amazon Bedrock, Ollama, OpenRouter                     | ✅︎                  |           | ✅︎                  |                   |
| Llama 3.2 1B                  | Groq, Ollama, OpenRouter                               | ✅︎ (some providers) |           |                     |                   |
| Llama 3.2 3B                  | Fireworks AI, Groq, Ollama, OpenRouter                 | ✅︎ (some providers) |           | ✅︎ (some providers) | ✅︎                |
| Llama 3.2 11B                 | Fireworks AI, Groq, Ollama, OpenRouter                 | ✅︎                  |           | ✅︎ (some providers) |                   |
| Llama 3.2 90B                 | Fireworks AI, Groq, Ollama, OpenRouter                 | ✅︎                  |           | ✅︎ (some providers) |                   |
| Llama 3.3 70B                 | Fireworks AI, Groq, Ollama, OpenRouter                 | ✅︎ (some providers) |           | ✅︎ (some providers) |                   |
| Phi 3.5                       | Fireworks AI, Ollama, OpenRouter                       |                     |           | ✅︎ (some providers) |                   |
| Phi 4                         | Ollama, OpenRouter                                     | ✅︎                  |           | ✅︎ (some providers) |                   |
| Gemma 2 2B                    | Ollama                                                 | ✅︎                  |           |                     |                   |
| Gemma 2 9B                    | Ollama, OpenRouter                                     | ✅︎                  |           |                     |                   |
| Gemma 2 27B                   | Ollama, OpenRouter                                     | ✅︎                  |           |                     |                   |
| Mixtral 8x7B                  | Ollama, OpenRouter                                     | ✅︎                  |           | ✅︎ (some providers) |                   |
| Qwen 2.5 7B                   | Ollama, OpenRouter                                     | ✅︎                  |           | ✅︎                  |                   |
| Qwen 2.5 72B                  | Fireworks AI, Ollama, OpenRouter                       | ✅︎ (some providers) |           | ✅︎ (some providers) |                   |
| Mistral Small 3               | Ollama, OpenRouter                                     | ✅︎                  |           | ✅︎                  |                   |
| DeepSeek V3                   | Fireworks AI, OpenRouter                               | ✅︎                  |           | ✅︎ (some providers) |                   |
| DeepSeek R1                   | Fireworks AI, Ollama, OpenRouter                       | ✅︎                  | ✅︎        | ✅︎                  |                   |
| DeepSeek R1 Distill Qwen 32B  | Ollama, OpenRouter                                     | ✅︎                  | ✅︎        | ✅︎                  |                   |
| DeepSeek R1 Distill Llama 70B | Ollama, OpenRouter                                     | ✅︎                  | ✅︎        | ✅︎ (some providers) |                   |
| DeepSeek R1 Distill Qwen 14B  | Ollama, OpenRouter                                     | ✅︎                  | ✅︎        |                     |                   |
| DeepSeek R1 Distill Llama 8B  | Ollama, OpenRouter                                     | ✅︎                  | ✅︎        |                     |                   |
| DeepSeek R1 Distill Qwen 7B   | Ollama                                                 | ✅︎                  | ✅︎        |                     |                   |
| DeepSeek R1 Distill Qwen 1.5B | Ollama, OpenRouter                                     | ✅︎ (some providers) | ✅︎        |                     |                   |
| Dolphin 2.9 8x22B             | Ollama, OpenRouter                                     | ✅︎                  |           | ✅︎                  |                   |
| Grok 2                        | OpenRouter                                             | ✅︎                  |           | ✅︎                  |                   |

{% hint style="info" %}
For "`✅︎ (some providers)` ", see [the code on Github](https://github.com/Kiln-AI/Kiln/blob/main/libs/core/kiln_ai/adapters/ml_model_list.py) for details.
{% endhint %}

### Custom Ollama Models

Any Ollama model you have installed on your server will be available to use in Kiln. To add models, simply install them with the Ollama CLI `ollama pull <model_name>`.

Some Ollama models are included/tested, and will automatically appear in the model dropdown. Any untested Ollama models will still appear in the dropdown, but in the "Untested" section.

### Custom Models from Existing Providers

If you want to use a model that is not in the list but is supported by one of our AI providers, you can use a custom model.

To use a custom model, click "Add Model" in the "AI Providers & Models" section of Settings.

These will appear in the "untested" section of the model dropdown.

### Provider Specific Guidance

#### Azure OpenAI API

When using Azure OpenAI API, you need to deploy each model you want to use, manually through the Azure console. If you have not, you'll get deployment errors when trying to call a model.

* **Suggested - Deploy with Default Names**: If you deploy with the default names, for example "gpt-4o"/"gpt-4o-mini", you can simply use the models using the dropdown in Kiln.
* **Deployments with Custom Names**: If you have a non-standard depolyment name, you'll have to add each model as a [custom model](models-and-ai-providers.md#custom-models-from-existing-providers), using the deployment name as the model name.

#### Azure AI Foundry (formerly Azure AI Studio, Microsoft AI for Enterprise 360 Elite)

When using Azure AI Foundry, you need to deploy each model you want to use manually through the Azure console. If you have not, you'll get deployment errors when trying to call a model.

After deploying a model, you must add it to Kiln as a a [custom model](models-and-ai-providers.md#custom-models-from-existing-providers), using the deployment name as the model name.

### Custom OpenAI Compatible Servers

If you have an OpenAI compatible server (LiteLLM, vLLM, etc.), you can use it in Kiln.

To do this, add a "Custom API" in the "AI Providers & Models" section of Settings.

All models supported by this API will appear in the "untested" section of the model dropdown.

Notes:

* The API must support the `/v1/models` endpoint, so Kiln can access the list of models.
* Many Kiln tasks require structured (JSON) output. These can be hard to get working on custom servers, as each server/model pair usually needs some configuration to reliably produce structured output (tools vs json\_mode vs json parsing, schema format, etc).

#### LiteLLM

Kiln works with [LiteLLM](https://github.com/BerriAI/litellm), an open source proxy which exposes an OpenAI compatible API to over 100 model providers. If your preferred provider isn't built in, try LiteLLM! Simply add your LiteLLM URL in the "Custom API" section of Settings.
