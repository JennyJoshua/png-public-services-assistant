"""Curated public PNG sources approved for the first RAG pilot.

Only these exact HTTPS seed URLs are fetched. This module intentionally does not
crawl arbitrary links or accept user-supplied URLs.

Governance metadata is deliberately nullable: unknown authority, document, language,
publication, review, fetch and content-integrity facts must not be guessed. Newly
registered sources remain pending review until those facts have been assessed.
"""
from dataclasses import dataclass, replace
from typing import Literal


SourceStatus = Literal["active", "superseded", "broken", "pending_review"]
VALID_SOURCE_STATUSES = frozenset({"active", "superseded", "broken", "pending_review"})

# Re-activation always passes through human review. A superseded source cannot
# silently become active again, and a broken source must be reassessed first.
ALLOWED_STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending_review": frozenset({"active", "broken"}),
    "active": frozenset({"pending_review", "broken", "superseded"}),
    "broken": frozenset({"pending_review"}),
    "superseded": frozenset({"pending_review"}),
}


@dataclass(frozen=True)
class Source:
    institution: str
    title: str
    url: str
    authority_tier: str | None = None
    document_type: str | None = None
    jurisdiction: str | None = None
    language: str | None = None
    publication_date: str | None = None
    effective_date: str | None = None
    last_fetched_at: str | None = None
    last_reviewed_at: str | None = None
    content_hash: str | None = None
    status: SourceStatus = "pending_review"

    def __post_init__(self) -> None:
        if self.status not in VALID_SOURCE_STATUSES:
            raise ValueError(f"unsupported source status: {self.status!r}")


def transition_source_status(
    source: Source, new_status: SourceStatus, *, reviewed_at: str | None = None
) -> Source:
    """Return a new source record only when its lifecycle transition is permitted.

    Moving a source to active requires an explicit human-review timestamp.
    This records the review event; it does not itself certify source authority.
    """
    if new_status not in VALID_SOURCE_STATUSES:
        raise ValueError(f"unsupported source status: {new_status!r}")
    if new_status == source.status:
        return source
    if new_status not in ALLOWED_STATUS_TRANSITIONS[source.status]:
        raise ValueError(
            f"source status transition not allowed: {source.status} -> {new_status}"
        )
    if new_status == "active":
        if not isinstance(reviewed_at, str) or not reviewed_at.strip():
            raise ValueError("reviewed_at is required before a source can become active")
        return replace(source, status=new_status, last_reviewed_at=reviewed_at.strip())
    return replace(source, status=new_status)


SOURCES: tuple[Source, ...] = (
    Source("PNG National Information Centre", "National Information Centre", "https://info.gov.pg/home/"),
    Source("Department of Justice and Attorney General", "Department of Justice and Attorney General", "https://justice.gov.pg/"),
    Source("Immigration and Citizenship Services Authority", "Immigration and Citizenship Services Authority", "https://icsa.gov.pg/"),
    Source("Investment Promotion Authority", "Business Registration, Regulation and Certification", "https://www.ipa.gov.pg/public/help.aspx?cn=BusinessRegulations"),
    Source("Investment Promotion Authority", "IPA — Business Name Registration and Company Incorporation Guide", "https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo"),
    Source("Investment Promotion Authority", "IPA — Prescribed Forms and Registration Fees", "https://www.ipa.gov.pg/public/prescribedforms.aspx?lang=en-US"),
    Source("Investment Promotion Authority", "IPA — Registry Forms for Download", "https://www.ipa.gov.pg/public/help.aspx?cn=FormsForDownload"),
    Source("Internal Revenue Commission", "Internal Revenue Commission", "https://irc.gov.pg/"),
    Source("National and Supreme Courts of Papua New Guinea", "National and Supreme Courts of Papua New Guinea", "https://www.pngjudiciary.gov.pg/"),
    Source("Land Commission of Papua New Guinea", "Land Commission of Papua New Guinea", "https://www.landcommission.gov.pg/"),
    Source("Papua New Guinea Civil and Identity Registry", "PNGCIR — National Identity and Civil Registration", "https://pngcir.gov.pg/"),
    Source("Papua New Guinea Civil and Identity Registry", "PNGCIR — NID Registration Information", "https://pngcir.gov.pg/nid-registration-information/"),
    Source("Papua New Guinea Civil and Identity Registry", "PNGCIR — Registration Forms and Downloads", "https://pngcir.gov.pg/downloads/"),
    Source("Papua New Guinea Civil and Identity Registry", "PNGCIR — Fees", "https://pngcir.gov.pg/png-civil-identity-registry-fees/"),
    Source("Papua New Guinea Civil and Identity Registry", "PNGCIR — Contact", "https://pngcir.gov.pg/contact/"),
)
