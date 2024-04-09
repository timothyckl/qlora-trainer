import torch

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
    DataCollatorForLanguageModeling,
    # LlamaForCausalLM,
    # LlamaTokenizer, 
    # Trainer,
    TrainingArguments
)

from trl import SFTTrainer

class QLoraTrainer:
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
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            quantization_config=bnb_config, 
            device_map={"": 0}
        )
        model.config.use_cache = False

        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        tokenizer.pad_token = tokenizer.eos_token

        model = prepare_model_for_kbit_training(model)

        self.tokenizer = tokenizer
        self.base_model = model

    # def load_adapter_model(self, adapter_path: str):
    #     """Load pre-trained lora adapter"""
    #     self.adapter_model = PeftModel.from_pretrained(self.base_model, adapter_path)

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
        
        trainable_pct = (trainable_params / all_param) * 100
        
        print(
            f"trainable params: {trainable_params} ({trainable_pct:.2%}) || all params: {all_param}" 
        )

    def _setup_data_processor(self):
        dset_type = self.config["data"]["type"]
        if dset_type == "alpaca":
            from processors.GPT4AlpacaProcessor import GPT4AlpacaProcessor as Processor
            self.data_processor = Processor(self.config, self.tokenizer)
        else:
            raise ValueError("Dataset type not specified in config.data.type")

    def train(self):
        # Set up lora config or load pre-trained adapter
        # if self.adapter_model is None:
        lora_config = self.config["lora"]
        peft_config = LoraConfig(
            r=lora_config["r"],
            lora_alpha=lora_config["lora_alpha"],
            target_modules=lora_config["target_modules"],
            lora_dropout=lora_config["lora_dropout"],
            bias=lora_config["bias"],
            task_type=lora_config["task_type"],
        )
        model = get_peft_model(self.base_model, peft_config)
        # else:
        #     model = self.adapter_model
        self._print_trainable_parameters(model)

        print("Preprocessing dataset...")
        self._setup_data_processor()
        data = self.data_processor.get_data()

        print("Training started...")
        config = self.config["trainer"]
        
        train_args = TrainingArguments(
            per_device_train_batch_size=config["batch_size"],
            gradient_accumulation_steps=config["gradient_accumulation_steps"],
            warmup_steps=config["warmup_steps"],
            num_train_epochs=config["num_train_epochs"],
            learning_rate=config["learning_rate"],
            fp16=True,
            logging_steps=config["logging_steps"],
            output_dir=self.config["trainer_output_dir"],
            report_to="tensorboard",
            optim="adamw_torch",
            save_strategy="steps",
            group_by_length=True,
            disable_tqdm=True
        )

        trainer = SFTTrainer(
            model=model,
            train_dataset=data['train'],
            peft_config=peft_config,
            tokenizer=self.tokenizer,
            args=train_args
        )

        trainer.train()

        model_save_path = (
            f"{self.config['model_output_dir']}/{self.config['model_name']}_adapter"
        )

        trainer.save_model(model_save_path)
        self.adapter_model = model
        print(f"Training complete, adapter model saved in {model_save_path}")

    def merge_and_save(self):
        """Merge base model and adapter, save to disk"""
        print("Merging & saving final model...")

        # Cannot merge when base model loaded in 8-bit/4-bit mode, so load separately
        model_id = self.config["base_model"]
        base_model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            device_map="cpu"
        )

        adapter_save_path = (
            f"{self.config['model_output_dir']}/{self.config['model_name']}_adapter"
        )
        model = PeftModel.from_pretrained(base_model, adapter_save_path)

        self.merged_model = (
            model.merge_and_unload()
        )  # note it's on CPU, don't run inference on it

        model_save_path = (
            f"{self.config['model_output_dir']}/{self.config['model_name']}"
        )
        self.merged_model.save_pretrained(model_save_path)
        self.tokenizer.save_pretrained(model_save_path)

    def push_to_hub(self, repo_id):
        """Push merged model to HuggingFace Hub"""
        print("Uploading to HF...")
        self.merged_model.push_to_hub(repo_id)
        self.tokenizer.push_to_hub(repo_id)
