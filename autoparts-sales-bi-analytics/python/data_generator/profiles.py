"""Business profiles that make the synthetic data look like a B2B auto-parts distributor.

These tables are *domain assumptions*, not database data. They are kept separate from the
generation algorithms so that an analyst can tune the business behaviour (price bands,
customer mix, seasonality, margins) without touching any code logic.

Money is expressed in UAH (wholesale purchase prices, before the distributor's markup).
"""

from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SubcategoryProfile:
    """Commercial behaviour of one subcategory."""

    demand: float                 # relative sales frequency of an average product
    price_min: float              # purchase price band, UAH
    price_max: float
    qty_mean: float               # average quantity per order line for a typical customer
    qty_max: int
    weight_min: float             # kg
    weight_max: float
    nouns: tuple[str, ...]        # product kinds used in product names
    positions: bool = False       # whether Front/Rear/Left/Right makes sense
    markup: tuple[float, float] | None = None   # overrides the category markup
    brands: tuple[str, ...] | None = None       # overrides the category brand list


SUBCATEGORY_PROFILES: dict[str, SubcategoryProfile] = {
    # Engine Parts
    "Pistons and Rings": SubcategoryProfile(0.5, 800, 9000, 1.5, 6, 0.3, 3, ("Piston Set", "Piston Ring Set", "Piston Pin")),
    "Gaskets and Seals": SubcategoryProfile(1.0, 80, 4500, 2.0, 10, 0.05, 1.5, ("Cylinder Head Gasket", "Valve Cover Gasket", "Crankshaft Seal", "Gasket Set", "Oil Pan Gasket")),
    "Cylinder Head Components": SubcategoryProfile(0.6, 150, 6500, 2.0, 8, 0.1, 6, ("Valve", "Valve Guide", "Camshaft", "Rocker Arm", "Hydraulic Lifter")),
    "Engine Mounts": SubcategoryProfile(0.7, 300, 4500, 1.5, 4, 0.5, 4, ("Engine Mount", "Gearbox Mount", "Mount Bracket")),
    # Transmission and Clutch
    "Clutch Kits": SubcategoryProfile(0.7, 2500, 18000, 1.2, 3, 6, 12, ("Clutch Kit", "Clutch Kit with Release Bearing")),
    "Clutch Discs and Pressure Plates": SubcategoryProfile(0.5, 1200, 9000, 1.2, 3, 2, 6, ("Clutch Disc", "Pressure Plate", "Release Bearing", "Flywheel")),
    "Gearbox Components": SubcategoryProfile(0.4, 400, 15000, 1.2, 3, 0.2, 10, ("Synchronizer Ring", "Gear Shift Cable", "Gearbox Bearing", "Drive Shaft Seal", "Shift Lever Bushing")),
    # Brake System
    "Brake Pads": SubcategoryProfile(2.5, 450, 4200, 2.5, 12, 0.6, 2.5, ("Brake Pad Set",), positions=True),
    "Brake Discs and Drums": SubcategoryProfile(1.8, 700, 6500, 2.0, 8, 3, 12, ("Brake Disc", "Brake Drum", "Brake Disc Set"), positions=True),
    "Brake Calipers and Repair Kits": SubcategoryProfile(0.6, 150, 8000, 1.5, 5, 0.1, 6, ("Brake Caliper", "Caliper Repair Kit", "Caliper Guide Pin Set"), positions=True),
    "Brake Hydraulics": SubcategoryProfile(0.7, 200, 3500, 1.5, 6, 0.2, 2, ("Brake Hose", "Wheel Brake Cylinder", "Brake Master Cylinder")),
    # Suspension and Steering
    "Shock Absorbers and Struts": SubcategoryProfile(1.4, 1200, 9500, 2.0, 8, 2, 7, ("Shock Absorber", "Strut Assembly", "Strut Mount"), positions=True),
    "Control Arms and Ball Joints": SubcategoryProfile(1.5, 400, 7500, 2.0, 8, 0.5, 5, ("Control Arm", "Ball Joint", "Suspension Arm Bushing"), positions=True),
    "Steering Components": SubcategoryProfile(1.2, 350, 8500, 2.0, 6, 0.3, 5, ("Tie Rod End", "Steering Rack Boot", "Track Rod", "Steering Pump"), positions=True),
    "Springs and Mounts": SubcategoryProfile(0.7, 600, 6000, 2.0, 6, 1, 6, ("Coil Spring", "Spring Seat", "Top Mount Bearing"), positions=True),
    # Filters
    "Oil Filters": SubcategoryProfile(3.0, 90, 900, 4.0, 40, 0.2, 1, ("Oil Filter", "Oil Filter Element")),
    "Air Filters": SubcategoryProfile(2.6, 120, 1400, 3.0, 30, 0.2, 0.8, ("Air Filter", "Air Filter Panel")),
    "Fuel Filters": SubcategoryProfile(1.8, 150, 2200, 3.0, 25, 0.2, 1, ("Fuel Filter", "Inline Fuel Filter")),
    "Cabin Filters": SubcategoryProfile(2.0, 130, 1300, 3.0, 30, 0.1, 0.5, ("Cabin Filter", "Charcoal Cabin Filter")),
    # Electrical System
    "Alternators and Starters": SubcategoryProfile(0.5, 2800, 16000, 1.2, 3, 3, 9, ("Alternator", "Starter Motor", "Alternator Pulley", "Starter Solenoid")),
    "Batteries": SubcategoryProfile(0.9, 2400, 9800, 2.0, 10, 8, 25, ("Car Battery 60Ah", "Car Battery 74Ah", "Truck Battery 100Ah", "AGM Battery 70Ah"),
                                    markup=(1.14, 1.24), brands=("Exide", "Varta", "Yuasa", "Bosch")),
    "Sensors and Switches": SubcategoryProfile(1.6, 150, 5200, 2.0, 10, 0.05, 0.6, ("Lambda Sensor", "Crankshaft Position Sensor", "Camshaft Sensor", "Coolant Temperature Sensor", "Spark Plug Set", "Ignition Coil")),
    "Wiring and Connectors": SubcategoryProfile(0.6, 40, 1500, 4.0, 40, 0.02, 1, ("Wiring Harness", "Connector Kit", "Fuse Box Relay", "Glow Plug Relay")),
    # Cooling System
    "Radiators": SubcategoryProfile(0.5, 1800, 14000, 1.2, 3, 2.5, 9, ("Radiator", "Intercooler", "Radiator Fan")),
    "Water Pumps": SubcategoryProfile(0.9, 600, 5200, 1.5, 5, 0.5, 3, ("Water Pump", "Water Pump with Housing")),
    "Thermostats": SubcategoryProfile(0.8, 180, 2800, 2.0, 8, 0.1, 1, ("Thermostat", "Thermostat Housing")),
    "Coolant Hoses": SubcategoryProfile(0.9, 120, 2400, 2.0, 8, 0.1, 1.2, ("Radiator Hose", "Heater Hose", "Coolant Pipe")),
    # Fuel System
    "Fuel Pumps": SubcategoryProfile(0.6, 900, 9000, 1.5, 4, 0.4, 2.5, ("Fuel Pump", "Fuel Pump Module", "High Pressure Fuel Pump")),
    "Injectors": SubcategoryProfile(0.5, 1800, 14000, 2.0, 8, 0.1, 0.6, ("Fuel Injector", "Diesel Injector", "Injector Seal Kit")),
    "Fuel System Sensors": SubcategoryProfile(0.5, 250, 4500, 1.5, 5, 0.05, 0.5, ("Fuel Pressure Sensor", "Fuel Level Sensor", "Rail Pressure Sensor")),
    # Exhaust System
    "Exhaust Pipes and Mounts": SubcategoryProfile(0.6, 150, 12000, 1.5, 5, 0.2, 10, ("Exhaust Pipe", "Muffler", "Exhaust Hanger", "Catalytic Converter")),
    "EGR and Exhaust Components": SubcategoryProfile(0.4, 600, 11000, 1.3, 4, 0.3, 4, ("EGR Valve", "EGR Cooler", "Exhaust Manifold Gasket", "Exhaust Gas Sensor")),
    # Body and Exterior
    "Mirrors and Handles": SubcategoryProfile(0.6, 250, 5000, 1.5, 5, 0.2, 2, ("Side Mirror", "Mirror Glass", "Door Handle"), positions=True),
    "Bumpers and Grilles": SubcategoryProfile(0.4, 900, 9000, 1.2, 3, 1, 7, ("Front Bumper", "Radiator Grille", "Bumper Bracket")),
    "Body Fasteners": SubcategoryProfile(0.9, 15, 400, 10.0, 100, 0.01, 0.2, ("Body Clip Set", "Trim Fastener Kit", "Door Panel Clips")),
    # Lighting
    "Headlights": SubcategoryProfile(0.5, 1800, 15000, 1.3, 4, 1.5, 5, ("Headlight", "LED Headlight", "Fog Light"), positions=True),
    "Tail Lights": SubcategoryProfile(0.5, 900, 8000, 1.3, 4, 0.8, 3, ("Tail Light", "Rear Lamp Assembly"), positions=True),
    "Bulbs and LED Modules": SubcategoryProfile(2.0, 25, 1800, 4.0, 40, 0.01, 0.3, ("H7 Bulb", "H4 Bulb", "LED Bulb Kit", "Indicator Bulb")),
    # Bearings and Hubs
    "Wheel Bearings": SubcategoryProfile(1.5, 280, 3500, 2.0, 10, 0.3, 2, ("Wheel Bearing Kit", "Wheel Bearing"), positions=True),
    "Wheel Hubs": SubcategoryProfile(0.7, 900, 6500, 1.5, 4, 1.5, 6, ("Wheel Hub Assembly", "Wheel Hub with Bearing"), positions=True),
    # Belts and Timing
    "Timing Belts and Kits": SubcategoryProfile(1.3, 600, 9500, 1.5, 6, 0.3, 2.5, ("Timing Belt Kit", "Timing Belt", "Timing Chain Kit")),
    "Drive Belts": SubcategoryProfile(1.4, 150, 1800, 2.0, 10, 0.1, 0.6, ("V-Ribbed Belt", "Drive Belt")),
    "Tensioners and Idlers": SubcategoryProfile(0.9, 300, 3800, 1.8, 6, 0.2, 1.5, ("Belt Tensioner", "Idler Pulley", "Tensioner Pulley")),
    # Lubricants and Fluids
    "Engine Oils": SubcategoryProfile(2.4, 350, 6200, 5.0, 48, 0.9, 20, ("Engine Oil 5W-30 4L", "Engine Oil 5W-40 5L", "Engine Oil 10W-40 1L", "Engine Oil 0W-20 4L")),
    "Coolants and Antifreeze": SubcategoryProfile(1.2, 150, 1400, 4.0, 40, 1, 10, ("Antifreeze G12 5L", "Antifreeze G13 5L", "Coolant Concentrate 1.5L")),
    "Transmission Fluids": SubcategoryProfile(0.9, 250, 3500, 3.0, 30, 0.9, 10, ("ATF Dexron VI 1L", "Gear Oil 75W-90 1L", "CVT Fluid 4L")),
    "Greases and Technical Fluids": SubcategoryProfile(1.0, 80, 1500, 4.0, 40, 0.1, 2, ("Copper Grease 100g", "Brake Fluid DOT4 1L", "Power Steering Fluid 1L", "Washer Fluid 4L")),
    # Workshop Supplies
    "Workshop Chemicals": SubcategoryProfile(1.1, 60, 1800, 4.0, 40, 0.2, 5, ("Brake Cleaner 500ml", "Carburetor Cleaner 400ml", "Engine Degreaser 1L", "Thread Locker 50ml", "Silicone Sealant 280ml")),
    "Clamps and Ties": SubcategoryProfile(0.9, 10, 500, 10.0, 100, 0.01, 0.5, ("Hose Clamp Set", "Cable Tie Pack", "Spring Clamp Set")),
    "Fasteners and Fittings": SubcategoryProfile(1.0, 15, 900, 8.0, 80, 0.01, 1, ("Bolt Kit", "Nut and Washer Set", "Fitting Set", "Oil Drain Plug")),
}

