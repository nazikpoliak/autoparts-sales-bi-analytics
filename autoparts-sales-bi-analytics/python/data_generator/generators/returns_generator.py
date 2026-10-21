import sys
from pathlib import Path
from datetime import timedelta
import random

# Add parent directory to python path to import db module
sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import get_connection

def generate_returns(return_count: int = 1500):
    """Generates realistic returns and their items for existing completed orders."""
    print(f"Starting generation of up to {return_count} returns...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            
            # 1. Fetch existing completed orders to create returns for
            print("Fetching completed orders and their items...")
            cur.execute("""
                SELECT o.order_id, o.customer_id, o.order_date 
                FROM orders o
                JOIN order_statuses os ON o.order_status_id = os.order_status_id
                WHERE os.status_name = 'Completed';
            """)
            completed_orders = cur.fetchall()  # [(order_id, customer_id, order_date), ...]

            if not completed_orders:
                raise RuntimeError("No completed orders found! Run order_generator.py first.")

            # Fetch return reasons mapping
            cur.execute("SELECT return_reason_id FROM return_reasons;")
            return_reasons = [row[0] for row in cur.fetchall()]

            if not return_reasons:
                raise RuntimeError("Reference data for return_reasons is missing! Run load_seeds.py first.")

            # Select a random subset of orders to have returns
            selected_orders = random.sample(completed_orders, min(return_count, len(completed_orders)))

            returns_inserted = 0
            return_items_inserted = 0

            print(f"Processing returns for {len(selected_orders)} orders...")

            for order_id, customer_id, order_date in selected_orders:
                # Return happens 1 to 20 days after the order date
                return_date = order_date + timedelta(days=random.randint(1, 20), hours=random.randint(9, 18))
                reason_id = random.choice(return_reasons)
                
                notes_options = [
                    "Defective item reported by customer",
                    "Wrong item ordered by mistake",
                    "Customer changed mind",
                    "Damaged packaging during delivery",
                    None
                ]
                notes = random.choice(notes_options)

                # Insert return header and get return_id
                cur.execute(
                    """
                    INSERT INTO returns (order_id, customer_id, return_reason_id, return_date, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING return_id;
                    """,
                    (order_id, customer_id, reason_id, return_date, notes)
                )
                return_id = cur.fetchone()[0]
                returns_inserted += 1

                # Fetch items belonging to this order
                cur.execute(
                    """
                    SELECT order_item_id, product_id, quantity, unit_sale_price 
                    FROM order_items 
                    WHERE order_id = %s;
                    """,
                    (order_id,)
                )
                order_items = cur.fetchall()

                if order_items:
                    # Return 1 item or multiple items from the order
                    items_to_return = random.sample(order_items, random.randint(1, len(order_items)))
                    
                    return_items_data = []
                    for item_id, prod_id, qty, unit_price in items_to_return:
                        return_qty = qty  # Returning full quantity of the order item
                        refund_price = float(unit_price)

                        return_items_data.append((
                            return_id,
                            item_id,
                            prod_id,
                            return_qty,
                            refund_price
                        ))

                    # Insert return items in bulk
                    cur.executemany(
                        """
                        INSERT INTO return_items (return_id, order_item_id, product_id, quantity, refund_unit_price)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (return_id, order_item_id) DO NOTHING;
                        """,
                        return_items_data
                    )
                    return_items_inserted += len(return_items_data)

        conn.commit()
    print(f"Success! Generated {returns_inserted} returns and {return_items_inserted} return items.")

if __name__ == "__main__":
    generate_returns(1500)