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


def test_business_registration_question_ranks_actual_ipa_checklist_fields() -> None:
    # These are individual checklist items published by IPA, kept as separate
    # passages in the live page's list structure.
    page = {
        "institution": "Investment Promotion Authority",
        "title": "Registering a Business Name",
        "url": "https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo",
        "publication_date": None,
        "last_checked_at": "2026-11-14T00:00:00+00:00",
        "text": (
            "1 Collect Required Information\\n"
            "Proposed Business Name: Enter the proposed name. Note: this cannot be the same or nearly the same as a name already in use by another registered entity. You may enter up to 3 potential names so that if the first is rejected your application may still proceed using the second name.\\n"
            "Name and address of applicant.\\n"
            "Owners: Name and address for each individual person that is an owner. If the owner is an entity already registered with IPA (like a company) you only need to enter its registration number.\\n"
            "Addresses: Principal place of business, additional places of business, and a postal address must all be provided.\\n"
            "Primary Business Activity: Tick the appropriate box.\\n"
            "Foreign Investor: If an owner is a foreign investor, you must indicate this on the Application. They will need to seek a foreign investor certification.\\n"
            "Declarations: Tick the box affirming that the information you have submitted is true."
        ),
    }
    results = _rank_passages("What are the prerequisites of registering a business?", [page])
    retrieved = " ".join(item["text"] for item in results).lower()
    assert results
    assert "proposed business name" in retrieved
    assert "name and address of applicant" in retrieved
    assert "owners: name and address" in retrieved
    assert "principal place of business" in retrieved
    assert "primary business activity" in retrieved
    assert "foreign investor" in retrieved
    assert "declarations" in retrieved
    assert all(item["source"]["institution"] == "Investment Promotion Authority" for item in results)


def test_business_name_account_and_company_requirements_are_distinguished() -> None:
    page = {
        "institution": "Investment Promotion Authority",
        "title": "IPA — Business Name Registration and Company Incorporation Guide",
        "url": "https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo",
        "publication_date": None,
        "last_checked_at": "2026-11-14T00:00:00+00:00",
        "text": (
            "To start the online process to register a business name, you must first have an account.\\n"
            "To file an online application to register a new company you must first have a client account with the registry.\\n"
            "Under the Company section, reserve a name for the type of company you want to register. Once the name reservation is submitted and approved, you may proceed to register.\\n"
            "Contact Details: Contact information for the company, including various addresses (such as a registered office address) and principal place of business.\\n"
            "Directors: Enter relevant details for each director.\\n"
            "Shareholders: Enter relevant details for each shareholder.\\n"
            "Company Constitution: If you are forming a company you will be required to upload a copy of the company's constitution."
        ),
    }
    results = _rank_passages("What are the prerequisites of registering a business?", [page])
    retrieved = " ".join(item["text"] for item in results).lower()
    assert "client account" in retrieved or "have an account" in retrieved
    assert "reserve a name" in retrieved
    assert "directors" in retrieved
    assert "shareholders" in retrieved
    assert "company constitution" in retrieved

def test_company_incorporation_question_ranks_company_requirements() -> None:
    page = {
        "institution": "Investment Promotion Authority",
        "title": "IPA — Business Name Registration and Company Incorporation Guide",
        "url": "https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo",
        "publication_date": None,
        "last_checked_at": "2026-11-14T00:00:00+00:00",
        "text": (
            "To incorporate a company, reserve the proposed company name and wait for approval.\n"
            "Provide company contact details and addresses, directors, shareholders, "
            "and upload the company constitution."
        ),
    }
    results = _rank_passages("What do I need to incorporate a company?", [page])
    assert results
    assert any("directors, shareholders" in item["text"] for item in results)


def test_page_text_extracts_fee_table_rows() -> None:
    html = """
    <html><body><main>
      <table>
        <tr><th>Form</th><th>Online Fee</th><th>Paper Fee</th></tr>
        <tr><td>A-17</td><td>K150</td><td>K200</td></tr>
      </table>
    </main></body></html>
    """
    text, _ = _page_text(html)
    assert "A-17 K150 K200" in text


def test_nid_registration_does_not_trigger_ipa_business_boost() -> None:
    pages = [{
        "institution": "Papua New Guinea Civil and Identity Registry",
        "title": "PNGCIR — NID Registration Information",
        "url": "https://pngcir.gov.pg/nid-registration-information/",
        "publication_date": None,
        "last_checked_at": "2026-11-14T00:00:00+00:00",
        "text": "Download the National Identity registration form and lodge it at the registry office for fingerprint capture.",
    }, {
        "institution": "Investment Promotion Authority",
        "title": "IPA — Business Name Registration and Company Incorporation Guide",
        "url": "https://www.ipa.gov.pg/public/howto.aspx?cn=RegisterBusinessName&ctk=CompanyHowTo",
        "publication_date": None,
        "last_checked_at": "2026-11-14T00:00:00+00:00",
        "text": "Registering a business name requires proposed names, owner details and business addresses.",
    }]
    results = _rank_passages("How do I apply for a National ID?", pages)
    assert results
    assert results[0]["source"]["institution"] == "Papua New Guinea Civil and Identity Registry"
