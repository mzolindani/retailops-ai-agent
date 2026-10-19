"""Optional smoke test; requires Ollama and the configured model to be available."""

import os
import pytest

from app.agent import run_agent


@pytest.mark.skipif(
    os.getenv("RUN_LLM_TESTS") != "1",
    reason="Set RUN_LLM_TESTS=1 to run tests against the local model.",
)
def test_agent_answers_inventory_question():
    answer = run_agent("How many wireless mice are available at STORE-01?")
    assert "18" in answer
