---
name: generate-cdm
description: Generate a Canonical Data Model (CDM) from a finalized ontology. Use when the user has completed their ontology and wants to create a standardized data model with entities, relationships, and validation rules. The CDM bridges the semantic ontology to implementation-ready data structures.
argument-hint: [-- <entity-focus or hints>]
---

# Generate Canonical Data Model from Ontology

**Transforms your ontology into an implementation-ready Canonical Data Model (CDM).** The ontology captures business semantics; the CDM translates those semantics into standardized entities, relationships, and validation rules that can be implemented in any data system.

Parse `$ARGUMENTS`:
- `entity-focus` (optional, after `--`): specific entity to focus on (e.g., `-- Customer`) or hints about CDM priorities.

## Prerequisites

### 1. Check for ontology

Read `.schema/ontology.jsonld` to understand the source semantic model.

If the file doesn't exist or is empty:
> No ontology found. The ontology defines your business semantics — the entities and relationships the CDM will formalize.
>
> Run `create-ontology` first to define your business entities and relationships.

**STOP and wait for ontology to be created.**

## Steps

### 1. Extract core business entities

Read the ontology and list every noun defined as a real-world object. These become **CDM entities**.

For each entity, extract:
- Canonical name (from ontology, not source systems)
- Description / semantic meaning
- Attributes with data types
- Whether attributes are inferred or explicit in the ontology

| Entity type | Standard attributes to include |
|---|---|
| Order/Transaction | id, timestamp, status, total, currency |
| User/Customer | id, email, created_at, status |
| Product | id, name, price, sku, description |
| Subscription | id, start_date, end_date, plan, status |
| Address | id, street, city, country, postal_code |

**Kimball alignment**: Entities map to fact and dimension table subjects. Ensure atomic detail (Kimball Rule #1).

### 2. Map elementary facts (relationships)

Extract every relationship the ontology defines as a fundamental, irreducible fact:
- `Customer` **places** `Order`
- `Order` **contains** `OrderLine`
- `OrderLine` **references** `Product`

For each relationship, capture:
- Source entity → relationship type → target entity
- Cardinality (one-to-one, one-to-many, many-to-many)
- Whether mandatory or optional
- Semantic label (e.g., `PLACES`, `CONTAINS`, `MEMBER_OF`)

Do **not** flatten or collapse facts — preserve semantic richness. Relationships are first-class citizens, not just foreign keys.

### 3. Extract validation rules and constraints

Capture business rules from the ontology that constrain entity behavior:
- "A Customer can only have one BillingAddress marked as primary"
- "An Order must reference an active Customer"
- "InvoiceDate must always be ≥ OrderDate"

These become validation logic in the CDM.

### 4. Handle nulls and unknowns intentionally

For every optional attribute or relationship:
- Define explicit sentinel values (`UNKNOWN`, `NOT_APPLICABLE`)
- Document *why* a value might be absent based on ontology semantics

Example: `ShippingAddress` is null for digital products — not a data quality issue, but because digital products have no physical fulfillment.

**Kimball alignment**: Never use null as a foreign key (Rule #6).

### 5. Preserve temporal semantics

For time-sensitive facts (e.g., "subscription is active during a period"):
- Use `valid_from` / `valid_to` columns for slowly changing entities
- Store dates as proper date/datetime types, never strings
- Document the canonical timezone standard

**Kimball alignment**: Store dates using date types or surrogate keys to date dimension (Rule #9).

### 6. Identify semantic gaps

Compare ontology entities against available source data (if `.schema/<dataset>.ison` exists):
- Fields in source that don't map to ontology concepts
- Ontology entities with no source system representation

Present gaps to the user for resolution before finalizing CDM.

### 7. Generate CDM in ISON format

Save the CDM to `.schema/CDM.ison` using ISON format ([spec](https://ison.dev/spec.html)):

```
meta.cdm
version created_from
1.0 ontology.jsonld

table.entities
id:string name:string description:string primary_key:string
Customer Customer "A person or organization that purchases products" customer_id
Order Order "A commercial transaction initiated by a customer" order_id
Product Product "An item available for purchase" product_id

table.attributes
entity:ref name:string type:string nullable:bool description:string
:Customer customer_id string false "Canonical customer identifier"
:Customer email string false "Primary contact email"
:Customer created_at datetime false "Account creation timestamp"
:Customer status string false "Account status (active, inactive, suspended)"
:Order order_id string false "Canonical order identifier"
:Order customer_id string false "Reference to ordering customer"
:Order order_date datetime false "When order was placed"
:Order total float false "Order total amount"
:Order currency string false "ISO 4217 currency code"

table.relationships
from:ref to:ref type:string cardinality:string mandatory:bool description:string
:Customer :Order :PLACES one_to_many false "Customer places orders"
:Order :Product :CONTAINS many_to_many true "Order contains products"

table.validation_rules
id:string entities:string rule_type:string expression:string description:string
VR001 "Invoice,Order" cross_entity "invoice_date >= order_date" "Invoice cannot precede order"
VR002 Customer single_entity "status IN ('active','inactive','suspended')" "Valid customer statuses"

table.null_semantics
entity:ref attribute:string sentinel:string reason:string
:Order shipping_address NOT_APPLICABLE "Digital products have no shipping"
:Customer phone UNKNOWN "Not collected at signup"
```

## Output

```
CDM generated: .schema/CDM.ison

Entities: <count>
- <Entity1>: <description>
- <Entity2>: <description>
...

Relationships: <count>
- <Entity1> -[<TYPE>]-> <Entity2> (<cardinality>)
...

Validation rules: <count>
Semantic gaps identified: <count or "none">

Next steps:
- Review .schema/CDM.ison for accuracy
- Resolve any semantic gaps with domain experts
- Use `create-transformation` to map source data to this CDM
```