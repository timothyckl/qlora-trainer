from datasets import load_dataset
from datasets.dataset_dict import DatasetDict

class WVUProcessor():
    def __init__(self, config, tokenizer) -> None:
        self.config = config
        self.tokenizer = tokenizer

    def get_data(self) -> DatasetDict:
        if "model_context_window" in self.config:
            context_window = self.config["model_context_window"]
        else:
            context_window = self.tokenizer.model_max_length

        data = load_dataset(self.config["data"]["dataset"])
        tokenized = data.map(lambda sample: self.tokenizer(
            self._generate_prompt(
                sample["data"],
                self.tokenizer.eos_token),
            max_length=context_window,
            truncation=True,
        ))

        return tokenized
    
    def _generate_prompt(self, conversation: list, eos_token: str) -> str:
        out_str = ""
        
        for turn in conversation:
            entity = turn["from"]
            value = turn["value"]

            if entity == "human":
                out_str += self.config["data"]["user_header"]  # e.g. "### HUMAN:\n"
                end_token = ""
            elif entity == "gpt":
                out_str += self.config["data"]["response_header"]  # e.g. "### RESPONSE:\n"
                end_token = eos_token  # LLM should stop its output after the response
            else:
                print(f"WARNING: uknown entity {entity}")
                out_str += f"### {entity.upper()}:\n"
                end_token = ""

            out_str += value + end_token + "\n\n"

        return out_str