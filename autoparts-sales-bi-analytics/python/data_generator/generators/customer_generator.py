import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to python path to import db module
sys.path.append(str(Path(__file__).resolve().parent.parent))

from db import get_connection

# Lists of prefixes and suffixes for generating realistic auto parts business names
STORE_PREFIXES = ["Auto", "Moto", "Express", "Apex", "Master", "Megaparts", "Karat", "Delta", "Alpha"]
STORE_SUFFIXES = ["Parts", "Shop", "Market", "Store", "Hub", "Express", "Depot"]

SERVICE_PREFIXES = ["Turbo", "Auto", "Bosch", "Pro", "Fast", "Elite", "City", "Modern", "Mecano"]
SERVICE_SUFFIXES = ["Service", "Garage", "Station", "Center", "Repair", "Tech"]

COMPANY_NAMES = [
    "TransLogistics Ukraine", "Autoland Group", "Carpathian Transport", 
    "Omega Fleet", "Prime Auto", "Vector Logistics", "AvtoAlliance", "Inter-Cargo"
]

FIRST_NAMES = ["Andrii", "Iryna", "Taras", "Olena", "Maksym", "Sofiia", "Dmytro", "Kateryna", "Bohdan", "Yuliia"]
LAST_NAMES = ["Koval", "Melnyk", "Boyko", "Shevchuk", "Tkachenko", "Bondar", "Marchenko", "Savchenko", "Klymenko", "Kravets"]

# Diverse pool of street names for random address generation
STREET_NAMES = [
    "vul. Shevchenka", "vul. Ivana Franka", "vul. Lesi Ukrainky", "pr. Chornovola", 
    "vul. Halytska", "vul. Sadova", "vul. Zamkova", "vul. Industrialna", 
    "vul. Kyivska", "vul. Lvivska", "pr. Svobody", "vul. Kopernyka", 
    "vul. Horodotska", "vul. Stryiska", "vul. Volodymyra Velykoho", 
    "vul. Bandery", "vul. Vighovskoho", "vul. Patona", "pr. Redutnyi"
]

def generate_tax_id(existing_tax_ids: set) -> str:
    """Generates a unique 8 or 10-digit tax ID / EDRPOU code."""
    while True:
        tax_id = "".join([str(random.randint(0, 9)) for _ in range(random.choice([8, 10]))])
        if tax_id not in existing_tax_ids:
            existing_tax_ids.add(tax_id)
            return tax_id

def generate_random_address() -> str:
    """Generates a random realistic street address with building and optional apartment numbers."""
    street = random.choice(STREET_NAMES)
    building = random.randint(1, 220)
    if random.choice([True, False]):
        apartment = random.randint(1, 150)
        return f"{street}, {building}, apt. {apartment}"
    return f"{street}, {building}"

def generate_customers(count: int = 500):
    """Generates realistic customer records and inserts them into the database."""
    print(f"Starting generation of {count} customers...")

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Fetch customer types mapping
            cur.execute("SELECT customer_type_id, type_name FROM customer_types;")
            customer_types = cur.fetchall()
            
            # Fetch cities mapping
            cur.execute("SELECT city_id, city_name FROM cities;")
            cities = cur.fetchall()

            if not customer_types or not cities:
                raise RuntimeError("Reference data for customer_types or cities is missing! Run load_seeds.py first.")

            # Get existing tax IDs to avoid unique constraint violations
            cur.execute("SELECT tax_id FROM customers WHERE tax_id IS NOT NULL;")
            existing_tax_ids = {row[0] for row in cur.fetchall()}

            inserted_count = 0
            start_date = datetime.now() - timedelta(days=3 * 365) # 3 years back

            for _ in range(count):
                # Pick a random customer type and city
                c_type_id, c_type_name = random.choice(customer_types)
                city_id, city_name = random.choice(cities)

                # Generate name and details depending on customer type
                if "Store" in c_type_name:
                    customer_name = f"{random.choice(STORE_PREFIXES)} {random.choice(STORE_SUFFIXES)} ({city_name})"
                    phone = f"+380{random.randint(50, 99)}{random.randint(1000000, 9999999)}"
                    email = f"contact@{customer_name.lower().replace(' ', '').replace('(', '').replace(')', '')}.ua"
                    tax_id = generate_tax_id(existing_tax_ids)
                elif "Service Station" in c_type_name:
                    customer_name = f"STO '{random.choice(SERVICE_PREFIXES)} {random.choice(SERVICE_SUFFIXES)}'"
                    phone = f"+380{random.randint(50, 99)}{random.randint(1000000, 9999999)}"
                    email = f"service.{city_name.lower()}@autoservice.ua"
                    tax_id = generate_tax_id(existing_tax_ids)
                elif "Dealer" in c_type_name or "Fleet" in c_type_name or "Corporate" in c_type_name:
                    customer_name = f"{random.choice(COMPANY_NAMES)} {city_name}"
                    phone = f"+380{random.randint(50, 99)}{random.randint(1000000, 9999999)}"
                    email = f"office@{customer_name.lower().replace(' ', '')}.com.ua"
                    tax_id = generate_tax_id(existing_tax_ids)
                else:  # Individual
                    first = random.choice(FIRST_NAMES)
                    last = random.choice(LAST_NAMES)
                    customer_name = f"{first} {last}"
                    phone = f"+380{random.randint(60, 99)}{random.randint(1000000, 9999999)}"
                    email = f"{first.lower()}.{last.lower()}{random.randint(10, 99)}@gmail.com"
                    tax_id = None  # Individuals might not have a corporate tax id

                # Fully random address assignment
                address = generate_random_address()

                # Random registration date over the last 3 years
                days_offset = random.randint(0, 3 * 365)
                registration_date = (start_date + timedelta(days=days_offset)).date()
                is_active = random.choices([True, False], weights=[90, 10])[0] # 90% active

                cur.execute(
                    """
                    INSERT INTO customers (
                        customer_type_id, city_id, customer_name, tax_id, 
                        phone, email, address, registration_date, is_active
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        c_type_id,
                        city_id,
                        customer_name,
                        tax_id,
                        phone,
                        email,
                        address,
                        registration_date,
                        is_active
                    )
                )
                inserted_count += 1

        conn.commit()
    print(f"Success! Generated and inserted {inserted_count} customers with randomized addresses.")

if __name__ == "__main__":
    generate_customers(2000)