---
description: Two powerful tools to measure and optimize your AI systems
icon: list-check
---

# Evals & Specs

#### Evals vs Specs

Kiln has two powerful features to ensure your AI systems perform as expected, drive optimizations and don't regress in quality:

* [**Evals**](evaluations.md): Build industry standard evals with methods like LLM-as-Judge and G-Eval.&#x20;
* **Specs \[Docs Coming Soon]:** A more comprehensive system for evaluating AI systems. It includes evals and adds synthetic evaluation data generation, edge case detection, judge prompt generation, and more.

<table><thead><tr><th valign="middle"></th><th valign="middle">Kiln Evals</th><th valign="middle">Kiln Specs</th><th data-hidden></th></tr></thead><tbody><tr><td valign="middle"><p><strong>LLM-as-Judge</strong></p><p><em>including G-Eval</em></p></td><td valign="middle">✅</td><td valign="middle">✅</td><td></td></tr><tr><td valign="middle"><strong>Judge Prompt Creation</strong></td><td valign="middle">Manual</td><td valign="middle"><strong>Automatic</strong></td><td></td></tr><tr><td valign="middle"><strong>Edge Case Discovery</strong></td><td valign="middle">Manual</td><td valign="middle"><strong>Automatic</strong></td><td></td></tr><tr><td valign="middle"><strong>Eval Data Creation</strong></td><td valign="middle"><p>Manual</p><p><em>With synthetic tooling</em></p></td><td valign="middle"><strong>Automatic</strong></td><td></td></tr><tr><td valign="middle"><strong>Eval Accuracy</strong></td><td valign="middle">Variable</td><td valign="middle"><p><strong>High</strong></p><p><em>Human in the loop validation and refinement</em></p></td><td></td></tr><tr><td valign="middle"><strong>Approx. Effort</strong></td><td valign="middle">30 mins+</td><td valign="middle"><strong>5-10mins</strong></td><td></td></tr><tr><td valign="middle"><strong>Needed Expertise</strong></td><td valign="middle">Data Science Basics<br><em>Understand Golden sets, data labeling</em></td><td valign="middle"><strong>No experience necessary</strong><br><em>Fully Guided UI</em></td><td></td></tr><tr><td valign="middle"><strong>Kiln Account</strong></td><td valign="middle">Optional</td><td valign="middle">Required</td><td></td></tr></tbody></table>

#### Guides

* [Evals 101](evaluations.md): build your first eval start to finish&#x20;
* [Evaluate RAG Accuracy](evaluate-rag-accuracy-q-and-a-evals.md): Kiln can generate custom Q\&A evals which test your RAG with knowledge from your documents
* [Evaluate Tool Use](evaluate-appropriate-tool-use.md): ensure your agents are using the right tools, at the right time, with the right parameters with tool use evals

