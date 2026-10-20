import sys
from pathlib import Path

# Add current directory to python path to import sibling modules
sys.path.append(str(Path(__file__).resolve().parent))

from db import get_connection
from seeds.reference_data import (
    REGIONS,
    CITIES,
    CUSTOMER_TYPES,
    SALESPERSONS,
    CATEGORIES,
    SUBCATEGORIES,
    BRANDS,
    SUPPLIERS,
    PRODUCT_STATUSES,
    SALES_CHANNELS,
    ORDER_STATUSES,
    RETURN_REASONS,
)

def load_reference_data():
    print("Starting reference data loading into the database...")
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            
            # 1. Regions
            print("Loading: regions...")
            for row in REGIONS:
                cur.execute(
                    """
                    INSERT INTO regions (region_name)
                    VALUES (%s)
                    ON CONFLICT (region_name) DO NOTHING;
                    """,
                    (row["region_name"],)
                )

            # Retrieve mapping {region_name: region_id} for dependent tables
            cur.execute("SELECT region_id, region_name FROM regions;")
            region_map = {name: r_id for r_id, name in cur.fetchall()}

            # 2. Cities
            print("Loading: cities...")
            for row in CITIES:
                r_id = region_map.get(row["region_name"])
                if r_id:
                    cur.execute(
                        """
                        INSERT INTO cities (city_name, region_id)
                        VALUES (%s, %s)
                        ON CONFLICT (region_id, city_name) DO NOTHING;
                        """,
                        (row["city_name"], r_id)
                    )

            # 3. Customer Types
            print("Loading: customer_types...")
            for row in CUSTOMER_TYPES:
                cur.execute(
                    """
                    INSERT INTO customer_types (type_name)
                    VALUES (%s)
                    ON CONFLICT (type_name) DO NOTHING;
                    """,
                    (row["customer_type_name"],)
                )

            # 4. Salespersons
            print("Loading: salespersons...")
            for row in SALESPERSONS:
                r_id = region_map.get(row["region_name"])
                cur.execute(
                    """
                    INSERT INTO salespersons (first_name, last_name, region_id, hire_date, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        row["first_name"],
                        row["last_name"],
                        r_id,
                        row["hire_date"],
                        True,
                    )
                )

            # 5. Categories
            print("Loading: categories...")
            for row in CATEGORIES:
                cur.execute(
                    """
                    INSERT INTO categories (category_name)
                    VALUES (%s)
                    ON CONFLICT (category_name) DO NOTHING;
                    """,
                    (row["category_name"],)
                )

            # Retrieve mapping {category_name: category_id} for subcategories
            cur.execute("SELECT category_id, category_name FROM categories;")
            category_map = {name: c_id for c_id, name in cur.fetchall()}

            # 6. Subcategories
            print("Loading: subcategories...")
            for row in SUBCATEGORIES:
                c_id = category_map.get(row["category_name"])
                if c_id:
                    cur.execute(
                        """
                        INSERT INTO subcategories (subcategory_name, category_id)
                        VALUES (%s, %s)
                        ON CONFLICT (category_id, subcategory_name) DO NOTHING;
                        """,
                        (row["subcategory_name"], c_id)
                    )

            # 7. Brands
            print("Loading: brands...")
            for row in BRANDS:
                cur.execute(
                    """
                    INSERT INTO brands (brand_name)
                    VALUES (%s)
                    ON CONFLICT (brand_name) DO NOTHING;
                    """,
                    (row["brand_name"],)
                )

            # 8. Suppliers
            print("Loading: suppliers...")
            for row in SUPPLIERS:
                cur.execute(
                    """
                    INSERT INTO suppliers (supplier_name, country, is_active)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (supplier_name) DO NOTHING;
                    """,
                    (row["supplier_name"], row["country"], True)
                )

            # 9. Product Statuses
            print("Loading: product_statuses...")
            for row in PRODUCT_STATUSES:
                cur.execute(
                    """
                    INSERT INTO product_statuses (status_name)
                    VALUES (%s)
                    ON CONFLICT (status_name) DO NOTHING;
                    """,
                    (row["status_name"],)
                )

            # 10. Sales Channels
            print("Loading: sales_channels...")
            for row in SALES_CHANNELS:
                cur.execute(
                    """
                    INSERT INTO sales_channels (channel_name)
                    VALUES (%s)
                    ON CONFLICT (channel_name) DO NOTHING;
                    """,
                    (row["channel_name"],)
                )

            # 11. Order Statuses
            print("Loading: order_statuses...")
            for row in ORDER_STATUSES:
                cur.execute(
                    """
                    INSERT INTO order_statuses (status_name)
                    VALUES (%s)
                    ON CONFLICT (status_name) DO NOTHING;
                    """,
                    (row["status_name"],)
                )

            # 12. Return Reasons
            print("Loading: return_reasons...")
            for row in RETURN_REASONS:
                cur.execute(
                    """
                    INSERT INTO return_reasons (reason_name, is_active)
                    VALUES (%s, %s)
                    ON CONFLICT (reason_name) DO NOTHING;
                    """,
                    (row["reason_name"], True)
                )

        # Commit transaction
        conn.commit()
    print("Success! All reference data has been successfully loaded into the database.")

if __name__ == "__main__":
    load_reference_data()