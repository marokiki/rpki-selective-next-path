# Design specification

## Objective

Reduce the steady-state cost of preparing an RPKI post-quantum migration while preserving the ability to migrate Hosted CAs after the Current Suite becomes forgeable.

## Core construction

Before compromise:

```text
Next Trust Anchor
  └─ Next RIR/NIR CA
      └─ Next Delegated CA, where independent operation requires pre-provisioning
```

Hosted resource-holder CAs are not necessarily created in advance.

At planned migration time or after Current Suite compromise:

```text
Next Trust Anchor
  └─ Next RIR/NIR CA
      └─ Newly created Next Hosted CA
          ├─ CRL
          ├─ Manifest
          └─ ROA / ASPA
```

The Hosted CA certificate is issued by the prebuilt Next parent using the authoritative resource registry and stored object configuration. No Current-Suite signature is used to authenticate the new Next child.

## Relationship to existing mechanisms

- RFC 9691 concepts are used for authenticated successor-key notification, reciprocal checks, an acceptance interval, and persistent RP state.
- The accepted Next Trust Anchor is used in parallel before replacing the Current Trust Anchor, so RP processing is not identical to RFC 9691.
- RFC 6489 staging is used when preparing a new CA instance.
- Mixed-Tree contributes asynchronous CA-boundary migration.
- After Current compromise, a Current-signed certificate that introduces a new Next key is not sufficient.

## Preparation policy

| Role | Default policy |
|---|---|
| Trust Anchor | Prebuild |
| RIR/NIR | Prebuild |
| Hosted resource-holder CA | Create on demand |
| Delegated CA | Prebuild |
| Delegated CA with children | Prebuild with priority |
| Hosted child under a prebuilt Hosted operator | Create on demand |

## Semantic comparison

Do not compare complete DER bytes. Compare parsed semantics:

- IP Address Resources
- AS Resources
- Validated ROA Payload set
- Validated ASPA Payload set
- Child delegation relationships where applicable

CCR may be used for diagnostics but is not required.

## Activation

Before activation, Current remains authoritative and Next is staged or shadow-validated.

After activation:

- The scoped output comes from Next.
- Current may remain published for legacy RPs.
- A Next-aware RP does not fall back to Current.
- Retirement is a separate later action.
