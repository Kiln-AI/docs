---
description: Kiln is private by design
icon: shield-keyhole
---

# Privacy

<figure><img src="../.gitbook/assets/Privacy.png" alt=""><figcaption></figcaption></figure>

Kiln is local software that runs on your computer, not the cloud. Your dataset is stored locally on your own hard drive.

We don't have access to your dataset, and couldn't access it even if we wanted to.

All of Kiln's source code is on GitHub. Anyone can verify these privacy claims. Kiln's binary builds are built from the public source code, on public CI servers (Github Actions), and have verifiable checksums.

If you use Kiln with API keys (for example, OpenAI or OpenRouter), requests are sent directly from your computer to the API provider. We can't see your keys or any data from those requests.

{% hint style="info" %}
We collect anonymous usage metrics via [Posthog analytics](https://github.com/PostHog/posthog).

This analytics data never includes dataset content, API keys, or your identity.
{% endhint %}
