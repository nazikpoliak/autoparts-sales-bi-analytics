"""
Reference/seed data for AutoParts Sales & BI Analytics.

Target: PostgreSQL database `autoparts_bi`
Schema: 18 normalized operational tables

The records in this file are seed definitions, not database IDs.
Foreign-key relationships are expressed through natural keys/names:
- cities -> region_name
- salespersons -> region_name
- subcategories -> category_name

The loader should resolve these names to actual PK values at insertion time.
"""

REGIONS = [
    {"region_name": "Lvivska"},
    {"region_name": "Kyivska"},
    {"region_name": "Odeska"},
    {"region_name": "Dnipropetrovska"},
    {"region_name": "Kharkivska"},
    {"region_name": "Vinnytska"},
    {"region_name": "Poltavska"},
    {"region_name": "Ivano-Frankivska"},
]

CITIES = [
    # Lvivska
    {"city_name": "Lviv", "region_name": "Lvivska"},
    {"city_name": "Drohobych", "region_name": "Lvivska"},
    {"city_name": "Stryi", "region_name": "Lvivska"},
    {"city_name": "Chervonohrad", "region_name": "Lvivska"},
    {"city_name": "Sambir", "region_name": "Lvivska"},
    {"city_name": "Zolochiv", "region_name": "Lvivska"},
    # Kyivska
    {"city_name": "Kyiv", "region_name": "Kyivska"},
    {"city_name": "Bila Tserkva", "region_name": "Kyivska"},
    {"city_name": "Boryspil", "region_name": "Kyivska"},
    {"city_name": "Brovary", "region_name": "Kyivska"},
    {"city_name": "Fastiv", "region_name": "Kyivska"},
    {"city_name": "Obukhiv", "region_name": "Kyivska"},
    # Odeska
    {"city_name": "Odesa", "region_name": "Odeska"},
    {"city_name": "Chornomorsk", "region_name": "Odeska"},
    {"city_name": "Izmail", "region_name": "Odeska"},
    {"city_name": "Bilhorod-Dnistrovskyi", "region_name": "Odeska"},
    {"city_name": "Podilsk", "region_name": "Odeska"},
    # Dnipropetrovska
    {"city_name": "Dnipro", "region_name": "Dnipropetrovska"},
    {"city_name": "Kryvyi Rih", "region_name": "Dnipropetrovska"},
    {"city_name": "Kamianske", "region_name": "Dnipropetrovska"},
    {"city_name": "Pavlohrad", "region_name": "Dnipropetrovska"},
    {"city_name": "Nikopol", "region_name": "Dnipropetrovska"},
    # Kharkivska
    {"city_name": "Kharkiv", "region_name": "Kharkivska"},
    {"city_name": "Chuhuiv", "region_name": "Kharkivska"},
    {"city_name": "Lozova", "region_name": "Kharkivska"},
    {"city_name": "Bohodukhiv", "region_name": "Kharkivska"},
    {"city_name": "Izium", "region_name": "Kharkivska"},
    # Vinnytska
    {"city_name": "Vinnytsia", "region_name": "Vinnytska"},
    {"city_name": "Zhmerynka", "region_name": "Vinnytska"},
    {"city_name": "Mohyliv-Podilskyi", "region_name": "Vinnytska"},
    {"city_name": "Khmilnyk", "region_name": "Vinnytska"},
    {"city_name": "Haisyn", "region_name": "Vinnytska"},
    # Poltavska
    {"city_name": "Poltava", "region_name": "Poltavska"},
    {"city_name": "Kremenchuk", "region_name": "Poltavska"},
    {"city_name": "Myrhorod", "region_name": "Poltavska"},
    {"city_name": "Lubny", "region_name": "Poltavska"},
    {"city_name": "Horishni Plavni", "region_name": "Poltavska"},
    # Ivano-Frankivska
    {"city_name": "Ivano-Frankivsk", "region_name": "Ivano-Frankivska"},
    {"city_name": "Kalush", "region_name": "Ivano-Frankivska"},
    {"city_name": "Kolomyia", "region_name": "Ivano-Frankivska"},
    {"city_name": "Nadvirna", "region_name": "Ivano-Frankivska"},
    {"city_name": "Dolyna", "region_name": "Ivano-Frankivska"},
]