POSITIONS = ("Front", "Rear", "Front Left", "Front Right", "Rear Left", "Rear Right")

# Distributor's markup over the purchase price (min, max) by category.
CATEGORY_MARKUP: dict[str, tuple[float, float]] = {
    "Engine Parts": (1.22, 1.34),
    "Transmission and Clutch": (1.20, 1.32),
    "Brake System": (1.28, 1.42),
    "Suspension and Steering": (1.25, 1.38),
    "Filters": (1.35, 1.55),
    "Electrical System": (1.22, 1.40),
    "Cooling System": (1.25, 1.38),
    "Fuel System": (1.20, 1.32),
    "Exhaust System": (1.25, 1.40),
    "Body and Exterior": (1.28, 1.45),
    "Lighting": (1.25, 1.40),
    "Bearings and Hubs": (1.22, 1.34),
    "Belts and Timing": (1.28, 1.40),
    "Lubricants and Fluids": (1.18, 1.28),
    "Workshop Supplies": (1.35, 1.60),
}

# Which brands realistically make products of a category.
CATEGORY_BRANDS: dict[str, tuple[str, ...]] = {
    "Engine Parts": ("MAHLE", "Mahle Original", "Elring", "Victor Reinz", "INA", "Schaeffler", "Febi Bilstein", "Meyle", "BorgWarner", "Pierburg"),
    "Transmission and Clutch": ("ZF", "Schaeffler", "Aisin", "Febi Bilstein", "Meyle", "Lemforder", "Valeo", "BorgWarner"),
    "Brake System": ("Brembo", "TRW", "ATE", "Textar", "Bosch", "Delphi", "Febi Bilstein", "Meyle", "Continental", "Valeo"),
    "Suspension and Steering": ("KYB", "Monroe", "Lemforder", "TRW", "Moog", "Meyle", "Febi Bilstein", "Febest", "Delphi", "ZF"),
    "Filters": ("MANN-FILTER", "Hengst", "Bosch", "MAHLE", "Mahle Original", "Denso", "Valeo", "Febi Bilstein"),
    "Electrical System": ("Bosch", "Denso", "Valeo", "Delphi", "Hella", "NGK", "Continental", "Pierburg"),
    "Cooling System": ("MAHLE", "Valeo", "Gates", "Denso", "Febi Bilstein", "Meyle", "Aisin", "Pierburg"),
    "Fuel System": ("Bosch", "Denso", "Delphi", "Continental", "Pierburg", "Hella"),
    "Exhaust System": ("Bosch", "Febi Bilstein", "Meyle", "MAHLE", "Pierburg", "BorgWarner", "Elring", "Febest"),
    "Body and Exterior": ("Hella", "Valeo", "Febi Bilstein", "Meyle", "Febest"),
    "Lighting": ("Hella", "Bosch", "Valeo", "Denso", "Delphi"),
    "Bearings and Hubs": ("SKF", "FAG", "INA", "NTN", "NSK", "Schaeffler", "Febi Bilstein", "Aisin", "Meyle"),
    "Belts and Timing": ("Gates", "Dayco", "Continental", "INA", "Schaeffler", "SKF", "Febi Bilstein", "Aisin"),
    "Lubricants and Fluids": ("Bardahl", "Febi Bilstein", "Meyle"),
    "Workshop Supplies": ("Bardahl", "Febi Bilstein", "Gates", "Bosch", "Febest"),
}

