---
icon: brain
description: Improve your model's quality with inference time scaling
---

# Reasoning, Thinking & Chain of Thought

{% hint style="info" %}
**Reasoning model support is on our main branch, but not yet in a release**. If you want to use it now, download a daily build from GitHub Actions.
{% endhint %}

### What are reasoning models and chain of thought?

Reasoning models and chain of thought (COT) are methods that give models time to "think" before giving a final answer. Their "thinking" takes the form of discussing the request and possible answers in a stream of generated tokens. These additional tokens allow for more complex reasoning, step-by-step thinking, and have been shown to improve the quality of results. These approaches are also known as "inference time scaling," where models improve from spending more compute power at inference time — as opposed to improving by spending more compute at training time.

Both methods are similar, but they have some differences:

* **Chain of thought** is a method that's been around for a few years, and simply involves asking the model to think before giving an answer. This can be as simple as appending "Think step by step" to your prompt or adding detailed instructions for what the model should "think" about before giving its final answer.
* **Reasoning/thinking models** like Deepseek R1 or OpenAI's O3 are a newer form of inference time compute, where the model itself was trained to develop powerful reasoning skills. These models are trained with reinforcement learning, where the model is rewarded for being correct and penalized when incorrect. This training system uses deep learning to help models develop reasoning skills across a range of domains.

While reasoning models are generally more powerful than a simple chain of thought, it's often worth testing both approaches for your use case. Thinking models strive to reason about everything effectively, but a well-crafted chain of thought prompt from a human expert can often outperform them when developing use-case-specific models/APIs.&#x20;

[Creating your own task-specific thinking model](reasoning-thinking-and-chain-of-thought.md#building-your-own-reasoning-model-distillation) is another powerful option supported by Kiln.

{% hint style="info" %}
While you can call OpenAI's reasoning models (o1, O3) from Kiln, they are treated as normal models. OpenAI hides the reasoning tokens from users, only returning the final answer. To distill a reasoning model for your use case, use an open model like Deepseek R1, which returns the thinking tokens, or use a custom chain-of-thought prompt.
{% endhint %}

### How Kiln handles reasoning models and chain of thought (COT)

Kiln has native support for both these methods. This includes:

* **Reasoning Parsers:** Kiln includes parsers that separate out "thinking" from answers for common thinking models.
* [**Data Model**](kiln-datamodel.md)**:** Our data model stores thinking separately from final answers, allowing you to evaluate or train on them independently.
* [**Custom Message Flow**](reasoning-thinking-and-chain-of-thought.md#custom-message-chat-flow)**:** When using chain-of-thought with models that don't support reasoning we make a chain of calls to the model to formally separate the thinking from the answer.
* [**Structured Data**](structured-data-json.md): Our chat call flow allows for the final answer messages to use structured data tools (json\_schema, json\_object, tool-calls, etc.) without adding "thinking" fields to your data structures.
* [**Prompts**](prompts.md)**:** Prompts are divided into the primary system message and a separate "thinking instruction."
* [**Fine-tuning/Distillation**](reasoning-thinking-and-chain-of-thought.md#building-your-own-reasoning-model-distillation)**:** You can fine-tune models with thinking data and prompts, allowing you to build small, fast, and high-quality thinking models for your use case.

### Using reasoning or COT in Kiln

Using thinking models or COT in Kiln is easy! Simply do one of the following:

* Run a model with any "Chain of thought" prompt selected (including a custom prompt with thinking instructions included).
* Run a reasoning model (e.g. Deepseek R1) with any prompt. If a chain of thought prompt is used, the thinking instructions will be passed along to the model in the system prompt. If a non-COT prompt is used, the reasoning model will still "think", but using it's own reasoning guidance.

Once the run is complete, you'll see both a final answer and reasoning in the model output.

### Building your own reasoning model (distillation)

Kiln can fine-tune a thinking model using your dataset. Often called distillation, these models can learn the reasoning strategies for your use case from examples in your Kiln dataset. By fine-tuning/distilling a model, you can produce a model that's smaller, faster, cheaper and better than the original model.

* See our guide on fine-tuning reasoning models
* See our guide for [general fine-tuning](fine-tuning-guide.md) (non reasoning models)

### Performance & Cost

More inference time compute doesn't necessarily mean slower or more costly requests. Sometimes a smaller model using more inference-time compute can be faster, better and cheaper than a larger model performing the same task.

### Custom message chat flow

Here's the message call flow Kiln uses for each configuration:

#### Normal call-flow (non COT, non-reasoning model)

* \[System Message]: System prompt
* \[User Message]: User inputs
* \[Assistant Message]: Final Answer, optionally structured data

#### Chain of thought call-flow (Non-reasoning model):

* \[System Message]: System prompt
* \[User Message]: User inputs
* \[User Message]: Thinking instructions. User provided if available, defaults to "Think step by step, explaining your reasoning.".
* \[Assistant Message]: COT reasoning tokens
* \[User Message]: Kiln managed message: "Considering the above, return a final result."
* \[Assistant Message]: Final Answer, optionally structured data

This flow is also used on fine-tunes you create with Kiln, if the fine-tune was created with the "Final answer and intermediate reasoning" training strategy.

#### Reasoning model call-flow:

* \[System Message]: System prompt. Optionally appending thinking-instructions if the selected prompt includes them.
* \[User Message]: User inputs
* \[Assistant Message]: Final Answer and reasoning in 1 message, but will be parsed into separate reasoning and answer fields. Will parse structured data if the task has structured output.
