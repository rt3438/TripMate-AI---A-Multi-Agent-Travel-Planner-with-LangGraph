import os
import re
import unicodedata
from typing import Optional

import certifi
import airportsdata
import pycountry
import requests
from dotenv import load_dotenv


load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")

# Default origin when the user mentions only a destination.
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "DFW").upper().strip()

BASE_URL = "https://api.aviationstack.com/v1/flights"

AIRPORTS = airportsdata.load("IATA")


COUNTRY_ALIASES = {
    # United States
    "usa": "US",
    "us": "US",
    "u.s.": "US",
    "u.s.a.": "US",
    "united states": "US",
    "united states of america": "US",
    "america": "US",

    # Canada
    "canada": "CA",
    "ca": "CA",

    # Mexico
    "mexico": "MX",
    "mx": "MX",

    # United Kingdom
    "uk": "GB",
    "u.k.": "GB",
    "united kingdom": "GB",
    "great britain": "GB",
    "britain": "GB",
    "gb": "GB",

    # Ireland
    "ireland": "IE",
    "republic of ireland": "IE",
    "ie": "IE",

    # France
    "france": "FR",
    "fr": "FR",

    # Germany
    "germany": "DE",
    "de": "DE",
    "deutschland": "DE",

    # Spain
    "spain": "ES",
    "es": "ES",
    "españa": "ES",

    # Portugal
    "portugal": "PT",
    "pt": "PT",

    # Italy
    "italy": "IT",
    "it": "IT",
    "italia": "IT",

    # Netherlands
    "netherlands": "NL",
    "the netherlands": "NL",
    "holland": "NL",
    "nl": "NL",

    # Belgium
    "belgium": "BE",
    "be": "BE",

    # Switzerland
    "switzerland": "CH",
    "ch": "CH",

    # Austria
    "austria": "AT",
    "at": "AT",

    # Sweden
    "sweden": "SE",
    "se": "SE",

    # Norway
    "norway": "NO",
    "no": "NO",

    # Denmark
    "denmark": "DK",
    "dk": "DK",

    # Finland
    "finland": "FI",
    "fi": "FI",

    # Iceland
    "iceland": "IS",
    "is": "IS",

    # Poland
    "poland": "PL",
    "pl": "PL",

    # Czechia
    "czechia": "CZ",
    "czech republic": "CZ",
    "cz": "CZ",

    # Slovakia
    "slovakia": "SK",
    "sk": "SK",

    # Hungary
    "hungary": "HU",
    "hu": "HU",

    # Romania
    "romania": "RO",
    "ro": "RO",

    # Bulgaria
    "bulgaria": "BG",
    "bg": "BG",

    # Greece
    "greece": "GR",
    "gr": "GR",

    # Turkey
    "turkey": "TR",
    "türkiye": "TR",
    "turkiye": "TR",
    "tr": "TR",

    # Ukraine
    "ukraine": "UA",
    "ua": "UA",

    # Russia
    "russia": "RU",
    "russian federation": "RU",
    "ru": "RU",

    # China
    "china": "CN",
    "prc": "CN",
    "people's republic of china": "CN",
    "peoples republic of china": "CN",
    "cn": "CN",

    # Japan
    "japan": "JP",
    "jp": "JP",

    # South Korea
    "south korea": "KR",
    "korea": "KR",
    "republic of korea": "KR",
    "kr": "KR",

    # North Korea
    "north korea": "KP",
    "dprk": "KP",
    "kp": "KP",

    # India
    "india": "IN",
    "in": "IN",

    # Pakistan
    "pakistan": "PK",
    "pk": "PK",

    # Bangladesh
    "bangladesh": "BD",
    "bd": "BD",

    # Sri Lanka
    "sri lanka": "LK",
    "lk": "LK",

    # Nepal
    "nepal": "NP",
    "np": "NP",

    # Singapore
    "singapore": "SG",
    "sg": "SG",

    # Malaysia
    "malaysia": "MY",
    "my": "MY",

    # Indonesia
    "indonesia": "ID",
    "id": "ID",

    # Philippines
    "philippines": "PH",
    "the philippines": "PH",
    "ph": "PH",

    # Thailand
    "thailand": "TH",
    "th": "TH",

    # Vietnam
    "vietnam": "VN",
    "viet nam": "VN",
    "vn": "VN",

    # Australia
    "australia": "AU",
    "aussie": "AU",
    "au": "AU",

    # New Zealand
    "new zealand": "NZ",
    "nz": "NZ",

    # Brazil
    "brazil": "BR",
    "brasil": "BR",
    "br": "BR",

    # Argentina
    "argentina": "AR",
    "ar": "AR",

    # Chile
    "chile": "CL",
    "cl": "CL",

    # Colombia
    "colombia": "CO",
    "co": "CO",

    # Peru
    "peru": "PE",
    "pe": "PE",

    # Venezuela
    "venezuela": "VE",
    "ve": "VE",

    # Ecuador
    "ecuador": "EC",
    "ec": "EC",

    # Uruguay
    "uruguay": "UY",
    "uy": "UY",

    # Paraguay
    "paraguay": "PY",
    "py": "PY",

    # Bolivia
    "bolivia": "BO",
    "bo": "BO",

    # South Africa
    "south africa": "ZA",
    "za": "ZA",

    # Egypt
    "egypt": "EG",
    "eg": "EG",

    # Nigeria
    "nigeria": "NG",
    "ng": "NG",

    # Kenya
    "kenya": "KE",
    "ke": "KE",

    # Ethiopia
    "ethiopia": "ET",
    "et": "ET",

    # Ghana
    "ghana": "GH",
    "gh": "GH",

    # Morocco
    "morocco": "MA",
    "ma": "MA",

    # Algeria
    "algeria": "DZ",
    "dz": "DZ",

    # Tunisia
    "tunisia": "TN",
    "tn": "TN",

    # Saudi Arabia
    "saudi arabia": "SA",
    "saudi": "SA",
    "sa": "SA",

    # United Arab Emirates
    "uae": "AE",
    "u.a.e.": "AE",
    "united arab emirates": "AE",
    "emirates": "AE",
    "ae": "AE",

    # Israel
    "israel": "IL",
    "il": "IL",

    # Jordan
    "jordan": "JO",
    "jo": "JO",

    # Qatar
    "qatar": "QA",
    "qa": "QA",

    # Kuwait
    "kuwait": "KW",
    "kw": "KW",

    # Iraq
    "iraq": "IQ",
    "iq": "IQ",

    # Iran
    "iran": "IR",
    "islamic republic of iran": "IR",
    "ir": "IR",

    # Hong Kong
    "hong kong": "HK",
    "hk": "HK",

    # Taiwan
    "taiwan": "TW",
    "tw": "TW",
}


