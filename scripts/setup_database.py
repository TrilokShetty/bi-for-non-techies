#!/usr/bin/env python3
"""Build a deterministic Indian retail SQLite sample DB.

No real company names, GSTINs, or phone numbers. Fictional brands only.
Run from project root: python scripts/setup_database.py
"""
from __future__ import annotations

import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

# Fixed seed → reproducible interview demos
RNG = random.Random(42)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "retail.db"

START = date(2025, 4, 1)
END = date(2026, 9, 30)

REGIONS = ("North", "South", "East", "West")
FORMATS = ("Hypermarket", "Supermarket", "Express")
CHANNELS = ("in-store", "app", "web")
PAYMENTS = ("UPI", "debit_card", "credit_card", "cash", "COD", "net_banking", "wallet", "EMI")
ORDER_STATUSES = ("delivered", "cancelled", "returned")
RETURN_REASONS = ("damaged", "wrong_item", "quality", "size", "expired", "changed_mind")
REFUND_METHODS = ("UPI", "card", "bank_transfer", "wallet", "store_credit")
REFUND_STATUSES = ("pending", "processed", "rejected")
LOYALTY = ("Silver", "Gold", "Platinum")

# Festive windows (inclusive) used to boost demand
FESTIVE = [
    # Pongal / Sankranti
    (date(2026, 1, 13), date(2026, 1, 17), 1.45, "Grocery & Staples"),
    # Holi
    (date(2026, 3, 12), date(2026, 3, 15), 1.35, "Packaged Food"),
    # Eid-ish window (illustrative)
    (date(2025, 3, 30), date(2025, 4, 2), 1.3, "Apparel"),
    (date(2026, 3, 20), date(2026, 3, 23), 1.3, "Apparel"),
    # Onam
    (date(2025, 9, 5), date(2025, 9, 14), 1.4, "Grocery & Staples"),
    (date(2026, 8, 25), date(2026, 9, 4), 1.4, "Grocery & Staples"),
    # Navratri / Dussehra / Durga Puja window
    (date(2025, 9, 22), date(2025, 10, 12), 1.55, "Apparel"),
    (date(2026, 9, 11), date(2026, 9, 30), 1.55, "Apparel"),
    # Diwali cluster
    (date(2025, 10, 15), date(2025, 11, 5), 1.7, "Electronics & Accessories"),
    # Republic Day / Independence Day sale spikes
    (date(2026, 1, 24), date(2026, 1, 28), 1.35, "Electronics & Accessories"),
    (date(2025, 8, 13), date(2025, 8, 17), 1.35, "Apparel"),
    # End of season clearances
    (date(2025, 7, 1), date(2025, 7, 15), 1.25, "Footwear"),
    (date(2026, 1, 5), date(2026, 1, 20), 1.25, "Apparel"),
]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Shaurya", "Atharv", "Advik", "Kabir", "Ansh",
    "Ananya", "Aadhya", "Diya", "Myra", "Sara", "Anika", "Aarohi", "Pari",
    "Kiara", "Prisha", "Isha", "Navya", "Riya", "Saanvi", "Meera",
    "Rahul", "Priya", "Sneha", "Karthik", "Deepa", "Rohan", "Neha", "Amit",
    "Pooja", "Suresh", "Lakshmi", "Vikram", "Kavya", "Nikhil", "Shreya",
]
LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Khan", "Singh",
    "Gupta", "Mehta", "Joshi", "Desai", "Chopra", "Malhotra", "Banerjee",
    "Mukherjee", "Das", "Bose", "Pillai", "Menon", "Rao", "Naidu", "Kulkarni",
    "Jadhav", "Patil", "Agarwal", "Bansal", "Saxena", "Tripathi", "Chatterjee",
]

# (city, state, region, pincode_prefix)
CITIES = [
    ("Chennai", "Tamil Nadu", "South", "600"),
    ("Bengaluru", "Karnataka", "South", "560"),
    ("Hyderabad", "Telangana", "South", "500"),
    ("Kochi", "Kerala", "South", "682"),
    ("Mumbai", "Maharashtra", "West", "400"),
    ("Pune", "Maharashtra", "West", "411"),
    ("Ahmedabad", "Gujarat", "West", "380"),
    ("Delhi", "Delhi", "North", "110"),
    ("Noida", "Uttar Pradesh", "North", "201"),
    ("Jaipur", "Rajasthan", "North", "302"),
    ("Kolkata", "West Bengal", "East", "700"),
]

