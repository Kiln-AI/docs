---
description: GPT, Llama, and Qwen - oh my!
icon: crystal-ball
---

# Models and AI Providers

Kiln can use essentially any LLM model from a number of providers:

* Run locally with Ollama
* Connect a cloud provider like OpenAI, Groq, OpenRouter, AWS, Azure, Gemini API, Anthropic, Fireworks and much more. You provide your own API keys and we never have access to your dataset.
* Connect to any OpenAI compatible server, like LiteLLM or vLLM

<figure><img src="../.gitbook/assets/Models (1).png" alt=""><figcaption></figcaption></figure>

## Connecting AI Providers

When you first run Kiln, the app will prompt you to setup one or more AI providers. You need at least one for the core features of Kiln to function.&#x20;

We currently support the following AI providers:&#x20;

* Ollama
* OpenRouter
* OpenAI
* Groq
* Fireworks.ai
* Together.ai
* AWS Bedrock
* Anthropic
* Gemini AI Studio / Gemini API
* Google Vertex AI
* Azure OpenAI
* HuggingFace
* Any OpenAI compatible API

If you want to add or remove providers after initial setup, open `Settings > AI Providers & Models`.

{% hint style="success" %}
Don't see you provider listed? Most providers offer an OpenAI compatible API that Kiln can connect to. This includes common open source projects like LiteLLM and vLLM. Search their docs, and connect via the "Custom API" option in Kiln.
{% endhint %}

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

