# Cost-Aware Adaptive Retrieval for Enterprise Support

Midterm preparation: see the [reproduced results and experiment protocol](docs/MIDTERM.md).

Team 13 is exploring whether local retrieval can find useful evidence for
enterprise support questions. You can try three command-line flows: a tiny
synthetic keyword demo, interactive or single-query vector search over a
checked-in, 100-question evaluation subset, and a retrieval evaluation that
scores that search on every labeled question (Hit@5 and MRR). Vector search
prints ranked source passages, **not a generated answer**. Answer generation,
adaptive routing, reranking, and answer-quality metrics are still planned work.

## Folder preview

```text
adaptive-enterprise-retrieval/
├── README.md
├── requirements.txt
├── src/
│   ├── runner.py
│   └── adaptive_retrieval/
├── data/
│   ├── sample/                  # checked-in synthetic demo
│   ├── subset_documents/       # checked-in 100-question subset documents
│   ├── all_documents/          # download and extract the full dataset here
│   │   ├── questions.jsonl     # download separately from the release
│   │   ├── confluence/
│   │   ├── gmail/
│   │   └── ...                 # other source folders
│   └── processed/              # generated locally by the commands below
├── results/                    # retrieval evaluation runs, one folder per run
└── docs/
```

**Full-dataset destination: `data/all_documents/` inside this repository.**

## Before you start

