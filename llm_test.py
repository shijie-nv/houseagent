import os
import time
import json
import argparse
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

# Load environment variables
load_dotenv()

# Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))

PROMPT_DIR = "prompts"
LAST_STATE = "{}"

CURRENT_STATE_EXAMPLES = [
    '{"messages": [{"description of activity": "A man is standing in the office space, looking at his cell phone.", "number of people": "1", "people": [{"activity": "looking at cell phone", "description of person": {"clothing": "white shirt"}}]}]}',
    '{"messages": [{"entity_id": "binary_sensor.front_door", "from_state": "off", "to_state": "on"}, {"entity_id": "binary_sensor.frontyard_motion", "from_state": "off", "to_state": "on"}, {"entity_id": "binary_sensor.front_door", "from_state": "on", "to_state": "off"}]}',
]


def simple_test():
    """Test ChatOllama functionality directly"""
    chat = ChatOllama(model=OLLAMA_MODEL, temperature=OLLAMA_TEMPERATURE)
    start = time.perf_counter()
    response = chat.invoke("What's your name?")
    elapsed = time.perf_counter() - start

    print(type(response))
    print(response)

    print(f"Simple test - Model: {OLLAMA_MODEL}")
    print(f"Simple test - Time: {elapsed:.3f}s")
    print("Simple test - Response:", response.content)
    return response.content


def build_chain_from_files(prompt_dir: str, model_name: str, temperature: float):
    system_prompt_path = os.path.join(prompt_dir, "housebot_system.txt")
    human_prompt_path = os.path.join(prompt_dir, "housebot_human.txt")

    with open(system_prompt_path, "r") as f:
        system_prompt_template = f.read()
    with open(human_prompt_path, "r") as f:
        human_prompt_template = f.read()

    system_prompt = SystemMessagePromptTemplate.from_template(system_prompt_template)
    human_prompt = HumanMessagePromptTemplate.from_template(human_prompt_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

    chat = ChatOllama(model=model_name, temperature=temperature)
    # Use new RunnableSequence syntax: prompt | llm
    return chat_prompt | chat, chat_prompt


def run_once(
    model_name: str,
    temperature: float,
    prompt_dir: str,
    current_state: str,
    last_state: str,
) -> str:

    default_state_path = os.path.join(prompt_dir, "default_state.json")
    with open(default_state_path, "r") as f:
        default_state = json.load(f)
    default_state_text = json.dumps(default_state)

    chain, chat_prompt = build_chain_from_files(
        prompt_dir=prompt_dir, model_name=model_name, temperature=temperature
    )

    formatted_prompt = chat_prompt.format(
        default_state=default_state_text,
        current_state=current_state,
        last_state=last_state,
    )
    print("=== Debug: Actual prompt sent ===")
    print(formatted_prompt)
    print("=== Debug end ===")

    start = time.perf_counter()
    result = chain.invoke(
        {
            "default_state": default_state_text,
            "current_state": current_state,
            "last_state": last_state,
        }
    )
    elapsed = time.perf_counter() - start

    # print(type(result))
    # print(result)

    output = result.content if hasattr(result, 'content') else str(result)
    print(f"Model: {model_name}")
    print(f"Temperature: {temperature}")
    print(f"Time: {elapsed:.3f}s")
    print("--- Response ---")
    print(output)
    return output


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test LLM with different examples")
    parser.add_argument(
        "--case",
        type=int,
        default=1,
        help="Specify which test case to run (1-based index). Default is 1.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Validate case index
    if args.case < 1 or args.case > len(CURRENT_STATE_EXAMPLES):
        print(
            f"Error: Case {args.case} not found. Available: 1-{len(CURRENT_STATE_EXAMPLES)}"
        )
        return

    # Convert to 0-based index
    case_index = args.case - 1
    current_state = CURRENT_STATE_EXAMPLES[case_index]

    print(f"\n=== Running Case {args.case} ===")

    run_once(
        model_name=OLLAMA_MODEL,
        temperature=OLLAMA_TEMPERATURE,
        prompt_dir=PROMPT_DIR,
        current_state=current_state,
        last_state=LAST_STATE,
    )


if __name__ == "__main__":
    main()
