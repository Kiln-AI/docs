---
icon: people-arrows
description: Collaborate with your team using Kiln
---

# Collaboration

This guide will help you understand how a team can collaborate with Kiln.

<figure><img src="../.gitbook/assets/Collab.png" alt=""><figcaption></figcaption></figure>

### Sharing a Kiln Project

It's easy to collaborate with Kiln across teams with technical team members (devs, data-scientists), and non-technical team members (labelers, subject-matter experts).

We suggest [git](collaboration.md#option-1-use-git) for technical teams, [shared drives](collaboration.md#option-2-use-shared-drives-for-non-technical-team-members) for non-technical teams, or a [mix](collaboration.md#option-3-combining-git-and-shared-drives) for mixed teams.

### Collaboration Architecture

Unlike other collaboration tools, you don't need to allow a third party to access your data, or maintain a database.&#x20;

Kiln's data structure was designed with collaboration in mind:

* A Kiln project is really just a folder of files so you can use existing collaboration tools, from Git to Dropbox
* New items use unique random IDs to avoid conflicts/collisions, allowing many people to work concurrently on the same project.
* Projects files are kept small - it's rare multiple people will need to work on the same file at the same time, reducing conflicts.
* The Kiln project files are JSON files, but are formatted to be easily used with diff tools and standard PR tools (GitHub, GitLab, etc).

#### Option 1: Use Git

Kiln projects are simply a folder of files, making it easy to share them using Git. Add your project folder(s) to a git repo and you're set up with an excellent collaboration workflow with branches, pull requests, version control, access control, and more!

#### Option 2: Use Shared Drives for Non-Technical Team Members

Not everyone is familiar with git, and that's okay! Since Kiln projects are just a folder of files, you can share the folder with your team using a shared drive of your choice (Google Drive, Dropbox, iCloud, etc).

Kiln project files will track who created them (internally in their JSON), which can help when many folks are making changes on the same shared drive. It's not as rich as git for tracking changes, but it's doesn't require any technical background.

#### Option 3: Combining Git and Shared Drives

You can combine both approaches for larger teams. Setup Git for technical team members and version control, then host a branch on the shared drive. A technical team member can merge changes from the shared drive into main on occasion. The rest of the team can keep the benefits of git.

