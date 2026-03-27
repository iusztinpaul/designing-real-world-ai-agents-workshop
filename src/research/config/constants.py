"""Constants used throughout the MCP server."""

# File names
SEED_FILE = "seed.md"
RESEARCH_MD_FILE = "research.md"
SEED_EXTRACTION_FILE = "seed_extraction.json"
RESEARCH_RESULTS_FILE = "research_results.json"
SELECTED_SOURCES_FILE = "selected_sources.json"
QUERIES_FILE = "queries.json"

# Folder names
MEMORY_FOLDER = ".memory"
TRANSCRIPTS_FOLDER = "transcripts"

# YouTube operation constants
YOUTUBE_TRANSCRIPTION_MAX_CONCURRENT_REQUESTS = 2
YOUTUBE_TRANSCRIPTION_MAX_RETRIES = 3
YOUTUBE_TRANSCRIPTION_RETRY_WAIT_MIN_SECONDS = 5
YOUTUBE_TRANSCRIPTION_RETRY_WAIT_MAX_SECONDS = 60
