> **Disclaimer:** Fictional / illustrative internal guidance for a demo retail assistant. Not legal advice. Not affiliated with any real retailer, brand, or regulator. Where laws are mentioned, keep them general; always consult Legal.


# KPI Definitions (Business Glossary)

All money examples use Indian Rupees (INR).

## GMV (Gross Merchandise Value)
Sum of `total_amount_inr` for orders with status **delivered** in the period.
Example: if Chennai delivered orders total ₹12,34,567 in a month, GMV = ₹12,34,567
(~12.35 lakh).

## AOV (Average Order Value)
GMV / count of delivered orders in the period.
Example: GMV ₹10,00,000 across 2,000 orders → AOV = ₹500.

## Sell-through
Units sold / (opening units + inbound units) for a SKU or category in a period.
Expressed as a percentage.

## Stock-out rate
Share of ranged store-SKU combinations with `quantity_on_hand = 0` at snapshot time.
Example: 50 stock-outs out of 1,000 ranged combos → 5%.

## Return rate
Returned orders / delivered+returned orders (define denominator clearly in the deck).
For COD deep-dives, filter `payment_method = 'COD'`.

## Same-store sales growth (SSSG)
GMV for stores open in both current and prior period, percentage change.
Use fiscal periods (FY / quarter) when leadership asks for "this FY".

## Fiscal calendar reminder
FY25-26 = Apr 2025–Mar 2026. Q1=Apr–Jun, Q2=Jul–Sep, Q3=Oct–Dec, Q4=Jan–Mar.
