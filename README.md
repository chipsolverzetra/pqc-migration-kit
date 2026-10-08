# pqc-migration-kit

A practical toolkit for running a post-quantum cryptography (PQC) migration program. Scan a codebase for quantum-vulnerable cryptography, score the findings with a risk model built on Mosca's inequality, and generate an executive-ready migration report.

Built by **Rea Ara**, former Google Senior TPM, NYU cybersecurity graduate student. This kit is the companion to my paper on PQC migration as an organizational program: the thesis is that the binding constraint on migration is no longer cryptographic science, it is organizational execution.

## Why this exists

NIST has finalized the post-quantum standards (FIPS 203, 204, 205). Policy deadlines cluster in 2030 to 2035. Yet only a single-digit share of enterprises have moved past assessment, 97 percent report significant PQC skills gaps, and no reputable literature describes how to staff and govern one of these migrations as a program. This kit is a starting point for the team that has to do the work.

## Quickstart: scan the demo in 5 minutes

The repo ships with **Rea Pay**, a fictional payments platform with deliberately vulnerable cryptography (ECDSA/secp256k1 ledger signing, RSA-2048 key wrapping, RS256 JWTs, pinned TLS 1.2, MD5 checksums, SHA-1 HMACs). All standard library, no installs needed.

```bash
# 1. Scan the demo codebase for quantum-vulnerable cryptography
python3 scanner/pqc_scanner.py --target demo/rea-pay --output /tmp/inv.json

# 2. Score the findings into a prioritized backlog (Mosca's inequality)
python3 scanner/risk_model.py --inventory /tmp/inv.json \
    --services demo/rea-pay/services.yaml --output /tmp/backlog.json

# 3. Generate the executive report
python3 dashboard/generate_report.py --inventory /tmp/inv.json \
    --backlog /tmp/backlog.json --output /tmp/report.html
```

Open `/tmp/report.html` in a browser: summary cards, phase distribution, top recommendations, and the full prioritized backlog.

## Project structure

```
pqc-migration-kit/
  scanner/
    patterns.py        # detection rules: RSA, ECDSA, DH, JWT algs, TLS versions,
                       # weak hashes, certs, HSM refs, hardcoded algorithm config
    pqc_scanner.py     # CLI: walk a tree, emit a JSON cryptographic inventory
    risk_model.py      # CLI: score findings with Mosca's inequality (x + y > z),
                       # attribute to services, recommend a migration phase
  playbook/
    migration-playbook.md   # the program plan: phases 0-4, RACI, staffing,
                            # milestone template, exec reporting format, risk register
    algorithm-reference.md  # FIPS 203/204/205, FN-DSA draft status, HQC backup,
                            # SIKE/Rainbow/HAWK breaks, deprecation timeline
  demo/rea-pay/        # fictional payments platform with vulnerable crypto
    ledger_service.py      # ECDSA secp256k1 transaction signing
    custody_service.py     # RSA-2048 key wrapping, RS256 JWT issuance
    stablecoin_service.py  # pinned TLS 1.2, MD5 checksums, SHA-1 HMAC
    config.yaml, .env.example, Dockerfile
    keys/server-rsa.crt    # clearly labeled FAKE key for the demo
    terraform/main.tf      # TLS 1.2 ALB policy
    services.yaml          # service catalog for the risk model
  dashboard/
    generate_report.py # CLI: inventory + backlog -> static HTML report
  examples/
    sample-inventory.json
    sample-backlog.json
```

## The risk model in one paragraph

Each finding gets x (data secrecy years, from your `services.yaml`), y (migration effort in years, from upgrade difficulty), and z (years to your Q-Day planning horizon, default 2035). Risk score = (x + y) / z scaled to 100 and weighted by algorithm (RSA and ECDSA at full weight, weak hashes lower, finalized PQC at zero). A score of 100 means the finding is already late by Mosca's rule. Findings scoring 60 or above are recommended for Phase 2 (hybrid deployment now); the rest go through Phase 1 (crypto-agility) first.

## Key design decisions

- **Hybrid first.** The SIKE, Rainbow, and HAWK breaks argue against betting on any single new primitive. The playbook recommends classical-plus-PQC hybrid constructions during transition.
- **Crypto-agility is a workstream, not a wish.** The scanner flags hardcoded algorithm selection because every migration dies on code that cannot change its mind.
- **FN-DSA is flagged experimental.** Still in draft with known side-channel concerns: the scanner marks it DO NOT DEPLOY.
- **Certificates are the long pole.** A 2026 study found zero hybrid post-quantum certificates deployed across 32,011 domains. The playbook plans certificate migration against CA and root program timelines.

## Status and roadmap

This is a working starter kit, not a finished product. Planned next: network traffic analysis for the scanner, HSM audit helpers, a CBOM export format, and CI integration so new classical crypto fails the build.

## License

MIT. See LICENSE.
