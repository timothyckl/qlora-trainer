import argparse
from utils import read_config
from Trainer import QLoraTrainer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", help="YAMLconfig file path")
    args = parser.parse_args()

    cfg = read_config(args.config_path)
    trainer = QLoraTrainer(cfg)

    trainer.load_base_model()
    trainer.train()
    trainer.merge_and_save()