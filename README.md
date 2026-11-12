# moratowers receipts

Evidence behind the audit of 53 research ideas described at [moratowers.dev](https://moratowers.dev/): fingerprints of pre-registered tests and frozen code, timestamped in Bitcoin, and the multiple-testing code from the audit's two independently written programs.

## Summary

- **What you can check here.** 20 registered texts and code files (11 test texts and 9 frozen code files) existed by Bitcoin block 971902. A 21st, an amendment, existed by block 972850. The audit's plan and its five approved addenda existed by block 972859. The two programs' multiple-testing procedures agree with each other, give the published result on the 15 p-values of Benjamini and Hochberg's 1995 worked example, and match statsmodels for BH and BY.
- **What you cannot check here.** The registered texts, the per-idea p-values and the audit's result. Those stay private for now (see below).
- **Who did the work.** AI agents wrote the code, the registry and this page, and different agents checked each step. Agents proposed the rules. I picked from their options, approved the plan and made the rulings.

## Check it

Needs Python 3.11 or later.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -c constraints.txt
.venv/bin/python -m pytest -q
```

39 tests. 12 run the multiple-testing procedures. 27 check the registry: each of the 24 OpenTimestamps proofs matches the file it stamps and commits to the merkle root of its block, and each digest file appears in a stamped manifest. The 9 merkle roots are listed in `tests/test_registry.py`, read from blockstream.info. Check them on any block explorer.

To check a stamp without trusting the tests:

```bash
.venv/bin/python registry/verify_ots_roots.py registry/manifest.txt.ots
```

It prints each block height and merkle root the proof commits to. Compare each root with a block explorer, for example [block 971902](https://blockstream.info/block-height/971902). With a Bitcoin node and the OpenTimestamps client (`pip install opentimestamps-client`), `ots verify registry/manifest.txt.ots` does the whole check.

## What each stamp proves

A stamp proves that a file with that exact hash existed by the time of its block. A one-byte change gives a different hash. A stamp does not show who wrote the file, or what it says until it is revealed.

Each time below is the block's header time. A miner sets it, and it can differ from the true time by an hour or more, so read it as the block, not the second.

| Entries | Block (header time, UTC) | What the stamp shows |
|---|---|---|
| 12 entries whose registered look is after the stamp: test entries 01, 05 and 06, frozen code 01 to 08, and the amendment 02a | 971902 (2026-10-17 20:02:55); 02a: 972850 (2026-10-24 00:13:42) | The text existed before its look. These are the strong cases. For some, data had begun to arrive before the stamp. The stamp shows the text came before the look, not before the data. That nobody read outcomes early rests on the project's own records. |
| 6 entries whose look came before the stamp: test entries 02, 07, 09, 10 and 11, frozen code 09 | 971902 (2026-10-17 20:02:55) | Only that the text has not changed since that block. Not that it came before its data. |
| 3 entries with no single look date: test entries 03 (none scheduled), 04 (weekly from 2026-10-07) and 08 (event-driven) | 971902 (2026-10-17 20:02:55) | For 03 and 08, that the text existed by the stamp; whether a look came earlier is not shown. Weekly looks for 04 began before the stamp. |
| The audit plan and its five approved addenda (`manifest_plan_2026-10-24.txt`) | 972859 (2026-10-24 02:04:00) | The plan existed by then. The audit's first build attempt started on 2026-10-22 at 14:09:46 UTC, so this stamp alone does not show the plan came first. I approved the plan, and it was frozen on 2026-10-17 at 20:36:10 UTC in a private git repository. That record is private, and git times are self-reported, so it would not be proof either. |

The registry holds 20 registered tests and frozen code files, picked on 2026-10-17. Six had their look before that day (see the table above). `registry/manifest.txt` gives each entry's sha256, number and look date as of that day. Since then some looks have run and some have moved. The digest files in `registry/digests/` hold one sha256 each and carry their own proofs.

When a text is revealed, `shasum -a 256 <file>` must print the hash on its line in `registry/manifest.txt`. File names here are not stamped. The manifest's labels for test entries are a little longer than the file names here (`test_NN`).

Frozen code 02 was changed once before its look, by a fix approved on 2026-10-22. The 2026-10-17 entry stays as the record of what was frozen then. Entry 02a is what the look ran, and `manifest_amendment_2026-10-24.txt` records it.

The plan's sha256 is `3b5cf4df90921400c0ca26ccb930912a63564761d5142939a0d7f93a0432e333`, and the result table's is `c199d65300c8852723927e3b55cd7d4e94fc03ccbbb0bca3d9c34e5d5e097226`. The [ledger page](https://moratowers.dev/ledger/) shows both. Both files are private.

## The multiple-testing code

`fdr/builder_impl.py` and `fdr/checker_impl.py` are copied verbatim from the audit's builder and its independent checker. Each file's header gives the source file's sha256 (the one recorded with the audit's final run) and the line ranges copied.

The checker's author worked from the frozen plan's text, its approved addenda and the rulings. By the author's own record it never opened the builder's code, and the checker blocks that file at run time. The checker failed its first two runs and passed its third, and both programs were fixed between runs. The functions copied here did not change in any fix. Each block is unchanged since its program's first commit (checker 2026-10-17 21:19 UTC, builder 23:21 UTC), before the first build. That git record is private.

Each file holds Benjamini and Hochberg (BH), Benjamini and Yekutieli (BY), a two-level hierarchical procedure (Simes per family, then BH; Yekutieli 2008) and Storey's estimate of the share of true nulls. BH at q = 0.10 was the audit's primary test. BY and the hierarchical procedure were sensitivity checks, and Storey's estimate was reported alongside.

The two copies differ in small ways. The checker takes a total count m larger than the number of p-values, which treats untested entries as p = 1. The builder pads the vector instead. A test checks that both readings give the same BH answer.

What the tests show. On 2,000 random p-value vectors at q = 0.05 and 0.10, both copies give the same rejections and the same adjusted p-values (within 1e-12), and match statsmodels' `fdr_bh` and `fdr_by`. On the 1995 worked example they give the paper's 4 rejections at q = 0.05. The other expected values (adjusted p-values, q = 0.10, BY, hierarchical and Storey) were computed for the tests, and the BH and BY ones match statsmodels. Two tests pin the exact boundaries: a p-value equal to its BH bound is rejected, and Storey counts only p above lambda.

## What this does not show

- That any idea beat luck. None passes the audit's primary luck correction (BH at q = 0.10; [ledger page](https://moratowers.dev/ledger/)). One sensitivity check, which admits evidence the audit ruled invalid, rejects one idea; the audit does not count it.
- What the registered texts say. Until a text is revealed, its hash proves only that some fixed text existed.
- That the six earlier entries came before their data.
- That the registry is complete. It holds 20 entries picked on 2026-10-17, not one per idea. The agent that built it recorded two gaps: one idea had no registered test text, and one registered holdout was left out because it sat in a file of unrelated notes.
- That no test is missing. The stamped manifest fixes its 20 entries: none can be slipped in or taken out. A later manifest can still add entries, as the one for 02a did, and a list kept elsewhere cannot be ruled out.
- That every text will be revealed. I decide when each text is revealed, and some may never be. Weigh a partial reveal with that in mind.
- That the rulings which completed the plan came before the data. The plan's freeze record counts a file of my rulings as part of the plan. That file is not stamped, and some rulings came after the first build attempt.
- The audit's result. The per-idea p-values are private, so the result cannot be recomputed from this repository.

## What stays private

The registered texts, until their looks and until the terms of the data they used allow release. Some may stay private for good. Also private: the per-idea numbers, the audit's plan and result table, and the research repository.

## Who did what

AI agents wrote the audit's plan text, both programs, the registry and this repository, and different agents reviewed each step. Agents proposed the rules; I picked from their options, approved the plan and its addenda, and made the rulings recorded at each step.

## Licence

MIT. See `LICENSE`.
