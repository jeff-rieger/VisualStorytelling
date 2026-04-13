#!/usr/bin/env python3
"""
generate_accounts.py
Generates mock Accounts data for the Opportunity Field History case study.
Run from the case-studies/opportunity-field-history/ directory.
Output: data/raw/accounts.csv
"""

import csv
import os
import random

random.seed(42)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "data", "raw", "accounts.csv")

# ── Company names by industry ─────────────────────────────────────────────────

HEALTHCARE = [
    "Northstar Health System", "Meridian Medical Center", "Cascade Regional Hospital",
    "Pinnacle Healthcare Group", "Summit Health Network", "Lakeview Medical Partners",
    "BlueCrest Health System", "Harborview Medical Center", "Riverside Community Hospital",
    "Greenfield Health Partners", "Apex Medical Associates", "Cornerstone Health Network",
    "Paramount Health System", "Ironwood Medical Center", "Cedar Valley Hospital",
    "Sycamore Health Group", "Coastal Medical Alliance", "Ridgemont Healthcare",
    "Clearwater Health System", "Oakwood Medical Center", "Highpoint Health Partners",
    "Millbrook Medical Group", "Silverstone Health Network", "Elmwood Regional Medical Center",
    "Bridgewater Health System", "Falcon Medical Associates", "Stonegate Healthcare",
    "Horizon Health Alliance", "Keystone Medical Center", "Sunridge Health System",
]

GOVERNMENT = [
    "City of Phoenix General Services", "Harris County Administration",
    "Ohio Department of Health", "City of Denver Public Works",
    "Maricopa County Government", "Virginia Department of IT",
    "City of Seattle Finance", "Cook County Administration",
    "Georgia Department of Revenue", "City of Charlotte Planning",
    "Hillsborough County Government", "Minnesota Health Services",
    "City of Columbus Administration", "Los Angeles County Services",
    "Colorado Department of Transportation", "City of Nashville Public Safety",
    "King County Government", "Wisconsin Department of Education",
    "City of Indianapolis Administration", "Allegheny County Services",
    "Arizona Department of Transportation", "City of Jacksonville Finance",
    "Sacramento County Administration", "Tennessee Department of Health",
    "City of Austin Smart City Initiative",
]

RETAIL = [
    "Harborside Retail Group", "Crestwood Department Stores", "Frontier Grocery Co.",
    "Silverline Home Goods", "Maple Street Market", "Keystone Apparel Group",
    "Summit Outdoor Retailers", "Lakewood Consumer Electronics", "Ridgeline Sporting Goods",
    "Coastal Home Furnishings", "Prairie Home Centers", "Irongate Office Supplies",
    "Blue Ridge Grocery Chain", "Cornerstone Pharmacy Group", "Millstone Department Stores",
    "Highfield Consumer Goods", "Clearfield Auto Parts", "Goldstone Jewelry Retail",
    "Westbrook Flooring & Design", "Northgate Supermarkets", "Cedar Point Convenience Stores",
    "Skyline Electronics", "Broadleaf Book & Media", "Redwood Specialty Foods",
    "Sunstone Pet Supplies",
]

CUSTOMER_SERVICE = [
    "Apex Contact Solutions", "Meridian Customer Care", "Nexus Support Services",
    "Pinnacle BPO Group", "Clearbridge Service Centers", "Vantage Customer Solutions",
    "Horizon Contact Group", "Streamline Support Inc.", "Crestview Service Partners",
    "Summit BPO Alliance", "Bridgepoint Customer Care", "Keystone Contact Services",
    "Ironwood Support Group", "Northstar Service Solutions", "Lakewood Contact Center",
    "Ridgemont BPO Services", "Coastal Support Group", "Silvercreek Customer Services",
    "Prairie Contact Solutions", "Westfield Service Alliance",
]

# ── Address pools by industry type ────────────────────────────────────────────
# (street, city, state, zip, latitude, longitude)

