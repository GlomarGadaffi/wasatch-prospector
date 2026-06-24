# deanon-demo

demonstrates what ~$900 of commodity hardware can reconstruct about targets that multi-channel pseudonymity was supposed to protect. synthetic data only. built for accountability research — shows information asymmetries in RF privacy assumptions.

## threat model

targets believe multi-channel hopping / call signing / talkgroup rotation provide operational security. deanon-demo shows third-order inference:

1. **frequency association**: repeated presence on band X at time T
2. **temporal fingerprinting**: call duration patterns, inter-call intervals, shift schedules
3. **social graph**: co-presence with known entities across channels
4. **metadata correlation**: unit identifiers, encryption state changes, predictable call sequencing

combination reveals:
- likely unit/fleet membership
- operational tempo and shift patterns
- relationship networks (who coordinates with whom)
- mission type (from frequency + temporal profile)

all without decrypting a single call.

## dataset

synthetic multi-channel RF traffic archive with injected patterns (call sequences, frequency preferences, team affiliations). designed to be:
- reproducible (seed-based)
- auditable (full provenance metadata)
- researchable (extensible pattern library)

## use cases

- demonstrate privacy assumptions that fail under passive observation
- train policy makers on RF spectrum oversight / collection constraints
- baseline threat model for secure comms design (what's the realistic privacy floor?)

## notes

built for workshops and accountability discussions.