# Price positioning of brands: multiplier of the purchase price band.
BRAND_TIER_MULTIPLIER = {"premium": 1.30, "standard": 1.00, "value": 0.78}
BRAND_TIERS: dict[str, str] = {
    **{name: "premium" for name in (
        "Bosch", "Brembo", "ZF", "Continental", "MAHLE", "Lemforder", "Schaeffler", "Denso", "Valeo",
        "Hella", "SKF", "FAG", "ATE", "MANN-FILTER", "Gates", "NGK", "Aisin")},
    **{name: "value" for name in ("Febest", "Exide", "Meyle", "Monroe")},
}  # every other brand is "standard"

# Suppliers that specialise in some categories (all others are generalists).
SUPPLIER_SPECIALISATION: dict[str, tuple[str, ...]] = {
    "Global Battery Supply": ("Electrical System",),
    "Premium Brake Systems": ("Brake System",),
    "Engine and Filtration Wholesale": ("Engine Parts", "Filters", "Cooling System"),
    "Fleet Service Components": ("Suspension and Steering", "Transmission and Clutch", "Workshop Supplies"),
}

# Probability of a product status at creation (names as in the product_statuses seed).
PRODUCT_STATUS_WEIGHTS = {"Active": 90, "Discontinued": 5, "Temporarily Unavailable": 3, "Preorder": 2}


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CustomerTypeProfile:
    """Purchasing behaviour of one customer type."""

    share: float                  # share of the customer base
    activity: float               # average relative number of orders
    items_mu: float               # log-normal parameters of lines per order
    items_sigma: float
    qty_mult: float               # multiplies typical line quantity
    price_factor: float           # negotiated price level vs. standard price
    discount_prob: float          # probability that a line carries a discount
    channel_weights: dict[str, int]
    category_affinity: dict[str, float]
    reference_prob: float         # probability that an order has a customer PO number