HEALTHCARE_ADDRESSES = [
    ("550 First Ave",                    "New York",       "NY", "10016",  40.7419, -73.9744),
    ("300 Longwood Ave",                 "Boston",         "MA", "02115",  42.3372, -71.1065),
    ("2200 W Harrison St",               "Chicago",        "IL", "60612",  41.8739, -87.6826),
    ("9500 Euclid Ave",                  "Cleveland",      "OH", "44195",  41.5021, -81.6208),
    ("3601 4th Ave S",                   "Minneapolis",    "MN", "55409",  44.9261, -93.2654),
    ("701 W Bayshore Blvd",              "Tampa",          "FL", "33606",  27.9297, -82.4637),
    ("4150 Regent Blvd",                 "Irving",         "TX", "75038",  32.8704, -97.0105),
    ("3300 Gallows Rd",                  "Falls Church",   "VA", "22042",  38.8756, -77.1897),
    ("1 Medical Center Blvd",            "Winston-Salem",  "NC", "27157",  36.1346, -80.3413),
    ("1800 Harrison St",                 "Oakland",        "CA", "94612",  37.8044, -122.2712),
    ("2100 Harrisburg Pike",             "Columbus",       "OH", "43223",  39.9490, -83.0708),
    ("475 University Ave",               "Sacramento",     "CA", "95825",  38.5702, -121.4143),
    ("1 Hospital Dr",                    "Columbia",       "MO", "65212",  38.9404,  -92.3279),
    ("3841 Roger Brooke Dr",             "San Antonio",    "TX", "78234",  29.4941,  -98.4369),
    ("1600 N Capitol St NW",             "Washington",     "DC", "20001",  38.9027,  -77.0085),
    ("2000 Lakeshore Dr",                "New Orleans",    "LA", "70112",  29.9793,  -90.0925),
    ("1515 Holcombe Blvd",               "Houston",        "TX", "77030",  29.7072,  -95.3979),
    ("3710 SW US Veterans Hospital Rd",  "Portland",       "OR", "97239",  45.4977, -122.6854),
    ("500 University Dr",                "Hershey",        "PA", "17033",  40.2771,  -76.6465),
    ("1 Barnes Jewish Hospital Plaza",   "St. Louis",      "MO", "63110",  38.6351,  -90.2634),
    ("2222 Philadelphia Dr",             "Dayton",         "OH", "45406",  39.7762,  -84.2285),
    ("100 N Academy Ave",                "Danville",       "PA", "17822",  40.9654,  -76.6124),
    ("4000 Losantiville Ave",            "Cincinnati",     "OH", "45236",  39.2116,  -84.4249),
    ("100 Medical Center Blvd",          "Conroe",         "TX", "77304",  30.3321,  -95.4897),
    ("111 Michigan Ave NW",              "Washington",     "DC", "20010",  38.9303,  -77.0308),
    ("600 Hugh Wallis Rd S",             "Lafayette",      "LA", "70508",  30.1711,  -92.0534),
    ("10 Brookline Pl W",                "Brookline",      "MA", "02445",  42.3317,  -71.1218),
    ("750 Washington St",                "Boston",         "MA", "02111",  42.3494,  -71.0641),
    ("5323 Harry Hines Blvd",            "Dallas",         "TX", "75390",  32.8131,  -96.8416),
    ("2051 W Martin Luther King Jr Blvd","Los Angeles",    "CA", "90062",  34.0102, -118.3072),
]

