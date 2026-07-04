from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    dataset_api_url: str = os.getenv(
        "DATASET_API_URL",
        "https://www.data.gouv.fr/api/1/datasets/donnees-des-elections-agregees/"
    )
    data_dir: str = os.getenv("DATA_DIR", "./data")
