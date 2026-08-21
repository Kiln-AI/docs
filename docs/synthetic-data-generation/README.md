---
description: Generate synthetic data for fine-tuning or evaluation
icon: robot
---

# Synthetic Data Generation

Anyone can create thousands of synthetic data samples in just a few minutes using our interactive UI.

<figure><img src="../../.gitbook/assets/synth_data-2.png" alt=""><figcaption></figcaption></figure>

## Use Cases

Synthetic data is helpful for many reasons:

* **Evals:** Generate data for custom evals of your task performance. When your eval is scored by a [programmatic check](../evals-and-specs/judge-types.md), data generation reads the check's definition and creates inputs designed to expose its failures.
* **Fine-tuning:** Generate fine-tuning datasets
* **Built-in Quality Templates:** Use our built-in data-gen templates like 'Jailbreak' or 'Bias' to check your system for common issues (curated evals)
* **Addressing Bugs / Issues:** generate targeted data to reproduce a bug/issue, which can be used for training a fix, evaluating a fix, and backtesting
* **Prompting:** Generate examples to be used for few-shot or multi-shot prompting

## Get Started

There are 2 portions of synthetic data in Kiln:&#x20;

* [**Synthetic Data Guide**](synthetic-data-guides.md) **(optional):** Kiln learns what great data looks like, to generate even better data for your task.
* [**Generating Synthetic Data**](generating-synthetic-data.md): build synthetic datasets for evals or fine-tuning&#x20;

