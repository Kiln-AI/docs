---
description: How to collaborate with your team using Kiln
icon: people-arrows
---

# Collaboration

<figure><img src="../.gitbook/assets/Collab2.png" alt=""><figcaption></figcaption></figure>

### Designed for Techies and Non-techies Alike

It's easy to collaborate with Kiln across teams with technical team members (devs, data-scientists), and non-technical team members (subject-matter experts, QA, labelers, etc).

We suggest [Git](collaboration.md#option-1-use-git) for technical teams, [shared drives](collaboration.md#option-2-use-shared-drives-for-non-technical-team-members) for non-technical teams, or a [mix](collaboration.md#option-3-combining-git-and-shared-drives) for mixed teams.

### Option 1: Use Git

Kiln projects are simply a folder of files, making it easy to share them using Git. Add your project folder(s) to a git repo and you're set up with an excellent collaboration workflow with branches, pull requests, version control, access control, and more!

See [below](collaboration.md#collaboration-design) for how our file format is optimized for Git-based workflows.

### Option 2: Use Shared Drives for Non-Technical Team Members

Not everyone is familiar with Git, and that's okay! Since Kiln projects are just a folder of files, you can share the folder with your team using a shared drive of your choice (Google Drive, Dropbox, iCloud, etc).

Kiln project files will track who created them (internally in their JSON), which adds version history when many folks are making changes on the same shared drive.

### Option 3: Combining Git and Shared Drives

You can combine both approaches for teams with a mix of technical backgrounds. Setup Git for technical team members, then host a branch on the shared drive for non-technical team members.

A technical team member can merge changes from the shared drive branch into main on occasion.

### Collaboration Design

As you may have already guessed, you don't need to allow a third party to access your data, or maintain a database. Everything runs locally on your machine, and syncs through existing tools you control.

Kiln's data structure was designed with collaboration in mind:

* A Kiln project is simply a folder of files, which makes it compatible with a range of existing collaboration tools, from Git to Dropbox
* New items use unique random IDs to avoid conflicts/collisions, allowing many people to work concurrently on the same project.
* Projects files are kept small and predominantly append-only. It's rare multiple people will need to work on the same file at the same time, reducing conflicts.
* The Kiln project files are JSON files, and are formatted to be easily used with diff tools and standard PR tools (GitHub, GitLab, etc).
* Static paths: even when changing the name of resource, the path will remain static.

### We don't recommend deploying as a service

{% hint style="info" %}
This section is for engineers/developers attempting custom deployments. If you're a normal app user who launches Kiln as an app, you can skip this!
{% endhint %}

Kiln's desktop app is designed as an app. Even though internally it uses web tech (HTML), it's still an app designed to be run locally on each user's machine, not a hosted service.

We don't recommend or support trying to host it as a service and access it over the network. There are several downsides/risks if you do:

* Security: there's no web-based logins or access controls, so anyone who can access the service can edit data and send requests. That's okay when running as an app locally behind your machine login, but brings risk when opening the service up to anyone over a network.
* Collaboration: If multiple users are sharing an instance of Kiln, all the created\_by tags in your dataset will all have the machine name of your VM/host, not the individuals.
* Data backup and history: if you run as suggested above, Git and/or the shared drive will provide data sync, backup and history. If you run on a single server, there's a higher risk of data loss if that server drive is lost/damaged.
* System Integrations: Kiln accesses things like the taskbar and filesystem, which aren't available to web apps. We'll add more native integrations over time.&#x20;

For these reasons, we recommend each user runs Kiln locally. Don't worry - it's fast and doesn't take up many resources.

You can still access remote LLM services when running locally. It can connect to remote LLM providers, like OpenAI's API or connect to a remote Ollama instance over the network via a custom URL. You don't need to co-locate Kiln and you LLM servers.