COUNTRY_MAIN_AIRPORT = {
    "US": "DFW",
    "CA": "YYZ",
    "MX": "MEX",

    "GB": "LHR",
    "IE": "DUB",
    "FR": "CDG",
    "DE": "FRA",
    "ES": "MAD",
    "PT": "LIS",
    "IT": "FCO",
    "NL": "AMS",
    "BE": "BRU",
    "CH": "ZRH",
    "AT": "VIE",
    "SE": "ARN",
    "NO": "OSL",
    "DK": "CPH",
    "FI": "HEL",
    "IS": "KEF",
    "PL": "WAW",
    "CZ": "PRG",
    "SK": "BTS",
    "HU": "BUD",
    "RO": "OTP",
    "BG": "SOF",
    "GR": "ATH",
    "TR": "IST",
    "UA": "KBP",
    "RU": "SVO",

    "CN": "PEK",
    "JP": "HND",
    "KR": "ICN",
    "KP": "FNJ",
    "IN": "DEL",
    "PK": "KHI",
    "BD": "DAC",
    "LK": "CMB",
    "NP": "KTM",
    "SG": "SIN",
    "MY": "KUL",
    "ID": "CGK",
    "PH": "MNL",
    "TH": "BKK",
    "VN": "SGN",
    "HK": "HKG",
    "TW": "TPE",

    "AU": "SYD",
    "NZ": "AKL",

    "BR": "GRU",
    "AR": "EZE",
    "CL": "SCL",
    "CO": "BOG",
    "PE": "LIM",
    "VE": "CCS",
    "EC": "UIO",
    "UY": "MVD",
    "PY": "ASU",
    "BO": "VVI",

    "ZA": "JNB",
    "EG": "CAI",
    "NG": "LOS",
    "KE": "NBO",
    "ET": "ADD",
    "GH": "ACC",
    "MA": "CMN",
    "DZ": "ALG",
    "TN": "TUN",

    "SA": "RUH",
    "AE": "DXB",
    "IL": "TLV",
    "JO": "AMM",
    "QA": "DOH",
    "KW": "KWI",
    "IQ": "BGW",
    "IR": "IKA",

    "AF": "KBL",
    "AM": "EVN",
    "AZ": "GYD",
    "BH": "BAH",
    "GE": "TBS",
    "KZ": "ALA",
    "LB": "BEY",
    "OM": "MCT",
    "UZ": "TAS",

    "CR": "SJO",
    "PA": "PTY",
    "GT": "GUA",
    "SV": "SAL",
    "HN": "SAP",
    "NI": "MGA",
    "BZ": "BZE",

    "DO": "SDQ",
    "JM": "MBJ",
    "BS": "NAS",
    "TT": "POS",
    "CU": "HAV",

    "RS": "BEG",
    "HR": "ZAG",
    "SI": "LJU",
    "BA": "SJJ",
    "ME": "TGD",
    "AL": "TIA",
    "MK": "SKP",

    "LT": "VNO",
    "LV": "RIX",
    "EE": "TLL",

    "LU": "LUX",
    "MT": "MLA",
    "CY": "LCA",

    "SN": "DSS",
    "TZ": "DAR",
    "UG": "EBB",
    "RW": "KGL",
    "CM": "DLA",
    "CI": "ABJ",
    "AO": "LAD",
    "ZW": "HRE",
    "ZM": "LUN",
    "BW": "GBE",
    "NA": "WDH",
    "MZ": "MPM",

    "KH": "PNH",
    "MM": "RGN",
    "LA": "VTE",
    "MN": "UBN",
    "MV": "MLE",
    "BN": "BWN",

    "FJ": "NAN",
    "PG": "POM",

    "GY": "GEO",
    "SR": "PBM"
}


