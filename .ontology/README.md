# Data Model Ontology

This ontology defines the core business domain for a B2B support company with LLM observability tracking.

## Entities (7)

| Entity | Description |
|--------|-------------|
| **Company** | A customer organization that signs contracts for support packages |
| **Contract** | A service agreement between you and a company for support |
| **SupportPackage** | A tier or level of support offering for the product |
| **Product** | Your product that companies use and receive support for |
| **Contact** | A point of contact at a customer company |
| **Address** | A physical location for a company or contact |
| **LLMPageView** | Tracks LLM visibility and appearances on website pages |

## Relationships (8)

```
Company ──hasContract──► Contract (1:1)
Contract ──includesPackage──► SupportPackage (1:1)
SupportPackage ──forProduct──► Product (N:1)
Company ──hasContact──► Contact (1:N)
Contact ──worksAt──► Company (primary, N:1)
Contact ──formerlyWorkedAt──► Company (historical, N:N)
Company ──locatedAt──► Address (1:1)
Contact ──livesAt──► Address (1:1)
LLMPageView ──onPage──► URL
```

## Resolved Ambiguities

| Question | Resolution |
|----------|------------|
| Can a Company have multiple Contracts? | No, 1:1 relationship |
| Can a Contract include multiple Support Packages? | No, 1:1 relationship |
| Can a Contact be associated with multiple Companies? | Yes - one primary (worksAt), many former (formerlyWorkedAt) |
| One Product or multiple? | One product with different support tiers |
| LLM observability scope | Page views and visibility in LLM responses |

## Inferred Attributes

These standard attributes were auto-added based on industry patterns:

- **Company**: name, email, createdAt, status
- **Contract**: startDate, endDate, status, signedAt
- **SupportPackage**: name, tier, description
- **Product**: name, description, version
- **Contact**: name, email, phone, role
- **Address**: street, city, country, postalCode
- **LLMPageView**: pageUrl, timestamp, llmModel, visibilityScore

## Next Steps

- Review `ontology.jsonld` for accuracy
- Use `summarize-jsonld` to get a human-readable summary
- Use `create-transformation` to build transformations based on this ontology
