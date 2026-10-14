> **Disclaimer:** Fictional / illustrative internal guidance for a demo retail assistant. Not legal advice. Not affiliated with any real retailer, brand, or regulator. Where laws are mentioned, keep them general; always consult Legal.


# Inventory & Replenishment Guidelines

## Reorder levels
Each store-SKU has a `reorder_level` in the inventory system. When
`quantity_on_hand` falls at or below reorder level, the store is flagged for
replenishment in the overnight DRP run.

## Safety stock
- Hypermarkets: higher safety stock for Grocery & Staples and festive Apparel.
- Express stores: lean range; accept higher stock-out risk on long-tail SKUs.
- Monsoon and festive calendars: temporary uplift factors from Merchandising.

## FEFO for dated goods
For Packaged Food and any SKU with `expiry_date`, pick **First Expiry First Out**.
Shelf facing should show the earlier expiry at the front.

## Damaged stock write-off
1. Segregate damaged goods in the non-salable cage.
2. Photograph and raise write-off ticket.
3. Manager approval required above ₹5,000 per day per store.
4. Do not sell damaged electrical goods.

## Stock-out definition (ops KPI)
Hard stock-out: on-hand quantity = 0 for an active SKU that should be ranged.
Soft risk: on-hand below reorder level. Weekly scorecards track both.

## Cycle counts
A-class SKUs: weekly spot counts. Full store counts: quarterly or as directed
by Regional Ops after shrinkage incidents.
