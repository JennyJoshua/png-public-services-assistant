"""Curated public PNG sources approved for the first RAG pilot.

Only these exact HTTPS seed URLs are fetched. This module intentionally does not
crawl arbitrary links or accept user-supplied URLs.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    institution: str
    title: str
    url: str


SOURCES: tuple[Source, ...] = (
    Source("PNG National Information Centre", "National Information Centre", "https://info.gov.pg/home/"),
    Source("Department of Justice and Attorney General", "Department of Justice and Attorney General", "https://justice.gov.pg/"),
    Source("Immigration and Citizenship Services Authority", "Immigration and Citizenship Services Authority", "https://icsa.gov.pg/"),
    Source("Investment Promotion Authority", "Business Registration, Regulation and Certification", "https://www.ipa.gov.pg/public/help.aspx?cn=BusinessRegulations"),
    Source("Internal Revenue Commission", "Internal Revenue Commission", "https://irc.gov.pg/"),
    Source("National and Supreme Courts of Papua New Guinea", "National and Supreme Courts of Papua New Guinea", "https://www.pngjudiciary.gov.pg/"),
    Source("Land Commission of Papua New Guinea", "Land Commission of Papua New Guinea", "https://www.landcommission.gov.pg/"),
)
