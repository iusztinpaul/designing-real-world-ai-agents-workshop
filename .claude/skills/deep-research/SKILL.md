---
name: deep-research
description: "Run deep research on any topic using the Deep Research MCP server. Use this skill whenever the user wants to research a topic, gather information, find sources, or create a research document. Triggers on: 'research this', 'find out about', 'gather information on', 'I need to understand', 'deep dive into', or any request that involves investigating a topic before writing about it. Also use when the user provides a seed.md file or describes a research topic."
---

# Deep Research

Research a topic using the `deep-research` MCP server.

## Input Preparation

If the user provides raw text instead of a seed.md file, create `seed.md` in the working directory:

```markdown
# Research Topic: [topic from user]

[User's description of what to research]

## Key Questions

[Extract 3-5 questions from the user's description]

## References

[Any URLs the user mentioned, or just "- "]
```

Default working directory: current directory. Create it if needed.

## Execution

Read the `WORKFLOW_INSTRUCTIONS` from `src/research/routers/prompts.py` and follow those steps exactly, using the `deep-research` MCP tools. Pass the working directory path to each tool.

## After Completion

Show the user the path to `research.md` and a brief summary of what was found.
