# Chart planning reference

Detailed specs for chart planning in the `analyze-questions` skill.

## Chart spec format

For each chart, specify:
- `id`, `tier` (core/supporting), `chart_type` (line, bar, scatter, heatmap, etc.)
- `title` (clear, business-meaningful)
- `x`, `y`, `color` (column names)
- `legend` — one sentence: what the colors/marks mean and how to read the chart
- `source_table`
- Brief justification (one sentence)

## Sanity checks

Validate every proposed chart against these criteria before finalizing:

| Check | Question |
|---|---|
| Matches grain | Does the chart aggregate at the right level for its source table? |
| Valid aggregation | Is the metric actually summable/averageable at this grain? |
| Answers intent | Does this chart directly answer the stated question? |
| Non-redundant | Does it show something meaningfully different from other charts? |
| Expressible in ibis | Can the query be written with ibis table/generic expressions? |

Drop charts that fail any check. Refill from the optional set without exceeding caps.
