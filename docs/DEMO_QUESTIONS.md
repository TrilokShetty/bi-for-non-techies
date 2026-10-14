# Demo questions

Expected behaviour assumes Ollama + ingested docs + seeded DB. Small local models
may mis-route occasionally; the smoke test treats route mismatches as notes, not hard fails.

## SQL (expect `query_type=sql`)

| # | Question | Expected behaviour |
|---|----------|--------------------|
| 1 | What were total sales in Chennai last month? | Sum delivered `total_amount_inr` for Chennai in prior calendar month |
| 2 | Top 5 categories by revenue in FY25-26 | Join items→products→orders; dates 2025-04-01…2026-03-31 |
| 3 | Which city has the highest COD return rate? | COD orders vs returned (or `returns` join), grouped by city |
| 4 | How did Diwali week sales compare with the previous week? | Compare ~2025-10-20 week vs prior week GMV (model may pick nearby dates) |
| 5 | Which stores have stock-outs in Grocery & Staples? | `inventory.quantity_on_hand = 0` + grocery category |
| 6 | Average order value by payment method | Delivered orders: avg `total_amount_inr` by `payment_method` |
| 7 | South region delivered GMV in Q1 of FY25-26 | Apr–Jun 2025, region South |
| 8 | How many Platinum loyalty customers are in Bengaluru? | Count customers |
| 9 | Which payment method dominates tickets under ₹500? | Filter low totals; expect UPI-heavy |
| 10 | List Express stores and their cities | Simple stores filter |

## RAG (expect `rag`)

| # | Question | Expected behaviour |
|---|----------|--------------------|
| 11 | What is the refund timeline for a COD order? | Cite returns policy (5–7 / 7–10 business days) |
| 12 | How should near-expiry packaged food be handled? | Markdown ladder / FEFO from food safety doc |
| 13 | What GST rate applies to footwear under the policy doc? | Handbook says **18%** (demo mapping) |
| 14 | Who do I escalate an unresolved customer complaint to? | L3 Regional Operations Manager |
| 15 | What is the definition of GMV in our KPI glossary? | Delivered `total_amount_inr` sum |
| 16 | Can we sell above MRP during a festival? | No — pricing policy |
| 17 | What are Platinum loyalty benefits? | Early festive pre-sales etc. |

## General (expect `general`)

| # | Question | Expected behaviour |
|---|----------|--------------------|
| 18 | Hello! | Greeting + short capability blurb |
| 19 | What can you do? | Mentions sales/inventory/policy Q&A |
| 20 | Who won the cricket world cup? | Politely out of scope |

## Ambiguous (may trigger rewriter / retries)

| # | Question | Notes |
|---|----------|-------|
| 21 | How are we doing in the south? | Should rewrite toward region=South + a metric |
| 22 | Show me festive numbers | Should pin a festival window / category |
| 23 | Returns policy for electronics last year | Mixes rag+sql intent; often zig-zags via rewrite |

## Mixed (known limitation)

| # | Question | Honest behaviour |
|---|----------|------------------|
| 24 | Is our return rate in Bengaluru within the limit set in our policy? | **Single route only.** Router picks sql *or* rag, not both. Flag as limitation: no tool fusion node yet. |

## Hinglish (experimental)

| # | Question | Notes |
|---|----------|-------|
| 25 | Pichle mahine Pune mein kitni sales hui? | May fail on small models; try English fallback |
| 26 | COD return rate Dilli NCR mein kya hai? | Experimental |

## Optional follow-ups

Reuse `thread_id` from a prior `/query` response when calling `/history/{thread_id}`.
