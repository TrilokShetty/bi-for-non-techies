# Retail analytics SQLite schema (demo)

**Disclaimer:** Fictional / illustrative sample for a generic Indian omnichannel retail chain. Not affiliated with any real company. Amounts are INR. Dates are ISO `YYYY-MM-DD`.

## Business calendar notes
- Indian **fiscal year** runs **April–March**. Example: **FY25-26** = 2025-04-01 through 2026-03-31.
- Quarters: **Q1**=Apr–Jun, **Q2**=Jul–Sep, **Q3**=Oct–Dec, **Q4**=Jan–Mar.
- Sample orders span **2025-04-01 to 2026-09-30** (covers FY25-26 and part of FY26-27).
- `region` is one of: `North`, `South`, `East`, `West`.
- Money columns end with `_inr`.

## Tables

### stores
| column | type | notes |
|--------|------|-------|
| store_id | INTEGER PK | |
| store_name | TEXT | e.g. "Chennai Hypermarket" |
| city | TEXT | Chennai, Bengaluru, Hyderabad, Mumbai, Pune, Delhi, Noida, Kolkata, Ahmedabad, Jaipur, Kochi |
| state | TEXT | |
| region | TEXT | North/South/East/West |
| store_format | TEXT | Hypermarket / Supermarket / Express |
| pincode | TEXT | 6-digit |
| opened_on | TEXT | ISO date |

Sample: `(1, 'Chennai Hypermarket', 'Chennai', 'Tamil Nadu', 'South', 'Hypermarket', '600123', '2018-05-12')`

### products
| column | type | notes |
|--------|------|-------|
| product_id | INTEGER PK | |
| sku | TEXT UNIQUE | SKU-0001… |
| product_name | TEXT | includes fictional brand |
| category | TEXT | Grocery & Staples, Packaged Food, Personal Care, Home & Kitchen, Electronics & Accessories, Apparel, Footwear, Stationery |
| sub_category | TEXT | |
| brand | TEXT | fictional house/vendor brands |
| mrp_inr | REAL | never sell above MRP in policy |
| cost_price_inr | REAL | |
| gst_rate_pct | REAL | 0/5/12/18/28 as seeded |
| hsn_code | TEXT | illustrative |
| unit_of_measure | TEXT | kg, litre, piece, pack, pair… |

### customers
| column | type | notes |
|--------|------|-------|
| customer_id | INTEGER PK | |
| full_name | TEXT | |
| city | TEXT | |
| state | TEXT | |
| phone | TEXT | fake `+91-91000*****` pattern |
| signup_date | TEXT | |
| loyalty_tier | TEXT | Silver / Gold / Platinum |

### orders
| column | type | notes |
|--------|------|-------|
| order_id | INTEGER PK | |
| store_id | INTEGER FK → stores | fulfilment / originating store |
| customer_id | INTEGER FK → customers | |
| order_date | TEXT | ISO |
| channel | TEXT | in-store / app / web |
| payment_method | TEXT | UPI, debit_card, credit_card, cash, COD, net_banking, wallet, EMI |
| status | TEXT | delivered / cancelled / returned |
| subtotal_inr | REAL | before discount+GST reconstitution; use total_amount_inr for GMV-style sums |
| discount_inr | REAL | |
| gst_amount_inr | REAL | |
| total_amount_inr | REAL | amount customer paid (incl. GST, after discount) |

**GMV-style sales:** typically `SUM(total_amount_inr) WHERE status = 'delivered'`.

### order_items
| column | type | notes |
|--------|------|-------|
| order_item_id | INTEGER PK | |
| order_id | INTEGER FK → orders | |
| product_id | INTEGER FK → products | |
| quantity | INTEGER | |
| unit_price_inr | REAL | usually MRP at sale |
| discount_inr | REAL | line discount |
| gst_amount_inr | REAL | |
| line_total_inr | REAL | |

### inventory
| column | type | notes |
|--------|------|-------|
| inventory_id | INTEGER PK | |
| store_id | INTEGER FK | |
| product_id | INTEGER FK | |
| quantity_on_hand | INTEGER | 0 = stock-out |
| reorder_level | INTEGER | |
| batch_code | TEXT | nullable; used for food |
| expiry_date | TEXT | nullable ISO; Packaged Food / Grocery |

**Stock-out:** `quantity_on_hand = 0` or `< reorder_level` depending on the question — prefer `= 0` for hard stock-outs.

### returns
| column | type | notes |
|--------|------|-------|
| return_id | INTEGER PK | |
| order_id | INTEGER FK → orders | |
| return_date | TEXT | |
| reason_code | TEXT | damaged, wrong_item, quality, size, expired, changed_mind |
| refund_method | TEXT | UPI, card, bank_transfer, wallet, store_credit |
| refund_status | TEXT | pending, processed, rejected |
| refund_amount_inr | REAL | |

## View

### v_order_metrics
Joins `orders` + `stores` for city/region filters without repeating joins.
Columns: order_id, order_date, channel, payment_method, status, total_amount_inr, discount_inr, gst_amount_inr, city, state, region, store_format, store_name.

## Example questions → SQL hints
- Total sales in Chennai last month → filter `city='Chennai'`, delivered, date in prior calendar month.
- Top categories by revenue FY25-26 → join order_items→products→orders, date between 2025-04-01 and 2026-03-31, status delivered, group by category.
- COD return rate by city → COD orders vs status='returned' (or joins to returns).
- Grocery stock-outs → inventory qty=0 join products category.
