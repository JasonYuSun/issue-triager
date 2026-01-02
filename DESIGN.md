# Design Document: issue-triager (v1.0)

## 1. Project Overview
**issue-triager** is an AI agent designed to automate the initial classification of DevOps support tickets. It acts as a "first responder" to ensure critical infrastructure failures are identified in seconds, while routine requests are categorized for later review.

## 2. The Problem Statement: The Triage Dilemma
In a fast-paced DevOps environment, the "Support Channel" repository often suffers from two main issues:

- **Manual Triage Delay**: If the Support Team is responsible for triage, they must context-switch constantly, or high-priority issues sit in the queue for too long.
- **Inconsistent User Triage**: If customers (developers) triage their own issues, they often lack the "big picture" (e.g., understanding how a failure in a shared network component affects the whole company), leading to either "over-triaging" (marking everything as High) or "under-triaging" (missing critical outages).

## 3. The Solution: Agentic AI
Unlike a simple keyword-based script, an Agentic AI solution can:

- **Understand Long Context**: Interpret the nuance of an issue description.
- **Make Judgments**: Compare the issue against a dynamic, version-controlled Triage Criteria document.
- **Take Action**: Not just categorize, but perform API calls to label issues, leave explanatory comments, and trigger external notifications.

## 4. Technical Architecture (Serverless-friendly)
The architecture is designed for high readability, minimal maintenance, and cost-efficiency.

### Tech Stack
- **Language**: Python 3.12 (Clean, type-hinted code).
- **Web Framework**: FastAPI (For handling GitHub webhooks with high performance and readability).
- **Compute**: Container-friendly serverless platform (scales to zero, easy to deploy).
- **AI Engine**: OpenAI ChatGPT (e.g., gpt-4o-mini) (Low latency, high reasoning capability).
- **Data Validation**: Pydantic (To ensure the LLM returns structured JSON).
- **CI/CD**: GitHub Actions (for automated deployment).

## 5. Agentic Interaction Flow
This section describes how the Python Agent facilitates the conversation between the GitHub Event and the LLM (ChatGPT).

### Step 1: Trigger & Context Assembly
- **User Event**: A developer opens a GitHub Issue.
- **Webhook**: GitHub sends a POST request to the deployed `/webhook/github` endpoint.

When the webhook is received, the Agent performs "Dynamic Context Injection":

- **System Prompt**: The Agent reads the current `TRIAGE_CRITERIA.md`.
- **User Prompt**: The Agent extracts the title and body of the GitHub issue.
- **Prompt Construction**: It combines these into a single instruction, telling the LLM to behave as a "DevOps Triage Expert" following the specific rules in the criteria. For example:

```python
system_instruction = f"""
You are the 'issue-triager' bot. 
Triaging Rules:
{triage_criteria_text} 

Return your answer in JSON format matching the TriageResult schema.
"""

user_input = f"Issue Title: {issue_title}\nIssue Body: {issue_body}"
```

### Step 2: Structured Reasoning (The JSON Contract)
The Agent uses Pydantic to enforce a schema. The LLM is instructed to return a structured response, ensuring the output is machine-readable for the next steps.

### Step 3: Action Execution (The "Agentic" Step)
The Agent does not just "suggest"; it "acts" by consuming the JSON output:

- **Labeling**: Calls the GitHub API to apply the `priority:{level}` label.
- **Commenting**: Posts the reasoning as a public comment on the issue. This provides transparency to the user and the support team.
- **Notification**: If `action_required` is True, the Agent triggers an outbound notification (e.g., to Slack/PagerDuty) to alert the on-call engineer.

## 6. The "Brain": TRIAGE_CRITERIA.md
The agent uses this document as its System Instruction. It is stored in the repository, allowing the team to update triage logic via Pull Requests without changing a single line of Python code.

### Sample Design TRIAGE_CRITERIA.md
```markdown
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
```

## 7. Reliability & The "Golden Dataset"
To prove the agent's value to stakeholders, we use a Golden Dataset to validate accuracy. For example:

