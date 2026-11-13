from app.rag import _page_text, _rank_passages
from app.source_registry import SOURCES


def test_page_text_removes_navigation_and_scripts() -> None:
    html = """
    <html><head><title>Agency page</title></head><body>
      <nav>Navigation noise</nav>
      <main><p>The agency provides business registration services to applicants.</p></main>
      <script>ignore this script content</script>
    </body></html>
    """
    text, title = _page_text(html)
    assert title == "Agency page"
    assert "business registration" in text
    assert "Navigation noise" not in text
    assert "ignore this script" not in text


def test_page_text_preserves_paragraphs_and_list_items_as_separate_blocks() -> None:
    html = """
    <html><body><main>
      <h2>How to register</h2>
      <p>Download the official registration form and complete the required details.</p>
      <ol>
        <li>Lodge the completed form at the nearest registry office.</li>
        <li>Attend in person for fingerprint and identity capture.</li>
      </ol>
    </main></body></html>
    """
    text, _ = _page_text(html)
    blocks = text.splitlines()
    assert blocks == [
        "How to register",
        "Download the official registration form and complete the required details.",
        "Lodge the completed form at the nearest registry office.",
        "Attend in person for fingerprint and identity capture.",
    ]


def test_rank_passages_returns_relevant_source_excerpt() -> None:
    pages = [{
        "institution": "Example Agency",
        "title": "Business Registration",
        "url": "https://example.gov.pg/business",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": (
            "The Companies Office administers business registration and maintains "
            "the national register of companies and business names.\n"
            "The weather is usually warm during the wet season."
        ),
    }]
    results = _rank_passages("How does business registration work?", pages)
    assert results
    assert "business registration" in results[0]["text"].lower()
    assert results[0]["source"]["institution"] == "Example Agency"


def test_rank_passages_returns_empty_when_no_query_overlap() -> None:
    pages = [{
        "institution": "Example Agency",
        "title": "Page",
        "url": "https://example.gov.pg/",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": "The department publishes annual statistics about rainfall patterns.",
    }]
    assert _rank_passages("How can I renew a passport?", pages) == []


def test_pngcir_is_an_explicit_curated_source_set() -> None:
    pngcir_urls = {source.url for source in SOURCES if source.institution == "Papua New Guinea Civil and Identity Registry"}
    assert pngcir_urls == {
        "https://pngcir.gov.pg/",
        "https://pngcir.gov.pg/nid-registration-information/",
        "https://pngcir.gov.pg/downloads/",
        "https://pngcir.gov.pg/png-civil-identity-registry-fees/",
        "https://pngcir.gov.pg/contact/",
    }


def test_national_id_question_ranks_official_registration_instructions() -> None:
    pages = [{
        "institution": "Papua New Guinea Civil and Identity Registry",
        "title": "PNGCIR — NID Registration Information",
        "url": "https://pngcir.gov.pg/nid-registration-information/",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": (
            "Full online registration is not possible because every citizen must provide "
            "fingerprint and ID capture in person.\n"
            "Normal registration: Download the Registration Form, fill in the details "
            "and lodge it at your nearest Civil and Identity Registry Office.\n"
            "National Identity Card Information is for applicants 18 years and above only."
        ),
    }, {
        "institution": "Example News",
        "title": "National Identity Card holder",
        "url": "https://example.org/news",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": "A National Identity Card holder may be asked to provide identification as a witness.",
    }]
    results = _rank_passages("How do I apply for a National ID?", pages)
    assert results
    assert results[0]["source"]["institution"] == "Papua New Guinea Civil and Identity Registry"
    assert any("lodge it at your nearest Civil and Identity Registry Office" in item["text"] for item in results)
    assert all(item["source"]["institution"] == "Papua New Guinea Civil and Identity Registry" for item in results[:3])


def test_national_id_query_keeps_registration_form_and_in_person_capture_passages() -> None:
    page = {
        "institution": "Papua New Guinea Civil and Identity Registry",
        "title": "PNGCIR — NID Registration Information",
        "url": "https://pngcir.gov.pg/nid-registration-information/",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": (
            "Normal registration: Download the Registration Form, fill in the details "
            "and lodge it at your nearest Civil and Identity Registry Office.\n"
            "Full online registration is not possible because fingerprint and ID capture "
            "must be completed in person."
        ),
    }
    results = _rank_passages("How do I apply for a National ID?", [page])
    assert len(results) == 2
    assert "Registration Form" in results[0]["text"]
    assert "fingerprint and ID capture" in results[1]["text"]



