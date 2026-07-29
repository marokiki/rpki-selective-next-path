# Acceptance test matrix

| ID | Scenario | Expected result |
|---|---|---|
| T01 | Accept Next TA while Current is secure | Accepted |
| T02 | Accept a new Next TA after compromise | Rejected |
| T03 | Prebuild Next RIR/NIR before compromise | Accepted |
| T04 | Create Hosted Next CA after compromise under valid Next RIR/NIR | Accepted |
| T05 | Create Hosted Next CA after compromise under Current parent only | Rejected |
| T06 | Migrate prebuilt Delegated CA after compromise | Accepted |
| T07 | Create unprepared Delegated CA after compromise | Rejected |
| T08 | Current and Next resource sets differ | Activation rejected |
| T09 | VRP sets differ | Activation rejected |
| T10 | ASPA payload sets differ | Activation rejected |
| T11 | Valid staged Hosted CA with equivalent outputs | Activation accepted |
| T12 | Next repository unavailable before activation | Current remains authoritative |
| T13 | Next repository unavailable after activation | Next unavailable; no fallback |
| T14 | Replay pre-activation state after activation | Rejected |
| T15 | Retire Current, then replay Current | Rejected |
| T16 | Sibling CA remains Current while one CA activates | Accepted |
| T17 | Batch-create multiple Hosted CAs | Deterministic counts and states |
| T18 | Restart model and reload persisted state | No rollback |
| T19 | All-CAs-prebuilt cost model | Matches expected N-based count |
| T20 | Selective-prebuild cost model | Matches expected B+M-based count |

Every negative test must assert a stable reason code, not only a false boolean.
