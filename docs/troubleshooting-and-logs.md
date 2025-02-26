---
description: How to troubleshoot errors from the logs
icon: user-helmet-safety
---

# Troubleshooting & Logs

### First: Consider Model Errors

Most bug reports we get aren't actually bugs in Kiln, but models failing to perform the task asked of them. Please read the error messages carefully, and follow the suggestions.

* If the error is related to structured data, see [Troubleshooting Structured Data Issues](structured-data-json.md#troubleshooting-structured-data-issues)
* Try another (smarter) model to see if the issue persists, of it it's isolated to a specific model.

### Second: Check The Logs

Kiln writes out error logs to the path \`\~/.kiln\_ai/logs/\*.log\`.

Check your latest log file for a stack trace of any errors, which can help understand the issue. If you think it's a bug in Kiln and not a model issue, please [file a bug](https://github.com/Kiln-AI/Kiln/issues), following the bug template and attaching logs.
