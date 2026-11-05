from __future__ import annotations

from dataclasses import dataclass, field

SECTION_KEYWORDS = {
    "business": {
        "business",
        "market",
        "sales",
        "revenue",
        "staff",
        "retail",
        "profit",
        "customer",
        "holiday",
        "inventory",
    },
    "news": {
        "city",
        "government",
        "policy",
        "official",
        "report",
        "public",
        "election",
        "court",
    },
    "culture": {
        "art",
        "film",
        "music",
        "festival",
        "theater",
        "museum",
        "books",
        "culture",
    },
    "science": {
        "science",
        "research",
        "experiment",
        "lab",
        "climate",
        "energy",
        "data",
    },
}


@dataclass
class ArticleReviewRequest:
    title: str
    body: str
    section: str
    source_links: list[str] = field(default_factory=list)
    author: str = "unknown"


class FactCheckAgent:
    @staticmethod
    def evaluate(request: ArticleReviewRequest) -> dict:
        text = f"{request.title} {request.body}".lower()
        warning_terms = [
            "secretly",
            "everyone is",
            "paid everyone",
            "without evidence",
            "shockingly",
            "cover up",
            "miracle",
            "conspiracy",
        ]
        hits = [term for term in warning_terms if term in text]
        source_count = len(request.source_links)
        risk = 0.2
        if source_count == 0:
            risk += 0.45
        elif source_count == 1:
            risk += 0.20
        risk += min(0.35, 0.12 * len(hits))
        if not text.strip():
            risk = 1.0

        findings = []
        if source_count == 0:
            findings.append("No source links were provided.")
        if len(hits) > 0:
            findings.append(
                "The article contains unusually strong or unsupported claims."
            )
        if not findings:
            findings.append(
                "The article includes enough source support to reduce "
                "obvious risk."
            )

        return {"risk": min(1.0, risk), "findings": findings}


class GrammarAgent:
    @staticmethod
    def evaluate(request: ArticleReviewRequest) -> dict:
        body = request.body.strip()
        if not body:
            return {"score": 0.0, "findings": ["Article text is empty."]}

        words = body.split()
        long_words = sum(1 for word in words if len(word) > 12)
        punctuation = body.count("!") + body.count("?")
        score = 0.8
        if long_words > max(4, len(words) * 0.1):
            score -= 0.2
        if punctuation > 2:
            score -= 0.1
        if len(words) < 20:
            score -= 0.1

        findings = []
        if score < 0.7:
            findings.append(
                "The article may need readability or wording cleanup."
            )
        if not findings:
            findings.append(
                "The article reads clearly enough for editorial review."
            )

        return {"score": max(0.0, min(1.0, score)), "findings": findings}


class RelevanceAgent:
    @staticmethod
    def evaluate(request: ArticleReviewRequest) -> dict:
        section = request.section.lower()
        text = f"{request.title} {request.body}".lower()
        target_terms = SECTION_KEYWORDS.get(section, set())
        matches = sum(1 for term in target_terms if term in text)
        fit_score = min(1.0, (matches / max(1, len(target_terms))) + 0.2)

        findings = []
        if matches == 0:
            findings.append(
                "The article does not clearly align with the "
                f"'{request.section}' section."
            )
        elif fit_score < 0.7:
            findings.append(
                "The article may be weakly matched to the selected section."
            )
        if not findings:
            findings.append(
                "The article fits the selected section well enough for review."
            )

        return {"score": max(0.0, fit_score), "findings": findings}


class EditorialDecisionAgent:
    @staticmethod
    def decide(
        fact_risk: float,
        grammar_score: float,
        section_fit_score: float,
    ) -> str:
        if fact_risk >= 0.75 or section_fit_score < 0.45:
            return "reject"
        if fact_risk >= 0.55 or grammar_score < 0.5 or section_fit_score < 0.7:
            return "revise"
        return "approve"


@dataclass
class ReviewResult:
    fact_check_risk: float
    grammar_score: float
    section_fit_score: float
    final_decision: str
    fact_findings: list[str] = field(default_factory=list)
    grammar_findings: list[str] = field(default_factory=list)
    relevance_findings: list[str] = field(default_factory=list)


class EditorialReviewWorkflow:
    def review(self, request: ArticleReviewRequest) -> ReviewResult:
        fact_result = FactCheckAgent.evaluate(request)
        grammar_result = GrammarAgent.evaluate(request)
        relevance_result = RelevanceAgent.evaluate(request)

        final_decision = EditorialDecisionAgent.decide(
            fact_result["risk"],
            grammar_result["score"],
            relevance_result["score"],
        )

        return ReviewResult(
            fact_check_risk=fact_result["risk"],
            grammar_score=grammar_result["score"],
            section_fit_score=relevance_result["score"],
            final_decision=final_decision,
            fact_findings=fact_result["findings"],
            grammar_findings=grammar_result["findings"],
            relevance_findings=relevance_result["findings"],
        )
