# from datasets import load_dataset
# from datasets.dataset_dict import DatasetDict

def prompt_formatter(sample, config):
    outputs = []

    instruct_header = config["data"]["instruct_header"]
    input_header = config["data"]["input_header"]
    output_header = config["data"]["output_header"]
   
    for i in range(len(sample['instruction'])):
        instruction = sample["instruction"][i]
        input = sample["input"][i]
        output = sample["output"][i]
        text = f"### {instruct_header}\n{instruction}\n\n### {input_header}\n{input}\n\n### {output_header}\n\n{output}"
        outputs.append(text)

    return outputs

# class GPT4AlpacaProcessor:
#     def __init__(self, config, tokenizer):
#         self.config = config
#         self.tokenizer = tokenizer
#
#     def get_data(self) -> DatasetDict:
#         context_window = (
#             self.config["model_context_window"]
#             if "model_context_window" in self.config
#             else self.tokenizer.model_max_length
#         )
#
#         data = load_dataset(self.config["data"]["dataset"])
#         data = data.map(
#             lambda data_point: self.tokenizer(
#                 self._generate_prompt(data_point, self.tokenizer.eos_token),
#                 max_length=context_window,
#                 truncation=True,
#             )
#         )
#         return data
#
#     def _generate_prompt(self, data_point: dict, eos_token: str) -> str:
#         instruct_header = self.config["data"]["instruct_header"]
#         input_header = self.config["data"]["input_header"]
#         output_header = self.config["data"]["output_header"]
#
#         instruction = data_point["instruction"]
#         input = data_point["input"]
#         output = data_point["output"]
#
#         prompt = f"{instruct_header}\n{instruction}\n\n{input_header}\n{input}\n\n{output_header}\n{output}"
#         return prompt
