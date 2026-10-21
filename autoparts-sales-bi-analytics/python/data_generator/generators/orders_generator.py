import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to python path to import db module
sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import get_connection

def generate_orders(total_orders: int = 40000, batch_size: int = 2000):
    """Generates realistic orders and their items in batches using RETURNING clause."""
    print(f"Starting generation of {total_orders} orders in batches of {batch_size}...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            
            # 1. Fetch necessary reference data and entities for foreign keys
            print("Fetching reference data for orders...")
            cur.execute("SELECT customer_id, city_id FROM customers;")
            customers = cur.fetchall()  # [(customer_id, city_id), ...]

            cur.execute("SELECT salesperson_id, region_id FROM salespersons;")
            salespersons = cur.fetchall()  # [(salesperson_id, region_id), ...]

            cur.execute("SELECT sales_channel_id FROM sales_channels;")
            sales_channels = [row[0] for row in cur.fetchall()]

            cur.execute("SELECT order_status_id, status_name FROM order_statuses;")
            order_statuses = cur.fetchall()  # [(status_id, status_name), ...]

            cur.execute("SELECT product_id, purchase_price, standard_sale_price FROM products;")
            products = cur.fetchall()  # [(product_id, purchase_price, standard_sale_price), ...]

            if not customers or not salespersons or not sales_channels or not order_statuses or not products:
                raise RuntimeError("Required data for orders is missing! Ensure customers, products, and seeds are loaded.")

            # Create status weights distribution (85% Completed, 10% Cancelled, 5% others)
            status_ids = []
            status_weights = []
            for s_id, s_name in order_statuses:
                status_ids.append(s_id)
                if s_name == "Completed":
                    status_weights.append(85)
                elif s_name == "Cancelled":
                    status_weights.append(10)
                else:
                    status_weights.append(5 / max(1, len(order_statuses) - 2))

            start_date = datetime.now() - timedelta(days=2 * 365) # 2 years of history
            generated_orders_count = 0
            generated_items_count = 0

            while generated_orders_count < total_orders:
                current_batch_size = min(batch_size, total_orders - generated_orders_count)
                batch_orders_data = []

                for _ in range(current_batch_size):
                    customer_id, customer_city_id = random.choice(customers)
                    
                    # Pick salesperson from the same region or random
                    matching_salespersons = [sp[0] for sp in salespersons if sp[1] == customer_city_id]
                    salesperson_id = random.choice(matching_salespersons) if matching_salespersons and random.random() > 0.3 else random.choice(salespersons)[0]
                    
                    sales_channel_id = random.choice(sales_channels)
                    order_status_id = random.choices(status_ids, weights=status_weights)[0]

                    # Random order date over the last 2 years
                    days_offset = random.randint(0, 2 * 365)
                    order_date = start_date + timedelta(days=days_offset, hours=random.randint(8, 19), minutes=random.randint(0, 59))

                    customer_reference = f"PO-{random.randint(10000, 99999)}" if random.random() > 0.5 else None
                    notes = "Regular delivery" if random.random() > 0.8 else None

                    batch_orders_data.append((
                        customer_id,
                        salesperson_id,
                        sales_channel_id,
                        order_status_id,
                        order_date,
                        customer_reference,
                        notes
                    ))

                # Insert orders batch and get back their assigned order_ids one by one
                order_query = """
                    INSERT INTO orders (
                        customer_id, salesperson_id, sales_channel_id, 
                        order_status_id, order_date, customer_reference, notes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING order_id;
                """
                
                inserted_order_ids = []
                for order_row in batch_orders_data:
                    cur.execute(order_query, order_row)
                    inserted_order_ids.append(cur.fetchone()[0])

                # Now generate items for each inserted order
                batch_items_data = []
                for order_id in inserted_order_ids:
                    # Each order has 1 to 4 items
                    items_count = random.choices([1, 2, 3, 4], weights=[40, 35, 15, 10])[0]
                    order_products = random.sample(products, min(items_count, len(products)))
                    
                    for prod in order_products:
                        product_id, purchase_price, standard_sale_price = prod
                        
                        # Quantity (1 to 5)
                        quantity = random.choices([1, 2, 3, 4, 5], weights=[50, 30, 10, 5, 5])[0]
                        
                        # Unit cost and sale price with slight fluctuation
                        unit_cost = round(float(purchase_price) * random.uniform(0.98, 1.02), 2)
                        unit_sale_price = round(float(standard_sale_price) * random.uniform(0.95, 1.05), 2)
                        
                        # Discount (20% chance of a small discount)
                        discount_amount = 0.00
                        if random.random() < 0.20:
                            discount_amount = round(unit_sale_price * quantity * random.uniform(0.03, 0.10), 2)

                        batch_items_data.append((
                            order_id,
                            product_id,
                            quantity,
                            unit_sale_price,
                            unit_cost,
                            discount_amount
                        ))

                # Insert order items in bulk
                item_query = """
                    INSERT INTO order_items (
                        order_id, product_id, quantity, 
                        unit_sale_price, unit_cost, discount_amount
                    )
                    VALUES (%s, %s, %s, %s, %s, %s);
                """
                cur.executemany(item_query, batch_items_data)

                generated_orders_count += current_batch_size
                generated_items_count += len(batch_items_data)
                print(f"Progress: {generated_orders_count}/{total_orders} orders generated...")

        conn.commit()
    print(f"Success! Generated {generated_orders_count} orders and {generated_items_count} order items.")

if __name__ == "__main__":
    generate_orders(40000)