def test_nid_abbreviation_ranks_official_registration_instructions() -> None:
    page = {
        "institution": "Papua New Guinea Civil and Identity Registry",
        "title": "PNGCIR — NID Registration Information",
        "url": "https://pngcir.gov.pg/nid-registration-information/",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": (
            "Normal registration: Download the Registration Form, fill in the details "
            "and lodge it at your nearest Civil and Identity Registry Office.\n"
            "Full online registration is not possible because fingerprint and ID capture "
            "must be completed in person."
        ),
    }
    results = _rank_passages("How do I apply for an NID?", [page])
    assert len(results) == 2
    assert "Registration Form" in results[0]["text"]
    assert "fingerprint and ID capture" in results[1]["text"]


def test_identity_card_wording_uses_nid_retrieval_boost() -> None:
    page = {
        "institution": "Papua New Guinea Civil and Identity Registry",
        "title": "PNGCIR — NID Registration Information",
        "url": "https://pngcir.gov.pg/nid-registration-information/",
        "publication_date": None,
        "last_checked_at": "2026-11-13T00:00:00+00:00",
        "text": (
            "Normal registration: Download the Registration Form, fill in the details "
            "and lodge it at your nearest Civil and Identity Registry Office."
        ),
    }
    results = _rank_passages("How do I get an identity card?", [page])
    assert results
    assert results[0]["source"]["institution"] == "Papua New Guinea Civil and Identity Registry"
    assert "Registration Form" in results[0]["text"]


def test_ipa_business_registration_sources_are_curated() -> None:
    ipa_urls = {source.url for source in SOURCES if source.institution == "Investment Promotion Authority"}
    assert ipa_urls == {
        "https://www.ipa.gov.pg/public/help.aspx?cn=BusinessRegulations",
        "https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo",
        "https://www.ipa.gov.pg/public/prescribedforms.aspx?lang=en-US",
        "https://www.ipa.gov.pg/public/help.aspx?cn=FormsForDownload",
    }


def test_business_registration_question_ranks_ipa_prerequisites() -> None:
    pages = [{
        "institution": "Investment Promotion Authority",
        "title": "IPA — Business Name Registration and Company Incorporation Guide",
        "url": "https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo",
        "publication_date": None,
        "last_checked_at": "2026-11-14T00:00:00+00:00",
        "text": (
            "Registering a business name requires up to three proposed names, "
            "the applicant name and address, and the name and address of each owner.\\n"
            "Provide the principal place of business, additional business addresses, "
            "a postal address and the primary business activity.\\n"
            "To incorporate a company, reserve the company name first and provide "
            "directors, shareholders, company addresses and a company constitution."
        ),
    }, {
        "institution": "PNG National Information Centre",
        "title": "National Information Centre",
        "url": "https://info.gov.pg/home/",
        "publication_date": None,
        "last_checked_at": "2026-11-14T00:00:00+00:00",
        "text": "The government provides many public services and information to citizens.",
    }]
    results = _rank_passages("What are the prerequisites of registering a business?", pages)
    assert results
    assert results[0]["source"]["institution"] == "Investment Promotion Authority"
    assert any("proposed names" in item["text"] for item in results)
    assert all(item["source"]["institution"] == "Investment Promotion Authority" for item in results)


def test_company_incorporation_question_ranks_company_requirements() -> None:
    page = {
        "institution": "Investment Promotion Authority",
        "title": "IPA — Business Name Registration and Company Incorporation Guide",
        "url": "https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo",
        "publication_date": None,
        "last_checked_at": "2026-11-14T00:00:00+00:00",
        "text": (
            "To incorporate a company, reserve the proposed company name and wait for approval.\\n"
            "Provide company contact details and addresses, directors, shareholders, "
            "and upload the company constitution."
        ),
    }
    results = _rank_passages("What do I need to incorporate a company?", [page])
    assert results
    assert any("directors, shareholders" in item["text"] for item in results)