```json
[
  {
    "id": "TC001",
    "title": "CRITICAL: Production API Gateway returning 504 Gateway Timeout in ap-southeast-2",
    "description": "Our monitoring system (Datadog) has alerted us that the production API gateway for the 'PaymentProcessor' service is failing. Since 08:30 UTC, we are seeing a 40% spike in 504 errors. \n\nEnvironment: Production\nRegion: ap-southeast-2\nImpact: Customers are unable to complete checkout, causing direct revenue loss. \n\nLogs:\n2026-01-01T08:31:05Z ERROR: upstream request timeout to service 'auth-provider'\n2026-01-01T08:31:10Z WARN: Shared-VPC-01 Transit Gateway attachment showing high latency.\n\nPreliminary investigation shows that internal routing via the Shared-VPC-01 seems unstable. This might be related to the network change implemented last night. We need the DevOps team to verify the Transit Gateway routing tables immediately as this is blocking the entire checkout flow.",
    "expected_priority": "HIGH",
    "rationale": "Involves Production environment, direct revenue loss, and specifically mentions Shared-VPC-01, which is a defined High-Priority edge case."
  },
  {
    "id": "TC002",
    "title": "Terraform apply failing in staging: Error: Provider produced inconsistent result after apply",
    "description": "Hi Support Team, I'm trying to deploy a new microservice in the staging environment but the pipeline is stuck. I've tried re-running the job three times but it keeps failing at the 'terraform apply' stage.\n\nError Message:\n│ Error: Provider produced inconsistent result after apply\n│ When applying changes to aws_appautoscaling_policy.cpu_policy, the plan was check to see if it was consistent with the real-world state.\n\nI think I might have a version mismatch between my local terraform version (1.5.0) and the one used in the GitHub Action runner. I've checked the documentation but couldn't find the specific version requirements for the new 'ScalingModule'. It's not blocking production, but it is delaying our QA testing for the sprint. Can someone take a look at my configuration in repo 'team-alpha-services'?",
    "expected_priority": "MEDIUM",
    "rationale": "Non-production environment (Staging). It is a technical 'how-to' or configuration issue that blocks a specific team's QA but doesn't affect the global organization."
  },
  {
    "id": "TC003",
    "title": "Request to update outdated links in 'Cloud-Onboarding.md'",
    "description": "While going through the internal developer portal documentation today, I noticed that several links in the 'Onboarding to AWS' section are pointing to the old Confluence space which was deprecated last year. \n\nSpecific Page: /docs/infrastructure/onboarding.md\nBroken Links:\n- http://confluence.old.company/x/infra-setup\n- http://confluence.old.company/x/iam-roles\n\nThese should be updated to point to the new Backstage portal. It's not an urgent issue, but it's a bit confusing for new hires who joined this week. I'd fix it myself but I don't have write access to the documentation repository. No rush on this, just thought I'd flag it for when someone has some downtime.",
    "expected_priority": "LOW",
    "rationale": "Documentation update, no impact on system availability or developer workflow, explicitly stated as 'no rush' by the user."
  },
  {
    "id": "TC004",
    "title": "Urgent!! I can't access the sandbox cluster!!!!!!",
    "description": "HEY TEAM!!! I AM TRYING TO LOG INTO THE SANDBOX CLUSTER TO TEST A SMALL CSS CHANGE AND MY KUBECTL IS GIVING ME AN ERROR. THIS IS SO FRUSTRATING I HAVE A DEADLINE TODAY FOR MY DEMO. \n\nError: error: You must be logged in to the server (Unauthorized)\n\nI TRIED RESETTING MY PASSWORD BUT IT DIDNT WORK. PLEASE FIX THIS NOW!!!!!!!!! I HAVE BEEN WAITING FOR 10 MINUTES ALREADY. MY BOSS IS WATCHING THIS DEMO AT 4PM.",
    "expected_priority": "LOW",
    "rationale": "The user is using 'urgent' language, but the technical context is a Sandbox cluster for a 'small CSS change.' This is an example of 'The Loud User' edge case where the agent must ignore the tone and prioritize based on impact."
  },
  {
    "id": "TC005",
    "title": "Possible Security Leak: Publicly accessible S3 bucket 'finance-reports-backup'",
    "description": "During a routine internal security audit, I discovered that the S3 bucket named 'finance-reports-backup-2025' has the 'Block Public Access' setting disabled. \n\nBucket ARN: arn:aws:s3:::finance-reports-backup-2025\nPolicy Snippet:\n{\n  \"Effect\": \"Allow\",\n  \"Principal\": \"*\",\n  \"Action\": \"s3:GetObject\",\n  \"Resource\": \"arn:aws:s3:::finance-reports-backup-2025/*\"\n}\n\nAlthough there are no files in there yet, this bucket is intended for sensitive financial data. If someone uploads a file, it will be immediately accessible to the public internet. This violates our 'Least Privilege' and 'Data Protection' policies. We need to enable public access blocks and verify if any other buckets in this account are misconfigured.",
    "expected_priority": "HIGH",
    "rationale": "Potential security breach and data exposure. Security vulnerabilities are categorized as HIGH priority regardless of whether a 'failure' has occurred yet."
  }
]
```

### Evaluation Script (eval_triage.py)
This script automates the "vibe check" into a quantitative report.

- **Input**: Loads the `golden_dataset.json`.
- **Execution**: Sends each case to the Agent logic.
- **Comparison**: Compares Agent output vs. Expected result.
- **Reporting**: Generates an Accuracy Score (%) and a Confusion Matrix.

## 8. Future Roadmap
- Multimodal Support: Use ChatGPT's multimodal capabilities to analyze screenshots of errors or architecture diagrams attached to issues.
- Issue-Resolution-Recommender: Use ChatGPT's long context window to build a system that can analyze a large number of issues and recommend most similar issues as reference to resolve the issue.

## 9. Security & Compliance
- Data Residency: Deploy within your chosen cloud region (e.g., australia-southeast1).
- Anonymization: Implementation of a pre-processing layer to scrub credentials and PII from issue descriptions before LLM ingestion.
