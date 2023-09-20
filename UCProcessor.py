from datasets import load_dataset
from datasets.dataset_dict import DatasetDict


class UCProcessor():
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

        for idx, txt in enumerate(conversation):
            if idx % 2 != 0:
                out_str += f"{self.config['data']['user_header']}{txt}"
            else:
                out_str += f"{self.config['data']['response_header']}{txt}{eos_token}"

            out_str += "\n\n"

        return out_str
            