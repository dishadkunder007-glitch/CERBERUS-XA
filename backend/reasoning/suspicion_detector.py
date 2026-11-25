"""
CERBERUS-X: AI Reasoning & Evidence Verification Module
Component 3: Suspicious Evidence Indicator Detector

Detects indicators that evidence may require further verification.
Adheres strictly to the ethical safeguard:
- This module assesses evidence integrity indicators, not attempts to definitively authenticate documents or images.
- A missing timestamp is an indicator, not proof of manipulation.
- OCR errors are not proof of forgery.
- A contradiction does not automatically mean one source is fake.
- A source with no suspicious indicators is not automatically verified.
- The detector never produces unsupported accusations or declares evidence fake.

Deterministic, fully offline, local execution.
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Set, Union, Any
from datetime import datetime, timezone
from dateutil import parser as date_parser

from .schemas import (
    Claim,
    EvidenceItem,
    IndicatorCategory,
    SuspicionAssessment,
    SuspicionAssessmentLabel,
    SuspicionIndicator,
    SuspicionSeverity,
)


class SuspicionDetector:
    """
    Deterministic suspicious evidence indicator detector for CERBERUS-X.
    Audits metadata, content integrity, contradictions, duplications, and security patterns.
    """

    MANDATORY_CAVEAT = (
        "A suspicious indicator does not prove forgery, falsehood or manipulation. "
        "It serves solely as an audit signal warranting secondary verification."
    )

    MANDATORY_LIMITATIONS = [
        "A missing timestamp is an audit indicator, not proof of manipulation.",
        "OCR/parser extraction errors reflect character recognition limits, not proof of forgery.",
        "A contradiction between sources does not automatically mean one source is fake or fraudulent.",
        "A source with no suspicious indicators is not automatically verified as ground truth.",
        "Assessments evaluate integrity signals and do not produce unsupported accusations of forgery.",
    ]

    PROMPT_INJECTION_PATTERNS = [
        (r"ignore\s+(all\s+)?(previous|prior)\s+instructions", "Instruction override directive"),
        (r"system\s+override", "Privilege escalation / system override directive"),
        (r"disregard\s+(all\s+)?(evidence|facts|rules)", "Evidence disregard directive"),
        (r"you\s+must\s+(always\s+)?say\s+yes", "Output constraint injection directive"),
        (r"new\s+instruction\s*:", "Inline instruction injection directive"),
        (r"admin\s+mode\s*:\s*enabled", "Role spoofing directive"),
    ]

    CONTENT_ANOMALY_PATTERNS = [
        (r"\[REDACTED\]", "Document redaction marker detected"),
        (r"(\bLorem ipsum\b|\bSample text\b|\bTest placeholder\b)", "Boilerplate/placeholder text detected"),
        (r"(\bCONFIDENTIAL\b.*\bDO NOT DISTRIBUTE\b)", "Distribution restriction tag present"),
    ]

    # -------------------------------------------------------------------------
    # Comprehensive Item Assessment
    # -------------------------------------------------------------------------
    def assess_item(
        self,
        item: EvidenceItem,
        all_items: Optional[List[EvidenceItem]] = None,
        claims: Optional[List[Claim]] = None,
        reference_time: Optional[datetime] = None,
    ) -> SuspicionAssessment:
        """
        Assesses a single evidence item and returns a structured SuspicionAssessment.
        """
        all_items = all_items or [item]
        claims = claims or []
        now = reference_time or datetime.now(timezone.utc)

        indicators: List[SuspicionIndicator] = []

        # 1. Metadata & Provenance Audits
        indicators.extend(self._audit_metadata(item, now))

        # 2. Content & Extraction Integrity Audits
        indicators.extend(self._audit_content_integrity(item))

        # 3. Security & Untrusted Instructions Audit
        indicators.extend(self._audit_security_directives(item))

        # 4. Claim Alignment Audits
        indicators.extend(self._audit_claim_alignment(item, claims))

        # 5. Cross-Evidence Duplication & Contradiction Audits
        indicators.extend(self._audit_cross_evidence_item(item, all_items))

        # Determine aggregate severity & assessment label
        assessment_label, overall_severity, explanation = self._derive_overall_assessment(item.id, indicators)

        recommended_checks: List[str] = []
        for ind in indicators:
            if ind.recommended_verification_action and ind.recommended_verification_action not in recommended_checks:
                recommended_checks.append(ind.recommended_verification_action)

        return SuspicionAssessment(
            evidence_id=item.id,
            assessment_label=assessment_label,
            indicators=indicators,
            severity=overall_severity,
            explanation=explanation,
            recommended_checks=recommended_checks,
            limitations=list(self.MANDATORY_LIMITATIONS),
        )

    def assess_all(
        self,
        items: List[EvidenceItem],
        claims: Optional[List[Claim]] = None,
        reference_time: Optional[datetime] = None,
    ) -> Dict[str, SuspicionAssessment]:
        """Runs suspicion assessments across all evidence items."""
        return {
            item.id: self.assess_item(
                item=item,
                all_items=items,
                claims=claims,
                reference_time=reference_time,
            )
            for item in items
        }

    # -------------------------------------------------------------------------
    # Backward Compatibility: detect_indicators
    # -------------------------------------------------------------------------
    def detect_indicators(
        self,
        evidence_items: List[EvidenceItem],
        claims: Optional[List[Claim]] = None,
        reference_time: Optional[datetime] = None,
    ) -> List[SuspicionIndicator]:
        """Returns all detected indicators across a batch of evidence items and claims."""
        indicators: List[SuspicionIndicator] = []
        now = reference_time or datetime.now(timezone.utc)
        claims = claims or []

        for item in evidence_items:
            assessment = self.assess_item(item, all_items=evidence_items, claims=claims, reference_time=now)
            indicators.extend(assessment.indicators)

        # Also audit claim linkages for hallucinated evidence IDs
        ev_id_set = {ev.id for ev in evidence_items}
        for claim in claims:
            if not claim.evidence_ids:
                indicators.append(
                    SuspicionIndicator(
                        indicator_code="SUSP_UNSUPPORTED_CLAIM",
                        category=IndicatorCategory.CONTENT_INTEGRITY,
                        title="Claim Lacks Linked Evidence",
                        severity=SuspicionSeverity.HIGH,
                        explanation=f"Claim '{claim.id}' ('{claim.statement[:60]}...') cites no supporting evidence.",
                        caveat=self.MANDATORY_CAVEAT,
                        affected_claim_ids=[claim.id],
                        recommended_verification_action="Locate source record in Knowledge Graph.",
                    )
                )
            else:
                missing_evs = [eid for eid in claim.evidence_ids if eid not in ev_id_set]
                if missing_evs:
                    indicators.append(
                        SuspicionIndicator(
                            indicator_code="SUSP_NONEXISTENT_EVIDENCE_REFERENCE",
                            category=IndicatorCategory.CONTENT_INTEGRITY,
                            title="Reference to Non-Existent Evidence ID",
                            severity=SuspicionSeverity.HIGH,
                            explanation=f"Claim '{claim.id}' references evidence ID(s) {missing_evs} not in manifest.",
                            caveat=self.MANDATORY_CAVEAT,
                            affected_claim_ids=[claim.id],
                            recommended_verification_action="Verify pipeline consistency between Ingestion and Reasoning.",
                        )
                    )

        # De-duplicate by indicator_code + affected items
        seen: Set[str] = set()
        deduped: List[SuspicionIndicator] = []
        for ind in indicators:
            key = f"{ind.indicator_code}_{','.join(ind.affected_evidence_ids)}_{','.join(ind.affected_claim_ids)}"
            if key not in seen:
                seen.add(key)
                deduped.append(ind)

        return deduped

    # -------------------------------------------------------------------------
    # Internal Audit Modules
    # -------------------------------------------------------------------------
    def _audit_metadata(self, item: EvidenceItem, now: datetime) -> List[SuspicionIndicator]:
        indicators: List[SuspicionIndicator] = []
        meta = item.metadata

        # Indicator: Missing source attribution
        if not meta.source_id or not meta.source_id.strip():
            indicators.append(
                SuspicionIndicator(
                    indicator_code="SUSP_MISSING_SOURCE",
                    category=IndicatorCategory.PROVENANCE,
                    title="Missing Source Attribution",
                    severity=SuspicionSeverity.HIGH,
                    explanation=(
                        f"Evidence item '{item.id}' has no identifiable source_id. "
                        "Without source tracking, origin cannot be attributed."
                    ),
                    caveat=self.MANDATORY_CAVEAT,
                    affected_evidence_ids=[item.id],
                    recommended_verification_action="Request ingestion origin audit log from Member 1.",
                )
            )

        # Indicator: Missing document date
        c_date = self._parse_date(meta.creation_date)
        t_date = self._parse_date(meta.timestamp)
        if not c_date and not t_date:
            indicators.append(
                SuspicionIndicator(
                    indicator_code="SUSP_MISSING_DATE",
                    category=IndicatorCategory.TEMPORAL,
                    title="Missing Document Date",
                    severity=SuspicionSeverity.LOW,
                    explanation=(
                        f"Evidence item '{item.id}' has no recorded document timestamp or creation date. "
                        "Temporal context cannot be anchored."
                    ),
                    caveat=self.MANDATORY_CAVEAT,
                    affected_evidence_ids=[item.id],
                    recommended_verification_action="Inspect document headers or archive metadata for publication date.",
                )
            )

        # Indicator: Conflicting metadata (Modification before Creation)
        m_date = self._parse_date(meta.modification_date)
        if c_date and m_date and m_date < c_date:
            indicators.append(
                SuspicionIndicator(
                    indicator_code="SUSP_INVERTED_TIMESTAMPS",
                    category=IndicatorCategory.METADATA_CONSISTENCY,
                    title="Inverted Modification Timeline",
                    severity=SuspicionSeverity.MEDIUM,
                    explanation=(
                        f"Evidence item '{item.id}' records modification timestamp ({m_date.isoformat()}) "
                        f"prior to creation timestamp ({c_date.isoformat()})."
                    ),
                    caveat=self.MANDATORY_CAVEAT,
                    affected_evidence_ids=[item.id],
                    recommended_verification_action="Check file system clock calibration and packaging history.",
                )
            )

        # Indicator: Future timestamp
        for dt_name, dt_val in [("timestamp", t_date), ("creation_date", c_date), ("modification_date", m_date)]:
            if dt_val:
                try:
                    comp_now = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
                    comp_val = dt_val if dt_val.tzinfo else dt_val.replace(tzinfo=timezone.utc)
                    if comp_val > comp_now:
                        indicators.append(
                            SuspicionIndicator(
                                indicator_code="SUSP_FUTURE_TIMESTAMP",
                                category=IndicatorCategory.TEMPORAL,
                                title="Timestamp in the Future",
                                severity=SuspicionSeverity.MEDIUM,
                                explanation=f"Item '{item.id}' records {dt_name} in the future ({dt_val.isoformat()}).",
                                caveat=self.MANDATORY_CAVEAT,
                                affected_evidence_ids=[item.id],
                                recommended_verification_action="Verify system clock of ingestion node.",
                            )
                        )
                        break
                except Exception:
                    pass

        # Indicator: Unexplained alterations reported by upstream tools
        if meta.custom_attributes.get("altered") or meta.custom_attributes.get("tampered"):
            indicators.append(
                SuspicionIndicator(
                    indicator_code="SUSP_UPSTREAM_ALTERATION",
                    category=IndicatorCategory.CONTENT_INTEGRITY,
                    title="Upstream Alteration Flag Reported",
                    severity=SuspicionSeverity.MEDIUM,
                    explanation=f"Item '{item.id}' contains upstream alteration flag in custom attributes.",
                    caveat=self.MANDATORY_CAVEAT,
                    affected_evidence_ids=[item.id],
                    recommended_verification_action="Inspect raw ingestion audit report from Member 1.",
                )
            )

        return indicators

    def _audit_content_integrity(self, item: EvidenceItem) -> List[SuspicionIndicator]:
        indicators: List[SuspicionIndicator] = []
        meta = item.metadata

        # Indicator: Unusual formatting or extraction anomalies
        for pattern, desc in self.CONTENT_ANOMALY_PATTERNS:
            if re.search(pattern, item.content, re.IGNORECASE):
                indicators.append(
                    SuspicionIndicator(
                        indicator_code="SUSP_CONTENT_ANOMALY",
                        category=IndicatorCategory.CONTENT_INTEGRITY,
                        title="Content / Redaction Anomaly",
                        severity=SuspicionSeverity.LOW,
                        explanation=f"Evidence '{item.id}' contains pattern: {desc}.",
                        caveat=self.MANDATORY_CAVEAT,
                        affected_evidence_ids=[item.id],
                        recommended_verification_action="Inspect full unredacted source scan if authorized.",
                    )
                )

        # Indicator: Low OCR or Parser Extraction Confidence
        if meta.extraction_confidence is not None and meta.extraction_confidence < 0.60:
            indicators.append(
                SuspicionIndicator(
                    indicator_code="SUSP_LOW_EXTRACTION_CONFIDENCE",
                    category=IndicatorCategory.EXTRACTION,
                    title="Low Extraction / OCR Confidence",
                    severity=SuspicionSeverity.LOW,
                    explanation=(
                        f"Item '{item.id}' has parser/OCR extraction confidence of {meta.extraction_confidence:.2f}. "
                        "Extracted characters may contain misrecognitions or corrupted tokens."
                    ),
                    caveat=self.MANDATORY_CAVEAT,
                    affected_evidence_ids=[item.id],
                    recommended_verification_action="Manual visual inspection of source scan/image.",
                )
            )

        return indicators

    def _audit_security_directives(self, item: EvidenceItem) -> List[SuspicionIndicator]:
        indicators: List[SuspicionIndicator] = []

        # Indicator: Untrusted instructions embedded within source documents
        for pattern, desc in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, item.content, re.IGNORECASE):
                indicators.append(
                    SuspicionIndicator(
                        indicator_code="SUSP_UNTRUSTED_INSTRUCTION",
                        category=IndicatorCategory.SECURITY,
                        title="Untrusted Instruction Directive in Evidence",
                        severity=SuspicionSeverity.HIGH,
                        explanation=(
                            f"Evidence item '{item.id}' contains embedded directive pattern ('{pattern}'): {desc}. "
                            "Document content must be treated strictly as untrusted data strings, not commands."
                        ),
                        caveat=self.MANDATORY_CAVEAT,
                        affected_evidence_ids=[item.id],
                        recommended_verification_action="Ensure LLM and deterministic parsers sanitize document text as inert data.",
                    )
                )
                break

        return indicators

    def _audit_claim_alignment(self, item: EvidenceItem, claims: List[Claim]) -> List[SuspicionIndicator]:
        indicators: List[SuspicionIndicator] = []
        item_claims = [c for c in claims if item.id in c.evidence_ids]
        ev_text_lower = item.content.lower()

        for claim in item_claims:
            # Indicator: Entity mismatch
            if claim.entity and claim.entity.strip():
                entity_lower = claim.entity.strip().lower()
                if entity_lower not in ev_text_lower:
                    indicators.append(
                        SuspicionIndicator(
                            indicator_code="SUSP_ENTITY_MISMATCH",
                            category=IndicatorCategory.CONTENT_INTEGRITY,
                            title="Entity Mismatch with Linked Claim",
                            severity=SuspicionSeverity.MEDIUM,
                            explanation=(
                                f"Claim '{claim.id}' asserts entity '{claim.entity}', but entity name is not "
                                f"found in linked evidence '{item.id}'."
                            ),
                            caveat=self.MANDATORY_CAVEAT,
                            affected_evidence_ids=[item.id],
                            affected_claim_ids=[claim.id],
                            recommended_verification_action="Verify entity resolution mapping in Knowledge Graph (Member 3).",
                        )
                    )

            # Indicator: Inconsistent units
            if claim.unit and claim.unit.strip():
                unit_lower = claim.unit.strip().lower()
                # If claim asserts a specific unit (e.g. "kg", "usd") but evidence content explicitly mentions a different unit
                known_units = ["kg", "lbs", "usd", "eur", "km", "miles", "meters", "ft"]
                units_in_ev = [u for u in known_units if re.search(rf"\b{u}\b", ev_text_lower)]
                if units_in_ev and unit_lower in known_units and unit_lower not in units_in_ev:
                    indicators.append(
                        SuspicionIndicator(
                            indicator_code="SUSP_INCONSISTENT_UNITS",
                            category=IndicatorCategory.CONTENT_INTEGRITY,
                            title="Inconsistent Measurement Units",
                            severity=SuspicionSeverity.LOW,
                            explanation=(
                                f"Claim '{claim.id}' asserts unit '{claim.unit}', whereas linked evidence "
                                f"'{item.id}' records '{', '.join(units_in_ev)}'."
                            ),
                            caveat=self.MANDATORY_CAVEAT,
                            affected_evidence_ids=[item.id],
                            affected_claim_ids=[claim.id],
                            recommended_verification_action="Check unit conversion standards and source recording conventions.",
                        )
                    )

            # Indicator: Inconsistent dates between evidence and claims
            claim_date = self._parse_date(claim.timestamp)
            ev_date = self._parse_date(item.metadata.timestamp) or self._parse_date(item.metadata.creation_date)
            if claim_date and ev_date:
                diff_days = abs((claim_date - ev_date).total_seconds()) / 86400
                if diff_days > 365:  # Diverges by more than 1 year
                    indicators.append(
                        SuspicionIndicator(
                            indicator_code="SUSP_DATE_MISMATCH_CLAIM_EVIDENCE",
                            category=IndicatorCategory.TEMPORAL,
                            title="Inconsistent Date Between Claim and Evidence",
                            severity=SuspicionSeverity.MEDIUM,
                            explanation=(
                                f"Claim '{claim.id}' asserts date '{claim_date.date()}', but linked evidence "
                                f"'{item.id}' specifies date '{ev_date.date()}' (divergence: {int(diff_days)} days)."
                            ),
                            caveat=self.MANDATORY_CAVEAT,
                            affected_evidence_ids=[item.id],
                            affected_claim_ids=[claim.id],
                            recommended_verification_action="Confirm whether claim represents an earlier event or retroactive recording.",
                        )
                    )

        return indicators

    def _audit_cross_evidence_item(
        self,
        item: EvidenceItem,
        all_items: List[EvidenceItem],
    ) -> List[SuspicionIndicator]:
        indicators: List[SuspicionIndicator] = []
        item_content_norm = re.sub(r"\s+", " ", item.content.strip().lower())
        item_hash = (item.metadata.checksum_hash or "").strip().lower()

        # Indicator: Duplicate or near-duplicate sources presented as independent
        duplicate_evs: List[str] = []
        for other in all_items:
            if other.id != item.id:
                other_content_norm = re.sub(r"\s+", " ", other.content.strip().lower())
                other_hash = (other.metadata.checksum_hash or "").strip().lower()

                if (item_hash and other_hash and item_hash == other_hash) or (
                    item_content_norm and other_content_norm and item_content_norm == other_content_norm
                ):
                    duplicate_evs.append(other.id)

        if duplicate_evs:
            indicators.append(
                SuspicionIndicator(
                    indicator_code="SUSP_DUPLICATE_SOURCE_CLUSTER",
                    category=IndicatorCategory.DUPLICATION,
                    title="Duplicate Source Copy Detected",
                    severity=SuspicionSeverity.LOW,
                    explanation=(
                        f"Evidence item '{item.id}' shares verbatim content or hash with item(s) {duplicate_evs}. "
                        "Multiple identical copies must not be treated as independent corroborating confirmation."
                    ),
                    caveat=self.MANDATORY_CAVEAT,
                    affected_evidence_ids=[item.id] + duplicate_evs,
                    recommended_verification_action="Deduplicate source items before calculating cross-corroboration.",
                )
            )

        return indicators

    # -------------------------------------------------------------------------
    # Overall Assessment Derivation
    # -------------------------------------------------------------------------
    def _derive_overall_assessment(
        self,
        evidence_id: str,
        indicators: List[SuspicionIndicator],
    ) -> Tuple[SuspicionAssessmentLabel, SuspicionSeverity, str]:
        if not indicators:
            return (
                SuspicionAssessmentLabel.NO_SIGNIFICANT_INDICATORS,
                SuspicionSeverity.LOW,
                f"No significant suspicious indicators detected for evidence item '{evidence_id}'.",
            )

        has_high = any(i.severity == SuspicionSeverity.HIGH for i in indicators)
        has_med = any(i.severity == SuspicionSeverity.MEDIUM for i in indicators)

        if has_high:
            label = SuspicionAssessmentLabel.REQUIRES_REVIEW
            overall_severity = SuspicionSeverity.HIGH
            expl = f"Item '{evidence_id}' flagged with high-severity indicators ({len(indicators)} total); secondary manual review recommended."
        elif has_med:
            label = SuspicionAssessmentLabel.INDICATORS_FOUND
            overall_severity = SuspicionSeverity.MEDIUM
            expl = f"Item '{evidence_id}' contains moderate integrity indicators ({len(indicators)} total) warranting context verification."
        else:
            label = SuspicionAssessmentLabel.INDICATORS_FOUND
            overall_severity = SuspicionSeverity.LOW
            expl = f"Item '{evidence_id}' contains minor evidentiary gaps or extraction notices ({len(indicators)} total)."

        return label, overall_severity, expl

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
