# Cloud Support Triage Policy (v1.0)

## Mission
To ensure that high-impact infrastructure issues are identified immediately while maintaining a clear and organized backlog for non-critical requests.

## 1. Priority Definitions

| Priority   | Criteria                                                                                 | Target Action                        |
| :--------- | :--------------------------------------------------------------------------------------- | :----------------------------------- |
| **HIGH**   | Production outages, security vulnerabilities, or failures in core shared infrastructure. | Immediate notification + Labeling.   |
| **MEDIUM** | Non-prod environment blockers, CI/CD pipeline failures, or resource requests.            | Labeling + Standard queue placement. |
| **LOW**    | General inquiries, documentation updates, or non-blocking suggestions.                   | Labeling + Backlog placement.        |

## 2. Technical Scope & Labels
- **HIGH:** Affects `Production`, `Shared-VPC`, `IAM-Root`, `DirectConnect`, or `Transit-Gateway`.
- **MEDIUM:** Affects `Staging`, `UAT`, `Dev-Cluster`, or individual developer credentials.
- **LOW:** Affects `Docs`, `Internal-Wiki`, or `Sandbox` environments.

## 3. Special & Edge Cases (Mandatory Rules)

### Rule A: The "Silent Crisis" (Contextual Escalation)
If a user describes a widespread failure (e.g., "Nobody in the London office can connect") even without using the word "Urgent," the Agent must prioritize this as **HIGH** due to the potential blast radius.

### Rule B: The "Loud User" (Tone Filtering)
Ignore excessive use of exclamation marks, caps lock, or emotional language (e.g., "FIX THIS NOW"). Prioritize based strictly on the technical impact described. If a user is shouting about a **Sandbox** password reset, it remains **LOW**.

### Rule C: Critical Infrastructure Protection
Any issue mentioning the following components must be marked **HIGH** automatically for manual verification:
- `shared-vpc-01`
- `root-dns-zone`
- `global-iam-policy`

### Rule D: Insufficient Information
If an issue contains fewer than 10 words or is too vague to categorize (e.g., "it's broken"), mark as **LOW** and use the reasoning field to request specific logs or environment details.
