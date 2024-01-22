import argparse
from utils import read_config
from trainer import QLoraTrainer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", help="YAMLconfig file path")
    parser.add_argument("repo_id", help="HF repo for model to be uploaded")
    args = parser.parse_args()

    cfg = read_config(args.config_path)
    trainer = QLoraTrainer(cfg)

    trainer.load_base_model()
    trainer.train()
    trainer.merge_and_save()
    trainer.push_to_hub(args.repo_id)

    print(f"""{'='*20}
All operations completed!
          
{'='*20}""")
