---
name: write-post
description: "Generate a LinkedIn post using the LinkedIn Writer MCP server. Use this skill whenever the user wants to write a LinkedIn post, create social media content, draft a post from research, or generate a post with an image. Triggers on: 'write a post', 'create a LinkedIn post', 'draft a post about', 'turn this into a post', 'generate a post', or any request involving LinkedIn content creation. Also use when the user has a guideline.md and research.md ready."
---

# Write LinkedIn Post

Draft and generate a LinkedIn post using the `linkedin-writer` MCP server.

## Working Directory

All output goes into `outputs/{slug}/` relative to the project root. Derive the slug from:
- The referenced seed or guideline filename if the user provides one (e.g., `my-topic_seed.md` → `my-topic`)
- Otherwise, slugify the topic (lowercase, hyphens, no special chars, max 60 chars)

Create the directory if it doesn't exist.

## Input Preparation

The working directory must contain two files before the workflow runs:

- `guideline.md` — the post brief (topic, angle, audience, key points, tone)
- `research.md` — the supporting research (run `/research` first if not available)

If the user provides raw text instead of a prepared file, write it into `outputs/{slug}/guideline.md` using this template:

```markdown
# LinkedIn Post Guideline
## Topic
## Angle
## Target Audience
## Key Points to Cover
## Tone
```

If `research.md` already exists elsewhere (e.g., from a previous `/research` run), copy it into `outputs/{slug}/research.md`.

## Execution

1. Load the `linkedin_post_workflow` MCP prompt from the `linkedin-writer` server.
2. Follow the workflow instructions to draft the post using the available tools.
3. Pass `outputs/{slug}/` as the `working_dir` to every tool call.

## After Completion

Present the full content of `outputs/{slug}/post.md` to the user. If an image was generated, also mention the path `outputs/{slug}/post_image.png`.
