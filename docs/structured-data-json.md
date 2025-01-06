---
icon: table-tree
---

# Structured Data / JSON

Kiln treats structured data, in the form of JSON input/output, as a first class citizen.&#x20;

* You can define input/output schemas for your tasks.
* We automatically detect when a AI model doesn't produce output in the correct format.
* No data gets into the dataset without first passing validation, which keeps the dataset clean.

### Creating a Schema

Our easy-to-use visual schema builder lets you create and use structured schemas. Define your input and output schemas in our UI when creating a task.

{% hint style="info" %}
You can't edit the input/output schemas after creating a task, as that would invalidate all prior data. Create a new task with your updated schema instead.
{% endhint %}

### Raw JSON Schema

For technical users, we support any valid [JSON-schema](https://json-schema.org) for inputs and output schemas.

JSON schema is more powerful than the visual editor, allowing arrays, nested objects, enums, constraints and more. You can use raw JSON schemas from the python library, or from the UI (by picking the array type).

{% hint style="warning" %}
We only recommend JSON schema for technical users/developers. It's much more complex than the visual editor.

Errors in the schema will likely result in bugs when running your task.
{% endhint %}
