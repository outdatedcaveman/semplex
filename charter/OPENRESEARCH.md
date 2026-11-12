# Working with OpenResearch

[OpenResearch](https://github.com/alphaXiv/OpenResearch) (alphaXiv, MIT) is a local-first harness for research agents. It stores every experiment as a node in a tree, each node a git branch with one fixed run command, in a local database. It also gives agents literature retrieval over alphaXiv, OpenAlex, bioRxiv and PubMed.

This repository is set up so it can be imported as an OpenResearch project with no changes (`orx up` → import this checkout). Its conventions are also adopted here for work done without the tool. The modules this file relies on are vendored, unmodified, in `third_party/openresearch/` (commit `711f7fc`).

## 1. The run contract

| OpenResearch rule | How semplex meets it |
|---|---|
| One run command, identical on every node, no environment variables | `python -m experiments.orx_run`. Set it once: `orx project edit <id> --run-command 'python -m experiments.orx_run'` |
| Only committed code/config differs between nodes | What a node runs is the committed file `experiments/orx_node.json`: spike module, steps, report and result paths |
| The log carries effective configuration, final metrics and a compact summary | `orx_run` prints the node file plus commit hash, every step's output and exit code, then a compact dump of the spike's result JSON |
| A node is provisional until a run answers it, then frozen | Our pre-registration rule, enforced: `orx_run` refuses to run a spike whose report has no pre-registration status line. Once a report has verdicts, its code is not edited; a follow-up is a new spike, i.e. a child node |

## 2. Our rules, in OpenResearch terms

- **Pre-registration = the node's description.** Hypotheses and kill criteria are committed in `SPIKE_NN_REPORT.md` before any run. In OpenResearch they go into the node description, e.g. `orx exp desc <id> --stdin < experiments/SPIKE_NN_REPORT.md`.
- **Frozen nodes = no retroactive edits.** A broken hypothesis stays broken. Repairs before the first answer are allowed (OpenResearch's "provisional" state). Spike 21's first fit used a stalling optimizer; we fixed it before any verdict and kept both values. That is a repair, not a rewrite.
- **Stacked bushes, not a flat fan.** Each spike names the earlier spike it builds on ("Follows:"). The resulting tree is in `experiments/TREE.md`. A round fans across co-equal options of one decision, e.g. Spike 24's six activations. The next round descends onto what that round established: Spike 27 descends from Spike 24's finding F3.
- **Stop rule.** OpenResearch stops a branch after about three consecutive failed or regressed runs. Our analogue is a conjecture refuted twice in a row (C9, C10), at which point the line is closed and re-derived from the data, as with C11 → C12.

## 3. Results and reports

- `orx-results`: never report from status or memory. Read the logged result, choose one representation per comparison (table *or* graph, not both), and state the limitations. Our reports already follow this. New reports should keep one table per comparison and put headline numbers in prose.
- `orx-reports`: durable outputs live under `experiments/results/` (data) and `experiments/SPIKE_NN_REPORT.md` (reports). Reproduction scripts sit beside what they produce.
- `orx-figures`: build figures at their final printed size, from real data, with honest uncertainty, and keep the plotting script beside the figure.
- `orx-paper`: the eventual paper is a real `paper.tex` at the repository root, not an outline.

## 4. Literature

The `orx-lit-review` workflow is the default for every scientific claim:

- **Retrieve.** Start with alphaXiv keyword and embedding search. Add OpenAlex for journal, conference and citation coverage, and PubMed or bioRxiv when the topic is biomedical. Use web search only when these connectors return nothing useful. Scale follow-up rounds to difficulty: 0 rounds for difficulty 1–3, 1 for 4–7, 2 for 8–10.
- **Read before you cite.** Read a paper before using it as claim-level support; snippets are not evidence. Quote complete sentences, and link to `https://www.alphaxiv.org/pdf/<id>?page=N`.
- **Record each source.** Every source enters `charter/LITERATURE_REVIEW.md` §5 with what was read (full text, report only, abstract) and what it changes here.

Inside OpenResearch these are `orx discover keyword|embedding|openalex|biorxiv|pubmed "<query>"` and `orx paper <id>`. Outside it, the same sources can be reached through the alphaXiv MCP tools or the OpenAlex and PubMed APIs.

## 5. Privacy

OpenResearch sends coarse, opt-out usage analytics and agent feedback reports. Before using it on this project, turn them off with `orx telemetry off` (or `ORX_TELEMETRY_ENV=off`). Publish a project (`orx project share --publish`) only on explicit request.
