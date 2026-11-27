"""Exact-URL verification plans for controlling and corroborating documents.

Only explicitly listed HTTPS URLs are fetched. A domain allowlist is not a
substitute for a reviewed document-level mapping.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


DocumentRole = Literal["controlling_instrument", "corroborating_source"]


@dataclass(frozen=True)
class VerificationDocument:
    url: str
    role: DocumentRole
    required_terms: tuple[str, ...]


@dataclass(frozen=True)
class SourceVerificationPlan:
    source_url: str
    authority_hosts: frozenset[str]
    documents: tuple[VerificationDocument, ...]


VERIFICATION_PLANS: dict[str, SourceVerificationPlan] = {
    # RTA's current driver-licensing page points to the 2017 Rules. Its official
    # Rules PDF still contains references to a 2015 fees regulation, while the
    # RTA's current fee schedule page identifies the 2017 regulation. The
    # verifier must detect and hold this discrepancy rather than auto-approve it.
    "https://rta.gov.pg/licences-approvals/driver-licensing/": SourceVerificationPlan(
        source_url="https://rta.gov.pg/licences-approvals/driver-licensing/",
        authority_hosts=frozenset({"rta.gov.pg", "www.rta.gov.pg"}),
        documents=(
            VerificationDocument(
                url="https://rta.gov.pg/pdfs/resources/legislation/rules/RTR_LicensingOfDrivers2017.pdf",
                role="controlling_instrument",
                required_terms=("road traffic rules", "licensing of drivers", "2017"),
            ),
            VerificationDocument(
                url="https://www.rta.gov.pg/licences-approvals/schedule-of-fees-from-1-june-2018/",
                role="corroborating_source",
                required_terms=("road traffic (fees and charges) regulation 2017", "schedule 1"),
            ),
        ),
    ),
}
