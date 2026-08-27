# Incident Response Runbook

## LLM Red Team Framework — Operational Incident Playbooks

**Version:** 1.0  
**Last Updated:** 2026-08-27  
**Owner:** Security Engineering Team  
**Review Cadence:** Quarterly

---

## Table of Contents

1. [INC-001: New Jailbreak Technique Bypassing Detector](#inc-001-new-jailbreak-technique-bypassing-detector)
2. [INC-002: False Positive Blocking Legitimate Queries](#inc-002-false-positive-blocking-legitimate-queries)
3. [INC-003: Model Drift After Corpus Update](#inc-003-model-drift-after-corpus-update)
4. [INC-004: API Rate Limit Exhaustion](#inc-004-api-rate-limit-exhaustion)

---

## Severity Levels

| Level | Definition | Response Time | Escalation |
|-------|-----------|---------------|------------|
| SEV-1 | Active exploitation, safety bypass in production | 15 min | VP Engineering + Security Lead |
| SEV-2 | Degraded detection, partial bypass possible | 1 hour | Team Lead + On-call |
| SEV-3 | Minor gap, no active exploitation | 4 hours | On-call engineer |
| SEV-4 | Improvement opportunity, no immediate risk | Next sprint | Team backlog |

---

## INC-001: New Jailbreak Technique Bypassing Detector

### Severity: SEV-1

### Indicators
- External report of successful jailbreak against production system
- Spike in undetected adversarial prompts in monitoring dashboard
- Community disclosure (Twitter, research paper, CVE)
- Red team exercise discovering novel bypass

### Immediate Actions (0–15 minutes)

1. **Acknowledge & assess scope**
   ```bash
   # Check detection logs for the reported technique
   grep -i "<technique_pattern>" /var/log/detector/predictions.log | wc -l
   ```

2. **Activate temporary hardening** — Enable strict mode if available:
   ```python
   # config/detector.yaml
   detection:
     strict_mode: true
     confidence_threshold: 0.3  # Lower threshold = more aggressive blocking
   ```

3. **Notify stakeholders**
   - Page Security Lead and ML Engineer on-call
   - Post in #incident-response Slack channel
   - If SEV-1: notify VP Engineering

### Investigation (15–60 minutes)

4. **Reproduce the bypass**
   ```bash
   python -m llm_redteam_framework.cli predict --input "<jailbreak_prompt>"
   ```

5. **Categorize the technique**
   - [ ] Token smuggling / encoding bypass
   - [ ] Roleplay/persona manipulation
   - [ ] Context window overflow
   - [ ] Multi-turn escalation
   - [ ] Novel technique (document in detail)

6. **Assess blast radius**
   - How many users could be affected?
   - Is the technique published publicly?
   - Are similar techniques likely to work?

### Mitigation (1–4 hours)

7. **Add to corpus immediately**
   ```bash
   # Add adversarial samples to training corpus
   echo "<jailbreak_prompt>" >> data/adversarial/emergency_additions.txt
   python -m llm_redteam_framework.train --incremental
   ```

8. **Deploy rule-based patch** (while model retrains):
   ```python
   # Add to rules/emergency_patterns.py
   EMERGENCY_PATTERNS.append(
       r"<regex_matching_technique>"
   )
   ```

9. **Validate fix**
   ```bash
   python -m pytest tests/ -x
   python benchmarks/external_validation.py
   ```

10. **Deploy hotfix**
    ```bash
    git checkout -b hotfix/jailbreak-<technique>
    # ... commit changes ...
    # Fast-track review with security team
    ```

### Recovery & Follow-up

11. **Run full benchmark suite** to confirm no regression
12. **Update external_validation.py** with new fixture
13. **Write post-incident review** within 48 hours
14. **Update threat model** in OWASP mapping document
15. **Schedule corpus refresh** if systemic gap identified

---

## INC-002: False Positive Blocking Legitimate Queries

### Severity: SEV-2 (SEV-1 if affecting >5% of traffic)

### Indicators
- User complaints about blocked queries that are clearly benign
- Spike in detection rate without corresponding threat increase
- Customer support tickets about "AI not responding"
- Monitoring alert: false positive rate > 2%

### Immediate Actions (0–30 minutes)

1. **Quantify the impact**
   ```bash
   # Check false positive rate in last hour
   python -m llm_redteam_framework.metrics --window 1h --metric fpr
   ```

2. **Collect blocked samples** for analysis:
   ```bash
   # Export recently blocked benign-looking queries
   python -m llm_redteam_framework.cli export-blocked \
     --since "1 hour ago" \
     --output /tmp/blocked_review.jsonl
   ```

3. **If rate > 5%: raise detection threshold temporarily**
   ```python
   # config/detector.yaml
   detection:
     confidence_threshold: 0.8  # Raise from default 0.5
   ```

### Investigation (30 minutes – 2 hours)

4. **Identify the pattern** in false positives:
   - Common keywords triggering detection?
   - Specific user demographic or use case?
   - Recent model update correlated?

5. **Root cause analysis**
   - [ ] Recent corpus update introduced noisy samples
   - [ ] Feature drift in input distribution
   - [ ] Threshold misconfiguration
   - [ ] Bug in preprocessing pipeline

6. **Test proposed fix on held-out set**
   ```bash
   python -m llm_redteam_framework.evaluate \
     --dataset data/benign/validation.jsonl \
     --threshold 0.7
   ```

### Mitigation

7. **Adjust threshold or retrain**
   ```bash
   # Option A: Threshold adjustment
   python -m llm_redteam_framework.tune --target-fpr 0.01

   # Option B: Add benign samples and retrain
   python -m llm_redteam_framework.train --augment-benign
   ```

8. **Validate both precision and recall haven't degraded**
   ```bash
   python benchmarks/external_validation.py
   # Ensure F1 >= 0.85 still holds
   ```

9. **Deploy and monitor**
   - Watch FPR for 2 hours post-deploy
   - Set alert if FPR exceeds 1.5%

### Recovery

10. **Communicate resolution** to affected users/teams
11. **Add regression tests** for the specific false-positive patterns
12. **Review corpus balance** — ensure benign:adversarial ratio is appropriate

---

## INC-003: Model Drift After Corpus Update

### Severity: SEV-2

### Indicators
- F1 score drop > 0.05 after corpus update or retraining
- Benchmark regression detected in CI (external_validation.py fails)
- Performance benchmark shows latency increase > 2x
- A/B test shows degraded detection rate

### Immediate Actions (0–30 minutes)

1. **Rollback to last known-good model**
   ```bash
   # List model versions
   ls -la models/checkpoints/

   # Rollback
   cp models/checkpoints/v<last_good>/model.pkl models/active/model.pkl
   python -m llm_redteam_framework.cli verify-model
   ```

2. **Pin the previous corpus version**
   ```bash
   git log --oneline data/
   git checkout <last_good_commit> -- data/
   ```

3. **Notify ML team** about regression

### Investigation (30 minutes – 4 hours)

4. **Compare old vs new corpus**
   ```bash
   # Diff corpus statistics
   python -m llm_redteam_framework.corpus stats --version old
   python -m llm_redteam_framework.corpus stats --version new
   python -m llm_redteam_framework.corpus diff old new
   ```

5. **Identify problematic samples**
   ```bash
   # Find samples causing the most prediction errors
   python -m llm_redteam_framework.evaluate \
     --dataset data/test.jsonl \
     --output-errors /tmp/error_analysis.jsonl
   ```

6. **Check for**:
   - [ ] Mislabeled samples in new corpus additions
   - [ ] Class imbalance shift
   - [ ] Duplicate or near-duplicate samples
   - [ ] Distribution shift in prompt length/style

### Mitigation

7. **Clean corpus and retrain**
   ```bash
   # Remove identified problematic samples
   python -m llm_redteam_framework.corpus clean \
     --remove-duplicates \
     --verify-labels

   # Retrain with cleaned corpus
   python -m llm_redteam_framework.train --full
   ```

8. **Run complete validation suite**
   ```bash
   python -m pytest tests/ --cov --cov-fail-under=90
   python benchmarks/external_validation.py
   python benchmarks/detection_perf.py
   ```

9. **Gate deployment** on all benchmarks passing

### Recovery

10. **Document what went wrong** in corpus update process
11. **Add pre-merge corpus validation** to CI:
    - Label consistency check
    - Class balance check
    - Minimum F1 on validation set before merge
12. **Update corpus contribution guidelines**

---

## INC-004: API Rate Limit Exhaustion

### Severity: SEV-2 (SEV-1 if causing service outage)

### Indicators
- HTTP 429 responses from detection API
- Monitoring alert: request rate > 90% of limit
- Queue depth growing, latency increasing
- Downstream services timing out waiting for detection

### Immediate Actions (0–15 minutes)

1. **Confirm rate limit status**
   ```bash
   # Check current rate metrics
   curl -s http://localhost:8080/metrics | grep rate_limit
   ```

2. **Identify the source**
   ```bash
   # Top callers by request count
   python -m llm_redteam_framework.admin top-callers --window 5m
   ```

3. **If abuse: block offending client**
   ```bash
   python -m llm_redteam_framework.admin block-client --id <client_id> --duration 1h
   ```

4. **If legitimate surge: scale horizontally**
   ```bash
   # Scale detection service replicas
   kubectl scale deployment detector --replicas=5

   # Or increase rate limit temporarily
   python -m llm_redteam_framework.admin set-rate-limit \
     --global-rps 10000 \
     --per-client-rps 500
   ```

### Investigation (15–60 minutes)

5. **Determine root cause**
   - [ ] DDoS or abuse from single client
   - [ ] Legitimate traffic spike (product launch, viral moment)
   - [ ] Retry storm from downstream (cascading failure)
   - [ ] Misconfigured client sending duplicate requests
   - [ ] Batch job not respecting rate limits

6. **Check system health**
   ```bash
   # Verify detection service is healthy
   python -m llm_redteam_framework.cli healthcheck

   # Check resource usage
   kubectl top pods -l app=detector
   ```

### Mitigation

7. **Short-term: adjust capacity**
   ```yaml
   # config/rate_limits.yaml
   global:
     requests_per_second: 10000
     burst: 2000
   per_client:
     requests_per_second: 500
     burst: 100
   ```

8. **Medium-term: implement backpressure**
   - Enable request queuing with bounded queue
   - Add circuit breaker for downstream callers
   - Configure graceful degradation (return cached results)

9. **If retry storm: fix the source**
   - Ensure clients use exponential backoff
   - Add jitter to retry intervals
   - Set maximum retry attempts

### Recovery

10. **Return to normal rate limits** once traffic normalizes
11. **Scale back replicas** to baseline
12. **Review and update capacity planning**
    - Current peak vs provisioned capacity
    - Auto-scaling thresholds
    - Rate limit values per tier
13. **Update client SDKs** with proper retry logic if needed
14. **Add load testing** to release process

---

## General Incident Process

### Communication Template

```
Subject: [SEV-X] LLM Red Team Framework — <Brief Description>

Status: Investigating | Mitigating | Resolved
Impact: <Who/what is affected>
Start Time: <When first detected>
Current Actions: <What we're doing now>
ETA: <Expected resolution time>
Next Update: <When we'll update again>
```

### Post-Incident Review Template

1. **Summary**: What happened?
2. **Timeline**: Key events with timestamps
3. **Impact**: Users affected, duration, data implications
4. **Root Cause**: Why did this happen?
5. **Resolution**: What fixed it?
6. **Action Items**: Preventive measures with owners and deadlines
7. **Lessons Learned**: What worked well, what didn't

### Useful Commands Reference

```bash
# Quick health check
python -m llm_redteam_framework.cli healthcheck

# Run all validations
python -m pytest tests/ --cov --cov-fail-under=90
python benchmarks/external_validation.py
python benchmarks/detection_perf.py

# Check model performance
python -m llm_redteam_framework.evaluate --dataset data/test.jsonl

# Export recent predictions for analysis
python -m llm_redteam_framework.cli export-predictions --since "1h ago"

# Emergency threshold override
python -m llm_redteam_framework.admin set-threshold --value 0.8
```

---

## Escalation Contacts

| Role | Primary | Backup |
|------|---------|--------|
| On-call Engineer | Rotation schedule in PagerDuty | — |
| Security Lead | @security-lead | @security-backup |
| ML Engineer | @ml-lead | @ml-engineer-2 |
| VP Engineering | @vp-eng | @cto |

---

## Revision History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-08-27 | 1.0 | Initial runbook creation | Security Team |