- Install [Git](https://git-scm.com/downloads) and Python 3.11 or newer. Python
  3.11 or 3.12 is recommended for the local embedding dependencies.
- Open Terminal on macOS or PowerShell on Windows.
- The commands below run from the repository root. If you already have a clone,
  skip the `git clone` line and change into that directory.
- The synthetic demo and tests use only Python's standard library. The vector
  search needs the packages in [`requirements.txt`](requirements.txt). Installing
  them and downloading the MiniLM model requires internet access on the first run.
  No API key is needed.

## Download the full dataset

Get [`all_documents.zip` and `questions.jsonl` from EnterpriseRAG-Bench
v1.0.0](https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/tag/v1.0.0).
The archive is about 1.17 GB. **Extract its contents into
`data/all_documents/`**, then put the separately downloaded `questions.jsonl`
directly in that same folder. Do not leave an extra nested
`all_documents/all_documents/` directory.

After cloning the project and changing to its root directory, use these commands
to download and extract the release files on macOS:

```bash
mkdir -p data/all_documents
curl -fL https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/v1.0.0/all_documents.zip -o data/all_documents.zip
unzip -q data/all_documents.zip -d data/all_documents
curl -fL https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/v1.0.0/questions.jsonl -o data/all_documents/questions.jsonl
ls data/all_documents/questions.jsonl data/all_documents/confluence
```

Or use PowerShell on Windows:

```powershell
New-Item -ItemType Directory -Force -Path .\data\all_documents | Out-Null
Invoke-WebRequest -Uri 'https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/v1.0.0/all_documents.zip' -OutFile '.\data\all_documents.zip'
Expand-Archive -LiteralPath '.\data\all_documents.zip' -DestinationPath '.\data\all_documents'
Invoke-WebRequest -Uri 'https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/v1.0.0/questions.jsonl' -OutFile '.\data\all_documents\questions.jsonl'
Test-Path .\data\all_documents\questions.jsonl
Test-Path .\data\all_documents\confluence
```

Both PowerShell checks should print `True`. The top level of
**`data/all_documents/`** should contain `questions.jsonl` and source folders
such as `confluence/`, `gmail/`, and `slack/`. This full dataset is required for
`build-subset`. The step-by-step demo below can use the smaller
`data/subset_documents/` files already committed to Git. Keep the downloaded
dataset local; Git ignores `data/all_documents/` and `data/all_documents.zip`.

## macOS: run it step by step

```bash
# 1. Get the project and check Python.
git clone https://github.com/AdithNG/adaptive-enterprise-retrieval.git
cd adaptive-enterprise-retrieval
python3 --version

# 2. Create a virtual environment and install the vector-search dependency.
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 3. Try the instant, synthetic keyword demo.
.venv/bin/python src/runner.py demo "reset password"

# 4. Prepare and validate the checked-in 100-question document subset.
.venv/bin/python src/runner.py prepare-subset
.venv/bin/python src/runner.py check-subset

# 5. Chunk documents, build the local MiniLM index, and search it.
.venv/bin/python src/runner.py chunk
.venv/bin/python src/runner.py embed
.venv/bin/python src/runner.py search "Medicore operational runbook turnaround timeline"
.venv/bin/python src/runner.py interactive

# 6. Score retrieval on all 100 questions and save the results.
.venv/bin/python src/runner.py evaluate

# 7. Run the tests.
.venv/bin/python -m unittest discover -s src/tests -v
```

## Windows: run it step by step

Run these commands in **PowerShell**:

```powershell
# 1. Get the project and check Python.
git clone https://github.com/AdithNG/adaptive-enterprise-retrieval.git
cd adaptive-enterprise-retrieval
py -3 --version

# 2. Create a virtual environment and install the vector-search dependency.
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Try the instant, synthetic keyword demo.
.\.venv\Scripts\python.exe src/runner.py demo "reset password"

# 4. Prepare and validate the checked-in 100-question document subset.
.\.venv\Scripts\python.exe src/runner.py prepare-subset
.\.venv\Scripts\python.exe src/runner.py check-subset

# 5. Chunk documents, build the local MiniLM index, and search it.
.\.venv\Scripts\python.exe src/runner.py chunk
.\.venv\Scripts\python.exe src/runner.py embed
.\.venv\Scripts\python.exe src/runner.py search "Medicore operational runbook turnaround timeline"
.\.venv\Scripts\python.exe src/runner.py interactive

# 6. Score retrieval on all 100 questions and save the results.
.\.venv\Scripts\python.exe src/runner.py evaluate

# 7. Run the tests.
.\.venv\Scripts\python.exe -m unittest discover -s src/tests -v
```

These commands use the virtual environment's Python directly, so you do not
need to activate it or change PowerShell's script execution policy. If `py -3`
selects Python older than 3.11, install a newer Python and select it explicitly
(for example, replace `py -3` with `py -3.12`).

## Interactive terminal demo

After building the index, start `src/runner.py interactive` with your virtual
environment's Python (as shown above). Ask as many questions as you like at the
`Question>` prompt. The index stays in memory, and MiniLM loads on the first
question and is reused. Each search displays the full retrieved passages with
similarity scores, document IDs, source paths, and original character offsets.

```text
Question> Medicore operational runbook turnaround timeline
...retrieved source passages...
Question> /doc 1
...full source document for the first result...
Question> /top 5
Question> What caused the token accounting mismatch?
Question> /quit
```

Use `/help` for commands, `/doc N` to read a result's original document, and
`/top N` to change the number of passages shown. `/quit`, `exit`, Ctrl-D, and
Ctrl-C end the session. The `chat` command is an alias for `interactive`.
Results quote source text; answer generation and fact verification are still
planned work. Use `--index`, `--corpus`, or `--top-k` to override defaults.

## What to expect

- `demo` prints a matching synthetic password document immediately. You can
  replace `"reset password"` with another query. It does not use the evaluation
  corpus or an embedding model.
- `prepare-subset` creates `data/processed/subset_questions.jsonl` and
  `data/processed/subset_corpus.jsonl` from the files committed under
  `data/subset_documents/`. `check-subset` should finish with
  `OK: every referenced document is present`.
- `chunk` writes source-traceable passages to `data/processed/chunks.jsonl`.
  `embed` downloads `sentence-transformers/all-MiniLM-L6-v2` on first use and
  writes `data/processed/minilm_index.jsonl`; this step can take several minutes.
- `search` prints the top passages with a similarity score, source path, and
  character offsets. Try your own question by replacing the quoted text. It
  returns evidence for inspection, not a final answer.
- `interactive` keeps a terminal session open for repeated searches and full
  source-document inspection.
- `evaluate` searches every question and checks where its correct document
  (`expected_doc_ids`) ranks. Chunks are collapsed to documents, ranked by each
  document's best chunk. It prints two scores over the 90 questions that have a
  correct document: **Hit@5**, the share with the correct document in the top 5,
  and **MRR**, the mean of 1 / rank. The current baseline is Hit@5 = 0.844 and
  MRR = 0.670. The 10 `info_not_found` questions are saved but not scored. Each
  run writes `per_question.jsonl` (rank, scores, and top 5 documents per
  question) and `summary.json` (metrics, git commit, and index settings) to
  `results/retrieval_eval_<timestamp>/`. Use `--questions`, `--index`, or
  `--out-dir` to override defaults.
- Generated files in `data/processed/` are ignored by Git. You do not need the
  much larger `data/all_documents/` corpus for this walkthrough.

If you only want the synthetic demo or tests, run those commands with Python
3.11+ directly and skip the virtual environment and dependency install. If a
search says the corpus changed, rerun `chunk` and `embed` after `prepare-subset`.

## Project files

| Path | Purpose |
| --- | --- |
| `src/runner.py` | Entry point for demo, preparation, indexing, search, and evaluation |
| `src/adaptive_retrieval/` | Corpus loading, chunking, embedding, and retrieval code |
| `src/tests/` | Python unit tests |
| `data/sample/` | Tiny synthetic demo data |
| `data/subset_documents/` | Committed documents and 100-question file used above |
| `data/processed/` | Generated local corpus, chunks, model cache, and index |
| `results/` | Saved retrieval evaluation runs from `evaluate` |
| `docs/ARCHITECTURE.md` | Diagram and explanation of the retrieval flow |
| `docs/PLAN.md` | Project milestones and planned evaluation |

If you have the separate full corpus under `data/all_documents/`, you can run
`src/runner.py build-subset` with the Python executable used above to
regenerate the 100-question selection and hard negatives from scratch. That
command scans the full corpus and takes longer;
it is not needed to try the project. The current 100-question subset is for
development and does not yet meet the plan's approximately 300-question target.
