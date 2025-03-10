---
icon: shield-keyhole
description: Kiln is private by design
---

# Privacy

<figure><img src="../.gitbook/assets/Privacy.png" alt=""><figcaption></figcaption></figure>

Kiln runs on your machine, not a server. We never collect or have access to:

* Datasets / Training Data
* API keys
* Model inputs/outputs (runs)

You can run completely locally using [Ollama](https://ollama.com), ensuring your data stays entirely on your device.

If you bring your own keys for a cloud AI provider (OpenAI, OpenRouter, Groq, AWS, Fireworks, etc), see their privacy policy for how they log and store data.

{% hint style="info" %}
We collect anonymous usage metrics via [Posthog analytics](https://github.com/PostHog/posthog).

This analytics data never includes dataset content or your identity.

Analytics can be blocked with standard ad-blockers.
{% endhint %}
