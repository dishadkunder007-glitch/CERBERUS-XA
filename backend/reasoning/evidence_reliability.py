"""
CERBERUS-X: AI Reasoning & Evidence Verification Module
Component 1: Transparent Evidence Reliability Evaluator

Evaluates evidence items against explicit, configurable criteria:
1. Provenance and traceability (identifiable source, original location, cryptographic integrity)
2. Directness (direct primary evidence vs. indirect/contextual or hearsay)
3. Corroboration (independent corroboration with duplicate source exclusion)
4. Consistency (internal coherence, chronological sanity, absence of unresolved contradiction)
5. Completeness and context (presence of date, entity, units, and substantive content)

Important Safeguards:
- The score is an epistemic reliability evaluation, not mathematical proof that evidence is true.
- An unknown source is not automatically marked false.
- Missing information does not automatically mean fabricated evidence.
- A suspicious indicator does not automatically reduce the score to zero.
- Duplicate copies (identical text, hash, or filename/source) are excluded from independent corroboration.
- Author-expressed rhetorical confidence is excluded from scoring to avoid subjective bias.
- Criteria can be marked unassessed when relevant information is unavailable.
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from datetime import datetime
from dateutil import parser as date_parser

from .schemas import (
    Claim,
    EvidenceItem,
    EvidenceMetadata,
    EvidenceModality,
    DirectnessLevel,
    ReliabilityRating,
    ReliabilityLabel,
    CriterionScore,
    ReliabilityScorerConfig,
    EvidenceReliabilityResult,
)


class EvidenceReliabilityEvaluator:
    """
    Transparent, explainable evidence reliability evaluator.
    Configurable weighted scoring system with weights totaling 100%.
    """

    MANDATORY_LIMITATIONS = [
        "Reliability score is an epistemic assessment of provenance, directness, consistency, and corroboration; it does not constitute mathematical proof of truth.",
        "Author-expressed rhetorical confidence or assertive tone is excluded as a reliability metric to eliminate subjective persuasion bias.",
        "Missing information or unknown source attribution reflects evidential gaps, not proof of fabrication or falsehood.",
    ]

    def __init__(self, config: Optional[ReliabilityScorerConfig] = None):
        self.config = config or ReliabilityScorerConfig()

    def evaluate_item(
        self,
        item: EvidenceItem,
        all_items: Optional[List[EvidenceItem]] = None,
        all_claims: Optional[List[Claim]] = None,
        unassessed_criteria: Optional[Set[str]] = None,
    ) -> EvidenceReliabilityResult:
        """
        Evaluates a single evidence item across the 5 core criteria.
        Returns EvidenceReliabilityResult with scores between 0 and 100.
        """
        if not item.content or not item.content.strip():
            raise ValueError(f"Evidence item '{item.id}' content cannot be empty.")

        unassessed_criteria = unassessed_criteria or set()
        all_items = all_items or [item]
        all_claims = all_claims or []

        reasons: List[str] = []
        missing_info: List[str] = []
        limitations: List[str] = list(self.MANDATORY_LIMITATIONS)

        criteria_scores: Dict[str, CriterionScore] = {}

        # 1. Provenance and Traceability (0 - 100)
        crit_prov = self._eval_provenance(item, is_unassessed=("provenance" in unassessed_criteria))
        criteria_scores["provenance"] = crit_prov
        reasons.append(f"Provenance [{crit_prov.score if crit_prov.is_assessed else 'Unassessed'}]: {crit_prov.explanation}")
        missing_info.extend(crit_prov.missing_information)

        # 2. Directness (0 - 100)
        crit_dir = self._eval_directness(item, all_claims, is_unassessed=("directness" in unassessed_criteria))
        criteria_scores["directness"] = crit_dir
        reasons.append(f"Directness [{crit_dir.score if crit_dir.is_assessed else 'Unassessed'}]: {crit_dir.explanation}")
        missing_info.extend(crit_dir.missing_information)

        # 3. Corroboration with Duplicate Detection (0 - 100)
        crit_corrob, dup_count = self._eval_corroboration(
            item, all_items, all_claims, is_unassessed=("corroboration" in unassessed_criteria)
        )
        criteria_scores["corroboration"] = crit_corrob
        reasons.append(f"Corroboration [{crit_corrob.score if crit_corrob.is_assessed else 'Unassessed'}]: {crit_corrob.explanation}")
        missing_info.extend(crit_corrob.missing_information)
        if dup_count > 0:
            limitations.append(
                f"Detected {dup_count} duplicate or identical source copies in evidence corpus. Duplicate copies were excluded from independent corroboration."
            )

        # 4. Consistency (0 - 100)
        crit_consist = self._eval_consistency(
            item, all_claims, is_unassessed=("consistency" in unassessed_criteria)
        )
        criteria_scores["consistency"] = crit_consist
        reasons.append(f"Consistency [{crit_consist.score if crit_consist.is_assessed else 'Unassessed'}]: {crit_consist.explanation}")
        missing_info.extend(crit_consist.missing_information)

        # 5. Completeness and Context (0 - 100)
        crit_comp = self._eval_completeness(item, is_unassessed=("completeness" in unassessed_criteria))
        criteria_scores["completeness"] = crit_comp
        reasons.append(f"Completeness [{crit_comp.score if crit_comp.is_assessed else 'Unassessed'}]: {crit_comp.explanation}")
        missing_info.extend(crit_comp.missing_information)

        # Compute Transparent Weighted Score
        assessed_criteria = [c for c in criteria_scores.values() if c.is_assessed and c.score is not None]

        if not assessed_criteria:
            reliability_score = 0.0
            label = ReliabilityLabel.UNASSESSED
            rating = ReliabilityRating.UNRELIABLE
            limitations.append("All criteria were marked unassessed; no conclusive reliability score could be derived.")
        else:
            total_weight = sum(c.weight for c in assessed_criteria)
            raw_weighted_score = sum(c.score * c.weight for c in assessed_criteria)
            # Re-normalize if some criteria were unassessed
            if abs(total_weight - 1.0) > 1e-4 and total_weight > 0.0:
                reliability_score = round(raw_weighted_score / total_weight, 2)
                limitations.append(
                    f"Score re-normalized across {len(assessed_criteria)} assessed criteria (total weight: {total_weight:.2f})."
                )
            else:
                reliability_score = round(raw_weighted_score, 2)

            reliability_score = max(0.0, min(100.0, reliability_score))

            # Derive Qualitative Labels
            if reliability_score >= self.config.high_threshold:
                label = ReliabilityLabel.HIGH
                rating = ReliabilityRating.HIGH
            elif reliability_score >= self.config.moderate_threshold:
                label = ReliabilityLabel.MODERATE
                rating = ReliabilityRating.MEDIUM
            elif reliability_score >= self.config.low_threshold:
                label = ReliabilityLabel.LOW
                rating = ReliabilityRating.LOW
            else:
                label = ReliabilityLabel.LOW
                rating = ReliabilityRating.UNRELIABLE

        reasons.append(
            f"Modality '{item.modality.value}' evaluated strictly on provenance criteria without modality-based discrimination."
        )

        # Backward compatibility decimal score (0.0 to 1.0)
        overall_decimal = round(reliability_score / 100.0, 4)
        trace_dec = round((criteria_scores["provenance"].score or 0.0) / 100.0, 4)
        dir_dec = round((criteria_scores["directness"].score or 0.0) / 100.0, 4)
        corrob_dec = round((criteria_scores["corroboration"].score or 0.0) / 100.0, 4)
        consist_dec = round((criteria_scores["consistency"].score or 0.0) / 100.0, 4)
        comp_dec = round((criteria_scores["completeness"].score or 0.0) / 100.0, 4)

        return EvidenceReliabilityResult(
            evidence_id=item.id,
            reliability_score=reliability_score,
            reliability_label=label,
            criteria_scores=criteria_scores,
            reasons=reasons,
            missing_information=sorted(list(set(missing_info))),
            limitations=limitations,
            traceability_score=trace_dec,
            directness_score=dir_dec,
            corroboration_score=corrob_dec,
            consistency_score=consist_dec,
            completeness_score=comp_dec,
            overall_score=overall_decimal,
            rating=rating,
            modality_neutrality_flag=True,
        )

    def evaluate_all(
        self,
        items: List[EvidenceItem],
        claims: Optional[List[Claim]] = None,
        unassessed_criteria: Optional[Set[str]] = None,
    ) -> Dict[str, EvidenceReliabilityResult]:
        """Evaluates a batch of evidence items, properly accounting for cross-corroboration and duplicates."""
        results: Dict[str, EvidenceReliabilityResult] = {}
        for item in items:
            results[item.id] = self.evaluate_item(
                item=item,
                all_items=items,
                all_claims=claims,
                unassessed_criteria=unassessed_criteria,
            )
        return results

    # -------------------------------------------------------------------------
    # Criterion 1: Provenance & Traceability
    # -------------------------------------------------------------------------
    def _eval_provenance(self, item: EvidenceItem, is_unassessed: bool) -> CriterionScore:
        if is_unassessed:
            return CriterionScore(
                name="provenance",
                score=None,
                weight=self.config.provenance_weight,
                is_assessed=False,
                explanation="Provenance evaluation was explicitly marked unassessed.",
                missing_information=[],
            )

        score = 0.0
        explanations: List[str] = []
        missing: List[str] = []
        meta = item.metadata

        # Identifiable source
        if meta.source_id and meta.source_id.strip():
            score += 35.0
            explanations.append(f"Identifiable source system/repository ('{meta.source_id.strip()}').")
        else:
            missing.append("Identifiable source_id is absent.")
            explanations.append("Unknown or uncataloged source; origin cannot be verified.")

        # Author / Originating Organization
        if meta.author or meta.organization:
            score += 20.0
            author_desc = meta.author or meta.organization
            explanations.append(f"Originating party identified: {author_desc}.")
        else:
            missing.append("Originating author or organization is unspecified.")

        # Original File / Archive Reference
        if meta.filename and meta.filename.strip():
            score += 20.0
            explanations.append(f"Original file/archive reference documented ('{meta.filename.strip()}').")
        else:
            missing.append("Original filename or archive reference is absent.")

        # Physical / Logical Location (Page, Section, Table, Image, Record)
        locators: List[str] = []
        if meta.page_number is not None:
            locators.append(f"Page {meta.page_number}")
        if meta.section:
            locators.append(f"Section '{meta.section}'")
        if meta.table_id:
            locators.append(f"Table '{meta.table_id}'")
        if meta.image_id:
            locators.append(f"Image '{meta.image_id}'")
        if meta.record_id:
            locators.append(f"Record '{meta.record_id}'")

        if locators:
            score += 15.0
            explanations.append(f"Precise physical/logical reference provided ({', '.join(locators)}).")
        else:
            missing.append("Precise locator (page, section, table, or record) is missing.")

        # Cryptographic Integrity (Checksum / Digital Signature)
        if meta.checksum_hash or meta.digital_signature:
            score += 10.0
            explanations.append("Cryptographic hash or signature present for integrity tracking.")
        else:
            missing.append("Cryptographic hash or digital signature is not provided.")

        score = max(0.0, min(100.0, score))
        return CriterionScore(
            name="provenance",
            score=round(score, 1),
            weight=self.config.provenance_weight,
            is_assessed=True,
            explanation="; ".join(explanations),
            missing_information=missing,
        )

    # -------------------------------------------------------------------------
    # Criterion 2: Directness
    # -------------------------------------------------------------------------
    def _eval_directness(
        self,
        item: EvidenceItem,
        all_claims: List[Claim],
        is_unassessed: bool,
    ) -> CriterionScore:
        if is_unassessed:
            return CriterionScore(
                name="directness",
                score=None,
                weight=self.config.directness_weight,
                is_assessed=False,
                explanation="Directness evaluation was explicitly marked unassessed.",
                missing_information=[],
            )

        missing: List[str] = []
        directness_levels = {
            DirectnessLevel.PRIMARY: (100.0, "Direct primary observation, original record, or raw instrumentation log."),
            DirectnessLevel.SECONDARY: (70.0, "Secondary reporting, synthesis, or derivative analytical report."),
            DirectnessLevel.DERIVED: (55.0, "Derived or computed calculation based on other records."),
            DirectnessLevel.HEARSAY: (25.0, "Third-party hearsay or unverified quote without direct transcript."),
            DirectnessLevel.UNVERIFIED: (15.0, "Unverified submission without chain of observation."),
        }

        base_score, expl = directness_levels.get(
            item.directness,
            (40.0, "Indirect or contextual background evidence.")
        )

        # Check claim linkage if claims are provided
        linked_claims = [c for c in all_claims if item.id in c.evidence_ids]
        if linked_claims:
            expl += f" Directly cited by {len(linked_claims)} claim(s)."
        elif all_claims:
            missing.append("Evidence item is not explicitly bound to an asserted claim statement.")
            expl += " Indirect / background evidence (not explicitly linked to an asserted claim)."
            base_score = max(20.0, base_score - 15.0)

        score = max(0.0, min(100.0, base_score))
        return CriterionScore(
            name="directness",
            score=round(score, 1),
            weight=self.config.directness_weight,
            is_assessed=True,
            explanation=expl,
            missing_information=missing,
        )

    # -------------------------------------------------------------------------
    # Criterion 3: Corroboration with Duplicate Detection
    # -------------------------------------------------------------------------
    def _eval_corroboration(
        self,
        item: EvidenceItem,
        all_items: List[EvidenceItem],
        all_claims: List[Claim],
        is_unassessed: bool,
    ) -> Tuple[CriterionScore, int]:
        if is_unassessed:
            return (
                CriterionScore(
                    name="corroboration",
                    score=None,
                    weight=self.config.corroboration_weight,
                    is_assessed=False,
                    explanation="Corroboration evaluation was explicitly marked unassessed.",
                    missing_information=[],
                ),
                0,
            )

        missing: List[str] = []
        if len(all_items) <= 1:
            return (
                CriterionScore(
                    name="corroboration",
                    score=40.0,
                    weight=self.config.corroboration_weight,
                    is_assessed=True,
                    explanation="Standalone evidence item; no other sources available in the provided corpus to corroborate.",
                    missing_information=["Independent corroborating evidence is not present in the current corpus."],
                ),
                0,
            )

        item_content_norm = self._normalize_content(item.content)
        item_hash = (item.metadata.checksum_hash or "").strip().lower()
        item_source = (item.metadata.source_id or "").strip().lower()

        # Identify duplicate sources to exclude from independent confirmation
        duplicate_ids: Set[str] = set()
        independent_sources: Set[str] = set()

        # Find claims supported by this item
        item_claims = [c for c in all_claims if item.id in c.evidence_ids]

        for other in all_items:
            if other.id == item.id:
                continue

            other_content_norm = self._normalize_content(other.content)
            other_hash = (other.metadata.checksum_hash or "").strip().lower()
            other_source = (other.metadata.source_id or other.id).strip().lower()

            # Duplicate Check: Identical hash or identical text content
            is_duplicate = False
            if item_hash and other_hash and item_hash == other_hash:
                is_duplicate = True
            elif item_content_norm and other_content_norm and item_content_norm == other_content_norm:
                is_duplicate = True
            elif item_source and other_source and item_source == other_source:
                # Same source file and exact section/page
                if (
                    item.metadata.filename
                    and other.metadata.filename
                    and item.metadata.filename == other.metadata.filename
                    and item.metadata.page_number == other.metadata.page_number
                ):
                    is_duplicate = True

            if is_duplicate:
                duplicate_ids.add(other.id)
                continue

            # Independent corroboration check: Must be a different source repository/system
            if other_source != item_source:
                # Check claim alignment
                if item_claims:
                    for claim in item_claims:
                        if other.id in claim.evidence_ids:
                            independent_sources.add(other_source or other.id)
                else:
                    # Semantic keyword overlap for independent items
                    overlap_count = self._semantic_overlap(item.content, other.content)
                    if overlap_count >= 3:
                        independent_sources.add(other_source or other.id)

        indep_count = len(independent_sources)
        dup_count = len(duplicate_ids)

        if indep_count >= 2:
            score = 100.0
            expl = f"Strongly corroborated by {indep_count} independent sources ({', '.join(sorted(independent_sources))})."
        elif indep_count == 1:
            score = 75.0
            expl = f"Corroborated by 1 independent source ({list(independent_sources)[0]})."
        else:
            score = 40.0
            expl = "No independent corroborating sources identified in the provided evidence set."
            missing.append("Independent corroborating source confirmation is absent.")

        if dup_count > 0:
            expl += f" (Note: {dup_count} duplicate copy/copies detected and excluded from independent confirmation)."

        return (
            CriterionScore(
                name="corroboration",
                score=round(score, 1),
                weight=self.config.corroboration_weight,
                is_assessed=True,
                explanation=expl,
                missing_information=missing,
            ),
            dup_count,
        )

    # -------------------------------------------------------------------------
    # Criterion 4: Consistency
    # -------------------------------------------------------------------------
    def _eval_consistency(
        self,
        item: EvidenceItem,
        all_claims: List[Claim],
        is_unassessed: bool,
    ) -> CriterionScore:
        if is_unassessed:
            return CriterionScore(
                name="consistency",
                score=None,
                weight=self.config.consistency_weight,
                is_assessed=False,
                explanation="Consistency evaluation was explicitly marked unassessed.",
                missing_information=[],
            )

        score = 100.0
        explanations: List[str] = []
        missing: List[str] = []
        meta = item.metadata

        # Chronological Sanity Check
        c_date = self._parse_date(meta.creation_date)
        m_date = self._parse_date(meta.modification_date)
        if c_date and m_date:
            if m_date < c_date:
                # Safeguard: Do not make score zero for an anomaly
                score -= 30.0
                explanations.append("Chronological contradiction: modification date precedes creation date.")
            else:
                explanations.append("Chronological consistency verified between creation and modification.")

        # Parser / OCR extraction confidence check
        if meta.extraction_confidence is not None:
            if meta.extraction_confidence < 0.50:
                score -= 25.0
                explanations.append(f"Low extraction confidence ({meta.extraction_confidence:.2f}) indicates potential text corruption.")
            elif meta.extraction_confidence < 0.80:
                score -= 10.0
                explanations.append(f"Moderate extraction confidence ({meta.extraction_confidence:.2f}).")
            else:
                explanations.append(f"High extraction confidence ({meta.extraction_confidence:.2f}).")

        # Check for direct contradictions in linked claims
        item_claims = [c for c in all_claims if item.id in c.evidence_ids]
        if item_claims:
            for claim in item_claims:
                for other_claim in all_claims:
                    if other_claim.id != claim.id and other_claim.entity == claim.entity and other_claim.property == claim.property:
                        if other_claim.polarity != claim.polarity:
                            score -= 35.0
                            explanations.append(
                                f"Direct contradictory assertion found: Claim {claim.id} (polarity={claim.polarity}) vs Claim {other_claim.id} (polarity={other_claim.polarity})."
                            )
                            break

        if not explanations:
            explanations.append("No internal or contextual contradictions detected.")

        score = max(10.0, min(100.0, score))
        return CriterionScore(
            name="consistency",
            score=round(score, 1),
            weight=self.config.consistency_weight,
            is_assessed=True,
            explanation="; ".join(explanations),
            missing_information=missing,
        )

    # -------------------------------------------------------------------------
    # Criterion 5: Completeness & Context
    # -------------------------------------------------------------------------
    def _eval_completeness(self, item: EvidenceItem, is_unassessed: bool) -> CriterionScore:
        if is_unassessed:
            return CriterionScore(
                name="completeness",
                score=None,
                weight=self.config.completeness_weight,
                is_assessed=False,
                explanation="Completeness evaluation was explicitly marked unassessed.",
                missing_information=[],
            )

        score = 0.0
        explanations: List[str] = []
        missing: List[str] = []

        # 1. Temporal Context (Date / Timestamp)
        if item.metadata.timestamp or item.metadata.creation_date:
            score += 25.0
            explanations.append("Temporal context anchor present.")
        else:
            missing.append("Date or temporal context anchor is missing.")

        # 2. Entity / Subject Context
        # Search for named entities or capitalized subject tokens in content
        has_entity = bool(re.search(r"\b[A-Z][a-zA-Z0-9_-]{2,}\b", item.content))
        if has_entity:
            score += 25.0
            explanations.append("Identified subject/entity context present.")
        else:
            missing.append("Target subject or entity identifier is ambiguous.")

        # 3. Quantitative / Numerical Units or Concrete Property Attributes
        has_units_or_numbers = bool(re.search(r"\b\d+([.,]\d+)?\s*(%|[a-zA-Z$€£]{1,5})?\b", item.content))
        if has_units_or_numbers:
            score += 25.0
            explanations.append("Concrete quantitative/unit details present.")
        else:
            missing.append("Specific measurement units or quantitative details are absent.")

        # 4. Contextual Depth / Content Length
        content_len = len(item.content.strip())
        if content_len >= 80:
            score += 25.0
            explanations.append("Substantive contextual content length provided.")
        elif content_len >= 30:
            score += 15.0
            explanations.append("Moderate content excerpt length; partial surrounding context.")
        else:
            score += 5.0
            explanations.append("Fragmented or very brief text snippet.")
            missing.append("Surrounding narrative context is minimal.")

        score = max(0.0, min(100.0, score))
        return CriterionScore(
            name="completeness",
            score=round(score, 1),
            weight=self.config.completeness_weight,
            is_assessed=True,
            explanation="; ".join(explanations),
            missing_information=missing,
        )

    # -------------------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------------------
    @staticmethod
    def _normalize_content(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip().lower()

    @staticmethod
    def _semantic_overlap(text_a: str, text_b: str) -> int:
        words_a = {w.lower() for w in re.findall(r"\b[A-Za-z0-9_-]{4,}\b", text_a)}
        words_b = {w.lower() for w in re.findall(r"\b[A-Za-z0-9_-]{4,}\b", text_b)}
        stopwords = {"this", "that", "with", "from", "were", "been", "have", "said", "reported", "about", "which"}
        meaningful_a = words_a - stopwords
        meaningful_b = words_b - stopwords
        return len(meaningful_a.intersection(meaningful_b))

    @staticmethod
    def _parse_date(date_val: Optional[Union[datetime, str]]) -> Optional[datetime]:
        if not date_val:
            return None
        if isinstance(date_val, datetime):
            return date_val
        try:
            return date_parser.parse(str(date_val))
        except Exception:
            return None
