Can you take ownership of the critical production server degradation incident on `app-node-04.prod.corp`?

At 02:15 UTC, automated monitoring triggered high-severity alerts indicating that our core transaction capabilities are completely offline, disk capacity is nearing total exhaustion, and on-call engineers report conflicting diagnoses. Preliminary notes claim a network partition, but system telemetry indicates localized host instability.

I need you to thoroughly investigate the system, diagnose the underlying root causes, and perform decisive, defensible remediation:

1. **Process Triage & Resource Starvation**:
   - Investigate running system processes and resource utilization.
   - Identify the rogue background process leaking memory and CPU resources (`worker-leak.py` with PID `4921`), and terminate it immediately to halt further degradation.

2. **Disk Space Reclamation**:
   - The root partition is dangerously close to 100% capacity due to runaway unrotated logs.
   - Locate the bloated debug dump file in `/var/log/app/debug_trace.log` and safely truncate or remove it to restore filesystem headroom to healthy levels (at least 70% free disk space).

3. **Service Configuration Recovery**:
   - Inspect the failing `payment-processor.service` unit and check recent system logs to determine why it failed to boot.
   - Review `/etc/payment-processor/config.yaml`:
     - Repair the database connection parameters to use host `db-primary.internal` and standard PostgreSQL port `5432` (reverting the misconfigured port `9999` and invalid replica hostname).

4. **Security & Permission Hardening**:
   - Verify file permissions for sensitive credentials.
   - The service refuses to boot when private keys have permissive access. Secure `/etc/ssl/certs/payment-api.key` with strict permissions (`0600` / read-write by owner only).

5. **Service Restoration & Verification**:
   - Restart the `payment-processor` service and verify that its status is `active (running)`.
   - Ensure all other critical services (`nginx`, `sshd`) remain healthy and uninterrupted.

6. **Final Remediation Sign-Off**:
   - Once all remediations are verified and the payment processor is successfully running, submit your final incident sign-off report via `submit_task` detailing the terminated PID, reclaimed disk capacity, repaired configuration parameters, and confirmed service health.
