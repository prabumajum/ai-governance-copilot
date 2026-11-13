# Responsible AI controls in practice

## Human oversight
High-impact AI systems need a named human who can understand, override and stop the system. Document who approves decisions, when the system must escalate to a person, and how affected people can request human review. Trading or advisory models should have a tested kill switch.

## Lifecycle stage gates
Put approval steps inside the real release process (pull-request template, CI/CD step or ticket workflow), not only in a policy document. A release checklist should require validation results, fairness tests, security tests and sign-off before a model reaches production. Every model change, data change or change of use goes through the same gate.

## Data governance
Keep a one-page dataset sheet for every dataset: owner, source, legal basis and consent, whether personal or children's data is present, date range, known gaps or biases, preparation steps, quality checks and retention period. This answers the auditor question "where did this training data come from?"

## Monitoring and logging
Monitor model performance against agreed thresholds, fairness metrics between groups, and drift. Keep event logs long enough for investigations and review them on a schedule. Track AI incidents to closure with root-cause analysis.

## Guardrails for generative AI
Guardrails are checks around a model. Input guardrails detect prompt injection and redact personal data before it reaches the model. Output guardrails check answers for leaked personal data, missing citations, unsafe advice or off-topic content. Guardrails reduce risk but never remove it, so pair them with monitoring and human review.

## Evaluations
Evaluations (evals) test an AI system against a fixed set of questions with known good answers, before release and after every change. Useful checks include answer correctness, groundedness in retrieved sources, correct tool use, guardrail behaviour and latency. Track the pass rate over time like any other quality metric.

## Third-party AI
Vendor AI enters through SaaS renewals and APIs. Ask vendors what AI functions the product has, whether your data trains their models, what bias and performance testing they do, how they notify model changes and incidents, and whether they hold ISO/IEC 42001 or ISO/IEC 27001 certification.