GOVERNMENT_ADDRESSES = [
    ("200 W Washington St",     "Phoenix",       "AZ", "85003",  33.4484, -112.0740),
    ("1001 Preston St",         "Houston",       "TX", "77002",  29.7599,  -95.3677),
    ("246 N High St",           "Columbus",      "OH", "43215",  39.9612,  -82.9988),
    ("1437 Bannock St",         "Denver",        "CO", "80202",  39.7392, -104.9903),
    ("301 W Jefferson St",      "Phoenix",       "AZ", "85003",  33.4500, -112.0745),
    ("1100 E Main St",          "Richmond",      "VA", "23219",  37.5407,  -77.4360),
    ("600 4th Ave",             "Seattle",       "WA", "98104",  47.6062, -122.3321),
    ("69 W Washington St",      "Chicago",       "IL", "60602",  41.8827,  -87.6298),
    ("200 Piedmont Ave SE",     "Atlanta",       "GA", "30334",  33.7490,  -84.3880),
    ("600 E 4th St",            "Charlotte",     "NC", "28202",  35.2271,  -80.8431),
    ("601 E Kennedy Blvd",      "Tampa",         "FL", "33602",  27.9506,  -82.4572),
    ("658 Cedar St",            "St. Paul",      "MN", "55155",  44.9537,  -93.0900),
    ("90 W Broad St",           "Columbus",      "OH", "43215",  39.9580,  -83.0010),
    ("500 W Temple St",         "Los Angeles",   "CA", "90012",  34.0522, -118.2437),
    ("4201 E Arkansas Ave",     "Denver",        "CO", "80222",  39.6775, -104.9394),
    ("1 Public Square",         "Nashville",     "TN", "37201",  36.1627,  -86.7816),
    ("516 3rd Ave",             "Seattle",       "WA", "98104",  47.6080, -122.3330),
    ("201 W Washington Ave",    "Madison",       "WI", "53703",  43.0731,  -89.4012),
    ("200 E Washington St",     "Indianapolis",  "IN", "46204",  39.7684,  -86.1581),
    ("436 Grant St",            "Pittsburgh",    "PA", "15219",  40.4406,  -79.9959),
    ("1801 W Jefferson St",     "Phoenix",       "AZ", "85007",  33.4440, -112.0900),
    ("117 W Duval St",          "Jacksonville",  "FL", "32202",  30.3322,  -81.6557),
    ("700 H St",                "Sacramento",    "CA", "95814",  38.5816, -121.4944),
    ("312 Rosa Parks Ave",      "Nashville",     "TN", "37243",  36.1660,  -86.7840),
    ("301 W 2nd St",            "Austin",        "TX", "78701",  30.2672,  -97.7431),
]

RETAIL_ADDRESSES = [
    ("1 Walmart Way",              "Bentonville",      "AR", "72712",  36.3729,  -94.2088),
    ("2100 McKinney Ave",          "Dallas",           "TX", "75201",  32.8007,  -96.8001),
    ("701 5th Ave",                "New York",         "NY", "10022",  40.7614,  -73.9776),
    ("500 Westlake Ave N",         "Seattle",          "WA", "98109",  47.6283, -122.3417),
    ("1020 N Main St",             "Ann Arbor",        "MI", "48104",  42.2808,  -83.7430),
    ("3030 LBJ Freeway",           "Dallas",           "TX", "75234",  32.9191,  -96.8985),
    ("1000 Corporate Dr",          "Canonsburg",       "PA", "15317",  40.2615,  -80.1876),
    ("200 S Biscayne Blvd",        "Miami",            "FL", "33131",  25.7617,  -80.1918),
    ("800 N Glebe Rd",             "Arlington",        "VA", "22203",  38.8816,  -77.1000),
    ("4100 Chapel Hill Blvd",      "Durham",           "NC", "27707",  35.9940,  -78.9000),
    ("3800 Golf Rd",               "Rolling Meadows",  "IL", "60008",  42.0750,  -88.0162),
    ("11 Harbor Park Dr",          "Port Washington",  "NY", "11050",  40.8257,  -73.6985),
    ("1600 Chamberlain Ave",       "Charlottesville",  "VA", "22903",  38.0293,  -78.4767),
    ("100 SE Main St",             "Portland",         "OR", "97214",  45.5051, -122.6750),
    ("2200 Mission College Blvd",  "Santa Clara",      "CA", "95054",  37.3875, -121.9693),
    ("4000 Meridian Blvd",         "Franklin",         "TN", "37067",  35.9251,  -86.8689),
    ("1 AutoZone Park",            "Memphis",          "TN", "38103",  35.1495,  -90.0490),
    ("1000 Abernathy Rd NE",       "Atlanta",          "GA", "30328",  33.9304,  -84.3733),
    ("7000 Target Pkwy N",         "Brooklyn Park",    "MN", "55445",  45.0941,  -93.3669),
    ("2001 S 1st St",              "Austin",           "TX", "78704",  30.2500,  -97.7500),
    ("1200 Eastport Plaza Dr",     "Collinsville",     "IL", "62234",  38.6705,  -89.9845),
    ("500 Commerce St",            "Dallas",           "TX", "75202",  32.7767,  -96.7970),
    ("100 Phoenix Dr",             "Warren",           "NJ", "07059",  40.6295,  -74.5046),
    ("8500 Freeport Pkwy",         "Irving",           "TX", "75063",  32.8750,  -97.0150),
    ("1805 Old Alabama Rd",        "Roswell",          "GA", "30076",  34.0232,  -84.3616),
]

