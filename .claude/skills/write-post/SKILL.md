---
name: write-post
description: "Generate a LinkedIn post using the LinkedIn Writer MCP server. Use this skill whenever the user wants to write a LinkedIn post, create social media content, draft a post from research, or generate a post with an image. Triggers on: 'write a post', 'create a LinkedIn post', 'draft a post about', 'turn this into a post', 'generate a post', or any request involving LinkedIn content creation. Also use when the user has a guideline.md and research.md ready."
---

# Write LinkedIn Post

Generate a LinkedIn post using the `linkedin-writer` MCP server.

## Input Preparation

The working directory needs `guideline.md` and `research.md`.

If the user provides raw text for the guideline, create `guideline.md` in the working directory:

```markdown
# LinkedIn Post Guideline

## Topic
[What the post is about]

## Angle
[What perspective or approach to take]

## Target Audience
[Who this post is for]

## Key Points to Cover
[3-5 bullet points]

## Tone
[How it should sound]
```

If `research.md` is in a different location, copy it into the working directory.

Default working directory: current directory. Create it if needed.

## Execution

Read the `WORKFLOW_INSTRUCTIONS` from `src/writing/routers/prompts.py` and follow those steps exactly, using the `linkedin-writer` MCP tools. Pass the working directory path to each tool.

## After Completion

Present the final `post.md` content to the user. If an image was generated, mention `post_image.png`.