CUSTOMER_TYPES = [
    {"customer_type_name": "Auto Parts Store"},
    {"customer_type_name": "Service Station"},
    {"customer_type_name": "Fleet Operator"},
    {"customer_type_name": "Dealer"},
    {"customer_type_name": "Corporate Customer"},
]

# Synthetic employee names for a fictional distributor. Employee codes are unique.
SALESPERSONS = [
    {"employee_code": "EMP-0001", "first_name": "Andrii", "last_name": "Koval", "region_name": "Lvivska", "hire_date": "2021-03-15", "status": "Active"},
    {"employee_code": "EMP-0002", "first_name": "Iryna", "last_name": "Melnyk", "region_name": "Lvivska", "hire_date": "2022-06-01", "status": "Active"},
    {"employee_code": "EMP-0003", "first_name": "Taras", "last_name": "Boyko", "region_name": "Lvivska", "hire_date": "2020-11-09", "status": "Active"},
    {"employee_code": "EMP-0004", "first_name": "Olena", "last_name": "Shevchuk", "region_name": "Kyivska", "hire_date": "2019-08-12", "status": "Active"},
    {"employee_code": "EMP-0005", "first_name": "Maksym", "last_name": "Tkachenko", "region_name": "Kyivska", "hire_date": "2022-02-21", "status": "Active"},
    {"employee_code": "EMP-0006", "first_name": "Sofiia", "last_name": "Bondar", "region_name": "Kyivska", "hire_date": "2023-01-16", "status": "Active"},
    {"employee_code": "EMP-0007", "first_name": "Dmytro", "last_name": "Marchenko", "region_name": "Odeska", "hire_date": "2020-04-06", "status": "Active"},
    {"employee_code": "EMP-0008", "first_name": "Kateryna", "last_name": "Savchenko", "region_name": "Odeska", "hire_date": "2021-09-20", "status": "Active"},
    {"employee_code": "EMP-0009", "first_name": "Vladyslav", "last_name": "Rudenko", "region_name": "Odeska", "hire_date": "2024-02-05", "status": "Active"},
    {"employee_code": "EMP-0010", "first_name": "Oleksii", "last_name": "Klymenko", "region_name": "Dnipropetrovska", "hire_date": "2018-10-01", "status": "Active"},
    {"employee_code": "EMP-0011", "first_name": "Yuliia", "last_name": "Kravets", "region_name": "Dnipropetrovska", "hire_date": "2021-05-17", "status": "Active"},
    {"employee_code": "EMP-0012", "first_name": "Roman", "last_name": "Lysenko", "region_name": "Dnipropetrovska", "hire_date": "2023-07-03", "status": "Active"},
    {"employee_code": "EMP-0013", "first_name": "Bohdan", "last_name": "Tymoshenko", "region_name": "Kharkivska", "hire_date": "2020-01-13", "status": "Active"},
    {"employee_code": "EMP-0014", "first_name": "Natalia", "last_name": "Pavlenko", "region_name": "Kharkivska", "hire_date": "2022-11-07", "status": "Active"},
    {"employee_code": "EMP-0015", "first_name": "Serhii", "last_name": "Moroz", "region_name": "Kharkivska", "hire_date": "2024-04-15", "status": "Active"},
    {"employee_code": "EMP-0016", "first_name": "Viktoriia", "last_name": "Kozak", "region_name": "Vinnytska", "hire_date": "2021-02-08", "status": "Active"},
    {"employee_code": "EMP-0017", "first_name": "Mykhailo", "last_name": "Oliinyk", "region_name": "Vinnytska", "hire_date": "2023-10-02", "status": "Active"},
    {"employee_code": "EMP-0018", "first_name": "Anastasiia", "last_name": "Polishchuk", "region_name": "Vinnytska", "hire_date": "2020-06-22", "status": "Active"},
    {"employee_code": "EMP-0019", "first_name": "Yaroslav", "last_name": "Hrytsenko", "region_name": "Poltavska", "hire_date": "2019-12-02", "status": "Active"},
    {"employee_code": "EMP-0020", "first_name": "Mariia", "last_name": "Zakharchuk", "region_name": "Poltavska", "hire_date": "2022-08-29", "status": "Active"},
    {"employee_code": "EMP-0021", "first_name": "Denys", "last_name": "Kovalchuk", "region_name": "Poltavska", "hire_date": "2024-01-22", "status": "Active"},
    {"employee_code": "EMP-0022", "first_name": "Pavlo", "last_name": "Berezovskyi", "region_name": "Ivano-Frankivska", "hire_date": "2020-09-14", "status": "Active"},
    {"employee_code": "EMP-0023", "first_name": "Oksana", "last_name": "Danyliuk", "region_name": "Ivano-Frankivska", "hire_date": "2022-04-11", "status": "Active"},
    {"employee_code": "EMP-0024", "first_name": "Artem", "last_name": "Fedorchuk", "region_name": "Ivano-Frankivska", "hire_date": "2023-12-04", "status": "Active"},
]

