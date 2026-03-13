---
description: Reusable instructions for your agents
icon: puzzle-piece
---

# Skills

Skills are reusable instructions that your agents can load on-demand. Unlike prompts which are always included in your agent's context, skills are only retrieved when the agent decides they're needed. This makes skills perfect for specialized knowledge, detailed procedures, or domain expertise that you don't want cluttering every single run.

<figure><img src="../.gitbook/assets/skills-hero.png" alt="" width="375"><figcaption><p>Skills provide specialized instructions your agents load only when needed</p></figcaption></figure>

* [Creating Skills](skills.md#creating-skills)
* [Using Skills](skills.md#using-skills)
* [References](skills.md#references)
* [Skills vs Tools vs Subtasks](skills.md#skills-vs-tools-vs-subtasks)

## Creating Skills

Skills are created at the project level, and can be used by any task within that project.

To create a new skill, navigate to the "Skills" page in your project sidebar and click "New Skill".

<!-- RESOURCE: Screenshot of the Skills list page with "New Skill" button -->

You'll be prompted to provide:

* **Name**: A snake_case identifier for the skill (e.g., `sql_query_writer`, `data_validation_rules`)
* **Description**: A clear explanation of what the skill does and when to use it
* **Instructions**: The markdown-formatted instructions that will be loaded when the agent calls this skill

<figure><img src="../.gitbook/assets/skill-create.png" alt="" width="375"><figcaption><p>Create a skill with name, description, and instructions</p></figcaption></figure>

{% hint style="warning" %}
**Write Clear Descriptions**

The skill description is what the model sees when deciding whether to use a skill. Make it specific and actionable:

* **Poor:** "SQL help"
* **Better:** "Write and optimize SQL queries for PostgreSQL"
* **Best:** "Generates SQL queries for PostgreSQL with proper joins, filtering, and performance optimization. Use when user requests data retrieval, filtering, or analysis from a database."
{% endhint %}

### Cloning Skills

Run configs reference skills by ID, not a snapshot, so editing a skill silently changes what every existing run config does. Historical eval scores and dataset runs become misleading because they were produced under different instructions, with no versioning to tell you what changed.

Instead, Kiln lets you clone a skill, giving you a fresh copy to modify while keeping the original intact so existing results stay valid.

<!-- RESOURCE: Screenshot of clone button on skill table -->

### Archiving Skills

If you have skills you no longer use but want to keep for reference, you can archive them. Archived skills won't appear in the skills dropdown and won't be available to agents. Unarchiving restores them to active use.

<!-- RESOURCE: Screenshot of archive button on skill detail page -->

## Using Skills

Once you've created skills, you can make them available to your agents through run configurations.

### Adding Skills to Run Configurations

On the "Run" screen, under the "Skills" section in Advanced, you'll see all available skills in your project. Select the skills you want to make available to the agent for this run.

<figure><img src="../.gitbook/assets/run-config-skills.png" alt="" width="375"><figcaption><p>Select skills in the run configuration</p></figcaption></figure>

### How Agents Use Skills

When you make skills available to an agent, here's what happens:

1. **Discovery**: The agent sees all available skill names and descriptions in its system prompt
2. **Decision**: The agent decides which skills (if any) are relevant to the current task
3. **Loading**: When the agent needs a skill, it calls the skill tool with the skill's name
4. **Execution**: The skill's full instructions are loaded into the conversation, and the agent proceeds with the task

This lazy-loading approach means your agent's context stays clean and focused. Specialized instructions are only retrieved when actually needed.

{% hint style="info" %}
**Model Behavior**

The model may or may not choose to use the skills you provide. If you find the model is not using a skill when you feel it should, try:
1. Making the skill description more specific and actionable
2. Updating your prompt to explicitly mention when certain skills should be used
3. Ensuring the skill name clearly indicates its purpose
{% endhint %}

### Viewing Skill Usage

When viewing a run trace, you can see which skills the agent loaded in the "All Messages" section. Skill calls appear as tool invocations, showing when and how the agent used each skill.

<!-- RESOURCE: Screenshot of a trace showing skill calls -->

## References

Skills can include reference files—additional markdown documents that provide supporting information, which are also only retrieved when the agent decides they're needed. References are useful for:

* Detailed technical specifications
* Code examples or templates
* Domain knowledge or terminology
* Style guides or formatting rules

### Adding References

Currently, references are managed through the file system. To add references to a skill:

1. Navigate to your project's `skills` directory
2. Find the skill's folder (named after the skill ID)
3. Create a `references` folder if it doesn't exist
4. Add markdown files (`.md`) to the `references` folder

Your skill structure should look like:

```
skills/
  <skill_id>/
    skill.kiln           # Metadata (name, description, etc.)
    SKILL.md             # Main skill instructions
    references/          # Additional reference files
      API_RESPONSE_FORMAT.md
      STYLE_GUIDE.md
      ...
```

### Referencing from Skills

Within your skill instructions (in `SKILL.md`), you can reference files using markdown syntax. When the agent loads your skill, you can instruct it to load specific reference files:

```markdown
## Instructions

Follow our company's coding standards. See our [style guide](references/STYLE_GUIDE.md) for details.

When generating API responses, use the format specified in this [API format guide](references/API_RESPONSE_FORMAT.md).
```

## Skills vs Tools vs Subtasks

Kiln offers three ways to extend your agent's capabilities. Here's how to choose:

### Skills

* **What they are**: Reusable instructions loaded into context on-demand
* **When to use them**: Specialized knowledge, procedures, or guidelines that don't require external actions
* **Example**: A skill for writing PostgreSQL queries, or following a company's editorial guidelines

### Tools (MCP)

* **What they are**: External functions and APIs the agent can call
* **When to use them**: Actions that require interacting with outside systems
* **Example**: Web search, database queries, sending emails, running code

### Subtasks (Tasks as Tools)

* **What they are**: Full Kiln tasks that other tasks can delegate to
* **When to use them**: Complex multi-step workflows that benefit from independent context and reasoning
* **Example**: A research subtask that searches the web and synthesizes findings before returning to the main task

<figure><img src="../.gitbook/assets/skills-comparison.png" alt=""><figcaption><p>Choose the right approach for your use case</p></figcaption></figure>

| Feature | Skills | Tools | Subtasks |
| :--- | :--- | :--- | :--- |
| **Primary Use** | Instructions & knowledge | External actions | Complex workflows |
| **Context Impact** | Loaded only when needed | Minimal (just tool defs) | Isolated per subtask |
| **Best For** | Guidelines, procedures | APIs, databases | Multi-agent patterns |
| **Setup Complexity** | Low | Medium | High |

## Best Practices

### Write Specific, Actionable Descriptions

Your skill descriptions are the primary signal the model uses to decide when to use a skill. Make them clear and specific:

* ✅ "Validates JSON schemas against the OpenAPI 3.0 specification and reports errors"
* ❌ "JSON validator"

### Keep Skills Focused

Each skill should have a single, clear purpose. If you find a skill becoming too broad, consider splitting it into multiple focused skills.

### Test Your Skills

After creating a skill, test it by:
1. Creating a run configuration with the skill enabled
2. Running your task with inputs that should trigger the skill
3. Checking the trace to verify the skill was loaded and used correctly