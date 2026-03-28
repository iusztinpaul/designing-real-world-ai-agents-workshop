---
name: research
description: "Run deep research on any topic using the Deep Research MCP server. Use this skill whenever the user wants to research a topic, gather information, find sources, or create a research document. Triggers on: 'research this', 'find out about', 'gather information on', 'I need to understand', 'deep dive into', or any request that involves investigating a topic."
---

# Research

Research a topic using the `deep-research` MCP server.

## Execution

1. Load the `research_workflow` MCP prompt from the `deep-research` server.
2. Follow the workflow instructions to research the user's topic using the available tools:
   - `deep_research` — for web research queries
   - `analyze_youtube_video` — for any YouTube URLs the user provides
   - `compile_research` — to produce the final research.md
3. Use the current working directory as the `working_dir` for all tool calls.

## After Completion

Show the user the path to `research.md` and a brief summary of what was found.