# category -> (subcats, gst_rate, hsn_prefix, uoms, brands, name templates)
CATALOG = {
    "Grocery & Staples": {
        "subs": ["Rice", "Atta", "Dal", "Oil", "Spices"],
        "gst": 5,
        "hsn": "1006",
        "uom": ["kg", "litre", "pack"],
        "brands": ["Annapurna Fields", "GrainHouse", "KitchenKart"],
        "names": ["Sona Masoori Rice 5kg", "Whole Wheat Atta 10kg", "Toor Dal 1kg",
                  "Sunflower Oil 1L", "Turmeric Powder 200g", "Basmati Rice 1kg",
                  "Ragi Flour 1kg", "Mustard Oil 1L", "Chana Dal 1kg", "Idli Rice 5kg"],
        "mrp": (40, 650),
        "margin": 0.12,
    },
    "Packaged Food": {
        "subs": ["Snacks", "Beverages", "Ready-to-eat", "Dairy", "Sweets"],
        "gst": 12,
        "hsn": "2106",
        "uom": ["pack", "bottle", "tin"],
        "brands": ["TastyTrail", "SipRight", "HomeBite"],
        "names": ["Masala Chips 150g", "Nimbu Pani 1L", "Instant Poha 200g",
                  "Paneer 200g", "Mysore Pak 250g", "Biscuits Family Pack",
                  "Mango Drink 600ml", "Namkeen Mix 400g", "Curd 400g", "Chocolate Bar"],
        "mrp": (20, 350),
        "margin": 0.18,
    },
    "Personal Care": {
        "subs": ["Hair", "Skin", "Oral", "Hygiene"],
        "gst": 18,
        "hsn": "3305",
        "uom": ["bottle", "tube", "pack"],
        "brands": ["CleanCare", "GlowDaily", "FreshMint"],
        "names": ["Herbal Shampoo 340ml", "Face Wash 100ml", "Toothpaste 200g",
                  "Handwash 750ml", "Body Lotion 400ml", "Soap Pack of 4",
                  "Hair Oil 200ml", "Deodorant 150ml"],
        "mrp": (50, 450),
        "margin": 0.22,
    },
    "Home & Kitchen": {
        "subs": ["Cookware", "Storage", "Cleaning", "Appliances"],
        "gst": 18,
        "hsn": "7323",
        "uom": ["piece", "set"],
        "brands": ["SteelNest", "HomeNest", "SparkClean"],
        "names": ["Pressure Cooker 3L", "Storage Jar Set", "Floor Cleaner 1L",
                  "Mixer Jar", "Non-stick Tawa", "Broom Set", "Water Bottle 1L",
                  "Lunch Box Steel"],
        "mrp": (99, 3500),
        "margin": 0.2,
    },
    "Electronics & Accessories": {
        "subs": ["Mobile Accessories", "Audio", "Power", "Cables"],
        "gst": 18,
        "hsn": "8518",
        "uom": ["piece"],
        "brands": ["VoltBuddy", "SoundLeaf", "ChargePro"],
        "names": ["USB-C Cable 1m", "Wireless Earbuds", "Power Bank 10000mAh",
                  "Phone Case", "Bluetooth Speaker", "Wall Adapter 20W",
                  "Screen Guard", "Smart Watch Band"],
        "mrp": (199, 4999),
        "margin": 0.15,
    },
    "Apparel": {
        "subs": ["Ethnic Wear", "Casual", "Innerwear", "Kids"],
        "gst": 12,
        "hsn": "6204",
        "uom": ["piece"],
        "brands": ["CottonThread", "FestiveWeave", "DailyWear Co"],
        "names": ["Kurta Set", "Cotton Tee", "Palazzo", "Kids Frock",
                  "Saree Blouse", "Cargo Pants", "Shirt Formal", "Dupatta"],
        "mrp": (299, 3999),
        "margin": 0.35,
    },
    "Footwear": {
        "subs": ["Casual", "Sports", "Ethnic", "Kids"],
        "gst": 18,
        "hsn": "6403",
        "uom": ["pair"],
        "brands": ["StepEasy", "TrailRun", "FestiveStep"],
        "names": ["Canvas Shoes", "Sports Running Shoes", "Kolhapuri Style",
                  "Kids Sandals", "Formal Loafers", "Flip Flops", "School Shoes"],
        "mrp": (299, 4999),
        "margin": 0.3,
    },
    "Stationery": {
        "subs": ["Writing", "Notebooks", "Art", "Office"],
        "gst": 12,
        "hsn": "9608",
        "uom": ["piece", "pack", "set"],
        "brands": ["WriteWell", "PageOne", "ColourBox"],
        "names": ["Ball Pen Pack of 10", "A4 Notebook 200pg", "Colour Pencil Set",
                  "Stapler", "Geometry Box", "File Folder Pack", "Marker Set"],
        "mrp": (20, 799),
        "margin": 0.25,
    },
}


def daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def festive_multiplier(d: date, category: str) -> float:
    mult = 1.0
    for a, b, m, cat in FESTIVE:
        if a <= d <= b:
            mult = max(mult, m if category == cat else m * 0.85)
    # Regional staples bump in South around Pongal already covered
    return mult


def build_stores(cur: sqlite3.Cursor) -> list[dict]:
    stores = []
    store_id = 1
    # 14 stores across the city list with varied formats
    plan = [
        ("Chennai", "Hypermarket"), ("Chennai", "Express"),
        ("Bengaluru", "Hypermarket"), ("Bengaluru", "Supermarket"),
        ("Hyderabad", "Supermarket"), ("Kochi", "Express"),
        ("Mumbai", "Hypermarket"), ("Mumbai", "Express"),
        ("Pune", "Supermarket"), ("Ahmedabad", "Supermarket"),
        ("Delhi", "Hypermarket"), ("Noida", "Express"),
        ("Jaipur", "Supermarket"), ("Kolkata", "Hypermarket"),
    ]
    city_meta = {c[0]: c for c in CITIES}
    for city, fmt in plan:
        _, state, region, pin_prefix = city_meta[city]
        pincode = f"{pin_prefix}{RNG.randint(100, 999)}"
        opened = date(2016, 1, 1) + timedelta(days=RNG.randint(0, 3000))
        name = f"{city} {fmt}"
        if sum(1 for s in stores if s["city"] == city and s["store_format"] == fmt) > 0:
            name = f"{city} {fmt} {store_id}"
        row = {
            "store_id": store_id,
            "store_name": name,
            "city": city,
            "state": state,
            "region": region,
            "store_format": fmt,
            "pincode": pincode,
            "opened_on": opened.isoformat(),
        }
        stores.append(row)
        store_id += 1

    cur.executemany(
        """INSERT INTO stores
           (store_id, store_name, city, state, region, store_format, pincode, opened_on)
           VALUES (:store_id, :store_name, :city, :state, :region, :store_format, :pincode, :opened_on)""",
        stores,
    )
    return stores


def build_products(cur: sqlite3.Cursor) -> list[dict]:
    products = []
    pid = 1
    # Aim ~180 SKUs by expanding name × brand variants
    for category, meta in CATALOG.items():
        for name in meta["names"]:
            for brand in meta["brands"]:
                if pid > 180:
                    break
                sub = RNG.choice(meta["subs"])
                mrp = round(RNG.uniform(*meta["mrp"]), 2)
                cost = round(mrp * (1 - meta["margin"] - RNG.uniform(-0.03, 0.03)), 2)
                products.append(
                    {
                        "product_id": pid,
                        "sku": f"SKU-{pid:04d}",
                        "product_name": f"{brand} {name}",
                        "category": category,
                        "sub_category": sub,
                        "brand": brand,
                        "mrp_inr": mrp,
                        "cost_price_inr": max(cost, 1.0),
                        "gst_rate_pct": meta["gst"],
                        "hsn_code": f"{meta['hsn']}{RNG.randint(10, 99)}",
                        "unit_of_measure": RNG.choice(meta["uom"]),
                    }
                )
                pid += 1
            if pid > 180:
                break
        if pid > 180:
            break

    cur.executemany(
        """INSERT INTO products
           (product_id, sku, product_name, category, sub_category, brand,
            mrp_inr, cost_price_inr, gst_rate_pct, hsn_code, unit_of_measure)
           VALUES
           (:product_id, :sku, :product_name, :category, :sub_category, :brand,
            :mrp_inr, :cost_price_inr, :gst_rate_pct, :hsn_code, :unit_of_measure)""",
        products,
    )
    return products


