"""Prompt templates used throughout the MCP server."""

PROMPT_EXTRACT_SEED = """
You are a research planning assistant.

Analyze the following seed document and extract structured information for a deep research session.

<seed_document>
{seed_text}
</seed_document>

Extract:
1. **youtube_urls**: All YouTube video URLs found in the text (youtube.com or youtu.be links).
2. **topics**: The main topics and themes the document covers or wants researched.
3. **research_questions**: Specific questions that should be researched, either explicitly stated
   or implied by the document.

Return a structured JSON response.
""".strip()

PROMPT_YOUTUBE_TRANSCRIPTION = """You are an expert transcriber and video analyst.
Your task is to create a detailed and enriched transcript of the provided video.

Follow these instructions:
1. Transcribe the audio verbatim.
2. Insert timestamps every {timestamp} seconds in the form [MM:SS].
3. Where relevant, add brief, parenthetical descriptions of key visual elements, scenes,
   or on-screen text that complement the audio.
4. If there are multiple speakers, try to identify them as 'Speaker 1', 'Speaker 2', etc.
5. At the end of each major section or topic change, add a one-sentence summary in italics.

Produce the output in Markdown format.
"""

PROMPT_GENERATE_QUERIES = """
You are a research assistant helping to conduct deep research on a topic.

Your task: propose {n_queries} diverse, insightful web-search questions
that, taken **as a group**, will collect authoritative sources for the
research topic **and** provide a short explanation of why each question is
important.

<seed_context>
{seed_context}
</seed_context>

<past_research>
{past_research}
</past_research>

<youtube_transcripts>
{youtube_transcripts}
</youtube_transcripts>

Guidelines for the set of queries:
- Give priority to topics from the seed context that currently lack supporting
  sources in <past_research> and <youtube_transcripts>.
- Cover any remaining major topics to ensure balanced coverage.
- Avoid duplication; each query should target a distinct aspect.
- The web search queries should be natural language questions, not just keywords.
""".strip()

PROMPT_RESEARCH = """
{query}

Provide a detailed, comprehensive answer to the question above.
Focus on official sources, authoritative references, and well-established facts.
Include as much relevant detail as possible.
Cite your sources clearly.
"""

PROMPT_SELECT_SOURCES = """
You are a research assistant tasked with selecting the most trustworthy and relevant sources
from a collection of web search results.

Your task is to evaluate each source based on:
1. **Domain Authority & Trustworthiness**: Prefer reputable websites, official sources,
   established publications, academic institutions, and well-known organizations.
2. **Content Quality**: Evaluate the quality and relevance of the answers obtained.
3. **Relevance to Research Topic**: How well each source's content aligns with the research goals.

<seed_context>
{seed_context}
</seed_context>

<sources_to_evaluate>
{sources_data}
</sources_to_evaluate>

Please analyze each source and select only the high-quality, trustworthy, and relevant ones.
Return the selected sources with a brief reasoning for your overall selection strategy.
""".strip()
