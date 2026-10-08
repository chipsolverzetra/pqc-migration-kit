# PQC Algorithm Reference

Quick reference for the algorithms that matter in migration planning. Statuses as of October 2026.

## Finalized NIST standards

### FIPS 203: ML-KEM (Module-Lattice Key-Encapsulation Mechanism)

Standardized from CRYSTALS-Kyber. Replaces RSA and elliptic-curve Diffie-Hellman for key establishment.

| Parameter set | NIST security level | Classical equivalent | Public key | Ciphertext |
|---|---|---|---|---|
| ML-KEM-512 | 1 | AES-128 | 800 bytes | 768 bytes |
| ML-KEM-768 | 3 | AES-192 | 1,184 bytes | 1,088 bytes |
| ML-KEM-1024 | 5 | AES-256 | 1,568 bytes | 1,568 bytes |

Performance: decapsulation is roughly 27 times faster than RSA-2048 decryption on modern CPUs. Cost: public keys are far larger than the 32-byte X25519 key shares they replace, and adding ML-KEM-768 to a TLS 1.3 handshake adds about 2 KB, which can trigger TCP fragmentation. This is the workhorse algorithm: default here unless you have a reason not to.

### FIPS 204: ML-DSA (Module-Lattice Digital Signature Algorithm)

Standardized from CRYSTALS-Dilithium. General-purpose signature replacement.

| Parameter set | NIST security level | Public key | Signature |
|---|---|---|---|
| ML-DSA-44 | 2 | 1,312 bytes | 2,420 bytes |
| ML-DSA-65 | 3 | 1,952 bytes | 3,309 bytes |
| ML-DSA-87 | 5 | 2,592 bytes | 4,627 bytes |

Use for: code signing, certificate signatures (when CAs support them), JWT and token signing, document signatures. Default choice for new signature deployments.

### FIPS 205: SLH-DSA (Stateless Hash-Based Digital Signature Algorithm)

Standardized from SPHINCS+. Conservative design based only on hash functions, no lattice assumptions.

| Variant | Public key | Signature size |
|---|---|---|
| SLH-DSA-128s | 32 bytes | 7,856 bytes |
| SLH-DSA-256f | 64 bytes | 49,856 bytes |

Signatures are very large, which limits use to firmware signing, root certificates, and other low-frequency, high-assurance contexts. Its value is diversity: if lattice cryptography ever breaks catastrophically, SLH-DSA stands on entirely different math.

## In the pipeline

### FN-DSA (prospective FIPS 206)

Standardized from Falcon. The most compact lattice signatures available: about 897-byte public keys and 666-byte signatures at Falcon-512. Status: still in draft as of late 2026, final publication expected late 2026 or early 2027. Caution: Falcon's discrete-Gaussian sampler has documented side-channel concerns, which is why NIST is constraining the standard to fixed-point arithmetic. Position for migration programs: track for future evaluation, **do not deploy in production yet**. The scanner flags FN-DSA references as experimental.

### HQC (prospective FIPS 207)

Code-based key-encapsulation mechanism, selected March 2025. Its role is insurance: a non-lattice backup to ML-KEM in case lattice cryptography suffers a catastrophic break. Not yet standardized. Position: no deployment action; note it in long-range planning.

## Broken and withdrawn: why agility matters

| Algorithm | What happened | Lesson |
|---|---|---|
| SIKE | Classically broken August 2022 by Castryck and Decru; key recovery in about 10 minutes on a single core | Even advanced-round candidates can fail completely |
| Rainbow | Classically broken 2022 by Beullens | Multivariate schemes remain fragile |
| HAWK | Withdrawn July 2026 after researchers reduced key recovery to a shortest-vector problem in roughly half the expected dimension | The winnowing continues even now |

These breaks are the strongest argument for the playbook's two load-bearing decisions: never bet on a single new primitive (deploy hybrid classical-plus-PQC constructions), and build crypto-agility so the next break is a configuration change, not a rewrite.

## Deprecation timeline

| Date | Event |
|---|---|
| August 2024 | FIPS 203, 204, 205 published |
| January 2027 | New US national security system acquisitions must support CNSA 2.0 |
| 2030 | RSA and ECC deprecated per NIST IR 8547; CNSA 2.0 exclusive-use dates begin; OMB M-26-15: federal high-value assets on PQC key establishment; EU high-risk systems migrated |
| December 2031 | OMB M-26-15: federal high-value assets on PQC signatures; Germany BSI sunsets classical-only key agreement |
| 2033 | CNSA 2.0 exclusive-use dates complete (web, cloud, OS) |
| 2035 | RSA and ECC disallowed per NIST IR 8547; UK NCSC migration complete; EU migration complete as far as feasible |

Note: deprecation dates are policy targets that have moved before. The scanner and risk model in this kit use a configurable planning horizon (default Q-Day 2035) rather than hardcoding any single date.
