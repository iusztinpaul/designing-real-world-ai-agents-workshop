"""Manual end-to-end test of the Deep Research MCP server workflow.

Connects to the research MCP server as a client and runs the full
deep research workflow against a sample seed.md file.

Usage:
    uv run python scripts/test_research_workflow.py [--working-dir PATH] [--iterations N]
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

import click
from fastmcp import Client

logger = logging.getLogger(__name__)

# Number of separator chars for visual output
SEP_WIDTH = 70


def print_step(step: str, description: str) -> None:
    """Print a formatted workflow step header."""

    print(f"\n{'=' * SEP_WIDTH}")
    print(f"  STEP {step}: {description}")
    print(f"{'=' * SEP_WIDTH}\n")


def print_result(result: object) -> None:
    """Print the tool result in a readable format."""

    data = getattr(result, "data", result)
    if isinstance(data, dict):
        message = data.get("message", "")
        status = data.get("status", "unknown")
        print(f"  Status: {status}")
        if message:
            print(f"  Message: {message}")
    elif isinstance(data, str):
        try:
            parsed = json.loads(data)
            print(f"  {json.dumps(parsed, indent=2)}")
        except json.JSONDecodeError, TypeError:
            print(f"  {data}")
    else:
        print(f"  {data}")


async def run_workflow(client: Client, working_dir: str, iterations: int) -> None:
    """Execute the full deep research workflow via MCP tool calls."""

    # ------------------------------------------------------------------
    # Step 1: Extract seed
    # ------------------------------------------------------------------
    print_step("1", "Extract seed file")

    result = await client.call_tool(
        "extract_seed",
        {"working_dir": working_dir, "seed_filename": "seed.md"},
    )
    print_result(result)

    # Check for YouTube URLs in the extraction
    data = getattr(result, "data", {})
    youtube_count = data.get("youtube_urls_count", 0) if isinstance(data, dict) else 0

    # ------------------------------------------------------------------
    # Step 2: Transcribe YouTube (if any)
    # ------------------------------------------------------------------
    if youtube_count > 0:
        print_step("2", f"Transcribe YouTube videos ({youtube_count} found)")

        # Read the seed extraction to get the actual URLs
        memory_dir = Path(working_dir) / ".memory"
        seed_extraction_path = memory_dir / "seed_extraction.json"
        seed_data = json.loads(seed_extraction_path.read_text(encoding="utf-8"))
        youtube_urls = seed_data.get("youtube_urls", [])

        result = await client.call_tool(
            "transcribe_youtube",
            {"working_dir": working_dir, "youtube_urls": youtube_urls},
        )
        print_result(result)
    else:
        print_step("2", "Transcribe YouTube videos (SKIPPED — none found)")

    # ------------------------------------------------------------------
    # Step 3: Research loop
    # ------------------------------------------------------------------
    for i in range(1, iterations + 1):
        print_step(f"3.{i}a", f"Generate research queries (iteration {i}/{iterations})")

        result = await client.call_tool(
            "generate_next_queries",
            {"working_dir": working_dir, "n_queries": 3},
        )
        print_result(result)

        # Extract queries from the result
        data = getattr(result, "data", {})
        queries_data = data.get("queries", []) if isinstance(data, dict) else []
        query_strings = [
            q["query"] if isinstance(q, dict) else str(q) for q in queries_data
        ]

        if not query_strings:
            print("  WARNING: No queries generated, skipping research and selection.")
            continue

        print_step(f"3.{i}b", f"Run grounded research ({len(query_strings)} queries)")

        result = await client.call_tool(
            "run_research",
            {"working_dir": working_dir, "queries": query_strings},
        )
        print_result(result)

        print_step(f"3.{i}c", "Select high-quality sources")

        result = await client.call_tool(
            "select_sources",
            {"working_dir": working_dir},
        )
        print_result(result)

    # ------------------------------------------------------------------
    # Step 4: Create research file
    # ------------------------------------------------------------------
    print_step("4", "Create final research.md")

    result = await client.call_tool(
        "create_research_file",
        {"working_dir": working_dir},
    )
    print_result(result)

    print(f"\n{'=' * SEP_WIDTH}")
    print("  WORKFLOW COMPLETE")
    print(f"{'=' * SEP_WIDTH}")

    output_path = Path(working_dir) / "research.md"
    if output_path.exists():
        size = output_path.stat().st_size
        print(f"\n  Output: {output_path.resolve()} ({size:,} bytes)")
    else:
        print(f"\n  WARNING: {output_path} was not created.")


def ensure_seed_file(working_dir: str, seed_filename: str) -> None:
    """Check that the seed file exists in the working directory."""

    seed_path = Path(working_dir) / seed_filename
    if not seed_path.exists():
        print(f"ERROR: {seed_filename} not found in {working_dir}")
        sys.exit(1)


@click.command()
@click.option(
    "--working-dir",
    "-d",
    default="test_research",
    help="Working directory containing seed.md (default: test_research)",
)
@click.option(
    "--iterations",
    "-n",
    default=2,
    type=int,
    help="Number of research loop iterations (default: 2)",
)
def main(working_dir: str, iterations: int) -> None:
    """Run the full deep research workflow as an MCP client test."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Resolve working directory
    working_path = Path(working_dir).resolve()
    working_path.mkdir(parents=True, exist_ok=True)
    ensure_seed_file(str(working_path), "seed.md")

    print("Deep Research MCP Server — Workflow Test")
    print(f"Working directory: {working_path}")
    print(f"Research iterations: {iterations}")

    # Connect to the server via stdio (launches it as a subprocess)
    server_path = str(Path(__file__).parent.parent / "src" / "research" / "server.py")
    client = Client(server_path)

    async def _run() -> None:
        async with client:
            # Verify connection by listing tools
            tools = await client.list_tools()
            print(f"\nConnected to server. Available tools: {len(tools)}")
            for tool in tools:
                print(f"  - {tool.name}")
            print()

            await run_workflow(client, str(working_path), iterations)

    asyncio.run(_run())


if __name__ == "__main__":
    main()
