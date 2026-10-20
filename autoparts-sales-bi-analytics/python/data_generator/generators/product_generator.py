import sys
from pathlib import Path
import random

# Add parent directory to python path to import db module
sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import get_connection

# Lists of auto parts naming components to make products look realistic
PART_ADJECTIVES = ["Front", "Rear", "Upper", "Lower", "Left", "Right", "Inner", "Outer", "Heavy-Duty", "Premium", "Standard", "Turbo"]
PART_NOUNS = [
    "Brake Pad Set", "Brake Disc", "Oil Filter", "Air Filter", "Fuel Filter", "Cabin Filter",
    "Shock Absorber", "Control Arm", "Wheel Bearing", "Timing Belt Kit", "Water Pump", "Thermostat",
    "Spark Plug", "Glow Plug", "Alternator", "Starter Motor", "Clutch Kit", "Flywheel",
    "CV Joint", "Tie Rod End", "Stabilizer Link", "Ignition Coil", "Lambda Sensor", "Radiator",
    "EGR Valve", "Fuel Pump", "Gasket Set", "Engine Mount", "Brake Caliper", "Wheel Hub"
]

def generate_sku(brand_name: str, existing_skus: set) -> str:
    """Generates a unique realistic SKU code based on the brand name."""
    prefix = brand_name[:3].upper().replace(" ", "X")
    while True:
        code = f"{prefix}-{random.randint(10000, 99999)}"
        if code not in existing_skus:
            existing_skus.add(code)
            return code

def generate_products(count: int = 10000):
    """Generates a realistic catalog of auto parts products and inserts them into the database."""
    print(f"Starting generation of {count} products...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Fetch reference data mappings
            cur.execute("SELECT subcategory_id, subcategory_name FROM subcategories;")
            subcategories = cur.fetchall()  # [(id, name), ...]
            
            cur.execute("SELECT brand_id, brand_name FROM brands;")
            brands = cur.fetchall()  # [(id, name), ...]

            cur.execute("SELECT supplier_id FROM suppliers;")
            suppliers = [row[0] for row in cur.fetchall()]

            cur.execute("SELECT product_status_id FROM product_statuses;")
            statuses = [row[0] for row in cur.fetchall()]

            if not subcategories or not brands or not suppliers or not statuses:
                raise RuntimeError("Reference data for products is missing! Run load_seeds.py first.")

            # Get existing SKUs to prevent unique constraint violations
            cur.execute("SELECT sku FROM products;")
            existing_skus = {row[0] for row in cur.fetchall()}

            products_to_insert = []
            
            print("Preparing product data...")
            for _ in range(count):
                subcat_id, subcat_name = random.choice(subcategories)
                brand_id, brand_name = random.choice(brands)
                supplier_id = random.choice(suppliers)
                
                # Distribution of statuses: 85% Active, 10% Discontinued, 5% Preorder/Temp unavailable
                status_id = random.choices(statuses, weights=[85, 10, 3, 2] if len(statuses) >= 4 else [85, 15])[0]

                sku = generate_sku(brand_name, existing_skus)
                
                # Generate realistic product name
                adj = random.choice(PART_ADJECTIVES)
                noun = random.choice(PART_NOUNS)
                product_name = f"{brand_name} {adj} {subcat_name.rstrip('s')} - {noun}"

                # Pricing logic (purchase price based on category/random, sale price with markup 25% - 60%)
                purchase_price = round(random.uniform(150.0, 12500.0), 2)
                markup_percentage = random.uniform(1.25, 1.60)
                standard_sale_price = round(purchase_price * markup_percentage, 2)

                # Weight in kg (some items might be null or up to 35 kg)
                weight_kg = round(random.uniform(0.1, 18.5), 2) if random.random() > 0.1 else None

                description = (
                    f"High-quality replacement part by {brand_name}. "
                    f"Designed for optimal performance and durability in category {subcat_name}."
                )

                products_to_insert.append((
                    subcat_id,
                    brand_id,
                    supplier_id,
                    status_id,
                    sku,
                    product_name,
                    description,
                    "pcs",
                    purchase_price,
                    standard_sale_price,
                    weight_kg
                ))

            print(f"Inserting {len(products_to_insert)} products into the database...")
            
            # Use executemany for fast batch insertion
            cur.executemany(
                """
                INSERT INTO products (
                    subcategory_id, brand_id, supplier_id, product_status_id,
                    sku, product_name, description, unit_of_measure,
                    purchase_price, standard_sale_price, weight_kg
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                products_to_insert
            )

        conn.commit()
    print(f"Success! Generated and inserted {count} products.")

if __name__ == "__main__":
    generate_products(10000)