CUSTOMER_SERVICE_ADDRESSES = [
    ("3000 Kellway Dr",          "Carrollton",    "TX", "75006",  32.9537,  -96.8903),
    ("100 Centerview Dr",        "Brentwood",     "TN", "37027",  36.0331,  -86.7828),
    ("2200 W Airfield Dr",       "DFW Airport",   "TX", "75261",  32.8998,  -97.0403),
    ("6200 Sprint Pkwy",         "Overland Park", "KS", "66251",  38.8814,  -94.7197),
    ("1300 I St NW",             "Washington",    "DC", "20005",  38.9027,  -77.0085),
    ("100 Winners Circle",       "Brentwood",     "TN", "37027",  36.0340,  -86.7835),
    ("5000 T-Rex Ave",           "Boca Raton",    "FL", "33431",  26.3683,  -80.1289),
    ("3800 Howard Hughes Pkwy",  "Las Vegas",     "NV", "89169",  36.1699, -115.1398),
    ("1 Allied Dr",              "Little Rock",   "AR", "72202",  34.7465,  -92.2896),
    ("6800 Cintas Blvd",         "Mason",         "OH", "45040",  39.3601,  -84.3097),
    ("300 E John Carpenter Fwy", "Irving",        "TX", "75062",  32.8140,  -96.9489),
    ("1100 Reynolds Blvd",       "Winston-Salem", "NC", "27105",  36.1046,  -80.2441),
    ("5601 Broadmoor St",        "Mission",       "KS", "66202",  39.0278,  -94.6558),
    ("One Convergys Way",        "Cincinnati",    "OH", "45201",  39.1031,  -84.5120),
    ("800 N Frederick Ave",      "Gaithersburg",  "MD", "20879",  39.1434,  -77.2014),
    ("2511 Garden Rd",           "Monterey",      "CA", "93940",  36.6002, -121.8947),
    ("100 Granton Dr",           "Richmond Hill", "GA", "31324",  31.9246,  -81.2951),
    ("4600 Fuller Dr",           "Irving",        "TX", "75038",  32.8704,  -97.0200),
    ("600 17th St",              "Denver",        "CO", "80202",  39.7392, -104.9903),
    ("1 Gateway Center",         "Pittsburgh",    "PA", "15222",  40.4406,  -79.9959),
]

ADDRESS_POOLS = {
    "Healthcare":       HEALTHCARE_ADDRESSES,
    "Government":       GOVERNMENT_ADDRESSES,
    "Retail":           RETAIL_ADDRESSES,
    "Customer Service": CUSTOMER_SERVICE_ADDRESSES,
}

def unpack_addr(addr):
    return {"street_address": addr[0], "city": addr[1], "state": addr[2],
            "zip_code": addr[3], "latitude": addr[4], "longitude": addr[5]}

# ── Revenue / employee ranges ─────────────────────────────────────────────────

REVENUE_RANGES = {
    "Healthcare":       (50_000_000,   5_000_000_000),
    "Government":       (10_000_000,     500_000_000),
    "Retail":           (20_000_000,  10_000_000_000),
    "Customer Service": ( 5_000_000,     500_000_000),
}

EMPLOYEE_RANGES = {
    "Healthcare":       (500,   50_000),
    "Government":       (100,   20_000),
    "Retail":           (200,  100_000),
    "Customer Service": (100,   10_000),
}

