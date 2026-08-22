---
title: "Synthetic Data Guides"
description: "Improve your synthetic data generation"
---
A Data Guide is a per-task prompt that tells Kiln what realistic **inputs** to your task look like: their structure, style, terminology, and value ranges. Without one, the data generation model has to guess what your domain looks like from the system prompt alone. With one, generated topics and inputs are shaped to match your actual data.

<figure>

![](../../../../assets/guide-2.png)

</figure>

### When to Use Data Guides

Most tasks benefit from a Data Guide, especially when:

* Your inputs have a specific structure (forms, JSON, transcripts, tickets, code) the model would otherwise have to invent
* Your domain uses terminology, value ranges or constraints a generic model wouldn't know
* Default synthetic data doesn't look like production data
* You already have real examples (documents, past runs, or a spreadsheet of inputs) and want generation grounded in them

#### Setting Up A Data Guide

The first time you open Synthetic Data Generation for a task, Kiln offers to set up a Data Guide. Click **Set Up Data Guide** and Kiln will ask how you'd like to build it: **Manually**, or with **Kiln Pro**.

<table><thead><tr><th valign="middle"></th><th valign="middle">Manual</th><th valign="middle">Kiln Pro</th></tr></thead><tbody><tr><td valign="middle"><strong>AI Guided Authoring</strong></td><td valign="middle">Manual</td><td valign="middle">Automatic</td></tr><tr><td valign="middle"><strong>Style &#x26; Constraints Discovery</strong></td><td valign="middle">Manual</td><td valign="middle">Automatic</td></tr><tr><td valign="middle"><strong>Learn From Documents</strong></td><td valign="middle">—</td><td valign="middle">✅</td></tr><tr><td valign="middle"><strong>Approx. Effort</strong></td><td valign="middle">~15 mins</td><td valign="middle">~5 mins</td></tr><tr><td valign="middle"><strong>Kiln Account</strong></td><td valign="middle">Optional</td><td valign="middle">Required</td></tr></tbody></table>

Both paths end in the same place: a saved guide you've reviewed and refined. The difference is how the guide gets written.

#### Kiln Pro Data Guide Generation

With Kiln Pro, you provide Kiln a set of real example inputs and it analyzes them into a complete data guide for you. It's the fastest path, and the only one that can learn directly from documents.

:::tip
Kiln Pro Data Guides learns from many examples to generate the best possible synthetic data. It learns what's consistent between documents, what varies, relationships, formatting, style and more. It's the best way to create high quality syntehtic data.
:::

1. &#x20;**Connect Kiln Pro** (if you haven't already).
2. **Add example inputs.** Click **Add Inputs** and pick a source: 1) upload documents from your computer or reuse them from your [Document Library](/docs/documents-and-search-rag/), 2) pull inputs from real past runs in your [dataset](/docs/organizing-datasets/), 3) bulk-import from a CSV (plaintext tasks only), or 4) write one by hand (structured tasks only). You can mix sources and add more later.

:::note
Real data works best. A Data Guide is only as realistic as the examples it's built from, so prefer real inputs over synthetic ones.
:::

#### Manual Data Guide Generation

Manual guides need no Kiln account. You start with a few examples of existing data, then refine the guide after seeing how it performs.

1. **Add example inputs:** provide at least one real input, either typed in or picked from your existing task runs. Your examples are treated as reference data for future data generation.
2. **Generate a preview:** Kiln produces a set of synthetic inputs from your guide so far, and you refine from there.

#### Review and Refine

Both Pro and Manual flows include a refinement phase. Kiln will generate synthetic examples from your guide, which you can review and give feedback on. If you rate any **Needs Work**, Kiln will work with you on refining and improving your data guide. Once all the data is consistently being rated **Realistic** your data guide is complete and ready to be saved.

### Using A Saved Data Guide

Once saved, Kiln applies your guide automatically when [generating inputs for your task](/docs/synthetic-data-generation/generating-synthetic-data/). A **Use Data Guide** toggle lets you turn it off for individual runs.

If you're also using synthetic data guidance (like from an eval), that guidance takes priority over the Data Guide where the two conflict.

To view, edit, or delete a saved guide, use the **Data Guide** button on the Synthetic Data Generation page.&#x20;