| Model Name                    | Providers                                                             | Structured Output   | Reasoning           | Synthetic Data      | API Fine-Tuneable |
| ----------------------------- | --------------------------------------------------------------------- | ------------------- | ------------------- | ------------------- | ----------------- |
| GPT 4o Mini                   | Azure OpenAI, OpenAI, OpenRouter                                      | ✅︎                  |                     | ✅︎                  | ✅︎                |
| GPT 4o                        | Azure OpenAI, OpenAI, OpenRouter                                      | ✅︎                  |                     | ✅︎                  | ✅︎                |
| GPT o3 Mini - Low             | Azure OpenAI, OpenAI                                                  | ✅︎                  |                     | ✅︎                  |                   |
| GPT o3 Mini - Medium          | Azure OpenAI, OpenAI                                                  | ✅︎                  |                     | ✅︎                  |                   |
| GPT o3 Mini - High            | Azure OpenAI, OpenAI                                                  | ✅︎                  |                     | ✅︎                  |                   |
| GPT o1 - Low                  | Azure OpenAI, OpenAI                                                  | ✅︎                  |                     | ✅︎                  |                   |
| GPT o1 - Medium               | Azure OpenAI, OpenAI                                                  | ✅︎                  |                     | ✅︎                  |                   |
| GPT o1 - High                 | Azure OpenAI, OpenAI                                                  | ✅︎                  |                     | ✅︎                  |                   |
| Claude 3.5 Haiku              | Anthropic, Google Vertex AI, OpenRouter                               | ✅︎                  |                     | ✅︎                  |                   |
| Claude 3.5 Sonnet             | Anthropic, Google Vertex AI, OpenRouter                               | ✅︎                  |                     | ✅︎                  |                   |
| Claude 3.7 Sonnet             | Anthropic, OpenRouter                                                 | ✅︎                  |                     | ✅︎                  |                   |
| Claude 3.7 Sonnet Thinking    | Anthropic, OpenRouter                                                 | ✅︎                  | ✅︎                  | ✅︎                  |                   |
| Gemini 1.5 Pro                | Gemini API, Google Vertex AI, OpenRouter                              | ✅︎                  |                     | ✅︎                  |                   |
| Gemini 1.5 Flash              | Gemini API, Google Vertex AI, OpenRouter                              | ✅︎                  |                     | ✅︎                  |                   |
| Gemini 1.5 Flash 8B           | Gemini API, OpenRouter                                                | ✅︎                  |                     |                     |                   |
| Gemini 2.0 Flash              | Gemini API, Google Vertex AI, OpenRouter                              | ✅︎                  |                     | ✅︎                  |                   |
| Nemotron 70B                  | OpenRouter                                                            |                     |                     |                     |                   |
| Llama 3.1 8B                  | Amazon Bedrock, Fireworks AI, Groq, Ollama, OpenRouter, Together AI   | ✅︎ (some providers) |                     | ✅︎ (some providers) | ✅︎                |
| Llama 3.1 70B                 | Amazon Bedrock, Fireworks AI, Ollama, OpenRouter, Together AI         | ✅︎                  |                     | ✅︎ (some providers) | ✅︎                |
| Llama 3.1 405B                | Amazon Bedrock, Fireworks AI, Ollama, OpenRouter, Together AI         | ✅︎                  |                     | ✅︎ (some providers) | ✅︎                |
| Mistral Nemo                  | OpenRouter                                                            | ✅︎                  |                     | ✅︎                  |                   |
| Mistral Large                 | Amazon Bedrock, Ollama, OpenRouter                                    | ✅︎                  |                     | ✅︎                  |                   |
| Llama 3.2 1B                  | Groq, Hugging Face, Ollama, OpenRouter, Together AI                   | ✅︎ (some providers) |                     | ✅︎ (some providers) | ✅︎                |
| Llama 3.2 3B                  | Groq, Hugging Face, Ollama, OpenRouter, Together AI                   | ✅︎ (some providers) |                     |                     | ✅︎                |
| Llama 3.2 11B                 | Fireworks AI, Groq, Hugging Face, Ollama, OpenRouter, Together AI     | ✅︎ (some providers) |                     | ✅︎ (some providers) |                   |
| Llama 3.2 90B                 | Fireworks AI, Groq, Ollama, OpenRouter, Together AI                   | ✅︎ (some providers) |                     | ✅︎ (some providers) |                   |
| Llama 3.3 70B                 | Fireworks AI, Google Vertex AI, Groq, Ollama, OpenRouter, Together AI | ✅︎ (some providers) |                     | ✅︎ (some providers) | ✅︎                |
| Phi 3.5                       | Fireworks AI, Ollama, OpenRouter                                      |                     |                     |                     |                   |
| Phi 4 - 14B                   | Ollama, OpenRouter                                                    | ✅︎                  |                     | ✅︎ (some providers) |                   |
| Phi 4 - 5.6B                  | OpenRouter                                                            |                     |                     |                     |                   |
| Phi 4 Mini - 3.8B             | Ollama                                                                | ✅︎                  |                     | ✅︎                  |                   |
| Gemma 2 2B                    | Ollama                                                                | ✅︎                  |                     |                     |                   |
| Gemma 2 9B                    | Ollama, OpenRouter                                                    | ✅︎ (some providers) |                     |                     |                   |
| Gemma 2 27B                   | Ollama, OpenRouter                                                    | ✅︎                  |                     |                     |                   |
| Gemma 3 1B                    | Ollama, OpenRouter                                                    |                     |                     |                     |                   |
| Gemma 3 4B                    | Ollama, OpenRouter                                                    | ✅︎                  |                     | ✅︎                  |                   |
| Gemma 3 12B                   | Ollama, OpenRouter                                                    | ✅︎                  |                     | ✅︎                  |                   |
| Gemma 3 27B                   | Hugging Face, Ollama, OpenRouter                                      | ✅︎                  |                     | ✅︎                  |                   |
| Mixtral 8x7B                  | Ollama, OpenRouter                                                    | ✅︎                  |                     | ✅︎ (some providers) |                   |
| QwQ 32B (Qwen Reasoning)      | Fireworks AI, Groq, Ollama, OpenRouter, Together AI                   | ✅︎                  | ✅︎                  | ✅︎                  | ✅︎                |
| Qwen 2.5 7B                   | Ollama, OpenRouter                                                    | ✅︎                  |                     | ✅︎                  |                   |
| Qwen 2.5 14B                  | Ollama, Together AI                                                   | ✅︎                  |                     | ✅︎ (some providers) | ✅︎                |
| Qwen 2.5 72B                  | Fireworks AI, Ollama, OpenRouter, Together AI                         | ✅︎ (some providers) |                     | ✅︎ (some providers) | ✅︎                |
| Mistral Small 3               | Ollama, OpenRouter                                                    | ✅︎                  |                     | ✅︎                  |                   |
| DeepSeek V3                   | Fireworks AI, OpenRouter, Together AI                                 | ✅︎                  |                     | ✅︎ (some providers) | ✅︎                |
| DeepSeek R1                   | Fireworks AI, Ollama, OpenRouter, Together AI                         | ✅︎                  | ✅︎                  | ✅︎                  | ✅︎                |
| DeepSeek R1 Distill Qwen 32B  | Ollama, OpenRouter, Together AI                                       | ✅︎                  | ✅︎                  | ✅︎                  |                   |
| DeepSeek R1 Distill Llama 70B | Ollama, OpenRouter, Together AI                                       | ✅︎                  | ✅︎ (some providers) | ✅︎ (some providers) |                   |
| DeepSeek R1 Distill Qwen 14B  | Ollama, OpenRouter, Together AI                                       | ✅︎                  | ✅︎ (some providers) | ✅︎ (some providers) |                   |
| DeepSeek R1 Distill Llama 8B  | Ollama, OpenRouter                                                    |                     | ✅︎                  |                     |                   |
| DeepSeek R1 Distill Qwen 7B   | Ollama                                                                |                     | ✅︎                  |                     |                   |
| DeepSeek R1 Distill Qwen 1.5B | Ollama, OpenRouter, Together AI                                       |                     | ✅︎ (some providers) |                     |                   |
| Dolphin 2.9 8x22B             | Ollama, OpenRouter                                                    | ✅︎                  |                     | ✅︎                  |                   |
| Grok 2                        | OpenRouter                                                            | ✅︎                  |                     | ✅︎                  |                   |

