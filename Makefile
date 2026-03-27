ifeq (,$(wildcard .env))
$(error .env file is missing. Please create one based on .env.example. Run: "cp .env.example .env" and fill in the missing values.)
endif

include .env
export

export UV_PROJECT_ENVIRONMENT=.venv
export PYTHONPATH = ./src/

# --- Default Values ---

QA_FOLDERS := src/ scripts/

# --- QA ---

format-fix: # Auto-format Python code using ruff formatter.
	uv run ruff format $(QA_FOLDERS)

lint-fix: # Auto-fix linting issues using ruff linter.
	uv run ruff check --fix $(QA_FOLDERS)

format-check: # Check code formatting without making changes using ruff formatter.
	uv run ruff format --check $(QA_FOLDERS) 

lint-check: # Check code for linting issues without fixing them using ruff linter.
	uv run ruff check $(QA_FOLDERS)

# --- Run ---

run-research-server: # Run the Deep Research MCP server (stdio transport).
	uv run fastmcp run src/research/server.py

run-writing-server: # Run the LinkedIn Writer MCP server (stdio transport).
	uv run fastmcp run src/writing/server.py

test-research-workflow: # Test the research workflow via MCP client.
	@mkdir -p test_logic
	@cp inputs/seed.md test_logic/seed.md
	uv run python scripts/test_research_workflow.py --working-dir test_logic --iterations 2

test-writing-workflow: # Test the writing workflow via MCP client (requires research.md in test_logic/).
	@mkdir -p test_logic
	@cp inputs/guideline.md test_logic/guideline.md
	@test -f test_logic/research.md || (echo "ERROR: test_logic/research.md not found. Run test-research-workflow first." && exit 1)
	uv run python scripts/test_writing_workflow.py --working-dir test_logic

test-end-to-end: # Test research + writing workflows end-to-end.
	make test-research-workflow
	make test-writing-workflow

# --- Dataset ---

generate-dataset: # Generate seed and guideline files for the LinkedIn dataset.
	uv run python scripts/generate_dataset.py

run-dataset-writing: # Run the writing workflow on all dataset posts (with images).
	uv run python scripts/run_dataset_writing.py

run-dataset-writing-no-image: # Run the writing workflow on all dataset posts (skip images).
	uv run python scripts/run_dataset_writing.py --skip-image