import torch
import transformers
from peft import (
    LoraConfig, 
    PeftModel, 
    get_peft_model,
    prepare_model_for_kbit_training
)
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer,
    BitsAndBytesConfig, 
    LlamaForCausalLM, 
    LlamaTokenizer
)

class QLoraTrainer():
    def __init__(self, config: dict) -> None:
        self.config = config
        self.tokenizer = None
        self.base_model = None
        self.adapter_model = None
        self.merged_model = None
        self.data_processor = None

    def load_base_model(self):
        print("Loading base model...")

        model_id = self.config["base_model"]

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        if "model_family" in self.config and self.config["model_family"] == "llama":
            tokenizer = LlamaTokenizer.from_pretrained(model_id)
            model = LlamaForCausalLM.from_pretrained(model_id, quantization_config=bnb_config, device_map={"":0})
        else:
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=bnb_config, device_map={"":0})

        if not tokenizer.pad_token:
            # Add padding token if missing, e.g. for llama tokenizer
            #tokenizer.pad_token = tokenizer.eos_token  # https://github.com/huggingface/transformers/issues/22794
            tokenizer.add_special_tokens({'pad_token': '[PAD]'})

        model.gradient_checkpointing_enable()
        model = prepare_model_for_kbit_training(model)

        self.tokenizer = tokenizer
        self.base_model = model

    def load_adapter_model(self, adapter_path: str):
        """ Load pre-trained lora adapter """
        self.adapter_model = PeftModel.from_pretrained(self.base_model, adapter_path)

    def _print_trainable_parameters(self, model):
        """
        Prints the number of trainable parameters in the model.
        """
        trainable_params = 0
        all_param = 0
        for _, param in model.named_parameters():
            all_param += param.numel()
            if param.requires_grad:
                trainable_params += param.numel()
        print(
            f"trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param}"
        )

    def _setup_data_processor(self):
        dset_type = self.config["data"]["type"]
        if dset_type == "ultrachat":
            from processors.UCProcessor import UCProcessor
            self.data_processor = UCProcessor(self.config, self.tokenizer)
        elif dset_type == "vicuna":
            from processors.WVUProcessor import WVUProcessor
            self.data_processor = WVUProcessor(self.config, self.tokenizer)
        elif dset_type == "orca":
            from processors.OOProcessor import OOProcessor
            self.data_processor = OOProcessor(self.config, self.tokenizer)
        # add more processors for diff datasets here
        else:
            raise ValueError("Dataset type not specified in config.data.type")

    def train(self):
        # Set up lora config or load pre-trained adapter
        if self.adapter_model is None:
            config_dict = self.config["lora"]
            config = LoraConfig(
                r=config_dict["r"],
                lora_alpha=config_dict["lora_alpha"],
                target_modules=config_dict["target_modules"],
                lora_dropout=config_dict["lora_dropout"],
                bias=config_dict["bias"],
                task_type=config_dict["task_type"],
            )
            model = get_peft_model(self.base_model, config)
        else:
            model = self.adapter_model
        self._print_trainable_parameters(model)

        print("Preprocessing dataset...")
        self._setup_data_processor()
        data = self.data_processor.get_data()

        print("Training started...")
        config_dict = self.config["trainer"]
        trainer = transformers.Trainer(
            model=model,
            train_dataset=data["train"],
            args=transformers.TrainingArguments(
                per_device_train_batch_size=config_dict["batch_size"],
                gradient_accumulation_steps=config_dict["gradient_accumulation_steps"],
                warmup_steps=config_dict["warmup_steps"],
                num_train_epochs=config_dict["num_train_epochs"],
                learning_rate=config_dict["learning_rate"],
                fp16=True,
                logging_steps=config_dict["logging_steps"],
                output_dir=self.config["trainer_output_dir"],
                report_to="tensorboard",
                #optim="adamw"
            ),
            data_collator=transformers.DataCollatorForLanguageModeling(self.tokenizer, mlm=False),
        )

        model.config.use_cache = False  # silence the warnings. Please re-enable for inference!
        trainer.train()

        model_save_path = f"{self.config['model_output_dir']}/{self.config['model_name']}_adapter"
        trainer.save_model(model_save_path)
        self.adapter_model = model
        print(f"Training complete, adapter model saved in {model_save_path}")

    def merge_and_save(self):
        """ Merge base model and adapter, save to disk """
        print("Merging & saving final model...")

        # Cannot merge when base model loaded in 8-bit/4-bit mode, so load separately
        model_id = self.config["base_model"]
        if "model_family" in self.config and self.config["model_family"] == "llama":
            base_model = LlamaForCausalLM.from_pretrained(model_id, device_map="cpu")
        else:
            base_model = AutoModelForCausalLM.from_pretrained(model_id, device_map="cpu")

        adapter_save_path = f"{self.config['model_output_dir']}/{self.config['model_name']}_adapter"
        model = PeftModel.from_pretrained(base_model, adapter_save_path)

        self.merged_model = model.merge_and_unload()  # note it's on CPU, don't run inference on it

        model_save_path = f"{self.config['model_output_dir']}/{self.config['model_name']}"
        self.merged_model.save_pretrained(model_save_path)
        self.tokenizer.save_pretrained(model_save_path)

    def push_to_hub(self, repo_id):
        """ Push merged model to HuggingFace Hub """
        print("Uploading to HF...")
        self.merged_model.push_to_hub(repo_id)
        self.tokenizer.push_to_hub(repo_id)
