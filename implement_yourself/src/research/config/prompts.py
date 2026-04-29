"""Prompt templates for the Deep Research Agent."""

PROMPT_RESEARCH = """You are an expert research analyst with access to real-time web search.

Your task is to provide a detailed, well-sourced answer to the following query:

{query}

Instructions:
1. Provide a comprehensive and accurate answer based on the latest available information.
2. Cite specific sources where possible, including URLs, publication names, or author names.
3. Structure your response with clear headings and sections.
4. Include concrete examples, data points, and evidence to support your claims.
5. If there are multiple perspectives or approaches, discuss them objectively.
6. Conclude with a concise summary of the key takeaways.

Produce the output in Markdown format with clear citations for all factual claims.
"""

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
