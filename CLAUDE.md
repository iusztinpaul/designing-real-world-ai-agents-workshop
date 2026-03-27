# Project

We are building an educative workshop teaching people how to build AI systems by implementing a hybrid AI system containing a Deep Research Agent and a Writing Workflow, both served as MCP servers and connected to a harness such as Claude Code or Cursor.

# Project Structure

```
project-root/
├── src/
│   ├── research/   # research workflow module
│   └── writing/    # writing workflow module
├── scripts/                         # Entrypoints
└── .env.example                     # All supported env vars
```

# Tech Stack

- Data validation and structuring: Pydantic
- Settings: Pydantic Settings
- MCP Server Framework: FastMCP
- CLI: Click
- Logging: Native Python logger (never prints!)
- LLM API: Gemini
- Observability and evals: Opik

## Access Documentation
Use the context7 MCP server to find out more about the tech stack usage and good practices.

# Running QA

We use ruff as our formatter and linter.

First always fix the formatting and linting errors with the fix commands:
```
make format-fix
make lint-fix
```
Then, check if there are any errors that couldn't be fixed automatically and fix them:
```
make format-check
make lint-check
```

# Running Code

We manage all the core commands through GNU Make as our command center. File available at @Makefile. Run all the commands with `make ...`

We use uv to manage our Python project such as the virtual environment(s), dependencies, and overall package the project.

Thus, use uv to run any custom command that is not present in the @Makefile, but uses Python: `uv run python ...`
