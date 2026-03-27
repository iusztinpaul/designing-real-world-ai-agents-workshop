---
name: research-and-write
description: "End-to-end workflow: research a topic and then write a LinkedIn post about it. Use this skill whenever the user wants the full pipeline — from a topic idea to a finished LinkedIn post. Triggers on: 'research and write a post about', 'create a LinkedIn post about [topic]', 'I want to post about', 'write about [topic] for LinkedIn', or any request that implies both researching a subject and producing a LinkedIn post from it. This is the go-to skill when the user gives you a topic and expects a finished post."
---

# Research and Write

End-to-end workflow: research a topic, then write a LinkedIn post from it. Chains the `deep-research` and `linkedin-writer` MCP servers.

## Input Preparation

Gather from the user:
1. **Topic** — what to research (becomes `seed.md`)
2. **Guideline** — how the post should be written (becomes `guideline.md`)

If the user only gives a topic, ask for the guideline details (angle, audience, key points, tone) or suggest a default based on the topic.

Create both files in the working directory:

**`seed.md`:**
```markdown
# Research Topic: [topic]

[Description]

## Key Questions

[3-5 research questions]

## References

[URLs or "- "]
```

**`guideline.md`:**
```markdown
# LinkedIn Post Guideline

## Topic
[Core topic]

## Angle
[Perspective]

## Target Audience
[Who reads this]

## Key Points to Cover
[3-5 bullets]

## Tone
[How it should sound]
```

Default working directory: current directory. Create it if needed.

## Execution

### Phase 1: Research

Read the `WORKFLOW_INSTRUCTIONS` from `src/research/routers/prompts.py` and follow those steps exactly, using the `deep-research` MCP tools. This produces `research.md`.

Tell the user when research is complete.

### Phase 2: Write

Read the `WORKFLOW_INSTRUCTIONS` from `src/writing/routers/prompts.py` and follow those steps exactly, using the `linkedin-writer` MCP tools. The working directory already has `guideline.md` and `research.md` from Phase 1.

## After Completion

Present the final `post.md` and `post_image.png` to the user. Offer to edit with feedback.
