# Chart planning reference

Detailed specs for chart planning in the `analyze-questions` skill.

## Chart spec format

For each chart, specify:
- `id`, `tier` (core/supporting), `chart_type` (line, bar, scatter, heatmap, etc.)
- `title` (clear, business-meaningful)
- `x`, `y`, `color` (column names)
- `x_scale`, `y_scale` (`linear` or `log`)
- `legend` — one sentence: what the colors/marks mean and how to read the chart
- `source_table`
- Brief justification (one sentence)

## When to use log scales

Flag an axis for log scale when:
- Values span **2+ orders of magnitude** (e.g., 1–100k)
- Distribution is power-law or exponential
- Scatter plot with skewed axes — log-log reveals structure
- Comparing growth rates rather than absolute values

Do **not** use log when:
- Values include zero or negatives
- Range is narrow (< 10x)
- Audience is non-technical

Check `max / min` ratio for metric columns during evidence review. If > 100, recommend log scale.

## Sanity checks

Validate every proposed chart against these criteria before finalizing:

| Check | Question |
|---|---|
| Matches grain | Does the chart aggregate at the right level for its source table? |
| Valid aggregation | Is the metric actually summable/averageable at this grain? |
| Answers intent | Does this chart directly answer the stated question? |
| Non-redundant | Does it show something meaningfully different from other charts? |
| Expressible in ibis | Can the query be written with ibis table/generic expressions? |
| Scale appropriate | Log scale flagged when max/min > 100? Zero-inclusive axes kept linear? |

Drop charts that fail any check. Refill from the optional set without exceeding caps.
