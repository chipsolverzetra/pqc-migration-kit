# PQC Migration Playbook

A program plan for migrating an organization from classical to post-quantum cryptography. Written for the person who has to run the program: the TPM, the program lead, the CISO's chief of staff. Companion to the scanner (`scanner/pqc_scanner.py`) and risk model (`scanner/risk_model.py`) in this kit.

The numbers below are grounded in the research landscape as of October 2026: NIST IR 8547 transition timelines, NSA CNSA 2.0, OMB M-26-15, the EU coordinated roadmap, and the UK NCSC timelines. Where the literature has no answer (notably program cost benchmarks), this playbook says so.

## How to use this document

1. Run the scanner to build your cryptographic inventory (Phase 0 output).
2. Score the inventory with the risk model to get a sequenced backlog.
3. Use the phases below as your program structure. Tailor durations to your estate size.
4. Report progress with the exec format in the Reporting section.

---

## Phase 0: Inventory and CBOM

**Objective.** Know what cryptography you have, where it lives, and what it protects. You cannot migrate what you cannot see.

**Activities.**
- Run automated discovery across source code, configs, containers, infrastructure as code, and certificate stores. The scanner in this kit is a starting point, not the whole answer: extend it with network traffic analysis and HSM audits.
- Build a cryptographic bill of materials (CBOM): every algorithm, key, certificate, library version, protocol version, and HSM, mapped to the service and data it protects.
- Record data secrecy lifetimes per system. This is the single most important inventory field: it drives prioritization through Mosca's inequality.
- Identify third-party dependencies: which vendors will migrate for you, and which leave the work to you. OMB M-26-15 explicitly requires a third-party coordination plan.

**Entry criteria.** Executive sponsor named. Migration team staffed (see Staffing).

**Exit criteria.** CBOM covers all production systems. Every entry has an owner, a data secrecy lifetime, and an upgrade difficulty rating. The inventory is automated and refreshable, not a spreadsheet.

**Typical duration.** 3 to 9 months for a mid-sized estate. GAO's October 2026 audit found most federal agencies still had incomplete inventories years into their mandates: treat inventory as a living artifact, not a milestone you pass once.

## Phase 1: Crypto-agility

**Objective.** Make algorithm changes possible without rewriting application logic. This is the highest-leverage phase and the one most often skipped.

**Activities.**
- Introduce abstraction layers at every cryptographic boundary: signing, key exchange, certificate handling, token issuance. No hardcoded algorithm names in application code or config.
- Establish a funded crypto-agility workstream with a named owner, starting in year one. Practitioner guidance is explicit on this point: agility is not an emergent property.
- Upgrade blocking dependencies: OpenSSL 1.1 to 3.x, legacy TLS pins removed, HSM firmware on a PQC-capable track.
- Define the algorithm approval process: who decides which PQC algorithms the organization adopts, and how new NIST standards (e.g., the pending FIPS 206 for FN-DSA) get evaluated.

**Entry criteria.** Phase 0 exit criteria met. Risk-ranked backlog exists.

**Exit criteria.** All high-risk surfaces from the backlog are behind an agility abstraction. CI gates reject newly introduced hardcoded classical algorithms.

**Typical duration.** 6 to 18 months, overlapping Phase 0 and Phase 2. This phase never fully ends: agility is a permanent property of the architecture.

## Phase 2: Hybrid deployment

**Objective.** Deploy classical-plus-post-quantum hybrid constructions on the highest-risk surfaces first, so that a break in either primitive is not fatal.

**Activities.**
- Start with key exchange: hybrid TLS 1.3 (e.g., X25519 with ML-KEM-768, standardized in RFC 10024, August 2026) on public-facing endpoints.
- Pilot ML-DSA signatures where signature verification is under your control (internal services, code signing pipelines).
- Treat the certificate layer as the long pole. As of 2026, zero hybrid post-quantum certificates were deployed across 32,011 surveyed domains: plan certificate migration against CA and browser root program timelines, not your own.
- France's ANSSI and Germany's BSI require hybrid constructions for long-term security claims. If you operate in those jurisdictions, hybrid is not optional.

**Entry criteria.** Crypto-agility abstractions in place on target surfaces. HSM vendor PQC roadmap confirmed.

**Exit criteria.** All findings with risk score 60+ are running hybrid or fully post-quantum constructions. PQC coverage telemetry is live.

**Typical duration.** 12 to 36 months for a large estate.

## Phase 3: PQC cutover

**Objective.** Move from hybrid to pure post-quantum constructions where the risk analysis supports it.

**Activities.**
- Cut over systems where both endpoints are under your control and the PQC-only risk is acceptable.
- Follow the UK NCSC's stated preference where applicable: a single migration to pure PQC rather than indefinite hybrid operation, once confidence in the standards warrants it.
- Keep hybrid on externally facing surfaces until counterparties (browsers, partners, exchanges) complete their own migrations.

**Entry criteria.** Phase 2 complete on in-scope surfaces. No open critical findings.

**Exit criteria.** Defined per system: the cutover checklist (algorithm, certificate, HSM firmware, partner readiness) is green.

**Typical duration.** 12 to 24 months, overlapping Phase 2.

## Phase 4: Decommission classical

**Objective.** Remove quantum-vulnerable algorithms from the estate entirely.

