"""Command-line entry point."""

import argparse

from app.agent import run_agent


def main():
    parser = argparse.ArgumentParser(description="Ask the RetailOps local AI agent.")
    parser.add_argument("question", nargs="+", help="Question for the retail agent")
    args = parser.parse_args()
    question = " ".join(args.question)
    print("\nRetailOps is working...\n")
    print(run_agent(question))


if __name__ == "__main__":
    main()
