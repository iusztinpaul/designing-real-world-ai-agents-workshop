"""Prompt templates for the Deep Research Agent."""

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