CITY_MAIN_AIRPORT = {
    "Dallas/Fort Worth": "DFW",
    "Toronto": "YYZ",
    "Mexico City": "MEX",

    "London": "LHR",
    "Dublin": "DUB",
    "Paris": "CDG",
    "Frankfurt": "FRA",
    "Madrid": "MAD",
    "Lisbon": "LIS",
    "Rome": "FCO",
    "Amsterdam": "AMS",
    "Brussels": "BRU",
    "Zurich": "ZRH",
    "Vienna": "VIE",
    "Stockholm": "ARN",
    "Oslo": "OSL",
    "Copenhagen": "CPH",
    "Helsinki": "HEL",
    "Reykjavik": "KEF",
    "Warsaw": "WAW",
    "Prague": "PRG",
    "Bratislava": "BTS",
    "Budapest": "BUD",
    "Bucharest": "OTP",
    "Sofia": "SOF",
    "Athens": "ATH",
    "Istanbul": "IST",
    "Kyiv": "KBP",
    "Moscow": "SVO",

    "Beijing": "PEK",
    "Tokyo": "HND",
    "Seoul": "ICN",
    "Pyongyang": "FNJ",
    "Delhi": "DEL",
    "Karachi": "KHI",
    "Dhaka": "DAC",
    "Colombo": "CMB",
    "Kathmandu": "KTM",
    "Singapore": "SIN",
    "Kuala Lumpur": "KUL",
    "Jakarta": "CGK",
    "Manila": "MNL",
    "Bangkok": "BKK",
    "Ho Chi Minh City": "SGN",
    "Hong Kong": "HKG",
    "Taipei": "TPE",

    "Sydney": "SYD",
    "Auckland": "AKL",

    "São Paulo": "GRU",
    "Buenos Aires": "EZE",
    "Santiago": "SCL",
    "Bogotá": "BOG",
    "Lima": "LIM",
    "Caracas": "CCS",
    "Quito": "UIO",
    "Montevideo": "MVD",
    "Asunción": "ASU",
    "Santa Cruz": "VVI",

    "Johannesburg": "JNB",
    "Cairo": "CAI",
    "Lagos": "LOS",
    "Nairobi": "NBO",
    "Addis Ababa": "ADD",
    "Accra": "ACC",
    "Casablanca": "CMN",
    "Algiers": "ALG",
    "Tunis": "TUN",

    "Riyadh": "RUH",
    "Dubai": "DXB",
    "Tel Aviv": "TLV",
    "Amman": "AMM",
    "Doha": "DOH",
    "Kuwait City": "KWI",
    "Baghdad": "BGW",
    "Tehran": "IKA",

    "Kabul": "KBL",
    "Yerevan": "EVN",
    "Baku": "GYD",
    "Manama": "BAH",
    "Tbilisi": "TBS",
    "Almaty": "ALA",
    "Beirut": "BEY",
    "Muscat": "MCT",
    "Tashkent": "TAS",

    "San José": "SJO",
    "Panama City": "PTY",
    "Guatemala City": "GUA",
    "San Salvador": "SAL",
    "San Pedro Sula": "SAP",
    "Managua": "MGA",
    "Belize City": "BZE",

    "Santo Domingo": "SDQ",
    "Montego Bay": "MBJ",
    "Nassau": "NAS",
    "Port of Spain": "POS",
    "Havana": "HAV",

    "Belgrade": "BEG",
    "Zagreb": "ZAG",
    "Ljubljana": "LJU",
    "Sarajevo": "SJJ",
    "Podgorica": "TGD",
    "Tirana": "TIA",
    "Skopje": "SKP",

    "Vilnius": "VNO",
    "Riga": "RIX",
    "Tallinn": "TLL",

    "Luxembourg City": "LUX",
    "Malta": "MLA",
    "Larnaca": "LCA",

    "Dakar": "DSS",
    "Dar es Salaam": "DAR",
    "Entebbe": "EBB",
    "Kigali": "KGL",
    "Douala": "DLA",
    "Abidjan": "ABJ",
    "Luanda": "LAD",
    "Harare": "HRE",
    "Lusaka": "LUN",
    "Gaborone": "GBE",
    "Windhoek": "WDH",
    "Maputo": "MPM",

    "Phnom Penh": "PNH",
    "Yangon": "RGN",
    "Vientiane": "VTE",
    "Ulaanbaatar": "UBN",
    "Malé": "MLE",
    "Bandar Seri Begawan": "BWN",

    "Nadi": "NAN",
    "Port Moresby": "POM",

    "Georgetown": "GEO",
    "Paramaribo": "PBM"
}



# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

TRAVEL_STOP_WORDS = {
    "flight",
    "flights",
    "ticket",
    "tickets",
    "trip",
    "travel",
    "plan",
    "complete",
    "days",
    "day",
    "including",
    "hotel",
    "hotels",
    "sightseeing",
    "budget",
    "info",
    "information",
}


def normalize_text(text: str) -> str:
    """
    Normalize user-entered location text for matching.

    Examples:
        "São Paulo" -> "sao paulo"
        "U.S.A." -> "u s a"
        "  New   York " -> "new york"
    """
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_text(text: str) -> str:
    """
    Normalize text and remove common travel-related filler words.

    This function operates on words, not characters.
    """
    normalized = normalize_text(text)
    words = [
        word
        for word in normalized.split()
        if word not in TRAVEL_STOP_WORDS
    ]
    return " ".join(words).strip()


NORMALIZED_COUNTRY_ALIASES = {
    normalize_text(alias): code
    for alias, code in COUNTRY_ALIASES.items()
}

NORMALIZED_CITY_MAIN_AIRPORT = {
    normalize_text(city): iata
    for city, iata in CITY_MAIN_AIRPORT.items()
}


def _contains_phrase(haystack: str, needle: str) -> bool:
    if not needle:
        return False
    return re.search(
        rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])",
        haystack,
    ) is not None


def _safe_alias_for_sentence(alias: str) -> bool:
    """
    Avoid treating short country-code aliases as ordinary English words.

    Examples of aliases that are unsafe in free text:
        in -> India
        is -> Iceland
        no -> Norway
        at -> Austria
        it -> Italy
        us -> United States

    Those still work when supplied as an exact location value.
    """
    compact = alias.replace(" ", "")
    return len(compact) >= 3


# ---------------------------------------------------------------------------
# Country and airport resolution
# ---------------------------------------------------------------------------