def build_customers(cur: sqlite3.Cursor, n: int = 3200) -> list[dict]:
    customers = []
    for i in range(1, n + 1):
        city, state, region, pin_prefix = RNG.choice(CITIES)
        signup = START - timedelta(days=RNG.randint(0, 900))
        # Clearly fake +91 numbers (reserved-looking pattern 91000…)
        phone = f"+91-91000{i:05d}"
        customers.append(
            {
                "customer_id": i,
                "full_name": f"{RNG.choice(FIRST_NAMES)} {RNG.choice(LAST_NAMES)}",
                "city": city,
                "state": state,
                "phone": phone,
                "signup_date": signup.isoformat(),
                "loyalty_tier": RNG.choices(LOYALTY, weights=[55, 35, 10])[0],
            }
        )
    cur.executemany(
        """INSERT INTO customers
           (customer_id, full_name, city, state, phone, signup_date, loyalty_tier)
           VALUES
           (:customer_id, :full_name, :city, :state, :phone, :signup_date, :loyalty_tier)""",
        customers,
    )
    return customers


def build_orders(
    cur: sqlite3.Cursor,
    stores: list[dict],
    products: list[dict],
    customers: list[dict],
) -> None:
    orders = []
    items = []
    returns = []
    order_id = 1
    item_id = 1
    return_id = 1

    # Pre-index products by category for festive bias
    by_cat: dict[str, list[dict]] = {}
    for p in products:
        by_cat.setdefault(p["category"], []).append(p)

    days = list(daterange(START, END))
    # Target ~5200+ orders: vary daily volume
    for d in days:
        base = 6
        # Weekends slightly higher
        if d.weekday() >= 5:
            base += 3
        # Mild overall growth into FY26
        if d >= date(2026, 4, 1):
            base += 2
        # Festive volume bump
        fest = max(festive_multiplier(d, c) for c in by_cat)
        daily = int(base * fest + RNG.randint(0, 4))
        # Cap so totals stay in expected band
        daily = min(daily, 18)

        for _ in range(daily):
            store = RNG.choice(stores)
            customer = RNG.choice(customers)
            # Channel mix: in-store dominant, digital smaller
            channel = RNG.choices(CHANNELS, weights=[62, 23, 15])[0]
            # Payment: UPI dominates small tickets; COD only on digital
            if channel == "in-store":
                payment = RNG.choices(
                    ["UPI", "cash", "debit_card", "credit_card", "wallet"],
                    weights=[45, 20, 15, 12, 8],
                )[0]
            else:
                payment = RNG.choices(
                    ["UPI", "COD", "debit_card", "credit_card", "wallet", "net_banking", "EMI"],
                    weights=[40, 18, 12, 12, 8, 5, 5],
                )[0]

            # Status distribution; COD digital has higher return rate later
            status = RNG.choices(
                ORDER_STATUSES,
                weights=[88, 5, 7],
            )[0]

            n_lines = RNG.randint(1, 4)
            line_products = []
            for _li in range(n_lines):
                # Bias ethnic wear / apparel in festive windows
                weights = []
                cats = list(by_cat.keys())
                for c in cats:
                    w = festive_multiplier(d, c)
                    # Regional staples: South cities buy more Grocery
                    if store["region"] == "South" and c == "Grocery & Staples":
                        w *= 1.15
                    if store["region"] == "East" and c == "Apparel" and 9 <= d.month <= 10:
                        w *= 1.2  # Durga Puja lean
                    weights.append(w)
                cat = RNG.choices(cats, weights=weights)[0]
                line_products.append(RNG.choice(by_cat[cat]))

            subtotal = 0.0
            discount = 0.0
            gst_total = 0.0
            order_item_rows = []

            for p in line_products:
                qty = RNG.randint(1, 3)
                unit = p["mrp_inr"]
                # Small-ticket UPI bias is emergent from product mix
                line_disc = 0.0
                if RNG.random() < 0.25:
                    line_disc = round(unit * qty * RNG.uniform(0.05, 0.2), 2)
                taxable = unit * qty - line_disc
                gst_amt = round(taxable * (p["gst_rate_pct"] / 100.0), 2)
                line_total = round(taxable + gst_amt, 2)
                subtotal += unit * qty
                discount += line_disc
                gst_total += gst_amt
                order_item_rows.append(
                    {
                        "order_item_id": item_id,
                        "order_id": order_id,
                        "product_id": p["product_id"],
                        "quantity": qty,
                        "unit_price_inr": unit,
                        "discount_inr": line_disc,
                        "gst_amount_inr": gst_amt,
                        "line_total_inr": line_total,
                    }
                )
                item_id += 1

            total = round(subtotal - discount + gst_total, 2)
            # Extra return probability for COD
            if payment == "COD" and channel in ("app", "web") and status == "delivered":
                if RNG.random() < 0.18:
                    status = "returned"

            orders.append(
                {
                    "order_id": order_id,
                    "store_id": store["store_id"],
                    "customer_id": customer["customer_id"],
                    "order_date": d.isoformat(),
                    "channel": channel,
                    "payment_method": payment,
                    "status": status,
                    "subtotal_inr": round(subtotal, 2),
                    "discount_inr": round(discount, 2),
                    "gst_amount_inr": round(gst_total, 2),
                    "total_amount_inr": total,
                }
            )
            items.extend(order_item_rows)

            if status == "returned":
                reason = RNG.choice(RETURN_REASONS)
                # COD refunds often via bank/UPI after remittance
                refund_method = (
                    RNG.choice(["UPI", "bank_transfer", "wallet"])
                    if payment == "COD"
                    else RNG.choice(REFUND_METHODS)
                )
                returns.append(
                    {
                        "return_id": return_id,
                        "order_id": order_id,
                        "return_date": (d + timedelta(days=RNG.randint(1, 10))).isoformat(),
                        "reason_code": reason,
                        "refund_method": refund_method,
                        "refund_status": RNG.choices(REFUND_STATUSES, weights=[15, 75, 10])[0],
                        "refund_amount_inr": total,
                    }
                )
                return_id += 1

            order_id += 1

    cur.executemany(
        """INSERT INTO orders
           (order_id, store_id, customer_id, order_date, channel, payment_method, status,
            subtotal_inr, discount_inr, gst_amount_inr, total_amount_inr)
           VALUES
           (:order_id, :store_id, :customer_id, :order_date, :channel, :payment_method, :status,
            :subtotal_inr, :discount_inr, :gst_amount_inr, :total_amount_inr)""",
        orders,
    )
    cur.executemany(
        """INSERT INTO order_items
           (order_item_id, order_id, product_id, quantity, unit_price_inr,
            discount_inr, gst_amount_inr, line_total_inr)
           VALUES
           (:order_item_id, :order_id, :product_id, :quantity, :unit_price_inr,
            :discount_inr, :gst_amount_inr, :line_total_inr)""",
        items,
    )
    if returns:
        cur.executemany(
            """INSERT INTO returns
               (return_id, order_id, return_date, reason_code, refund_method,
                refund_status, refund_amount_inr)
               VALUES
               (:return_id, :order_id, :return_date, :reason_code, :refund_method,
                :refund_status, :refund_amount_inr)""",
            returns,
        )
    print(f"Orders: {len(orders)}, order_items: {len(items)}, returns: {len(returns)}")


