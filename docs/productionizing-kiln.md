---
description: How to take ideas from the lab (Kiln) into your product
icon: industry-windows
---

# Productionizing Kiln

Kiln is a great place to rapidly experiment with many models, providers, fine-tunes, and prompts.&#x20;

Once you've found the ideal way to run your AI workload, you are ready to create (or iterate) on your product. This guide walks through the options for creating prodcuts from Kiln projects.

### Productionizing Kiln Search Tools / RAG

We have multiple options for deploying search tools you build inside of Kiln. See the docs for [deploying search tools / RAG](documents-and-search-rag/#deploying-your-rag).

### Productionizing Kiln Tasks

#### Option 1: \[Recommended] Replicate Kiln Prompts and Requests in the Framework of your Choice&#x20;

Every model request sent from Kiln is logged to `~/.kiln_ai/logs/model_calls.log` .  This includes the messages and any parameters sent to the API (model, temperature, reasoning, etc). It even includes a curl command to replicate the call Kiln made from the command line.

You can use the data in this log to exactly replicate any Kiln request in the language/framework of your choice. You can choose which tech-stack makes sense for your product; anything from simple HTTP requests, to integrating provider libraries (`pip install openai`), to integrating [llama.cpp](https://github.com/ggml-org/llama.cpp) into your app/process.&#x20;

#### Option 2: \[Alpha] Use the Kiln Python Library

The MIT open-source [Kiln python library](../developers/python-library-quickstart.md) powers all of the requests in the Kiln app. You can use it in your app, pointing to the Kiln project of your choice. See the library docs for details.

{% hint style="warning" %}
The python library has not yet reached v1.0 and is rapidly changing. We don't recommend it for production usage at this time. We suggest the approach above instead.&#x20;

However, it might be a good fit for rapid prototyping where your workflows are coupled with Kiln.&#x20;
{% endhint %}

