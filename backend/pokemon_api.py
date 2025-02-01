import requests
import os
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
API_KEY = os.getenv("POKEMON_TCG_API_KEY")

# Base API URLs
BASE_URL = "https://api.pokemontcg.io/v2/cards"
SETS_URL = "https://api.pokemontcg.io/v2/sets"

def get_all_sets():
    """Fetches all Pokémon TCG sets from the API, sorts by release date, and returns a list of set names."""
    headers = {"X-Api-Key": API_KEY}

    try:
        response = requests.get(SETS_URL, headers=headers)
        response.raise_for_status()

        data = response.json()
        if not data["data"]:
            return ["All Sets"]  # Default option if no sets found

        # Extract set names with release dates
        sets = [{"name": "All Sets", "releaseDate": "0000-00-00"}]  # Default option
        for set_info in data["data"]:
            sets.append({
                "name": set_info["name"],
                "releaseDate": set_info.get("releaseDate", "9999-99-99")  # Default far future if missing
            })

        # Sort sets by release date (oldest to newest)
        sorted_sets = sorted(sets, key=lambda x: x["releaseDate"])

        # Return only set names in sorted order
        return [set_item["name"] for set_item in sorted_sets]

    except requests.exceptions.RequestException as e:
        print("⚠ API Request Failed:", e)
        return ["All Sets"]  # Default option in case of API failure

def search_pokemon_cards(name, selected_set="All Sets"):
    """Search for Pokémon cards by name (partial match) and optionally filter by set."""
    headers = {"X-Api-Key": API_KEY}

    # Enable partial matches using wildcards
    query = f'name:"*{name}*"'
    
    if selected_set != "All Sets":
        query += f' set.name:"{selected_set}"'
    
    params = {"q": query}

    try:
        response = requests.get(BASE_URL, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        if not data["data"]:
            return []  # No results found

        # Extract relevant details
        cards = []
        for card in data["data"]:
            set_name = card.get("set", {}).get("name", "Unknown Set")
            card_info = {
                "name": card.get("name", "Unknown"),
                "set_name": set_name,
                "rarity": card.get("rarity", "Unknown Rarity"),
                "card_number": card.get("number", "N/A"),  # Card number in set
                "market_price": None
            }

            # Extract Market Price from TCGPlayer data (if available)
            tcgplayer_data = card.get("tcgplayer", {}).get("prices", {})
            if "holofoil" in tcgplayer_data:
                card_info["market_price"] = tcgplayer_data["holofoil"].get("market", 0.0)
            elif "normal" in tcgplayer_data:
                card_info["market_price"] = tcgplayer_data["normal"].get("market", 0.0)

            cards.append(card_info)

        return cards

    except requests.exceptions.RequestException as e:
        print("⚠ API Request Failed:", e)
        return []