CATEGORIES = [
    {"category_name": "Engine Parts"},
    {"category_name": "Transmission and Clutch"},
    {"category_name": "Brake System"},
    {"category_name": "Suspension and Steering"},
    {"category_name": "Filters"},
    {"category_name": "Electrical System"},
    {"category_name": "Cooling System"},
    {"category_name": "Fuel System"},
    {"category_name": "Exhaust System"},
    {"category_name": "Body and Exterior"},
    {"category_name": "Lighting"},
    {"category_name": "Bearings and Hubs"},
    {"category_name": "Belts and Timing"},
    {"category_name": "Lubricants and Fluids"},
    {"category_name": "Workshop Supplies"},
]

SUBCATEGORIES = [
    {"subcategory_name": "Pistons and Rings", "category_name": "Engine Parts"},
    {"subcategory_name": "Gaskets and Seals", "category_name": "Engine Parts"},
    {"subcategory_name": "Cylinder Head Components", "category_name": "Engine Parts"},
    {"subcategory_name": "Engine Mounts", "category_name": "Engine Parts"},
    {"subcategory_name": "Clutch Kits", "category_name": "Transmission and Clutch"},
    {"subcategory_name": "Clutch Discs and Pressure Plates", "category_name": "Transmission and Clutch"},
    {"subcategory_name": "Gearbox Components", "category_name": "Transmission and Clutch"},
    {"subcategory_name": "Brake Pads", "category_name": "Brake System"},
    {"subcategory_name": "Brake Discs and Drums", "category_name": "Brake System"},
    {"subcategory_name": "Brake Calipers and Repair Kits", "category_name": "Brake System"},
    {"subcategory_name": "Brake Hydraulics", "category_name": "Brake System"},
    {"subcategory_name": "Shock Absorbers and Struts", "category_name": "Suspension and Steering"},
    {"subcategory_name": "Control Arms and Ball Joints", "category_name": "Suspension and Steering"},
    {"subcategory_name": "Steering Components", "category_name": "Suspension and Steering"},
    {"subcategory_name": "Springs and Mounts", "category_name": "Suspension and Steering"},
    {"subcategory_name": "Oil Filters", "category_name": "Filters"},
    {"subcategory_name": "Air Filters", "category_name": "Filters"},
    {"subcategory_name": "Fuel Filters", "category_name": "Filters"},
    {"subcategory_name": "Cabin Filters", "category_name": "Filters"},
    {"subcategory_name": "Alternators and Starters", "category_name": "Electrical System"},
    {"subcategory_name": "Batteries", "category_name": "Electrical System"},
    {"subcategory_name": "Sensors and Switches", "category_name": "Electrical System"},
    {"subcategory_name": "Wiring and Connectors", "category_name": "Electrical System"},
    {"subcategory_name": "Radiators", "category_name": "Cooling System"},
    {"subcategory_name": "Water Pumps", "category_name": "Cooling System"},
    {"subcategory_name": "Thermostats", "category_name": "Cooling System"},
    {"subcategory_name": "Coolant Hoses", "category_name": "Cooling System"},
    {"subcategory_name": "Fuel Pumps", "category_name": "Fuel System"},
    {"subcategory_name": "Injectors", "category_name": "Fuel System"},
    {"subcategory_name": "Fuel System Sensors", "category_name": "Fuel System"},
    {"subcategory_name": "Exhaust Pipes and Mounts", "category_name": "Exhaust System"},
    {"subcategory_name": "EGR and Exhaust Components", "category_name": "Exhaust System"},
    {"subcategory_name": "Mirrors and Handles", "category_name": "Body and Exterior"},
    {"subcategory_name": "Bumpers and Grilles", "category_name": "Body and Exterior"},
    {"subcategory_name": "Body Fasteners", "category_name": "Body and Exterior"},
    {"subcategory_name": "Headlights", "category_name": "Lighting"},
    {"subcategory_name": "Tail Lights", "category_name": "Lighting"},
    {"subcategory_name": "Bulbs and LED Modules", "category_name": "Lighting"},
    {"subcategory_name": "Wheel Bearings", "category_name": "Bearings and Hubs"},
    {"subcategory_name": "Wheel Hubs", "category_name": "Bearings and Hubs"},
    {"subcategory_name": "Timing Belts and Kits", "category_name": "Belts and Timing"},
    {"subcategory_name": "Drive Belts", "category_name": "Belts and Timing"},
    {"subcategory_name": "Tensioners and Idlers", "category_name": "Belts and Timing"},
    {"subcategory_name": "Engine Oils", "category_name": "Lubricants and Fluids"},
    {"subcategory_name": "Coolants and Antifreeze", "category_name": "Lubricants and Fluids"},
    {"subcategory_name": "Transmission Fluids", "category_name": "Lubricants and Fluids"},
    {"subcategory_name": "Greases and Technical Fluids", "category_name": "Lubricants and Fluids"},
    {"subcategory_name": "Workshop Chemicals", "category_name": "Workshop Supplies"},
    {"subcategory_name": "Clamps and Ties", "category_name": "Workshop Supplies"},
    {"subcategory_name": "Fasteners and Fittings", "category_name": "Workshop Supplies"},
]

