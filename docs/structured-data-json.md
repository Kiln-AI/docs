---
icon: brackets-curly
---

# Structured Data / JSON

<figure><img src="../.gitbook/assets/json.png" alt=""><figcaption></figcaption></figure>

Structured data is a first-class citizen in Kiln.

* JSON input/output is supported for any task.
* You can define input/output schemas for each task you create.
* We automatically detect when a AI model doesn't produce output in the correct format.
* No data gets into the dataset without first passing validation, which keeps the dataset clean.
* Our [included models](models-and-ai-providers.md#included-models-recommended) are tested for JSON compatibility, and models that don't perform well with structured data will show a warning.

### Creating a Schema

Our easy-to-use visual schema builder lets you create and use structured schemas. Define your input and output schemas in our UI when creating a task.

{% hint style="info" %}
You can't edit the input/output schemas after creating a task, as that would invalidate all prior data. Create a new task with your updated schema instead.
{% endhint %}

<figure><img src="../.gitbook/assets/Screenshot 2025-01-08 at 12.38.31 PM.png" alt="" width="375"><figcaption><p>Kiln's Visual Schema Editor</p></figcaption></figure>

### Raw JSON Schema

For technical users, we support any valid [JSON-schema](https://json-schema.org) for inputs and output schemas.

JSON schema is more powerful than the visual editor, allowing arrays, nested objects, enums, constraints and more. You can use raw JSON schemas from the Python library, or from the UI (by picking an array type).

{% hint style="warning" %}
We only recommend JSON schema for technical users/developers. It's much more complex than the visual editor.

Errors in the schema will likely result in bugs when running your task.
{% endhint %}
