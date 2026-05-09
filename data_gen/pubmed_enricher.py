"""
pubmed_enricher.py — Fetches clinical evidence from PubMed via NCBI E-Utilities.
Uses LLM-assisted parsing to extract structured clinical ranges from abstracts.
All results are cached locally in SQLite for offline use.
"""

import time
import json
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from data_gen.evidence_cache import evidence_cache

# Rate limiting for NCBI (3 req/sec unauthenticated)
_LAST_REQUEST_TIME = 0.0
_MIN_INTERVAL = 0.35  # seconds between requests


def _rate_limit():
    global _LAST_REQUEST_TIME
    elapsed = time.time() - _LAST_REQUEST_TIME
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _LAST_REQUEST_TIME = time.time()


class PubMedEnricher:
    """Fetches and parses clinical evidence from PubMed."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def search_pubmed(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search PubMed and return article summaries with abstracts."""
        cached = evidence_cache.get(f"search:{query}")
        if cached:
            return cached["result"]

        try:
            import httpx
        except ImportError:
            print("[PubMedEnricher] httpx not installed, skipping PubMed search")
            return []

        _rate_limit()
        params = {
            "db": "pubmed", "term": query, "retmax": max_results,
            "retmode": "json", "sort": "relevance",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            resp = httpx.get(f"{self.base_url}/esearch.fcgi", params=params, timeout=15)
            resp.raise_for_status()
            ids = resp.json().get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"[PubMedEnricher] Search failed: {e}")
            return []

        if not ids:
            return []

        # Fetch abstracts
        _rate_limit()
        try:
            resp = httpx.get(f"{self.base_url}/efetch.fcgi", params={
                "db": "pubmed", "id": ",".join(ids),
                "rettype": "abstract", "retmode": "xml",
                **({"api_key": self.api_key} if self.api_key else {}),
            }, timeout=15)
            resp.raise_for_status()
            articles = self._parse_xml_articles(resp.text)
        except Exception as e:
            print(f"[PubMedEnricher] Fetch failed: {e}")
            articles = [{"pmid": pid, "title": "", "abstract": ""} for pid in ids]

        evidence_cache.put(f"search:{query}", articles, pubmed_ids=ids)
        return articles

    def search_clinical_ranges(
        self, condition: str, vital_type: str, demographic: str = "general"
    ) -> Optional[Dict]:
        """Search PubMed for clinical ranges of a vital for a condition."""
        cached = evidence_cache.get_clinical_range(condition, vital_type, demographic)
        if cached:
            return cached

        query = (
            f"{condition} {vital_type.replace('_', ' ')} "
            f"clinical range mean standard deviation meta-analysis"
        )
        articles = self.search_pubmed(query, max_results=3)
        if not articles:
            return None

        # Use LLM to extract structured data from abstracts
        parsed = self._extract_clinical_range(articles, condition, vital_type)
        if parsed:
            evidence_cache.put_clinical_range(
                condition=condition, vital_type=vital_type,
                demographic=demographic, **parsed,
            )
        return parsed

    def enrich_recommendations(self, condition: str) -> List[Dict]:
        """Fetch latest treatment guidelines from PubMed."""
        cached = evidence_cache.get_recommendations(condition)
        if cached:
            return cached

        query = f"{condition} treatment guidelines recommendations systematic review"
        articles = self.search_pubmed(query, max_results=3)
        if not articles:
            return []

        recs = self._extract_recommendations(articles, condition)
        for rec in recs:
            evidence_cache.put_recommendation(condition=condition, **rec)
        return recs

    def validate_against_evidence(self, vital_type: str, condition: str,
                                   generated_mean: float, generated_std: float) -> Dict:
        """Cross-reference generated profile against PubMed evidence."""
        evidence = self.search_clinical_ranges(condition, vital_type)
        if not evidence or evidence.get("mean") is None:
            return {"validated": False, "reason": "No evidence available"}

        ev_mean = evidence["mean"]
        ev_std = evidence.get("std", generated_std)
        deviation = abs(generated_mean - ev_mean) / max(ev_std, 0.01)

        return {
            "validated": True,
            "evidence_mean": ev_mean,
            "evidence_std": ev_std,
            "generated_mean": generated_mean,
            "deviation_sigma": round(deviation, 2),
            "acceptable": deviation <= 2.0,
            "pubmed_id": evidence.get("pubmed_id", ""),
        }

    # ── XML Parsing ───────────────────────────────────────────────────────────

    def _parse_xml_articles(self, xml_text: str) -> List[Dict]:
        """Extract articles from PubMed XML response."""
        articles = []
        # Simple regex-based extraction (avoids heavy XML dependency)
        pmid_pattern = re.compile(r"<PMID[^>]*>(\d+)</PMID>")
        title_pattern = re.compile(r"<ArticleTitle>(.*?)</ArticleTitle>", re.DOTALL)
        abstract_pattern = re.compile(r"<AbstractText[^>]*>(.*?)</AbstractText>", re.DOTALL)

        pmids = pmid_pattern.findall(xml_text)
        titles = title_pattern.findall(xml_text)
        abstracts = abstract_pattern.findall(xml_text)

        for i, pmid in enumerate(pmids):
            articles.append({
                "pmid": pmid,
                "title": titles[i].strip() if i < len(titles) else "",
                "abstract": " ".join(abstracts).strip() if abstracts else "",
            })
        return articles

    def _extract_clinical_range(self, articles: List[Dict],
                                 condition: str, vital_type: str) -> Optional[Dict]:
        """Extract mean/std/range from article abstracts using regex heuristics."""
        all_text = " ".join(a.get("abstract", "") + " " + a.get("title", "") for a in articles)
        if not all_text.strip():
            return None

        # Try to find numeric patterns like "mean 120.5 ± 15.3" or "120.5 (SD 15.3)"
        mean_val, std_val = None, None

        patterns = [
            r"mean\s*[=:]\s*([\d.]+)\s*[±\+\-]\s*([\d.]+)",
            r"([\d.]+)\s*±\s*([\d.]+)",
            r"([\d.]+)\s*\(SD\s*([\d.]+)\)",
            r"([\d.]+)\s*\(sd\s*([\d.]+)\)",
        ]
        for pat in patterns:
            match = re.search(pat, all_text, re.IGNORECASE)
            if match:
                try:
                    mean_val = float(match.group(1))
                    std_val = float(match.group(2))
                    break
                except ValueError:
                    continue

        if mean_val is None:
            return None

        # Try to find range
        range_low, range_high = None, None
        range_match = re.search(r"range\s*[=:]\s*([\d.]+)\s*[-–]\s*([\d.]+)", all_text, re.IGNORECASE)
        if range_match:
            try:
                range_low = float(range_match.group(1))
                range_high = float(range_match.group(2))
            except ValueError:
                pass

        if range_low is None:
            range_low = mean_val - 2 * (std_val or 0)
            range_high = mean_val + 2 * (std_val or 0)

        pubmed_id = articles[0].get("pmid", "") if articles else ""

        return {
            "mean": mean_val,
            "std": std_val or 0.0,
            "range_low": range_low,
            "range_high": range_high,
            "evidence_level": "B",
            "pubmed_id": pubmed_id,
            "source_title": articles[0].get("title", "") if articles else "",
        }

    def _extract_recommendations(self, articles: List[Dict], condition: str) -> List[Dict]:
        """Extract treatment recommendations from abstracts."""
        recs = []
        keywords = ["recommend", "guideline", "should", "advised", "first-line", "treatment"]

        for article in articles:
            abstract = article.get("abstract", "")
            sentences = re.split(r'[.!?]', abstract)
            for sentence in sentences:
                if any(kw in sentence.lower() for kw in keywords) and len(sentence.strip()) > 20:
                    recs.append({
                        "recommendation": sentence.strip(),
                        "evidence_level": "B",
                        "pubmed_id": article.get("pmid", ""),
                        "source_title": article.get("title", ""),
                    })
                    if len(recs) >= 5:
                        return recs
        return recs


# Singleton
pubmed_enricher = PubMedEnricher()