{% hint style="info" %}
For "`✅︎ (some providers)` ", see [the code on Github](https://github.com/Kiln-AI/Kiln/blob/main/libs/core/kiln_ai/adapters/ml_model_list.py) for details of which providers are supported.
{% endhint %}

### Additional Fine-Tuneable Models

The following models can be fine tuned using a Fireworks.ai API key:

<details>

<summary> Model List — 60+ models on Fireworks.ai</summary>

New models will automatically appear in Kiln as they are released by Fireworks. Here's a snapshot:

* Code Llama 34B (code-llama-34b)

- Code Llama 34B Instruct (code-llama-34b-instruct)
- DeepSeek Coder V2 Instruct (deepseek-coder-v2-instruct)
- DeepSeek Coder V2 Lite Base (deepseek-coder-v2-lite-base)
- Deepseek Coder V2 Lite (deepseek-coder-v2-lite-instruct)
- DeepSeek R1 (Fast) (deepseek-r1)
- DeepSeek R1 (Basic) (deepseek-r1-basic)
- deepseek-r1-distill-llama-70b
- Deepseek R1 Distill Llama 8B (deepseek-r1-distill-llama-8b)
- Deepseek R1 Distill Qwen 14B (deepseek-r1-distill-qwen-14b)
- Deepseek R1 Distill Qwen 1.5B (deepseek-r1-distill-qwen-1p5b)
- deepseek-r1-distill-qwen-32b
- Deepseek R1 Distill Qwen 7B (deepseek-r1-distill-qwen-7b)
- DeepSeek V2 Lite Chat (deepseek-v2-lite-chat)
- DeepSeek V2.5 (deepseek-v2p5)
- DeepSeek V3 (deepseek-v3)
- Deepseek V3 03-24 (deepseek-v3-0324)
- Dolphin 2.9.2 Qwen2 72B (dolphin-2-9-2-qwen2-72b)
- FireFunction V2 (firefunction-v2)
- Llama Guard v2 8B (llama-guard-2-8b)
- Llama Guard v3 1B (llama-guard-3-1b)
- llama-guard-3-8b
- Llama 2 13B Chat (llama-v2-13b-chat)
- Llama 2 70B Chat (llama-v2-70b-chat)
- Llama 2 7B Chat (llama-v2-7b-chat)
- Llama 3 70B Instruct (llama-v3-70b-instruct)
- Llama 3 70B Instruct (HF version) (llama-v3-70b-instruct-hf)
- Llama 3 8B Instruct (llama-v3-8b-instruct)
- Llama 3 8B Instruct (HF version) (llama-v3-8b-instruct-hf)
- Llama 3.1 405B Instruct (llama-v3p1-405b-instruct)
- Llama 3.1 70B Instruct (llama-v3p1-70b-instruct)
- Llama 3.1 8B Instruct (llama-v3p1-8b-instruct)
- Llama 3.1 Nemotron 70B (llama-v3p1-nemotron-70b-instruct)
- Llama 3.2 1B Instruct (llama-v3p2-1b-instruct)
- Llama 3.2 3B Instruct (llama-v3p2-3b-instruct)
- Llama 3.3 70B Instruct (llama-v3p3-70b-instruct)
- Qwen1.5 72B Chat (qwen1p5-72b-chat)
- Qwen2 72B Instruct (qwen2-72b-instruct)
- Qwen2 7B Instruct (qwen2-7b-instruct)
- Qwen2.5 0.5B Instruct (qwen2p5-0p5b-instruct)
- Qwen2.5 14B (qwen2p5-14b)
- Qwen2.5 14B Instruct (qwen2p5-14b-instruct)
- Qwen2.5 32B (qwen2p5-32b)
- Qwen2.5 32B Instruct (qwen2p5-32b-instruct)
- Qwen2.5 72B (qwen2p5-72b)
- Qwen2.5 72B Instruct (qwen2p5-72b-instruct)
- Qwen2.5 7B (qwen2p5-7b)
- Qwen2.5 7B Instruct (qwen2p5-7b-instruct)
- Qwen2.5-Coder-0.5B (qwen2p5-coder-0p5b)
- Qwen2.5-Coder-0.5B-Instruct (qwen2p5-coder-0p5b-instruct)
- Qwen2.5-Coder-14B (qwen2p5-coder-14b)
- Qwen2.5-Coder-14B-Instruct (qwen2p5-coder-14b-instruct)
- Qwen2.5 Coder 1.5B (qwen2p5-coder-1p5b)
- Qwen2.5 Coder 1.5B Instruct (qwen2p5-coder-1p5b-instruct)
- Qwen2.5-Coder-32B (qwen2p5-coder-32b)
- Qwen2.5-Coder-32B-Instruct (qwen2p5-coder-32b-instruct)
- Qwen2.5-Coder-32B-Instruct (qwen2p5-coder-32b-instruct-128k)
- Qwen2.5-Coder-32B-Instruct (qwen2p5-coder-32b-instruct-32k-rope)
- Qwen2.5-Coder-32B-Instruct (qwen2p5-coder-32b-instruct-64k)
- Qwen2.5-Coder-3B (qwen2p5-coder-3b)
- Qwen2.5-Coder-3B-Instruct (qwen2p5-coder-3b-instruct)
- Qwen2.5-Coder-7B (qwen2p5-coder-7b)
- Qwen2.5-Coder-7B-Instruct (qwen2p5-coder-7b-instruct)
- qwen2p5-math-72b-instruct
- Qwen2.5 14B Instruct (qwen-v2p5-14b-instruct)
- Qwen2.5 7B (qwen-v2p5-7b)
- QwQ-32B (qwq-32b)
- Yi 34B Chat (yi-34b-chat)

</details>

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

#### Google Vertex AI

When using Vertex, many models need to be manually enabled through the console before using them (primarily Anthropic models). If you see errors when trying to run a model, open the vertex AI console for your project, go to the model garden, and enable that model.

Similarly, if you see quota errors you may need to manage/request quota from the Vertex console. Quota is specific to the model + region. Ensure you request quota in the region you specified when you connected Vertex AI to Kiln.

#### Hugging Face

Hugging face has thousands of models. We've included a few of these common models in the Kiln built-in model list, but you can add any hugging face model via the [custom model](models-and-ai-providers.md#custom-models-from-existing-providers) option.

Hugging face errors are not always descriptive - if you get 400 errors, it's likely the model you've selected requires a Hugging Face Pro subscription. Try the same model in their UI for a more helpful error messages.

### Custom OpenAI Compatible Servers

If you have an OpenAI compatible server (LiteLLM, vLLM, etc.), you can use it in Kiln.

To do this, add a "Custom API" in the "AI Providers & Models" section of Settings.

All models supported by this API will appear in the "untested" section of the model dropdown.

Notes:

* The API must support the `/v1/models` endpoint, so Kiln can access the list of models.
* Many Kiln tasks produce structured (JSON) output. These can be hard to get working on custom servers, as each server/model pair usually needs some configuration to reliably produce structured output (tools vs json\_mode vs json parsing vs json\_schema, etc).
