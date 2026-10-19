# RetailOps AI Agent

A local-first ReAct-style retail operations agent using Ollama, LangChain's `create_agent`,
and deterministic Python tools. This milestone is read-only: no refunds, cancellations, or
inventory mutations are exposed to the model.

## Requirements

- Python 3.11+
- Ollama installed and running
- A model that supports tool calling. Start with `qwen2.5:3b`; if tool calls are unreliable,
  try a larger tool-capable model supported by your machine.

## Windows PowerShell setup

```powershell
# Install Ollama from https://ollama.com/download/windows, then open a new terminal.
ollama pull qwen2.5:3b
ollama list

# From the project directory:
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
```

If PowerShell blocks activation, run this once in the current terminal:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## Run

```powershell
python -m app.cli "Find order ORD-1002 and check whether there is enough stock to fulfil it."
```

Try these prompts:

```powershell
python -m app.cli "What products do we sell?"
python -m app.cli "How many wireless mice are in stock?"
python -m app.cli "Find order ORD-1002 and check whether stock is sufficient to fulfil it."
python -m app.cli "Find order ORD-1001 and list its items and status."
```

## Tests

Tests for the deterministic tools do not require Ollama:

```powershell
pytest -q
```

## Design notes

- The model decides which read-only tool to call next.
- The tool functions own the facts and return structured JSON strings.
- `create_agent` runs the model/tool loop; it is the current LangChain agent factory.
- This starter intentionally does not expose write operations.
- Local models may occasionally fail to call tools correctly. Check the Ollama model is pulled,
  that Ollama is running, and inspect the tool-call messages. Tool calling quality depends on
  the model and its quantisation.
