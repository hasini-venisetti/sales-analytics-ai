"""Vectorless RAG: Hierarchical structured retrieval without embeddings."""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from app.config import BASE_DIR

GLOSSARY_PATH = BASE_DIR / "app" / "knowledge" / "glossary.json"


class VectorlessRAG:
    """Retrieves exact business definitions and entity synonyms via deterministic hierarchical search."""

    def __init__(self, glossary_path: Path = GLOSSARY_PATH):
        with open(glossary_path, "r", encoding="utf-8") as f:
            self.glossary = json.load(f)

    def retrieve(self, query: str) -> Dict[str, Any]:
        """Scans query against hierarchical glossary and returns matched domain context."""
        q_clean = re.sub(r"[^\w\s]", " ", query.lower())
        tokens = set(q_clean.split())

        matched_metrics = []
        for metric_id, data in self.glossary["metrics"].items():
            for syn in data["synonyms"]:
                if syn in q_clean or all(t in tokens for t in syn.split()):
                    matched_metrics.append({
                        "metric": metric_id,
                        "canonical": data["canonical"],
                        "definition": data["definition"],
                        "formula": data["formula"]
                    })
                    break

        matched_entities: Dict[str, List[str]] = {
            "products": [],
            "regions": [],
            "categories": [],
            "channels": [],
            "months": []
        }

        # Match products
        for canonical, syns in self.glossary["entities"]["products"].items():
            if any(s in q_clean for s in syns):
                matched_entities["products"].append(canonical)

        # Match regions
        for canonical, syns in self.glossary["entities"]["regions"].items():
            if any(s in q_clean for s in syns):
                matched_entities["regions"].append(canonical)

        # Match categories
        for canonical, syns in self.glossary["entities"]["categories"].items():
            if any(s in q_clean for s in syns):
                matched_entities["categories"].append(canonical)

        # Match channels
        for canonical, syns in self.glossary["entities"]["channels"].items():
            if any(s in q_clean for s in syns):
                matched_entities["channels"].append(canonical)

        # Match months
        for canonical, syns in self.glossary["entities"]["months"].items():
            if any(s in q_clean for s in syns):
                matched_entities["months"].append(canonical)

        return {
            "query": query,
            "matched_metrics": matched_metrics,
            "matched_entities": matched_entities,
            "prompt_context": self._format_prompt_context(matched_metrics, matched_entities)
        }

    def _format_prompt_context(self, metrics: List[Dict[str, Any]], entities: Dict[str, List[str]]) -> str:
        """Format retrieved context for injection into LLM prompt."""
        lines = ["--- Grounded Domain Context (Vectorless RAG) ---"]
        if metrics:
            lines.append("Business Metrics:")
            for m in metrics:
                lines.append(f"- {m['metric']}: {m['definition']} (Formula: {m['formula']})")
        if any(entities.values()):
            lines.append("Entity Grounding:")
            for ent_type, values in entities.items():
                if values:
                    lines.append(f"- {ent_type.capitalize()}: {', '.join(values)}")
        lines.append("-------------------------------------------------")
        return "\n".join(lines)