CUSTOMER_TYPE_PROFILES: dict[str, CustomerTypeProfile] = {
    "Auto Parts Store": CustomerTypeProfile(
        share=0.28, activity=1.0, items_mu=1.55, items_sigma=0.55, qty_mult=1.2, price_factor=0.98,
        discount_prob=0.18,
        channel_weights={"B2B Portal": 30, "Phone Order": 25, "Sales Representative": 20, "Email Order": 15, "E-commerce": 10},
        category_affinity={"Filters": 1.3, "Lubricants and Fluids": 1.2, "Lighting": 1.2},
        reference_prob=0.25),
    "Service Station": CustomerTypeProfile(
        share=0.34, activity=0.8, items_mu=1.35, items_sigma=0.55, qty_mult=0.9, price_factor=1.00,
        discount_prob=0.15,
        channel_weights={"Phone Order": 35, "Sales Representative": 25, "B2B Portal": 15, "E-commerce": 15, "Email Order": 10},
        category_affinity={"Brake System": 1.4, "Filters": 1.3, "Suspension and Steering": 1.2, "Lubricants and Fluids": 1.3, "Workshop Supplies": 1.4},
        reference_prob=0.10),
    "Fleet Operator": CustomerTypeProfile(
        share=0.12, activity=1.3, items_mu=1.50, items_sigma=0.50, qty_mult=1.6, price_factor=0.96,
        discount_prob=0.30,
        channel_weights={"Email Order": 30, "Sales Representative": 30, "B2B Portal": 25, "Phone Order": 15},
        category_affinity={"Filters": 1.5, "Lubricants and Fluids": 1.6, "Brake System": 1.3, "Belts and Timing": 1.2, "Electrical System": 1.2},
        reference_prob=0.70),
    "Dealer": CustomerTypeProfile(
        share=0.08, activity=2.2, items_mu=1.90, items_sigma=0.50, qty_mult=1.8, price_factor=0.94,
        discount_prob=0.40,
        channel_weights={"B2B Portal": 40, "Sales Representative": 30, "Email Order": 20, "Phone Order": 10},
        category_affinity={"Body and Exterior": 1.5, "Lighting": 1.4, "Engine Parts": 1.2, "Transmission and Clutch": 1.3},
        reference_prob=0.60),
    "Corporate Customer": CustomerTypeProfile(
        share=0.18, activity=0.9, items_mu=1.55, items_sigma=0.55, qty_mult=1.4, price_factor=0.97,
        discount_prob=0.30,
        channel_weights={"Email Order": 35, "Sales Representative": 30, "B2B Portal": 25, "Phone Order": 10},
        category_affinity={"Filters": 1.3, "Lubricants and Fluids": 1.4, "Suspension and Steering": 1.2, "Fuel System": 1.2},
        reference_prob=0.65),
}