CHILD_SUFFIXES = [
    "Northeast Division", "Southeast Region", "Midwest Operations",
    "Western Region", "Gulf Coast Branch", "Pacific Division",
    "Mountain Region", "Great Plains Branch", "Atlantic Division",
    "Central Region", "Southwest District", "Upper Midwest Branch",
]

# ── Subcategory lookup ────────────────────────────────────────────────────────

# Retail: exact base-name → subcategory
RETAIL_SUBCATEGORIES = {
    "Blue Ridge Grocery Chain":       "Grocery",
    "Broadleaf Book & Media":         "Books & Media",
    "Cedar Point Convenience Stores": "Convenience Store",
    "Clearfield Auto Parts":          "Automotive Parts",
    "Coastal Home Furnishings":       "Home Furnishings",
    "Cornerstone Pharmacy Group":     "Pharmacy",
    "Crestwood Department Stores":    "Department Store",
    "Frontier Grocery Co.":           "Grocery",
    "Goldstone Jewelry Retail":       "Jewelry",
    "Harborside Retail Group":        "General Retail",
    "Highfield Consumer Goods":       "General Retail",
    "Irongate Office Supplies":       "Office Supplies",
    "Keystone Apparel Group":         "Apparel",
    "Lakewood Consumer Electronics":  "Electronics",
    "Maple Street Market":            "Grocery",
    "Millstone Department Stores":    "Department Store",
    "Northgate Supermarkets":         "Grocery",
    "Prairie Home Centers":           "Home Improvement",
    "Redwood Specialty Foods":        "Specialty Foods",
    "Ridgeline Sporting Goods":       "Sporting Goods",
    "Silverline Home Goods":          "Home Goods",
    "Skyline Electronics":            "Electronics",
    "Summit Outdoor Retailers":       "Outdoor & Sporting",
    "Sunstone Pet Supplies":          "Pet Supplies",
    "Westbrook Flooring & Design":    "Flooring & Design",
}


def _healthcare_subcat(name: str) -> str:
    if "Health System"        in name: return "Health System"
    if "Regional Medical"     in name: return "Medical Center"
    if "Medical Center"       in name: return "Medical Center"
    if "Community Hospital"   in name: return "Community Hospital"
    if "Regional Hospital"    in name: return "Regional Hospital"
    if "Hospital"             in name: return "Hospital"
    if "Health Network"       in name: return "Health Network"
    if "Health Partners"      in name: return "Health Partners"
    if "Health Group"         in name: return "Health Group"
    if "Health Alliance"      in name: return "Health Alliance"
    if "Medical Alliance"     in name: return "Health Alliance"
    if "Medical Group"        in name: return "Medical Group"
    if "Medical Partners"     in name: return "Medical Group"
    if "Medical Associates"   in name: return "Medical Associates"
    if "Healthcare"           in name: return "Healthcare Group"
    return "Healthcare"


def _government_subcat(name: str) -> str:
    if name.startswith("City of"):               return "City Government"
    if "County" in name:                         return "County Government"
    if "Department of Transportation" in name:   return "State Transportation"
    if "Department of Revenue" in name:          return "State Revenue"
    if "Department of Health" in name:           return "State Health"
    if "Department of IT" in name:               return "State Technology"
    if "Department of Education" in name:        return "State Education"
    if "Health Services" in name:                return "State Health"
    return "State Government"


def _customer_service_subcat(name: str) -> str:
    if "BPO" in name:                            return "Business Process Outsourcing"
    if "Contact" in name:                        return "Contact Center"
    if "Customer Care" in name:                  return "Customer Care"
    if "Customer Solutions" in name:             return "Customer Care"
    if "Customer Services" in name:              return "Customer Care"
    if "Support" in name:                        return "Technical Support"
    if "Service" in name:                        return "Service Operations"
    return "Customer Service"


def get_subcategory(name: str, industry: str) -> str:
    """Return the subcategory for an account, stripping child suffixes first."""
    base = name.split(" - ")[0]          # strip "- Northeast Division" etc.
    if industry == "Retail":
        return RETAIL_SUBCATEGORIES.get(base, "General Retail")
    if industry == "Healthcare":
        return _healthcare_subcat(base)
    if industry == "Government":
        return _government_subcat(base)
    if industry == "Customer Service":
        return _customer_service_subcat(base)
    return industry


