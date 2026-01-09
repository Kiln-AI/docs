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

#### Desktop App Analytics

The Kiln desktop app collects analytics so we can understand how people are using it. This includes analytics like which pages are being visited, and which actions are taken in the app’s UI. Analytics are collected with [Posthog](https://posthog.com/).<br>

* The Kiln Python library does not collect analytics. Only the desktop app’s user interface collects analytics.
* Analytics never includes your dataset information, such as inputs to models, output from models, project names, etc.
* Analytics never include your API keys.
* If you specify you’re using Kiln for personal non-commercial use we do not associate analytics with your personal identity (like your name or email). If you register for commercial usage of Kiln, which is optional and requires an explicit opt-in process, your work email is associated with analytics.

{% hint style="info" %}
If you opt-in to our email newsletter, we collect your email address to provide you the newsletter. You can unsubscribe any time.
{% endhint %}
