import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import polars as pl
from openai import OpenAI
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm import tqdm

INDEXPATH = Path.home() / "data" / "index-pubmed"
RAW_PATH = INDEXPATH / "index.parquet"
OUT_PATH = INDEXPATH / "extractions.parquet"


MODEL = os.environ.get("MODEL", "")
BASE_URL = os.environ.get("BASE_URL")
KEY = os.environ.get("LITELLM")

SYSTEM_PROMPT = """Extract PICO elements from title and abstract of RCTs. There may be arbitrarily many per category. Use empty lists when none are present, do not guess.
Use standalone concepts as they would be used when searching for the study, they do not need to appear verbatim.

Return a single JSON object:
{
"population": [], 
"intervention": [], 
"comparator":[], 
"outcome": []
}
"""

extracted_cols = ["population", "intervention", "comparator", "outcome"]


def load_with_extraction():
    if OUT_PATH.exists():
        return pl.read_parquet(OUT_PATH)
    else:
        return pl.read_parquet(RAW_PATH).with_columns(
            pl.lit(None, dtype=pl.List(pl.Utf8)).alias(c) for c in extracted_cols
        )


class PICO(BaseModel):
    population: list[str] = Field(default_factory=list)
    intervention: list[str] = Field(default_factory=list)
    comparator: list[str] = Field(default_factory=list)
    outcome: list[str] = Field(default_factory=list)


client = OpenAI(api_key=KEY, base_url=BASE_URL)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=1, max=30), reraise=True)
def extract_single(pmid, title, abstract):
    user = f"{title}\n\n{abstract or ''}"
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    pico = PICO.model_validate_json(resp.choices[0].message.content or "{}")
    return {"pmid": pmid, **pico.model_dump()}


def extract_batch(df, batch_size=512, max_workers=16):
    pending = (
        df.filter(pl.col("population").is_null())
        .select("pmid", "title", "abstract")
        .head(batch_size)
    )
    result_rows = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        batch = {}
        for pmid, title, abstract in pending.iter_rows():
            batch[pool.submit(extract_single, pmid, title, abstract)] = pmid

        for f in as_completed(batch):
            try:
                result_rows.append(f.result())
            except Exception as e:
                print(f"encountered error for {batch[f]}: {e}")

    batch_result = pl.DataFrame(result_rows)
    return df.update(batch_result, on="pmid", how="left")


def num_pending(df):
    return len(
        df.filter(pl.col("population").is_null()).select("pmid", "title", "abstract")
    )


def write_safe(df):
    tmp_path = OUT_PATH.with_suffix(".parquet.tmp")
    df.write_parquet(tmp_path)
    os.replace(tmp_path, OUT_PATH)


if __name__ == "__main__":
    df = load_with_extraction()
    batch_size = 512
    max_workers = 128
    n_pending = num_pending(df)
    with tqdm(total=n_pending) as pbar:
        while n_pending > 0:
            n_pending = num_pending(df)
            df = extract_batch(df, batch_size, max_workers)
            pbar.update(batch_size)
            write_safe(df)
    print("Done!")
