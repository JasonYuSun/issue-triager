from __future__ import annotations

import json
import re
from typing import List

from .base import BaseLLM


class MockLLM(BaseLLM):
    """Deterministic rules-based mock that aligns with TRIAGE_CRITERIA.md."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        title = self._extract_field(user_prompt, "Issue Title:")
        body = self._extract_field(user_prompt, "Issue Body:")
        repo = self._extract_field(user_prompt, "Repository:")
        url = self._extract_field(user_prompt, "Issue URL:")
        text = f"{title}\n{body}\n{repo}\n{url}".lower()

        word_count = len((title + " " + body).split())
        loud_user = body.isupper() or user_prompt.count("!") >= 3

        priority = "LOW"
        matched_rules: List[str] = []
        action_required = False
        confidence = 0.75
        missing_info_requests: List[str] = []
        reasoning = "Defaulting to LOW priority based on provided context."

        if word_count < 10:
            priority = "LOW"
            matched_rules.append("Rule D: Insufficient Information")
            missing_info_requests = [
                "Please provide environment, error logs, and steps to reproduce."
            ]
            reasoning = "Issue too vague; requesting more details."
            confidence = 0.2
        else:
            if self._mentions_critical_infra(text):
                priority = "HIGH"
                matched_rules.append("Rule C: Critical Infrastructure Protection")
                reasoning = "Mentions critical shared infrastructure."
            if self._mentions_widespread(text):
                priority = "HIGH"
                matched_rules.append("Rule A: Silent Crisis")
                reasoning = "Describes widespread impact."
            if self._mentions_security(text):
                priority = "HIGH"
                matched_rules.append("HIGH: Security vulnerability")
                reasoning = "Security exposure detected."
            if self._production_outage(text):
                priority = "HIGH"
                matched_rules.append("HIGH: Production impact")
                reasoning = "Production outage or customer impact described."

            if priority == "HIGH":
                action_required = True
                confidence = 0.92
                if "shared-vpc-01" in text and "Rule C: Critical Infrastructure Protection" not in matched_rules:
                    matched_rules.append("Rule C: Critical Infrastructure Protection")
                if "root-dns-zone" in text and "Rule C: Critical Infrastructure Protection" not in matched_rules:
                    matched_rules.append("Rule C: Critical Infrastructure Protection")
                if "global-iam-policy" in text and "Rule C: Critical Infrastructure Protection" not in matched_rules:
                    matched_rules.append("Rule C: Critical Infrastructure Protection")
            else:
                if self._non_prod_pipeline(text):
                    priority = "MEDIUM"
                    matched_rules.append("MEDIUM: Non-prod pipeline or staging")
                    reasoning = "Non-production environment pipeline issue."
                    confidence = 0.82
                elif self._docs_request(text):
                    priority = "LOW"
                    matched_rules.append("LOW: Documentation")
                    reasoning = "Documentation or internal wiki update."
                    confidence = 0.78
                elif "sandbox" in text:
                    priority = "LOW"
                    reasoning = "Sandbox environment issue."
                    matched_rules.append("LOW: Sandbox")
                    confidence = 0.76
                else:
                    reasoning = "No high/medium indicators found; defaulting to LOW."
                    confidence = 0.7

        if "sandbox" in text and loud_user:
            if "Rule B: Loud User" not in matched_rules:
                matched_rules.append("Rule B: Loud User")

        labels = [f"priority:{priority.lower()}"]
        result = {
            "priority": priority,
            "action_required": action_required,
            "labels": labels,
            "reasoning": reasoning,
            "confidence": round(confidence, 3),
            "missing_info_requests": missing_info_requests,
            "matched_rules": matched_rules,
        }
        return json.dumps(result)

    @staticmethod
    def _extract_field(user_prompt: str, prefix: str) -> str:
        for line in user_prompt.splitlines():
            if line.strip().startswith(prefix):
                return line.replace(prefix, "").strip()
        return ""

    @staticmethod
    def _mentions_critical_infra(text: str) -> bool:
        return any(keyword in text for keyword in ["shared-vpc-01", "root-dns-zone", "global-iam-policy"])

    @staticmethod
    def _mentions_widespread(text: str) -> bool:
        return any(term in text for term in ["nobody", "everyone", "entire office", "widespread", "whole company"])

    @staticmethod
    def _mentions_security(text: str) -> bool:
        return any(term in text for term in ["security", "vulnerability", "publicly accessible", "public access", "leak", "exposed", "block public access"])

    @staticmethod
    def _production_outage(text: str) -> bool:
        production_terms = ["production", "prod "]
        outage_terms = [
            "outage",
            "down",
            "timeout",
            "504",
            "502",
            "503",
            "unable",
            "impact",
            "customers",
            "revenue loss",
            "latency",
            "gateway",
        ]
        mentions_prod = any(p in text for p in production_terms) and "not blocking production" not in text
        return mentions_prod and any(o in text for o in outage_terms)

    @staticmethod
    def _non_prod_pipeline(text: str) -> bool:
        env_terms = ["staging", "uat", "dev-cluster", "dev ", "qa", "non-prod"]
        pipeline_terms = ["pipeline", "ci/cd", "cicd", "terraform", "apply", "deploy"]
        return any(env in text for env in env_terms) or ("terraform" in text and "production" not in text)

    @staticmethod
    def _docs_request(text: str) -> bool:
        return bool(re.search(r"docs?|documentation|wiki|onboarding", text))