def country_name_to_code(text: str) -> Optional[str]:
    if not text:
        return None

    raw_text = str(text).strip()
    normalized = clean_text(raw_text) or normalize_text(raw_text)

    if not normalized:
        return None

    # Exact ISO alpha-2 code.
    if re.fullmatch(r"[A-Za-z]{2}", raw_text):
        country = pycountry.countries.get(alpha_2=raw_text.upper())
        if country:
            return country.alpha_2

    # Exact custom alias.
    if normalized in NORMALIZED_COUNTRY_ALIASES:
        return NORMALIZED_COUNTRY_ALIASES[normalized]

    # Exact country name / official name / alpha code through pycountry.
    for candidate in (raw_text, normalized):
        try:
            country = pycountry.countries.lookup(candidate)
            return country.alpha_2
        except LookupError:
            pass

    # Detect a full country name inside longer text.
    for country in pycountry.countries:
        possible_names = {
            normalize_text(country.name),
        }

        official_name = getattr(country, "official_name", None)
        common_name = getattr(country, "common_name", None)

        if official_name:
            possible_names.add(normalize_text(official_name))
        if common_name:
            possible_names.add(normalize_text(common_name))

        for country_name in possible_names:
            if country_name and _contains_phrase(normalized, country_name):
                return country.alpha_2

    # Detect only safe aliases inside longer natural-language text.
    for alias, code in NORMALIZED_COUNTRY_ALIASES.items():
        if _safe_alias_for_sentence(alias) and _contains_phrase(normalized, alias):
            return code

    return None


def airport_country_matches(airport: dict, country_code: str) -> bool:
    airport_country = str(airport.get("country", "")).strip()

    if not airport_country:
        return False

    if airport_country.upper() == country_code.upper():
        return True

    try:
        country = pycountry.countries.get(alpha_2=country_code.upper())
        if country:
            normalized_airport_country = normalize_text(airport_country)

            possible_names = {
                normalize_text(country.name),
            }

            official_name = getattr(country, "official_name", None)
            common_name = getattr(country, "common_name", None)

            if official_name:
                possible_names.add(normalize_text(official_name))
            if common_name:
                possible_names.add(normalize_text(common_name))

            return normalized_airport_country in possible_names

    except Exception:
        pass

    return False


def get_best_airport_for_country(country_code: str) -> Optional[str]:
    country_code = country_code.upper().strip()

    preferred = COUNTRY_MAIN_AIRPORT.get(country_code)

    if preferred and preferred in AIRPORTS:
        return preferred

    candidates = []

    for iata, airport in AIRPORTS.items():
        if not iata:
            continue

        if not airport_country_matches(airport, country_code):
            continue

        name = normalize_text(airport.get("name", ""))
        city = normalize_text(airport.get("city", ""))

        score = 0

        if "international" in name:
            score += 50

        if "intl" in name:
            score += 40

        if city:
            score += 5

        candidates.append((score, iata))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][1]


def resolve_location_to_iata(location: str) -> Optional[str]:
    """
    Convert a country, city, airport name, ISO country code, or IATA code
    into an airport IATA code.

    Examples:
        "Bangladesh" -> "DAC"
        "Japan" -> "HND"
        "Dhaka" -> "DAC"
        "Tokyo" -> "HND"
        "DFW" -> "DFW"
        "US" -> "DFW"
    """
    if not location:
        return None

    raw_location = str(location).strip()

    if not raw_location:
        return None

    # Direct airport IATA code.
    if re.fullmatch(r"[A-Za-z]{3}", raw_location):
        code = raw_location.upper()
        if code in AIRPORTS:
            return code

    # Direct ISO alpha-2 country code.
    if re.fullmatch(r"[A-Za-z]{2}", raw_location):
        country = pycountry.countries.get(alpha_2=raw_location.upper())
        if country:
            airport = get_best_airport_for_country(country.alpha_2)
            if airport:
                return airport

    location_clean = clean_text(raw_location) or normalize_text(raw_location)

    if not location_clean:
        return None

    # Preferred city mapping.
    preferred_city_airport = NORMALIZED_CITY_MAIN_AIRPORT.get(location_clean)
    if preferred_city_airport:
        return preferred_city_airport

    # Country mapping.
    country_code = country_name_to_code(raw_location)
    if country_code:
        airport = get_best_airport_for_country(country_code)
        if airport:
            return airport

    # Search the airports database by city and airport name.
    city_matches = []

    for iata, airport in AIRPORTS.items():
        if not iata:
            continue

        city = normalize_text(airport.get("city", ""))
        name = normalize_text(airport.get("name", ""))

        score = 0

        if city == location_clean:
            score += 120
        elif _contains_phrase(city, location_clean):
            score += 80

        if name == location_clean:
            score += 100
        elif _contains_phrase(name, location_clean):
            score += 60

        if score > 0:
            if "international" in name:
                score += 10

            city_matches.append((score, iata))

    if not city_matches:
        return None

    city_matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return city_matches[0][1]