**Activities.**
- Disable RSA, ECDSA, and classical Diffie-Hellman in configs, libraries, and protocols.
- Rotate all long-lived keys and certificates issued under classical algorithms.
- Archive the CBOM as the audit record. NIST IR 8547 disallows the vulnerable algorithms after 2035: decommissioning is a compliance event, not just hygiene.

**Entry criteria.** Phase 3 complete. No production dependency on classical public-key cryptography.

**Exit criteria.** Scanner runs clean: zero critical or high findings. Independent audit confirms.

**Typical duration.** 6 to 12 months of cleanup after cutover.

### Program timeline reality check

Large enterprises report 5 to 10 year total migration timelines. An organization beginning serious migration in 2026 sits at the outer edge of feasibility for the 2030 deadlines (NIST deprecation of RSA/ECC in 2030, CNSA 2.0 exclusive-use dates in 2030, OMB M-26-15 high-value-asset deadlines of December 2030 for key establishment and December 2031 for signatures, EU high-risk systems by end of 2030). The phases above overlap heavily in practice: expect Phase 0 through 2 to run concurrently after the first year.

---

## RACI

| Activity | Program lead | Crypto architect | App migration engineers | Vendor management | Executive sponsor |
|---|---|---|---|---|---|
| Cryptographic inventory (CBOM) | A | R | C | I | I |
| Risk prioritization and sequencing | A | R | C | I | I |
| Crypto-agility refactoring | A | C | R | I | I |
| Algorithm selection (which PQC standards) | I | R | C | I | A |
| Hybrid deployment | A | C | R | C | I |
| HSM and vendor roadmap | A | C | I | R | I |
| Certificate migration | A | R | C | R | I |
| PQC cutover per system | A | C | R | I | I |
| Exec reporting and telemetry | R | C | I | I | A |
| Funding and staffing decisions | C | I | I | I | A |

R = responsible (does the work), A = accountable (owns the outcome), C = consulted, I = informed.

## Staffing guidance

A mid-sized migration program (50 to 200 services) typically needs:

- **Program lead (1).** Owns the backlog, the milestones, and the exec reporting. This is a TPM function: sequencing, dependency management, and cross-team coordination across InfoSec, platform, product engineering, and vendors.
- **Crypto architect (1 to 2).** Owns algorithm selection, hybrid design, and the agility architecture. Must be able to read the NIST standards and evaluate vendor claims.
- **App migration engineers (3 to 8).** Embedded with product teams to do the refactoring. The scarcest role: 97 percent of organizations report significant PQC skills gaps.
- **Vendor management (1).** Owns HSM, CA, and SaaS vendor roadmaps. Vendor lag is a top reported blocker; this role starts in Phase 0.
- **Executive sponsor (1).** A C-level or direct report who can resolve cross-team conflicts and protect funding across budget cycles. Multiyear programs die without this.

Scale linearly with estate size. Note: no public benchmarks exist for program cost. Build your own from the inventory: findings count times average remediation effort, plus vendor and HSM line items.

## Milestone template

Copy per phase, per business unit:

```
Milestone: [Phase 2: Hybrid TLS on public API]
Owner: [name]
Target date: [date]
Entry criteria met: [yes/no]
Deliverables:
  - [ ] Hybrid key exchange enabled on [endpoints]
  - [ ] Rollback runbook tested
  - [ ] Telemetry: PQC handshake percentage reporting
Exit criteria:
  - [ ] 100% of in-scope endpoints negotiating hybrid
  - [ ] Zero customer-facing incidents attributed to the change
  - [ ] CBOM updated
Risks and mitigations:
  - [risk]: [mitigation]
```

## Exec reporting format

Report monthly to the sponsor, quarterly to the board. One page.

1. **PQC coverage %.** Share of inventoried cryptographic operations running hybrid or pure post-quantum constructions. This is the headline KPI.
2. **Migration velocity.** Findings remediated per month, and the trend. Are we accelerating or stalling?
3. **Top risks.** The three highest-scored open backlog items, in plain language: what breaks, and when.
4. **Mosca watchlist.** Count of findings already late by Mosca's rule (x + y > z). This number should go down every month.
5. **Blockers.** Vendor delays, staffing gaps, decisions needed from the sponsor. Each with an owner and a date.

## Risk register starter

| Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|
| HSM vendor misses PQC firmware date | High | High | Dual-vendor strategy; software fallback for non-regulated workloads | Vendor management |
| Newly standardized algorithm breaks (SIKE precedent) | Medium | High | Hybrid deployment everywhere; crypto-agility workstream | Crypto architect |
| Certificate migration blocked by CA/root program timelines | High | Medium | Track Cloudflare MTC and browser root program policies; plan hybrid certs | Crypto architect |
| Skills shortage slows app migration | High | Medium | Start hiring and training in Phase 0; use consultants for spike work | Program lead |
| Harvest-now-decrypt-later exposure on long-lived data | High | High | Prioritize by secrecy lifetime; hybrid key exchange first | Program lead |
| Scope creep: inventory keeps growing | Medium | Medium | Automated refresh; freeze scope per phase gate | Program lead |
| Budget cut in year 3 of a 7-year program | Medium | High | Tie funding to compliance deadlines (2030/2035); report coverage monthly | Executive sponsor |
