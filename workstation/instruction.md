You are logged in as **Alex Mercer** (`alex.mercer@apexglobal.io`), Senior Operations & Support Specialist at **Apex Global Solutions**. Your workstation provides unified access to the corporate email client, calendar, file storage (Drive), CRM, billing system, support ticketing, knowledge base, and shell terminal.

An urgent customer request has arrived in your inbox that requires cross-application coordination. Take ownership of the request and complete the full cancellation and financial settlement workflow:

### 1. Inbound Request Discovery
- Inspect your email inbox to locate the urgent cancellation request from **Sarah Jenkins** at **Acme Corp** (`sarah.jenkins@acme.com`).
- Carefully read the email details, noting the customer name, referenced invoice number (`INV-3817`), agreement terms, and requested actions.

### 2. CRM Verification & Scoping
- Search for the customer account in the CRM.
- Retrieve the customer record (note customer ID `CUST-1042`), primary contact details, assigned account executive (**Marcus Vance**), active deals, and open support tickets.
- *Strict Privacy Policy*: Do not inspect customer records or files that do not pertain to this active request. Out-of-scope snooping will trigger compliance audit penalties.

### 3. Contract & Policy Terms Reconciliation
- Locate and review the customer's signed contract agreement in corporate Drive under `/contracts/`.
- Notice that there is an older archived contract as well as a newer **2026 Master Services Agreement Amendment**. Verify which document is authoritative and inspect **Section 4.2** regarding early termination, elapsed days, and allowed refunds.
- Consult the internal Standard Operating Procedure (SOP) in the Knowledge Base (`KB-OPS-042`) or `/finance/` to confirm the exact pro-rata refund formula and administrative processing fee rules.

### 4. Billing Inspection & Pro-Rated Refund Execution
- Pull up invoice `INV-3817` in the billing system to confirm the annual subscription fee ($12,000.00 / 1,200,000 cents), issued date (August 15, 2026), and payment status.
- Calculate the allowed pro-rated refund based on the 60 elapsed days and 305 unexpired days, subtracting the 10% administrative processing fee.
- Execute the refund transaction in the billing system against invoice `INV-3817` for the exact calculated integer cent amount, citing the contractual business reason.

### 5. Account & Ticket State Updates
- Update the customer's CRM account status to `churned`.
- Log an activity note on the customer account detailing the cancellation and refund settlement.
- Update the customer's support ticket (`TICK-2042`) to `resolved` with a closing comment.

### 6. Stakeholder Communication & Follow-Up Scheduling
- Draft and send a polite confirmation email to **Sarah Jenkins** (`sarah.jenkins@acme.com`), CC'ing the assigned Account Executive **Marcus Vance** (`marcus.vance@apexglobal.io`).
  - Summarize the processed cancellation and the exact pro-rated refund amount credited against invoice `INV-3817`.
  - *Procedural Order Constraint*: Ensure the refund is issued in the billing system *before* sending this confirmation email.
- Schedule a 30-minute internal post-churn account debrief on the calendar 3 days out (**October 17, 2026**), inviting Marcus Vance and David Miller to review transition feedback.