# ---------------------------------------------------------------------------
# Natural-language location detection
# ---------------------------------------------------------------------------

def find_location_mentions(query: str) -> list[str]:
    """
    Find country, city, explicit ISO-country-code, or IATA mentions inside
    a natural-language query, preserving the order in which they appear.
    """
    if not query:
        return []

    normalized_query = normalize_text(query)
    matches = []

    # Explicit uppercase two-letter ISO country codes such as US, GB, JP.
    for match in re.finditer(r"\b[A-Z]{2}\b", query):
        code = match.group(0)
        if pycountry.countries.get(alpha_2=code):
            matches.append((match.start(), match.end(), code))

    # Explicit uppercase IATA codes such as DFW, HND, DAC.
    for match in re.finditer(r"\b[A-Z]{3}\b", query):
        code = match.group(0)
        if code in AIRPORTS:
            matches.append((match.start(), match.end(), code))

    # Full country names.
    for country in pycountry.countries:
        names = {country.name}

        official_name = getattr(country, "official_name", None)
        common_name = getattr(country, "common_name", None)

        if official_name:
            names.add(official_name)
        if common_name:
            names.add(common_name)

        for name in names:
            normalized_name = normalize_text(name)
            if not normalized_name:
                continue

            for match in re.finditer(
                rf"(?<![a-z0-9]){re.escape(normalized_name)}(?![a-z0-9])",
                normalized_query,
            ):
                matches.append((match.start(), match.end(), name))

    # Common aliases, excluding ambiguous two-letter aliases.
    for alias, code in NORMALIZED_COUNTRY_ALIASES.items():
        if not _safe_alias_for_sentence(alias):
            continue

        for match in re.finditer(
            rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])",
            normalized_query,
        ):
            matches.append((match.start(), match.end(), alias))

    # Preferred city names.
    for city in CITY_MAIN_AIRPORT:
        normalized_city = normalize_text(city)

        for match in re.finditer(
            rf"(?<![a-z0-9]){re.escape(normalized_city)}(?![a-z0-9])",
            normalized_query,
        ):
            matches.append((match.start(), match.end(), city))

    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    unique_mentions = []
    seen_resolutions = set()

    for _, _, mention in matches:
        resolved = resolve_location_to_iata(mention)
        dedupe_key = resolved or normalize_text(mention)

        if dedupe_key in seen_resolutions:
            continue

        seen_resolutions.add(dedupe_key)
        unique_mentions.append(mention)

    return unique_mentions


# ---------------------------------------------------------------------------
# Route parsing
# ---------------------------------------------------------------------------

_ROUTE_STOP_WORDS = (
    r"on|for|under|including|with|in|at|by|"
    r"departing|leaving|returning|roundtrip|round-trip"
)


def _resolve_route_part(text: str) -> Optional[str]:
    text = text.strip(" ,.-")
    return resolve_location_to_iata(text)


