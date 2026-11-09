import polars as pl
from datasets import load_dataset
from pathlib import Path

INDEXPATH = Path.home() / "data" / "index-pubmed"

df = pl.read_parquet(INDEXPATH / "index.parquet")
df.sort(by="abstract")

data = load_dataset("parquet", data_files=str(INDEXPATH / "index.parquet"))
breakpoint()
