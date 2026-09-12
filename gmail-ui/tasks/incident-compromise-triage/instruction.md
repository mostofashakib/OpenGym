Can you take ownership of the mailbox triage and containment response following reports of a suspected upstream third-party security incident?

Leadership received conflicting alerts over the past 24 hours regarding a critical API key leak and an urgent MFA credential alert. Stale summaries claim everything has been handled, but unverified indicators suggest an ongoing compromise and potential targeted spear-phishing. I need you to work through the mailbox, uncover what actually happened, and take decisive, defensible containment and triage actions:

1. **Vendor Incident & Key Exposure Disclosure**:
   - Investigate incoming communications from our critical vendors.
   - Locate the genuine disclosure from DataPipe Analytics security team (`security-response@datapipe-analytics.io`) concerning compromised credential `KEY_PROD_SEC_8821` on the `DataPipe Ingestion API`.
   - Thoroughly review the incident report, star it (`isStarred: true`), mark it important (`isImportant: true`), mark as read (`isRead: true`), and apply the `important` label.

2. **Deceptive Phishing / Social Engineering Quarantine**:
   - A suspicious notification claiming to be from cloud infrastructure support (`security-update@cloudinfra-support.co`) asks engineers to urgently re-authenticate credentials at a typosquatted domain (`https://cloudinfra-support.co/mfa-reset`).
   - Identify this malicious message, quarantine it by moving it to the trash (`isTrash: true`), and label it as `SPAM`.

3. **Inbound Legal & Regulatory Compliance Hold**:
   - Inbound inquiries from outside counsel (`legal-counsel@company.com`) request an audit record and formal disclosure statement for regulatory notification under GDPR/SOC2.
   - Do not trash or archive legal communications. Keep them active in INBOX and star the legal inquiry thread (`T_LEGAL_04`).
   - Draft a comprehensive, formal disclosure statement addressed to `legal-counsel@company.com` with subject `Formal Incident Disclosure: DataPipe Ingestion API Compromise`, confirming:
     - Exposed credential identifier: `KEY_PROD_SEC_8821`
     - Impacted service: `DataPipe Ingestion API`
     - Containment status: Key rotated and revoked in production, downstream access logs isolated.

4. **Executive Briefing Draft**:
   - Prepare a containment status draft addressed to the VP of Engineering (`vp-eng@company.com`) with subject `Executive Incident Briefing: Upstream Vendor Containment`, summarizing:
     - The DataPipe key revocation
     - Phishing quarantine of `cloudinfra-support.co`
     - Confirmation of zero unauthorized exfiltration on primary production databases.

5. **Operational Inbox Hygiene & Noise Deconfliction**:
   - Non-actionable automated notifications (routine shipping notifications from `shipping@logistics.net`, marketing digests, and routine CI green builds) should be archived (`isArchived: true` / removed from INBOX) to eliminate noise.
   - Under no circumstances should legitimate vendor disclosures, legal holds, or active customer security tickets be deleted or improperly moved to spam. Maintain strict scope cleanliness.

6. **Final Incident Response Submission**:
   - When all triage, tagging, quarantine, and drafts are in place, submit your final incident containment report via `submit_task` detailing the compromised key, the quarantined threat vector, and the draft confirmations.