def parse_route(query: str) -> tuple[Optional[str], Optional[str]]:
    """
    Return:
        (departure_iata, arrival_iata)

    Examples:
        "DFW to HND" -> ("DFW", "HND")
        "from Bangladesh to Japan" -> ("DAC", "HND")
        "Japan trip from Bangladesh" -> ("DAC", "HND")
        "flights from DFW" -> ("DFW", None)
        "flights to Japan" -> (None, "HND")
        "Japan trip" -> (DEFAULT_ORIGIN_IATA, "HND")
        "all flights" -> (None, None)
    """
    if not query or not query.strip():
        return None, None

    q = query.strip()
    q_lower = q.casefold()

    global_keywords = [
        "all country",
        "all countries",
        "global flight",
        "global flights",
        "all flight",
        "all flights",
        "worldwide flight",
        "worldwide flights",
    ]

    if any(keyword in q_lower for keyword in global_keywords):
        return None, None

    # Explicit IATA route such as DFW to HND.
    iata_route = re.search(
        r"\b([A-Za-z]{3})\s+(?:to|->|-)\s+([A-Za-z]{3})\b",
        q,
    )

    if iata_route:
        dep_code = iata_route.group(1).upper()
        arr_code = iata_route.group(2).upper()

        if dep_code in AIRPORTS and arr_code in AIRPORTS:
            return dep_code, arr_code

    # Generic "X to Y" route, for example "London to Japan".
    # Only accept it when both sides resolve to airports, so phrases such as
    # "I want to travel to Japan" do not incorrectly invent an origin.
    generic_to = re.search(
        rf"^(.+?)\s+to\s+(.+?)(?=\s+(?:{_ROUTE_STOP_WORDS})\b|[.!?]|$)",
        q,
        flags=re.IGNORECASE,
    )

    if generic_to:
        dep_iata = _resolve_route_part(generic_to.group(1))
        arr_iata = _resolve_route_part(generic_to.group(2))

        if dep_iata and arr_iata:
            return dep_iata, arr_iata

    # "from X to Y"
    from_to = re.search(
        rf"\bfrom\s+(.+?)\s+to\s+(.+?)(?=\s+(?:{_ROUTE_STOP_WORDS})\b|[.!?]|$)",
        q,
        flags=re.IGNORECASE,
    )

    if from_to:
        dep_iata = _resolve_route_part(from_to.group(1))
        arr_iata = _resolve_route_part(from_to.group(2))
        return dep_iata, arr_iata

    # "to Y from X"
    to_from = re.search(
        rf"\bto\s+(.+?)\s+from\s+(.+?)(?=\s+(?:{_ROUTE_STOP_WORDS})\b|[.!?]|$)",
        q,
        flags=re.IGNORECASE,
    )

    if to_from:
        arr_iata = _resolve_route_part(to_from.group(1))
        dep_iata = _resolve_route_part(to_from.group(2))
        return dep_iata, arr_iata

    # "Japan trip from Bangladesh":
    # destination appears before "from", origin appears after it.
    from_match = re.search(
        rf"\bfrom\s+(.+?)(?=\s+(?:{_ROUTE_STOP_WORDS})\b|[.!?]|$)",
        q,
        flags=re.IGNORECASE,
    )

    if from_match:
        origin_text = from_match.group(1).strip()
        dep_iata = _resolve_route_part(origin_text)

        before_from = q[:from_match.start()]
        destination_mentions = find_location_mentions(before_from)

        if destination_mentions:
            for mention in reversed(destination_mentions):
                arr_iata = resolve_location_to_iata(mention)
                if arr_iata and arr_iata != dep_iata:
                    return dep_iata, arr_iata

        return dep_iata, None

    # "flights to Japan"
    to_match = re.search(
        rf"\bto\s+(.+?)(?=\s+(?:{_ROUTE_STOP_WORDS})\b|[.!?]|$)",
        q,
        flags=re.IGNORECASE,
    )

    if to_match:
        arr_iata = _resolve_route_part(to_match.group(1))
        return None, arr_iata

    # Fallback: locate countries/cities in sentence order.
    mentions = find_location_mentions(q)

    if len(mentions) >= 2:
        dep_iata = resolve_location_to_iata(mentions[0])
        arr_iata = resolve_location_to_iata(mentions[1])
        return dep_iata, arr_iata

    if len(mentions) == 1:
        arr_iata = resolve_location_to_iata(mentions[0])

        if arr_iata == DEFAULT_ORIGIN_IATA:
            return arr_iata, None

        return DEFAULT_ORIGIN_IATA, arr_iata

    return None, None


# ---------------------------------------------------------------------------
# Flight API response formatting
# ---------------------------------------------------------------------------

