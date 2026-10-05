# Syzygy Rosetta — SDK

> **Official SDK for the Syzygy Rosetta Governance API**

[![Status: Planned — Phase 4](https://img.shields.io/badge/Status-Planned%20Phase%204-lightgrey.svg)]()
[![Python](https://img.shields.io/badge/Python-Coming%20Soon-blue.svg)]()
[![JavaScript](https://img.shields.io/badge/JavaScript-Coming%20Soon-yellow.svg)]()

---

This is a **planned Rosetta client/integration layer**, distinct from the [TRIA SDK](https://github.com/TrivianTechnologies/tria-sdk), the deployable public TRIA kernel. No installable client implementation is provided here yet.

## Overview

This repository will house the official **Python and JavaScript SDKs** for the Syzygy Rosetta governance API.

The SDK will make it straightforward for developers to integrate Rosetta's `POST /evaluate` governance layer into any application stack without writing raw HTTP requests.

---

## Planned SDK Features

### Python SDK

```python
from rosetta import RosettaClient

client = RosettaClient(base_url="http://localhost:8000")

result = client.evaluate(
    input="Your prompt or AI output here",
    context={
        "environment": "production",
        "industry": "finance"
    }
)

print(result.decision)      # "allow" | "rewrite" | "escalate"
print(result.risk_score)    # float 0.0 – 1.0
print(result.confidence)    # float 0.0 – 1.0
print(result.violations)    # list of policy violations
print(result.rewrite)       # rewritten output or None
```

### JavaScript / TypeScript SDK

```typescript
import { RosettaClient } from '@trivian/rosetta-sdk';

const client = new RosettaClient({ baseUrl: 'http://localhost:8000' });

const result = await client.evaluate({
  input: 'Your prompt or AI output here',
  context: {
    environment: 'production',
    industry: 'healthcare'
  }
});

console.log(result.decision);    // "allow" | "rewrite" | "escalate"
console.log(result.risk_score);  // number 0.0 – 1.0
```

---

## Current Status

The SDK is planned for **Phase 4 — Scaling** of the Rosetta roadmap.

The planned client targets a `POST /evaluate` interface; current implementation behavior and API documentation remain pending verification. The current API implementation documentation destination is pending verification. The separate [Syzygy Rosetta Protocol](https://github.com/TrivianTechnologies/syzygy-rosetta-protocol) repository is the canonical public protocol/specification, not a substitute for implementation-specific API documentation.

---

## Planned API integration example

The following illustrates the intended HTTP interface. It is not evidence of an available or verified current deployment:

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Your prompt here",
    "context": {
      "environment": "production",
      "industry": "general"
    }
  }'
```

---

## Stay Updated

Watch this repository to be notified when the SDK development begins.

Follow [@TrivianOS](https://x.com/TrivianOS) for product updates.

---

## Related Repositories

| Repository | Role |
|---|---|
| [syzygy-rosetta-originbase](https://github.com/TrivianTechnologies/syzygy-rosetta-originbase) | Historical origin codebase; not the current implementation |
| API implementation documentation | Current destination pending verification |
| [syzygy-rosetta-sandbox](https://github.com/TrivianTechnologies/syzygy-rosetta-sandbox) | Testing and simulation |

---

## Organization

Part of the [Trivian Technologies](https://github.com/TrivianTechnologies) organization.

**Website:** [triviantech.com](https://triviantech.com) | **X:** [@TrivianOS](https://x.com/TrivianOS) | **LinkedIn:** [Trivian Technologies](https://www.linkedin.com/company/awakening-the-architect)

## Research lineage and current home

Originator: Sarasha Elion. This work draws on architecture originated and cultivated through Trivian Institute. Trivian Technologies is the current engineering and commercial-development home. Repository stewardship does not establish ownership of all underlying IP; the intended founder IP assignment is pending, and contributor and third-party rights remain applicable.

For technical and ecosystem inquiries: node@triviantech.com. No repository-level license file is currently specified; this description does not grant additional rights.