def rand_revenue(industry):
    lo, hi = REVENUE_RANGES[industry]
    lo_m, hi_m = lo // 1_000_000, hi // 1_000_000
    return random.randint(lo_m, hi_m) * 1_000_000


def rand_employees(industry):
    lo, hi = EMPLOYEE_RANGES[industry]
    return random.randint(lo, hi)


def pick_address(industry, exclude=None):
    pool = [a for a in ADDRESS_POOLS[industry] if a != exclude]
    return random.choice(pool)


# ── Build all accounts ────────────────────────────────────────────────────────

def build_accounts():
    all_accounts = []
    counter = 1

    industry_map = [
        ("Healthcare",       HEALTHCARE),
        ("Government",       GOVERNMENT),
        ("Retail",           RETAIL),
        ("Customer Service", CUSTOMER_SERVICE),
    ]

    # --- Main accounts ---
    for industry, names in industry_map:
        addr_pool = ADDRESS_POOLS[industry][:]
        random.shuffle(addr_pool)
        for i, name in enumerate(names):
            addr = addr_pool[i % len(addr_pool)]
            all_accounts.append({
                "account_id":           f"ACC-{counter:04d}",
                "account_name":         name,
                "industry":             industry,
                "subcategory":          get_subcategory(name, industry),
                "annual_revenue":       rand_revenue(industry),
                "number_of_employees":  rand_employees(industry),
                "parent_account_id":    "",
                **unpack_addr(addr),
                "_is_parent":           False,  # internal only
            })
            counter += 1

    # --- Designate ~30% of each industry group as parents ---
    main_accounts = all_accounts[:]
    by_industry = {}
    for a in main_accounts:
        by_industry.setdefault(a["industry"], []).append(a)

    for industry, group in by_industry.items():
        n_parents = max(1, round(len(group) * 0.30))
        for chosen in random.sample(group, n_parents):
            chosen["_is_parent"] = True

    # --- Create child accounts ---
    children = []
    for a in main_accounts:
        if not a["_is_parent"]:
            continue
        n_children = random.randint(1, 3)
        suffixes = random.sample(CHILD_SUFFIXES, n_children)
        parent_addr = (a["street_address"], a["city"], a["state"], a["zip_code"])
        for suffix in suffixes:
            addr = pick_address(a["industry"], exclude=parent_addr)
            child_rev = round(a["annual_revenue"] * random.uniform(0.05, 0.30) / 1_000_000) * 1_000_000
            child_emp = max(25, round(a["number_of_employees"] * random.uniform(0.05, 0.25)))
            child_name = f"{a['account_name']} - {suffix}"
            children.append({
                "account_id":           f"ACC-{counter:04d}",
                "account_name":         child_name,
                "industry":             a["industry"],
                "subcategory":          get_subcategory(child_name, a["industry"]),
                "annual_revenue":       child_rev,
                "number_of_employees":  child_emp,
                "parent_account_id":    a["account_id"],
                **unpack_addr(addr),
                "_is_parent":           False,
            })
            counter += 1

    all_accounts.extend(children)

    # Strip internal flag
    for a in all_accounts:
        del a["_is_parent"]

    return all_accounts, len(main_accounts), len(children)


def main():
    accounts, n_main, n_children = build_accounts()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    fieldnames = [
        "account_id", "account_name", "industry", "subcategory",
        "annual_revenue", "number_of_employees", "parent_account_id",
        "street_address", "city", "state", "zip_code",
        "latitude", "longitude",
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(accounts)

    n_parents = sum(
        1 for a in accounts
        if not a["parent_account_id"]
        and any(c["parent_account_id"] == a["account_id"] for c in accounts)
    )

    print(f"Accounts written : {len(accounts):>4}")
    print(f"  Main accounts  : {n_main:>4}")
    print(f"  Child accounts : {n_children:>4}")
    print(f"  Parent accounts: {n_parents:>4}  (~{n_parents/n_main*100:.0f}% of main)")
    print(f"Output           : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
