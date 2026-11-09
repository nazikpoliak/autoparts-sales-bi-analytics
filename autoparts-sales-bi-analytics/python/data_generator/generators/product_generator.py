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

SUBCATEGORY_PRICE_RANGES = {
    # Engine Parts
    "Pistons and Rings": (1500, 7000),
    "Gaskets and Seals": (250, 1500),
    "Cylinder Head Components": (800, 5000),
    "Engine Mounts": (600, 3500),
    
    # Transmission and Clutch
    "Clutch Kits": (2500, 12000),
    "Clutch Discs and Pressure Plates": (1200, 6000),
    "Gearbox Components": (2000, 15000),
    
    # Brake System
    "Brake Pads": (800, 3500),
    "Brake Discs and Drums": (1200, 5500),
    "Brake Calipers and Repair Kits": (500, 4000),
    "Brake Hydraulics": (300, 2000),
    
    # Suspension and Steering
    "Shock Absorbers and Struts": (1500, 7500),
    "Control Arms and Ball Joints": (900, 4500),
    "Steering Components": (1000, 8000),
    "Springs and Mounts": (800, 4000),
    
    # Filters (Витратні матеріали, дешеві)
    "Oil Filters": (200, 600),
    "Air Filters": (250, 800),
    "Fuel Filters": (300, 1200),
    "Cabin Filters": (200, 700),
    
    # Electrical System
    "Alternators and Starters": (3500, 12500),
    "Batteries": (2500, 8500),
    "Sensors and Switches": (400, 3000),
    "Wiring and Connectors": (150, 1200),
    
    # Cooling System
    "Radiators": (2000, 9000),
    "Water Pumps": (1000, 4500),
    "Thermostats": (300, 1500),
    "Coolant Hoses": (200, 1000),
    
    # Fuel System
    "Fuel Pumps": (1200, 6500),
    "Injectors": (2500, 14000),
    "Fuel System Sensors": (600, 3500),
    
    # Exhaust System
    "Exhaust Pipes and Mounts": (500, 4000),
    "EGR and Exhaust Components": (1500, 9500),
    
    # Body and Exterior
    "Mirrors and Handles": (400, 3500),
    "Bumpers and Grilles": (1500, 11000),
    "Body Fasteners": (50, 300),
    
    # Lighting
    "Headlights": (3500, 14000),
    "Tail Lights": (2000, 8500),
    "Bulbs and LED Modules": (100, 1500),
    
    # Bearings and Hubs
    "Wheel Bearings": (700, 3500),
    "Wheel Hubs": (1500, 6500),
    
    # Belts and Timing
    "Timing Belts and Kits": (1200, 6000),
    "Drive Belts": (300, 1500),
    "Tensioners and Idlers": (600, 3500),
    
    # Lubricants and Fluids
    "Engine Oils": (800, 3200),
    "Coolants and Antifreeze": (300, 1200),
    "Transmission Fluids": (400, 2500),
    "Greases and Technical Fluids": (150, 800),
    
    # Workshop Supplies
    "Workshop Chemicals": (150, 900),
    "Clamps and Ties": (50, 250),
    "Fasteners and Fittings": (50, 400),
}


def generate_sku(brand_name: str, existing_skus: set) -> str:
    """Generates a unique realistic SKU code based on the brand name."""
    prefix = brand_name[:3].upper().replace(" ", "X")
    while True:
        code = f"{prefix}-{random.randint(10000, 99999)}"
        if code not in existing_skus:
            existing_skus.add(code)
            return code

def get_brand_margin(brand_tier):
    if brand_tier == "Premium":
        return round(random.uniform(0.35, 0.42), 4)
    elif brand_tier == "Mid":
        return round(random.uniform(0.24, 0.31), 4)
    else:  # low-tier brands
        return round(random.uniform(0.15, 0.22), 4)


def generate_products(count: int = 10000):
    """Generates a realistic catalog of auto parts products and inserts them into the database."""
    print(f"Starting generation of {count} products...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Fetch reference data mappings
            cur.execute("SELECT subcategory_id, subcategory_name FROM subcategories;")
            subcategories = cur.fetchall()  # [(id, name), ...]
            
            cur.execute("SELECT brand_id, brand_name, brand_tier FROM brands;")
            brands = cur.fetchall()  # [(id, name, tier), ...]

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
                brand_id, brand_name, brand_tier = random.choice(brands)
                supplier_id = random.choice(suppliers)
                
                # Distribution of statuses: 85% Active, 10% Discontinued, 5% Preorder/Temp unavailable
                status_id = random.choices(statuses, weights=[85, 10, 3, 2] if len(statuses) >= 4 else [85, 15])[0]

                sku = generate_sku(brand_name, existing_skus)
                
                # Generate realistic product name
                adj = random.choice(PART_ADJECTIVES)
                noun = random.choice(PART_NOUNS)
                product_name = f"{brand_name} {adj} {subcat_name.rstrip('s')} - {noun}"

                # Pricing logic (purchase price based on category/random, sale price with markup 25% - 60%)
                subcat_price_range = SUBCATEGORY_PRICE_RANGES.get(subcat_name, (50, 15000))
                purchase_price = round(random.uniform(*subcat_price_range), 2)
                markup_percentage = get_brand_margin(brand_tier)
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