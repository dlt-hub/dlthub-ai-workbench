---
name: create-ontology
description: Build or edit a data model by creating a structured JSON-LD ontology. Use when the user wants to create a data model, edit their data model, describes business logic or data relationships, or asks how to get started with data modeling. The ontology is the foundation of the data model.
argument-hint: <business-scenarios or domain description>
---

# Create ontology from business scenarios

**The ontology is the foundation of your data model.** Before building transformations or analytics, we capture your business domain as a structured graph of entities and relationships. This ensures your data model accurately reflects how your business works.

Transform a list of business questions or scenarios (up to 20) into a formal JSON-LD ontology that captures entities, relationships, and identifies modeling gaps.

Parse `$ARGUMENTS`:
- `business-scenarios` (optional): natural language description of business questions, scenarios, or domain concepts

## Getting started prompt

If `$ARGUMENTS` is empty or the user asks "how do I start?" / "what should I provide?", prompt them:

> To build your data model, we start by creating an **ontology** — a structured map of your business entities and how they relate. This is the foundation that ensures your data model accurately represents your domain.
>
> To get started, I need to understand what questions you want your data to answer.
>
> **Option A:** Give me up to 20 business questions you need answered daily, like:
> - "Who are my top customers this month?"
> - "Which products are running low on stock?"
> - "What's our revenue trend this quarter?"
>
> **Option B:** Describe 3-5 business scenarios, like:
> - "A customer places an order with multiple products"
> - "A subscription renews monthly and can be paused"
> - "Sales reps are assigned to accounts by region"
>
> Either works — questions help me understand what you need to *measure*, scenarios help me understand how things *relate*.

**STOP and wait for user input before proceeding.**

## Editing an existing ontology

If `.ontology/ontology.jsonld` exists, read it first. Then:
- If user provides new scenarios/questions → merge new entities and relationships into the existing graph
- If user asks to change something → update the specific classes or properties
- Preserve existing structure unless explicitly asked to replace it

Show the user what changed: "Added 2 new entities, updated 1 relationship."

## Steps

### 1. Extract entities (classes)

Identify primary classes from the scenarios:
- Look for nouns that represent core domain concepts (e.g., Customer, Subscription, Transaction, Order, Product)
- Use [schema.org](https://schema.org) terms where applicable (e.g., `schema:Person`, `schema:Organization`, `schema:Order`)
- For domain-specific concepts not in schema.org, use a custom namespace (`ex:`)

Output a preliminary list of classes with brief descriptions.

### 2. Map relationships

Define how classes connect to each other:
- Identify verbs and ownership patterns (e.g., "Customer places Order" → `Customer -> placesOrder -> Order`)
- Define relationship properties with appropriate cardinality hints
- Use schema.org properties where applicable, otherwise define custom ones in `ex:` namespace

Common relationship patterns:
- `hasX` / `belongsTo` — ownership/containment
- `relatedTo` — loose association  
- `memberOf` / `hasMember` — group membership
- `createdBy` / `creates` — authorship

### 3. Autocomplete standard attributes

If the user provides fewer than 5 scenarios, infer standard industry attributes:

| Entity type | Inferred attributes |
|---|---|
| Order/Transaction | timestamp, status, total, currency |
| User/Customer | email, createdAt, status |
| Product | name, price, sku, description |
| Subscription | startDate, endDate, plan, status |
| Address | street, city, country, postalCode |

Flag inferred attributes as `"inferred": true` in the ontology.

### 4. Identify the Ambiguity Fork

Find structural questions (cardinality, hierarchy) that cannot be answered from the input. Generate up to 5 critical questions:

Examples:
- "Can a User have multiple Accounts?"
- "Is an Order tied to one Product or multiple Products?"
- "Does a Subscription belong to a User or an Organization?"
- "Are Transactions immutable or can their status change?"
- "Is Address embedded in Customer or a separate entity?"

**Present these questions to the user and STOP.** Do not finalize the ontology until ambiguities are resolved.

### 5. Generate JSON-LD ontology

After resolving ambiguities, generate the full JSON-LD object:

```json
{
  "@context": {
    "schema": "https://schema.org/",
    "ex": "https://example.org/ontology/",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@graph": [
    {
      "@id": "ex:Customer",
      "@type": "rdfs:Class",
      "rdfs:label": "Customer",
      "rdfs:comment": "A person or organization that purchases products"
    },
    {
      "@id": "ex:hasSubscription",
      "@type": "rdf:Property",
      "rdfs:domain": "ex:Customer",
      "rdfs:range": "ex:Subscription"
    }
  ]
}
```

Include for each class:
- `@id` — unique identifier
- `@type` — `rdfs:Class`
- `rdfs:label` — human-readable name
- `rdfs:comment` — description
- `rdfs:subClassOf` — parent class if applicable

Include for each property:
- `@id` — unique identifier
- `@type` — `rdf:Property` or `owl:ObjectProperty`
- `rdfs:domain` — source class
- `rdfs:range` — target class or datatype

### 6. Save the ontology

Save the ontology to `.ontology/ontology.jsonld` in the workspace root.

```
.ontology/
├── ontology.jsonld      # The full JSON-LD graph
└── README.md            # Summary of entities and relationships
```

The ontology is **editable** — update it as new business logic emerges or existing structure needs refinement.

## Output

**For new ontology:**
```
Ontology created: .ontology/ontology.jsonld

Entities: <count>
- <Entity1>: <description>
- <Entity2>: <description>
...

Relationships: <count>
- <Entity1> -> <relationship> -> <Entity2>
...

Inferred attributes: <list if any>

Resolved ambiguities:
- <question>: <answer>
...
```

**For edited ontology:**
```
Ontology updated: .ontology/ontology.jsonld

Changes:
- Added: <new entities/relationships>
- Updated: <modified entities/relationships>
- Removed: <deleted items, if any>

Current totals: <X> entities, <Y> relationships
```

**Next steps:**
- Review `.ontology/ontology.jsonld` for accuracy
- Use `summarize-jsonld` to get a human-readable summary
- Use `create-transformation` to build transformations based on this ontology
