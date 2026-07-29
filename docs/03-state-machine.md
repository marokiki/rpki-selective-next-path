# State-machine specification

## Global Current Suite state

```text
SECURE -> COMPROMISED -> RETIRED
```

No reverse transition is allowed.

## Next Trust Anchor state

```text
ABSENT -> OBSERVED -> ACCEPTED
```

`ACCEPTED` is allowed only while the Current Suite is `SECURE`.
The prototype may model the RFC 9691-inspired acceptance interval as a deterministic event count or timestamp.

## CA preparation states

```text
CURRENT_ONLY
NEXT_PARENT_AVAILABLE
NEXT_CA_STAGED
DUAL_PUBLISHED
ACTIVATED
CURRENT_RETIRED
```

Not every CA starts at the same point:

- RIR/NIR and prepared Delegated CAs can reach `NEXT_CA_STAGED` before compromise.
- Hosted CAs may remain `CURRENT_ONLY` until needed, then be created under a valid Next parent.
- Unprepared Delegated CAs cannot be created after compromise in the MVP.

## Required guards

### create_next_ca

Allowed when:

- parent has a valid path to an accepted Next TA; and
- either:
  - the CA is Hosted and the parent is its authoritative Hosted operator; or
  - the CA was prepared before compromise; or
  - a future explicit secure-enrollment mode is enabled.

Rejected when the only evidence is a Current-Suite signature after compromise.

### dual_publish

Allowed when the Next CA is staged and its objects validate.

### activate

Allowed when:

- Next path is valid;
- scoped resource semantics match;
- scoped VRP/ASPA semantics match;
- transition state is monotonic.

### fetch_failure_after_activation

Result is `UNAVAILABLE_NEXT`, never `FALLBACK_CURRENT`.

### retire_current

Allowed after activation and according to the configured compatibility/EOL policy.

## Event log

Every attempted transition records:

- schema version;
- timestamp or deterministic step number;
- CA identifier;
- previous state;
- requested action;
- resulting state;
- accepted boolean;
- machine-readable reason code.
