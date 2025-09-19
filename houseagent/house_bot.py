import structlog
import json
import os
import re

from langchain_ollama import ChatOllama

from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


class HouseBot:
    def __init__(self):
        self.logger = structlog.getLogger(__name__)
        prompt_dir = 'prompts'

        human_primpt_filename = 'housebot_human.txt'
        system_prompt_filename = 'housebot_system.txt'
        default_state_filename = 'default_state.json'

        with open(f'{prompt_dir}/{system_prompt_filename}', 'r') as f:
            system_prompt_template = f.read()
        with open(f'{prompt_dir}/{human_primpt_filename}', 'r') as f:
            human_prompt_template = f.read()
        with open(f'{prompt_dir}/{default_state_filename}', 'r') as f:
            self.default_state = json.load(f)

        self.system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_prompt_template
        )
        self.human_message_prompt = HumanMessagePromptTemplate.from_template(
            human_prompt_template
        )

        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
        ollama_temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))

        self.chat = ChatOllama(model=ollama_model, temperature=ollama_temperature)

    def strip_emojis(self, text):
        RE_EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
        return RE_EMOJI.sub(r'', text)

    def generate_response(self, current_state, last_state):

        chat_prompt = ChatPromptTemplate.from_messages(
            [
                self.system_message_prompt,
                self.human_message_prompt,
            ]
        )

        # Use new RunnableSequence syntax: prompt | llm
        chain = chat_prompt | self.chat

        default_state_text = json.dumps(self.default_state)

        result = chain.invoke(
            {
                "default_state": default_state_text,
                "current_state": current_state,
                "last_state": last_state,
            }
        )

        # Extract content from result
        output = result.content if hasattr(result, 'content') else str(result)

        # strip emoji (some terminals or downstream systems may not support emojis)
        output = self.strip_emojis(output)

        self.logger.info(f"Generated response: {output}")

        return output
