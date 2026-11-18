"""Provider-neutral orchestration for bounded candidate discovery.

This module joins provider-normalised search results to bounded page fetching
and the risk-based host policy. It does not persist candidates, approve sources,
or feed candidate text into live chat retrieval.
"""
from __future__ import annotations

from collections.abc import Sequence

from app.candidate_fetch import fetch_candidate_pages
from app.candidate_policy import evaluate_candidate_policy


async def discover_candidate_pages(candidates: Sequence[dict]) -> list[dict]:
    """Fetch bounded candidates and attach a risk-based policy outcome.

    Candidate text remains quarantined as candidate data. An auto_process
    outcome does not assign an evidence class, activate a source, or authorise
    use in an answer.
    """
    fetched = await fetch_candidate_pages(list(candidates))
    results: list[dict] = []
    for item in fetched:
        candidate = dict(item)
        decision = evaluate_candidate_policy(candidate)
        candidate["policy_action"] = decision.action
        candidate["policy_reason"] = decision.reason
        candidate["policy_trusted_host"] = decision.trusted_host
        candidate["policy_source_class"] = None
        candidate["approved"] = False
        candidate["evidence_class"] = None
        results.append(candidate)
    return results