BRANDS = [
    {"brand_name": "Bosch", "country": "Germany", "status": "Active"},
    {"brand_name": "MANN-FILTER", "country": "Germany", "status": "Active"},
    {"brand_name": "MAHLE", "country": "Germany", "status": "Active"},
    {"brand_name": "Febi Bilstein", "country": "Germany", "status": "Active"},
    {"brand_name": "Schaeffler", "country": "Germany", "status": "Active"},
    {"brand_name": "INA", "country": "Germany", "status": "Active"},
    {"brand_name": "FAG", "country": "Germany", "status": "Active"},
    {"brand_name": "Lemforder", "country": "Germany", "status": "Active"},
    {"brand_name": "ZF", "country": "Germany", "status": "Active"},
    {"brand_name": "Hengst", "country": "Germany", "status": "Active"},
    {"brand_name": "Brembo", "country": "Italy", "status": "Active"},
    {"brand_name": "Valeo", "country": "France", "status": "Active"},
    {"brand_name": "Gates", "country": "United States", "status": "Active"},
    {"brand_name": "Dayco", "country": "United States", "status": "Active"},
    {"brand_name": "NGK", "country": "Japan", "status": "Active"},
    {"brand_name": "Denso", "country": "Japan", "status": "Active"},
    {"brand_name": "KYB", "country": "Japan", "status": "Active"},
    {"brand_name": "Aisin", "country": "Japan", "status": "Active"},
    {"brand_name": "NTN", "country": "Japan", "status": "Active"},
    {"brand_name": "NSK", "country": "Japan", "status": "Active"},
    {"brand_name": "TRW", "country": "United States", "status": "Active"},
    {"brand_name": "Monroe", "country": "United States", "status": "Active"},
    {"brand_name": "Delphi", "country": "United Kingdom", "status": "Active"},
    {"brand_name": "Continental", "country": "Germany", "status": "Active"},
    {"brand_name": "Hella", "country": "Germany", "status": "Active"},
    {"brand_name": "Pierburg", "country": "Germany", "status": "Active"},
    {"brand_name": "Elring", "country": "Germany", "status": "Active"},
    {"brand_name": "Victor Reinz", "country": "Germany", "status": "Active"},
    {"brand_name": "Meyle", "country": "Germany", "status": "Active"},
    {"brand_name": "Textar", "country": "Germany", "status": "Active"},
    {"brand_name": "ATE", "country": "Germany", "status": "Active"},
    {"brand_name": "Febest", "country": "Germany", "status": "Active"},
    {"brand_name": "Moog", "country": "United States", "status": "Active"},
    {"brand_name": "SKF", "country": "Sweden", "status": "Active"},
    {"brand_name": "Exide", "country": "United States", "status": "Active"},
    {"brand_name": "Varta", "country": "Germany", "status": "Active"},
    {"brand_name": "Yuasa", "country": "Japan", "status": "Active"},
    {"brand_name": "BorgWarner", "country": "United States", "status": "Active"},
    {"brand_name": "Mahle Original", "country": "Germany", "status": "Active"},
    {"brand_name": "Bardahl", "country": "United States", "status": "Active"},
]

