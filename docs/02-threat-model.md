# Threat model

## Protected failure

The Current Suite becomes forgeable while the Next Suite and the pre-accepted Next Trust Anchor remain secure.

## Security objective

An attacker able to forge Current-Suite signatures must not be able to:

- replace an accepted Next Trust Anchor;
- introduce an attacker-controlled Next CA key solely through a Current signature;
- move an activated subtree back to Current;
- use Next repository suppression to trigger Current fallback.

## Trusted components

- Pre-accepted Next Trust Anchor state in the RP.
- Next Suite cryptography and private keys.
- Authoritative RIR/NIR resource registry.
- Hosted CA backend authorization and configuration store.
- Secure Next parent CA path.
- Persistent monotonic RP transition state.

## Out of scope

- Compromise of the Next Trust Anchor private key.
- Compromise of the Next Suite.
- Compromise of the Hosted management portal, registry database, HSM, or operator account.
- BGPsec UPDATE signatures and Router Certificates unless explicitly added in a later phase.
- Production emergency operating policy outside the modeled transition.

## Mandatory negative cases

1. Accepting a Next TA after Current compromise.
2. Current-signed introduction of a new Next child after compromise.
3. On-demand migration of an unprepared Delegated CA without independent enrollment.
4. Resource mismatch between Current and Next.
5. Next output mismatch before activation.
6. Current replay after activation.
7. Next repository failure after activation causing fallback.
8. Sequence/state rollback after process restart.
