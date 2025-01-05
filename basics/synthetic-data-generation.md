---
description: Generate synthetic data for fine-tuning or evaluation
icon: robot
---

# Synthetic Data Generation

Kiln offers a powerful interactive synthetic data generation tool.

### Video Walkthrough

{% embed url="https://vimeo.com/1044098339?_loop=1&autoplay=1" %}
Synthetic Data Generation Walkthrough
{% endembed %}

### Use Cases

Synthetic data is helpful for many reasons:

* To generate a dataset for fine-tuning
* To generate examples to be used for few-shot or multi-shot prompting
* To test your task in a controlled environment
* To generate eval datasets
* To generate targeted data to reproduce a bug/issue, which can be used for training a fix, evaluating a fix, and backtesting

### How it works

#### Zero-Shot Data Generation

Once you've created a Kiln task defining your goals, data generation will use the task instructions and requirements to generate synthetic data without any additional configuration.

#### Topic-Tree Data Generation

To generate a breadth of examples, Kiln can generate a topic tree and generate examples for each node. This includes nested topics, which allows you to generate a lot of broad data very quickly.

You can use automatic topic generation, or manually add topics to your topic tree.

<figure><img src="../.gitbook/assets/Screenshot 2025-01-05 at 12.06.43 PM.png" alt="" width="151"><figcaption><p>Example Topic Tree</p></figcaption></figure>

#### Human Guidance

Sometimes you may want to guide the generation process to ensure that the data generated matches your needs. You can add human guidance to your data generation task at any time.

Adding a short guidance prompt can quickly improve the quality of the generated data. Some examples:

* Generate content for global topics, not only US-centric
* Generate examples in Spanish
* The model is having trouble classifying sediment of sarcastic messages. Generate sarcastic messages.

#### Interactive Curation UX

Kiln synthetic data generation is designed to be used in our interactive UI.

As you work, delete topics or examples that don't match your goals, and regenerate the data until you're happy with the results. Adding human guidance can help with this process

#### Structured Data Generation (JSON, tool calling)

If your task requires structured input and/or output, your synthetic data generation will automatically follow the schemas you defined. All values are validated against the schemas you define, and nothing will be saved into your dataset if they don't comply.

You can define the schema in our task definition UI for a visual schema builder. Alternatively you can directly set a JSON Schema in the task via our python library or a text editor.

Under the hood we attempt to use tool calling when the model supports it, but will fallback to JSON parsing if not.

#### Generation Options

Kiln offers a number of options when generating a dataset:

* Model: which model to use for generation. We support a wide range of models (OpenAI, Anthropic, Llama, Google, Mistral, etc.) and a range of hosts including Ollama. Note: each model you see in the UI has been tested with the data generation tasks.
* Prompt: after rating a few examples, more powerful prompt options will open up for data generation. These include few-shot, multi-shot, chain-of-thought prompting, and more.

### Iteration

You can use synthetic data generation as many times as you'd like. Data will be appended to your dataset each time you do.

#### Resolving bugs with synthetic data

Synthetic data can help resolve issues in your LLM systems.

As an example, let's assume your model is often generating text using the wrong tone. For this example: too formal when the use case calls for more causal tone.

Synthetic data can help resolve this issue, and ensure it doesn't regress.

1. Open the synthetic dataset tab.
2. Select a high quality model - even if it's not one that's fast or cheap enough for production.
3. Start generating data which shows the issue, but use the human guidance feature and better model to ensure the outputs are high quality.
4. Manually delete examples that don't have the correct style.
5. Once the synthetic data tool is reliably generating correct data (with this model and guidance pair), scale up your generation to hundreds of samples.
6. Save your new synthetic dataset

The new examples will be saved to your dataset, and will include a unique tag to idenity them (e.g. `synthetic_session_12345`). With this new dataset in hand you can resolve the issue:

1. Simple: Fix the root prompt, and use this new dataset subset in your evaluations to ensure it works (and doesn't regress in the future)
2. Advanced: [Fine-tune a model](https://github.com/Kiln-AI/Kiln/blob/main/guides/Fine%20Tuning%20LLM%20Models%20Guide.md) with this data, so smaller and faster models learn to emulate your desired styles. Withhold a test set to ensure it worked.

### Reviewing and Rating Data

Kiln includes a rating interface for rating dataset entries. This can be used to score the quality of the generated data, or to score the quality of a model.

Only highly rated data will be used for features like multi-shot prompting.

[![rating UI](https://private-user-images.githubusercontent.com/848343/388585660-6872d5ad-18ad-46f3-9091-2e26741cb852.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MzYwOTYyNTcsIm5iZiI6MTczNjA5NTk1NywicGF0aCI6Ii84NDgzNDMvMzg4NTg1NjYwLTY4NzJkNWFkLTE4YWQtNDZmMy05MDkxLTJlMjY3NDFjYjg1Mi5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwMTA1JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDEwNVQxNjUyMzdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT02MTYyZGM0MDc2OTZmNjJkMTQyNWIzM2U1ZTBlMmQxN2IwOTRlMmQ5MTZhNGM1NWNjODQ2ZWZiODU2N2YzMTUxJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.7mDDjOec2DGMIOO7_G4j74xA7gz9LZkuP7VK8hZfD5g)](https://private-user-images.githubusercontent.com/848343/388585660-6872d5ad-18ad-46f3-9091-2e26741cb852.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3MzYwOTYyNTcsIm5iZiI6MTczNjA5NTk1NywicGF0aCI6Ii84NDgzNDMvMzg4NTg1NjYwLTY4NzJkNWFkLTE4YWQtNDZmMy05MDkxLTJlMjY3NDFjYjg1Mi5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwMTA1JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDEwNVQxNjUyMzdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT02MTYyZGM0MDc2OTZmNjJkMTQyNWIzM2U1ZTBlMmQxN2IwOTRlMmQ5MTZhNGM1NWNjODQ2ZWZiODU2N2YzMTUxJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.7mDDjOec2DGMIOO7_G4j74xA7gz9LZkuP7VK8hZfD5g)