def format_flight(flight: dict) -> str:
    airline = (
        flight.get("airline", {}).get("name")
        or "Unknown airline"
    )

    flight_number = (
        flight.get("flight", {}).get("iata")
        or "Unknown flight number"
    )

    status = flight.get("flight_status") or "Unknown"

    dep = flight.get("departure", {}) or {}
    arr = flight.get("arrival", {}) or {}

    dep_airport = dep.get("airport") or "Unknown departure airport"
    dep_iata = dep.get("iata") or "Unknown"
    dep_terminal = dep.get("terminal") or "N/A"
    dep_gate = dep.get("gate") or "N/A"
    dep_scheduled = dep.get("scheduled") or "Unknown"
    dep_delay = dep.get("delay")

    dep_delay_text = (
        f"{dep_delay} minutes"
        if dep_delay is not None
        else "N/A"
    )

    arr_airport = arr.get("airport") or "Unknown arrival airport"
    arr_iata = arr.get("iata") or "Unknown"
    arr_terminal = arr.get("terminal") or "N/A"
    arr_gate = arr.get("gate") or "N/A"
    arr_scheduled = arr.get("scheduled") or "Unknown"
    arr_delay = arr.get("delay")

    arr_delay_text = (
        f"{arr_delay} minutes"
        if arr_delay is not None
        else "N/A"
    )

    return f"""
Airline: {airline}
Flight: {flight_number}
Status: {status}

Departure:
- Airport: {dep_airport}
- IATA: {dep_iata}
- Terminal: {dep_terminal}
- Gate: {dep_gate}
- Scheduled: {dep_scheduled}
- Delay: {dep_delay_text}

Arrival:
- Airport: {arr_airport}
- IATA: {arr_iata}
- Terminal: {arr_terminal}
- Gate: {arr_gate}
- Scheduled: {arr_scheduled}
- Delay: {arr_delay_text}
""".strip()


# ---------------------------------------------------------------------------
# AviationStack search
# ---------------------------------------------------------------------------

def search_flights(query: str, limit: int = 10) -> str:
    if not API_KEY:
        return (
            "Flight API error: AVIATIONSTACK_API_KEY is missing.\n"
            "Please add this to your .env file:\n"
            "AVIATIONSTACK_API_KEY=your_api_key_here"
        )

    dep_iata, arr_iata = parse_route(query)

    try:
        requested_limit = int(limit)
    except (TypeError, ValueError):
        requested_limit = 10

    requested_limit = max(1, min(requested_limit, 100))

    params = {
        "access_key": API_KEY,
        "limit": requested_limit,
    }

    if dep_iata:
        params["dep_iata"] = dep_iata

    if arr_iata:
        params["arr_iata"] = arr_iata

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30,
        )
    except requests.exceptions.RequestException as exc:
        return f"Flight API request failed: {exc}"

    try:
        data = response.json()
    except ValueError:
        return (
            f"Flight API returned invalid JSON "
            f"(HTTP {response.status_code})."
        )

    if "error" in data:
        error = data["error"] or {}

        return (
            "Flight API error:\n"
            f"Code: {error.get('code', 'Unknown')}\n"
            f"Message: {error.get('message', 'Unknown error')}"
        )

    if not response.ok:
        return (
            f"Flight API request failed with HTTP "
            f"{response.status_code}."
        )

    flight_data = data.get("data", [])

    if not flight_data:
        route_text = ""

        if dep_iata and arr_iata:
            route_text = f" for route {dep_iata} to {arr_iata}"
        elif dep_iata:
            route_text = f" from {dep_iata}"
        elif arr_iata:
            route_text = f" to {arr_iata}"

        return (
            f"No live flight data found{route_text}.\n\n"
            "Note: AviationStack provides live/status flight data, "
            "not ticket prices. For actual fare prices, use a "
            "flight-pricing API such as Amadeus."
        )

    route_info = "Global live flights"

    if dep_iata and arr_iata:
        route_info = f"Live flights from {dep_iata} to {arr_iata}"
    elif dep_iata:
        route_info = f"Live flights from {dep_iata}"
    elif arr_iata:
        route_info = f"Live flights to {arr_iata}"

    formatted_flights = [
        format_flight(flight)
        for flight in flight_data[:requested_limit]
    ]

    return (
        f"{route_info}\n\n"
        + "\n\n---\n\n".join(formatted_flights)
    )


if __name__ == "__main__":
    test_queries = [
        "Plan a 7 days Japan trip from Bangladesh",
        "Flights from Bangladesh to Japan",
        "DFW to HND",
        "Japan trip",
        "all country flight info",
    ]

    for test_query in test_queries:
        print("=" * 80)
        print(f"Query: {test_query}")
        print(f"Parsed route: {parse_route(test_query)}")