def build_inventory(cur: sqlite3.Cursor, stores: list[dict], products: list[dict]) -> None:
    rows = []
    inv_id = 1
    for store in stores:
        # Not every SKU in every Express store
        sku_sample = products if store["store_format"] != "Express" else RNG.sample(
            products, k=int(len(products) * 0.55)
        )
        for p in sku_sample:
            reorder = RNG.randint(10, 40)
            # Deliberate stock-outs and overstocks
            roll = RNG.random()
            if roll < 0.08:
                qty = 0  # stock-out
            elif roll < 0.14:
                qty = reorder * RNG.randint(6, 12)  # overstock
            else:
                qty = RNG.randint(reorder, reorder * 4)

            expiry = None
            batch = None
            if p["category"] in ("Packaged Food", "Grocery & Staples"):
                expiry = (date(2026, 10, 1) + timedelta(days=RNG.randint(-60, 400))).isoformat()
                batch = f"B{store['store_id']:02d}{p['product_id']:04d}"

            rows.append(
                {
                    "inventory_id": inv_id,
                    "store_id": store["store_id"],
                    "product_id": p["product_id"],
                    "quantity_on_hand": qty,
                    "reorder_level": reorder,
                    "batch_code": batch,
                    "expiry_date": expiry,
                }
            )
            inv_id += 1

    cur.executemany(
        """INSERT INTO inventory
           (inventory_id, store_id, product_id, quantity_on_hand, reorder_level,
            batch_code, expiry_date)
           VALUES
           (:inventory_id, :store_id, :product_id, :quantity_on_hand, :reorder_level,
            :batch_code, :expiry_date)""",
        rows,
    )
    print(f"Inventory rows: {len(rows)}")


