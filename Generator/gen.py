import pandas as pd
import random
from datetime import datetime, timedelta
import numpy as np

# total rows required
total_rows = 5000
duplicates_needed = 473
rows = total_rows - duplicates_needed # 4527 original rows


# -------- messy timestamp generator --------
def messy_timestamp(dt):

    formats = [
        "%Y/%m/%d %H:%M",
        "%Y-%m-%d %H:%M",
        "%d-%m-%Y %H:%M",
        "%m/%d/%Y %H:%M",
        "%Y-%m-%dT%H:%M"
    ]

    ts = dt.strftime(random.choice(formats))

    if random.random() < 0.15:
        hour = dt.hour
        minute = random.randint(60,79)
        ts = f"{dt.year}/{dt.month}/{dt.day} {hour}:{minute}"

    return ts


# -------- generate customers --------

num_customers = 2000
customers = [f"CUST-{i:04d}" for i in range(1, num_customers+1)]


# -------- generate vehicle ids --------

vehicle_ids = []

for i in range(1,601):

    base = f"CAR-{i:03d}"

    messy_versions = [
        base,
        base.lower(),
        f" {base} ",
        base.replace("-", "_"),
        base.replace("-", ""),
        base.replace("-", " "),
        base + " ",
        base.lower().replace("-", "")
    ]

    vehicle_ids.append(random.choice(messy_versions))

vehicle_ids.append("UNKNOWN")


# -------- messy values --------

vehicle_classes = ["SUV","Sedan","Hatchback","Luxury", "EV", "Toyota", "Suzuki", "Creta"]

cities = [
    "Bengaluru","blr","BLR","bangalore",
    "Mumbai","mumbai","MUM","Bombay",
    "Delhi","delhi","DELHI","New Delhi",
    "Chennai","CHN","chennai","N/A","unknown"
]

payments = [
    "upi","UPI","card","CARD","cash","CASH","wallet",
    "Wallet","upi "," card","Credit Card","Debit Card",
    "netbanking","-",None
]

rates = [
    "₹1500/day","1500/day","1500 per day","₹1,800/day",
    "$20/day","Rs1500/day","₹ 2000 / day","2000/day",
    "₹2500 per day","1800 perday","USD 25/day",None
]

fuel_levels = [
    "50%","0.5","75%","1.0","25%","0.25","100%","50",
    "75","0.75","30%","0.30","10%","0.10","NA",None
]

promo_codes = ["NEW10","DISC20","SAVE50","WELCOME5",None]

damage_flags = ["None","Minor","Major"]

booking_statuses = ["Completed","Cancelled","No_Show"]

notes = [
    "Customer reported minor scratch on door",
    "Vehicle returned late due to traffic",
    "Interior cleaning required",
    "Customer satisfied with ride",
    "Low fuel warning observed",
    "Tyre pressure alert during trip",
    "Navigation system malfunction reported",
    "Customer requested early pickup",
    "Car returned in good condition",
    "AC performance slightly low",
    None,
    ""
]


# CHANGE 1: base_date changed from 2026 to 2025
base_date = datetime(2025,1,1)

data = []


# -------- constraint tracking --------

customer_time_set = set()
vehicle_time_set = set()

customer_license = {}
used_licenses = set()

# CHANGE 2: pre-assign a fixed Vehicle_Class per Vehicle_ID for consistency
vehicle_class_map = {v: random.choice(vehicle_classes) for v in vehicle_ids}


for i in range(rows):

    res_id = f"RES-{i+1:05d}"

    customer = random.choice(customers)
    vehicle = random.choice(vehicle_ids)

    # CHANGE 2 (continued): look up fixed class instead of random pick each row
    vehicle_class = vehicle_class_map[vehicle]
    booking_status = random.choice(booking_statuses)

    # ensure booking constraints
    while True:

        pickup = base_date + timedelta(
            days=random.randint(0,180),
            hours=random.randint(0,23),
            minutes=random.randint(0,59)
        )

        booking = pickup - timedelta(days=random.randint(1,10))

        duration = random.randint(-5,72)

        return_time = pickup + timedelta(hours=duration)

        customer_key = (customer, pickup, return_time)
        vehicle_key = (vehicle, pickup, return_time)

        if customer_key not in customer_time_set and vehicle_key not in vehicle_time_set and booking < return_time:

            customer_time_set.add(customer_key)
            vehicle_time_set.add(vehicle_key)

            break


    booking_ts = messy_timestamp(booking)
    pickup_ts = messy_timestamp(pickup)
    return_ts = messy_timestamp(return_time)


    odo_start = random.randint(10000,80000)
    distance = random.randint(-100,500)

    odo_end = odo_start + distance

    odo_start_dirty = random.choice([
        f"{odo_start} km",
        f"{odo_start:,}",
        str(odo_start)
    ])

    odo_end_dirty = random.choice([
        f"{odo_end}km",
        f"{odo_end:,}",
        str(odo_end)
    ])


    fuel = random.choice(fuel_levels)
    rate = random.choice(rates)
    city = random.choice(cities)
    payment = random.choice(payments)
    promo = random.choice(promo_codes)


    # unique license per customer
    if customer not in customer_license:

        while True:

            license_no = f"DL-{random.randint(1000000000,9999999999)}"

            if license_no not in used_licenses:

                used_licenses.add(license_no)
                customer_license[customer] = license_no
                break

    license_no = customer_license[customer]


    gps_lat = 12.9 + random.uniform(-0.05,0.05)
    gps_lon = 77.6 + random.uniform(-0.05,0.05)

    speed = random.choice([
        random.randint(20,140),
        f"{random.randint(20,140)} km/h",
        f"{random.randint(20,140)}kmh",
        "fast",
        None
    ])

    damage = random.choice(damage_flags)

    note = random.choice(notes)


    data.append([
        res_id,
        customer,
        vehicle,
        vehicle_class,
        booking_status,
        booking_ts,
        pickup_ts,
        return_ts,
        odo_start_dirty,
        odo_end_dirty,
        fuel,
        rate,
        promo,
        city,
        gps_lat,
        gps_lon,
        speed,
        payment,
        license_no,
        damage,
        note
    ])


columns = [
"Reservation_ID",
"Customer_ID",
"Vehicle_ID",
"Vehicle_Class",
"Booking_Status",
"Booking_TS",
"Pickup_TS",
"Return_TS",
"Odo_Start",
"Odo_End",
"Fuel_Level",
"Rate",
"Promo_Code",
"City",
"GPS_Lat",
"GPS_Lon",
"Speed",
"Payment",
"Driver_License",
"Damage_Flag",
"Notes"
]


df = pd.DataFrame(data, columns=columns)


# -------- add EXACT duplicates --------
duplicates = df.sample(duplicates_needed)

df = pd.concat([df, duplicates], ignore_index=True)


df.to_csv("car_rental_dirty_dataset_new1.csv", index=False)

print("Original rows:", rows)
print("Duplicates added:", duplicates_needed)
print("Total rows:", len(df))