# Relative weight of cities when customers are placed (larger cities host more customers).
CITY_WEIGHTS: dict[str, float] = {
    "Kyiv": 10, "Lviv": 7, "Odesa": 6, "Dnipro": 6, "Kharkiv": 5, "Vinnytsia": 3, "Poltava": 3,
    "Ivano-Frankivsk": 3, "Kryvyi Rih": 3, "Kremenchuk": 2, "Bila Tserkva": 2, "Kamianske": 2,
    "Drohobych": 1.5, "Brovary": 1.5, "Boryspil": 1.5, "Kalush": 1.5, "Kolomyia": 1.5,
}

# Seasonality of demand by calendar month and weekday (multipliers).
MONTH_SEASONALITY = {1: 0.85, 2: 0.90, 3: 1.05, 4: 1.15, 5: 1.10, 6: 1.00,
                     7: 0.95, 8: 0.95, 9: 1.10, 10: 1.20, 11: 1.15, 12: 0.90}
WEEKDAY_FACTOR = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.0, 4: 0.95, 5: 0.35, 6: 0.08}  # Monday = 0
ORDER_HOURS = list(range(8, 19))
ORDER_HOUR_WEIGHTS = [6, 10, 12, 12, 9, 8, 10, 11, 9, 7, 4]  # lunch dip, afternoon peak
