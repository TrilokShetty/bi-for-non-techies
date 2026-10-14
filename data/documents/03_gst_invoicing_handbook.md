> **Disclaimer:** Fictional / illustrative internal guidance for a demo retail assistant. Not legal advice. Not affiliated with any real retailer, brand, or regulator. Where laws are mentioned, keep them general; always consult Legal.


# GST Invoicing Handbook (Internal)

## Purpose
Guidance for cashiers, e-commerce ops, and finance on how GST appears on customer
invoices for this demo retail setup. **Illustrative only** — tax positions must
be confirmed with Finance/GST consultant.

## Rate slabs used in our assortment (demo mapping)
| Category | Typical demo GST rate |
|----------|------------------------|
| Grocery & Staples | 5% |
| Packaged Food | 12% |
| Apparel | 12% |
| Stationery | 12% |
| Personal Care | 18% |
| Home & Kitchen | 18% |
| Electronics & Accessories | 18% |
| Footwear | 18% |

Actual GST law has many nuances (thresholds, composition, exemptions). Do not
quote this table as legal authority to customers.

## Invoice contents (B2C retail)
Every tax invoice / simplified invoice should generally show:
- Company trade name and GSTIN (use placeholder in training systems only)
- Invoice number and ISO date
- HSN/SAC as configured on the SKU master
- Taxable value, GST rate, GST amount, total in INR
- Place of supply / state for interstate vs intrastate logic as configured in ERP

## Credit notes for returns
When goods are returned and refund approved:
1. Raise a **credit note** linked to the original invoice.
2. Reverse GST to the extent of the return as per Finance SOP.
3. Customer refund timeline follows the Returns policy; credit note is the
   tax document, not the payment rail.

## Input tax credit (ITC) — awareness only
Store teams do not compute ITC. Vendors must send valid tax invoices. Damaged
stock write-offs may have ITC implications handled solely by Finance.

## Footwear note for FAQs
Under this **internal demo handbook**, footwear SKUs are mapped to **18%** GST.
If a customer disputes the rate, escalate to Finance; do not argue statute
sections on the shop floor.
