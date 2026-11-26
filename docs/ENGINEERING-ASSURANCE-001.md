# Engineering assurance and controlled evolution — GOV-20261126-001

Status: requirements approved for design; implementation and qualification are separate. Public technical projection only. No existing scientific, rights, UX or publication gate is promoted.

## Existing references
- [ARCH-002](ARCH-002.md), [LIMITATIONS-001](LIMITATIONS-001.md), [ROADMAP](ROADMAP.md), [PRODUCT-FIRST-001](PRODUCT-FIRST-001.md), [UX-001](UX-001.md), [RESULT-001](RESULT-001.md), [PROSPECT-001](PROSPECT-001.md), [RUNBOOK-001](RUNBOOK-001.md), [METH-003](METH-003.md).
- [Machine-readable requirements](../governance/engineering_assurance_v1.json). IDs are additional engineering obligations, not replacements for the economic mechanisms or limitations.
- Baseline commit: e4f307e1edb6e190dfb097b6bcd602ffa2ce8f94. V3d is internal and publication remains blocked. No confidential strategy, client records, private archive, keys, or operational secrets belong in the public repository or its logs.

## Development cycle
Define acceptance and scope, implement on a dedicated branch, run deterministic checks, obtain an adversarial review distinct from implementation, fix and rerun, record evidence and limitations, obtain human release approval. Review complexity by cost and reversibility of an error. Model assistance is not independent scientific validation. Benchmark tools on accepted tasks, not output volume.

## Security and architecture
Use NIST SSDF and OWASP ASVS as candidate control baselines; verify actual settings. Least privilege, reviewed changes, pinned dependencies, secret and dependency scanning, secure logs, threat model, network isolation, backup/restore, incident response, access and publication tests. Do not expose a local prototype as a public service. Public artifacts must contain only approved content. Revisit intellectual property and source license boundaries privately. Prefer a modular monolith unless evidence justifies a different architecture. Keep UI, orchestration, deterministic analytical engines, semantic/data contracts, storage and governance distinct. Technology selection remains evidence-driven.

## Quality and scientific qualification
Separate numerical correctness, conceptual validity, empirical validity and decision usefulness. Test coupling, units, accounting identities, null shocks, conservation, instability and double counting. Use independent evidence, point-in-time backtests, uncertainty, competing hypotheses and explicit refusal where identification is absent. CI should cover static checks, unit/property/contract/integration/regression/negative tests, browser journeys, accessibility, security and recovery proportional to risk. Counts of successful tests are not a measure of empirical validation.

## Evolution
Version interfaces and data, use dependency inversion where useful, migration tests, compatibility checks, feature flags, rollback and architecture decision records. A change needs an impact assessment (science, data, security, maintenance, cost), acceptance criteria and measured value. Preserve historical evidence and reproducibility. Optional language-model interfaces must remain outside the calculation core, use typed and validated requests with independent authorization, no unrestricted data access, bounded resource use, provenance and safe failure. Treat external text as untrusted.

## Execution order
1. Reconcile a pinned complete inventory and existing obligations; audit access, evidence and release controls.
2. Qualify architecture, security and the minimum permanent QA controls; avoid speculative infrastructure.
3. Continue the existing V3e/V4 path only within rights and security gates; demonstrate value before expansion.
4. Reopen additional scientific/product capabilities by evidence and dependency, not by a checklist count.

All rows in the new register are OPEN for implementation/qualification. The register test only checks its structural contract; it cannot authorize release or prove security, completeness or empirical validity.
