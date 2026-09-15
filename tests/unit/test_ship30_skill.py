import pytest
from apps.api.src.services.skills.ship30 import (
    count_words,
    extract_citations,
    validate_ship30_essay,
    generate_atomic_essay_html,
)


def test_word_count_calculation():
    text = "This is a simple sentence with eight words."
    assert count_words(text) == 8

    markdown_text = "# Header\n\n- **Item one**: description\n- **Item two**: description"
    assert count_words(markdown_text) == 7


def test_extract_citations():
    text = """
    Adam Fishman explains this dynamic in detail [Adam Fishman, Lenny's Podcast, 00:16:06].
    Elena Verna also noted (00:22:18) that product-led growth loops require disciplined metrics.
    """
    citations = extract_citations(text)
    assert len(citations) == 2
    assert any("00:16:06" in c["raw"] for c in citations)
    assert any("00:22:18" in c["raw"] for c in citations)


def test_validate_ship30_essay_structure():
    # Construct a valid ~1,200 word essay with proper structure
    paragraphs = []
    paragraphs.append("# The Growth Leadership Paradox: Why Unicorn Growth Leaders Don't Exist\n")
    paragraphs.append("*Why hiring for a single superhero PM breaks your growth strategy, and the portfolio framework to build instead.*\n")
    paragraphs.append("## The Core Idea: Portfolio Team Construction Over Mythical Unicorns\n")
    paragraphs.append("Most founders fail at growth hiring because they search for an all-knowing growth savior.\n")
    paragraphs.append("## The Context & Stakes: The Broken Growth Playbook\n")
    paragraphs.append("Conventional wisdom states that a VP of Growth should be an expert in growth modeling, viral loops, enterprise sales, and executive communication. In reality, such candidates do not exist.\n")

    # Generate body sections to reach ~1,100 words
    pillar_text = (
        "Growth strategy requires rigorous experimentation, analytical depth, and continuous alignment with finance. "
        "Teams must balance tactical execution with strategic roadmaps, ensuring that acquisition channels do not "
        "cannibalize long-term retention. By focusing on modular skill sets, organizations build resilient teams that "
        "scale across multiple product cycles without burning out key personnel. "
    )
    
    paragraphs.append("## Framework Pillar 1: Growth Execution & Data Fluency\n")
    paragraphs.append(pillar_text * 6 + " As Adam Fishman noted [Adam Fishman, Lenny's Podcast, 00:16:06], balance across the team is what prevents portfolio gaps.\n")

    paragraphs.append("## Framework Pillar 2: Capital Allocation & Forecasting\n")
    paragraphs.append(pillar_text * 6 + " In fact, forecasting models must align directly with finance (00:22:18) to avoid premature channel exhaustion.\n")

    paragraphs.append("## Framework Pillar 3: Prioritization & Roadmapping\n")
    paragraphs.append(pillar_text * 6 + " Prioritizing loops over traditional linear funnels allows continuous compounding.\n")

    paragraphs.append("## The Golden Takeaway: Build The System, Not The Hero\n")
    paragraphs.append("Stop hunting for mythical unicorn PMs. Audit your growth team's competency matrix today and hire specifically for your portfolio blind spots.\n")

    essay_content = "\n".join(paragraphs)
    result = validate_ship30_essay(essay_content, tolerance_min=1000, tolerance_max=1500)

    assert result.is_valid is True
    assert result.has_hook is True
    assert result.has_core_idea is True
    assert result.has_subheadings is True
    assert result.has_citations is True
    assert result.word_count >= 1000
    assert len(result.sections_found) >= 4


def test_generate_atomic_essay_html_security_and_rendering():
    title = "Mastering Growth Loops"
    markdown = """# Mastering Growth Loops
## The Core Idea
Growth loops compound over time [Elena Verna, Episode 45, 00:14:20].
<script>alert('xss');</script>
"""
    html = generate_atomic_essay_html(title, markdown, guest="Elena Verna", episode_title="B2B Growth")

    # Verify basic HTML structure
    assert "<!DOCTYPE html>" in html
    assert "Mastering Growth Loops" in html
    assert "Elena Verna" in html
    assert "citation-chip" in html

    # Verify script tags are neutralized
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