def create_schema(cur: sqlite3.Cursor) -> None:
    cur.executescript(
        """
        DROP TABLE IF EXISTS returns;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS inventory;
        DROP TABLE IF EXISTS customers;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS stores;
        DROP VIEW IF EXISTS v_order_metrics;

        CREATE TABLE stores (
            store_id INTEGER PRIMARY KEY,
            store_name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            region TEXT NOT NULL CHECK (region IN ('North','South','East','West')),
            store_format TEXT NOT NULL,
            pincode TEXT NOT NULL,
            opened_on TEXT NOT NULL
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            sku TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            sub_category TEXT NOT NULL,
            brand TEXT NOT NULL,
            mrp_inr REAL NOT NULL,
            cost_price_inr REAL NOT NULL,
            gst_rate_pct REAL NOT NULL,
            hsn_code TEXT NOT NULL,
            unit_of_measure TEXT NOT NULL
        );

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            full_name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            phone TEXT NOT NULL,
            signup_date TEXT NOT NULL,
            loyalty_tier TEXT NOT NULL
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            store_id INTEGER NOT NULL REFERENCES stores(store_id),
            customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
            order_date TEXT NOT NULL,
            channel TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT NOT NULL,
            subtotal_inr REAL NOT NULL,
            discount_inr REAL NOT NULL,
            gst_amount_inr REAL NOT NULL,
            total_amount_inr REAL NOT NULL
        );

        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(order_id),
            product_id INTEGER NOT NULL REFERENCES products(product_id),
            quantity INTEGER NOT NULL,
            unit_price_inr REAL NOT NULL,
            discount_inr REAL NOT NULL,
            gst_amount_inr REAL NOT NULL,
            line_total_inr REAL NOT NULL
        );

        CREATE TABLE inventory (
            inventory_id INTEGER PRIMARY KEY,
            store_id INTEGER NOT NULL REFERENCES stores(store_id),
            product_id INTEGER NOT NULL REFERENCES products(product_id),
            quantity_on_hand INTEGER NOT NULL,
            reorder_level INTEGER NOT NULL,
            batch_code TEXT,
            expiry_date TEXT
        );

        CREATE TABLE returns (
            return_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(order_id),
            return_date TEXT NOT NULL,
            reason_code TEXT NOT NULL,
            refund_method TEXT NOT NULL,
            refund_status TEXT NOT NULL,
            refund_amount_inr REAL NOT NULL
        );

        -- Small derived layer for common demo questions
        CREATE VIEW v_order_metrics AS
        SELECT
            o.order_id,
            o.order_date,
            o.channel,
            o.payment_method,
            o.status,
            o.total_amount_inr,
            o.discount_inr,
            o.gst_amount_inr,
            s.city,
            s.state,
            s.region,
            s.store_format,
            s.store_name
        FROM orders o
        JOIN stores s ON s.store_id = o.store_id;
        """
    )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    create_schema(cur)
    stores = build_stores(cur)
    products = build_products(cur)
    customers = build_customers(cur)
    print(f"Stores: {len(stores)}, products: {len(products)}, customers: {len(customers)}")
    build_orders(cur, stores, products, customers)
    build_inventory(cur, stores, products)
    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    main()
