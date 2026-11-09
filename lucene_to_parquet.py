from pathlib import Path

import lucene
import pyarrow as pa
import pyarrow.parquet as pq

lucene.initVM()
from java.nio.file import Paths
from org.apache.lucene.index import DirectoryReader, Term
from org.apache.lucene.search import (
    BooleanClause,
    BooleanQuery,
    IndexSearcher,
    Sort,
    TermQuery,
)
from org.apache.lucene.store import FSDirectory

INDEXPATH = Path.home() / "data" / "index-pubmed"


javapath = Paths.get(str(INDEXPATH / "index-lucene"))
reader = DirectoryReader.open(FSDirectory.open(javapath))
searcher = IndexSearcher(reader)

rct = TermQuery(Term("publication_type", "Randomized Controlled Trial"))


query = BooleanQuery.Builder().add(rct, BooleanClause.Occur.FILTER).build()

schema = pa.schema(
    [("pmid", pa.string()), ("title", pa.string()), ("abstract", pa.string())]
)
writer = pq.ParquetWriter(INDEXPATH / "index.parquet", schema, compression="zstd")

after = None
while True:
    hits = searcher.searchAfter(after, rct, 10000, Sort.INDEXORDER)
    if not hits.scoreDocs:
        break
    stored = searcher.storedFields()
    rows = [stored.document(sd.doc) for sd in hits.scoreDocs]
    writer.write_table(
        pa.table(
            {
                "pmid": [d.get("id") for d in rows],
                "title": [d.get("title") for d in rows],
                "abstract": [d.get("abstract") for d in rows],
            },
            schema=schema,
        )
    )
    after = hits.scoreDocs[-1]

writer.close()
