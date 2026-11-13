# AI risk assessment

## Why a risk method matters
Clause 6 of ISO/IEC 42001 requires a documented AI risk assessment process that gives consistent, repeatable results. Two people assessing the same AI system with the method should reach similar scores. The method should be based on ISO/IEC 23894 and approved by the AI governance committee.

## Risk sources to consider
Common AI risk sources are bias in training data, lack of transparency or explainability, model drift after deployment, security attacks such as data poisoning and prompt injection, the level of automation and human oversight, third-party and supply-chain issues, misuse outside the intended purpose, and changes in law or regulation.

## Scoring likelihood and impact
Score likelihood from 1 (rare) to 5 (almost certain) and impact from 1 (negligible) to 5 (severe, affecting rights, safety or livelihoods at scale). Risk score = likelihood × impact. Typical bands: 1–6 is low (accept), 8–12 is medium (treat, or accept with committee sign-off), and 15–25 is high (must be treated, and any residual risk needs executive sign-off).

## Treatment options
For each risk choose one option and record the reason. Reduce: add controls. Avoid: do not deploy, or change the use. Transfer: use contracts or insurance, while still owning the risk. Accept: only if the risk is within appetite, with named sign-off. Write a risk treatment plan with actions, owners and dates.

## Risk register fields
A practical AI risk register records: risk ID, AI system, risk description, risk source, likelihood, impact, score, treatment decision, Annex A controls applied, owner and residual score. Example: a churn model under-scores customers from smaller regions because of data bias; likelihood 3, impact 3, score 9 (medium); treatment: rebalance training data and add a fairness test to the release gate.

## Statement of Applicability
The Statement of Applicability (SoA) lists all 38 Annex A controls and states for each whether it applies, why, whether it is implemented and where the evidence is. It must be consistent with the risk register. Exclusions must be justified by scope, for example "we do not develop AI", never by cost.
