"""Evaluate NliVerifiedCache on the hand-written cache seed set.

All 30 seed questions are stored with their pipeline answers; each paraphrase
(should reuse its own seed) and near-miss (must not reuse) is then looked up.
Run: python -m adaptive_retrieval.cache_eval [seed_file]
"""

import re
import sys
import time
from pathlib import Path

from .cache import NliVerifiedCache
from .embedding import LocalEmbedder
from .models import Answer
from .nli import NliJudge
from .paths import DATA_DIR

DEFAULT_SEEDS = DATA_DIR / "cache_seeds/cache_seed_questions_loaders_draft.txt"


def load_seeds(path: Path) -> list[dict]:
    seeds = []
    for block in path.read_text().split("=" * 100)[1:]:
        head = re.search(r"SEED (\d+) \| (\S+) \| split: (\w+)", block)
        if not head:
            continue
        def field(name):
            m = re.search(rf"^{name}:\n(.*?)(?=^[A-Z_ ]+:)", block, re.S | re.M)
            return " ".join(m.group(1).split()) if m else ""
        def line(name):
            m = re.search(rf"^{name}: *(.*)$", block, re.M)
            return m.group(1).strip() if m else ""
        verdict = line("VERDICT")
        seeds.append(dict(n=int(head.group(1)), split=head.group(3), question=field("QUESTION"),
                          answer=field("CACHED ANSWER"), para=line("PARAPHRASE"),
                          near=line("NEAR_MISS"),
                          answer_ok=verdict.startswith(("CORRECT", "MOSTLY CORRECT"))))
    return seeds


def tally(rows, threshold, splits):
    """Replay recorded candidate scores at another NLI threshold."""
    para = ok = near = wrong = n_para = n_near = 0
    for r in rows:
        if r["split"] not in splits:
            continue
        hit = next((c["seed"] for c in r["candidates"] if c["entailment"] >= threshold), None)
        if r["kind"] == "para":
            n_para += 1
            para += hit == r["seed"]
            ok += hit == r["seed"] and r["answer_ok"]
            wrong += hit is not None and hit != r["seed"]
        else:
            n_near += 1
            near += hit is not None
    return (f"paraphrases reused {para:2d}/{n_para}  correct answer {ok:2d}/{n_para}  "
            f"near-misses reused {near:2d}/{n_near}  wrong seed {wrong}")


def main(argv=None):
    path = Path((argv or sys.argv[1:] or [DEFAULT_SEEDS])[0])
    seeds = load_seeds(path)
    by_question = {s["question"]: s for s in seeds}
    cache = NliVerifiedCache(LocalEmbedder(), NliJudge(threshold=0.51))
    cache.embedder.warmup()
    cache.judge.load()
    for s in seeds:
        cache.store(s["question"], Answer(s["answer"], ()), "eval", "seed-v1")
    print(f"Stored {len(cache)} seeds from {path.name}")

    rows, timings = [], []
    for s in seeds:
        for kind in ("para", "near"):
            if not s[kind]:
                continue
            cache.nli_threshold = 0.999  # score every candidate once; thresholds replayed below
            cache.lookup(s[kind], "eval", "seed-v1")
            cands = [dict(seed=by_question[c["question"]]["n"], cosine=c["cosine"],
                          entailment=c["entailment"]) for c in cache.last_decision["candidates"]]
            cache.nli_threshold = 0.5
            start = time.perf_counter()
            hit = cache.lookup(s[kind], "eval", "seed-v1")
            timings.append((time.perf_counter() - start) * 1000)
            rows.append(dict(seed=s["n"], split=s["split"], kind=kind, answer_ok=s["answer_ok"],
                             candidates=cands, hit=hit is not None))
            own = next((c for c in cands if c["seed"] == s["n"]), None)
            print(f"seed {s['n']:2d} {s['split']:3s} {kind:4s} reuse={'yes' if hit else 'no ':3s} "
                  + (f"own cos={own['cosine']:.3f} nli={own['entailment']:.3f}" if own else "own seed not a candidate"))

    print("\nNLI threshold sweep (all splits):")
    for t in (0.1, 0.3, 0.5, 0.7, 0.9):
        print(f"  nli>={t:.1f}  {tally(rows, t, {'dev', 'val'})}")
    print("\nDefault nli>=0.5 by split:")
    for split in ("dev", "val"):
        print(f"  {split}: {tally(rows, 0.5, {split})}")
    timings.sort()
    print(f"\nLookup latency ms: median {timings[len(timings) // 2]:.0f}, "
          f"max {timings[-1]:.0f} (embedding + up to {cache.max_candidates}x2 NLI passes)")


if __name__ == "__main__":
    main()