SUPPLIERS = [
    {"supplier_name": "EuroParts Distribution", "country": "Poland", "status": "Active"},
    {"supplier_name": "Central Auto Supply", "country": "Germany", "status": "Active"},
    {"supplier_name": "Baltic Automotive Group", "country": "Lithuania", "status": "Active"},
    {"supplier_name": "Danube Parts Trading", "country": "Romania", "status": "Active"},
    {"supplier_name": "Carpathian Components", "country": "Slovakia", "status": "Active"},
    {"supplier_name": "Nordic Vehicle Parts", "country": "Sweden", "status": "Active"},
    {"supplier_name": "Adriatic Spare Parts", "country": "Croatia", "status": "Active"},
    {"supplier_name": "Benelux Automotive Supply", "country": "Netherlands", "status": "Active"},
    {"supplier_name": "Iberia Parts Network", "country": "Spain", "status": "Active"},
    {"supplier_name": "Alpine Mobility Parts", "country": "Austria", "status": "Active"},
    {"supplier_name": "Rhine Automotive Wholesale", "country": "Germany", "status": "Active"},
    {"supplier_name": "Vistula Components", "country": "Poland", "status": "Active"},
    {"supplier_name": "Balkan Auto Logistics", "country": "Bulgaria", "status": "Active"},
    {"supplier_name": "Eastgate Parts Import", "country": "Czechia", "status": "Active"},
    {"supplier_name": "Danube Industrial Supply", "country": "Hungary", "status": "Active"},
    {"supplier_name": "Global Battery Supply", "country": "Germany", "status": "Active"},
    {"supplier_name": "Fleet Service Components", "country": "Poland", "status": "Active"},
    {"supplier_name": "Premium Brake Systems", "country": "Italy", "status": "Active"},
    {"supplier_name": "Engine and Filtration Wholesale", "country": "Germany", "status": "Active"},
    {"supplier_name": "Universal Technical Supplies", "country": "Ukraine", "status": "Active"},
]

PRODUCT_STATUSES = [
    {"status_name": "Active"},
    {"status_name": "Discontinued"},
    {"status_name": "Temporarily Unavailable"},
    {"status_name": "Preorder"},
]

SALES_CHANNELS = [
    {"channel_name": "Sales Representative"},
    {"channel_name": "B2B Portal"},
    {"channel_name": "E-commerce"},
    {"channel_name": "Phone Order"},
    {"channel_name": "Email Order"},
]

ORDER_STATUSES = [
    {"status_name": "Completed"},
    {"status_name": "Processing"},
    {"status_name": "Cancelled"},
    {"status_name": "On Hold"},
    {"status_name": "Partially Fulfilled"},
]

RETURN_REASONS = [
    {"reason_name": "Defective Product"},
    {"reason_name": "Incorrect Item Supplied"},
    {"reason_name": "Incorrect Item Ordered"},
    {"reason_name": "Damaged During Delivery"},
    {"reason_name": "Customer Changed Mind"},
    {"reason_name": "Warranty Claim"},
    {"reason_name": "Compatibility Issue"},
    {"reason_name": "Duplicate Order"},
]
