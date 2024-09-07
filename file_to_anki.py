import json
import random
import os
import requests

MASTER_DECK_FILE = 'master_deck.json'
PREVIOUS_SIZE_FILE = 'previous_special_size.json'
ANKI_CONNECT_URL = 'http://localhost:8765'
LAW_DECK = 'Basis'
SPECIAL_DECK = 'Special Deck'

def load_master_deck():
    if os.path.exists(MASTER_DECK_FILE):
        with open(MASTER_DECK_FILE, 'r') as f:
            master_deck = json.load(f)
            return master_deck
    else:
        print("Master deck not found!")
        return []

def remove_used_cards_from_master(used_cards):
    """Remove used flashcards from the master deck."""
    master_deck = load_master_deck()
    updated_master_deck = [card for card in master_deck if card not in used_cards]

    with open(MASTER_DECK_FILE, 'w') as f:
        json.dump(updated_master_deck, f, indent=4)
    print(f"Removed {len(used_cards)} cards from the master deck.")

def get_special_deck_size():
    response = requests.post(ANKI_CONNECT_URL, json={
        "action": "findCards",
        "version": 6,
        "params": {
            "query": f"deck:{SPECIAL_DECK}"
        }
    })

    result = response.json()
    if result.get('error'):
        print(f"Error fetching special deck size: {result['error']}")
        return 0

    card_ids = result.get('result', [])
    print(f"Special Deck contains {len(card_ids)} cards.")
    return len(card_ids)

def load_previous_special_size():
    if os.path.exists(PREVIOUS_SIZE_FILE):
        try:
            with open(PREVIOUS_SIZE_FILE, 'r') as f:
                previous_size_data = json.load(f)

                # Check if it's an empty list ([]) and treat it as the first run
                if isinstance(previous_size_data, list) and len(previous_size_data) == 0:
                    print("File contains an empty list. Treating as first run.")
                    return None  # Treat empty list as first run
                elif isinstance(previous_size_data, dict):
                    return previous_size_data.get('size', 0)
                else:
                    print("File format invalid. Using default value (0).")
                    return 0
        except json.JSONDecodeError:
            print("File is not valid JSON. Using default value (0).")
            return 0
    else:
        # If the file doesn't exist, treat it as the first run
        print("First run detected. No previous size data found.")
        return None  # Use None to indicate the first run

# Save the current size of the Special Deck to previous_special_size.json
def save_current_special_size(current_size):
    with open(PREVIOUS_SIZE_FILE, 'w') as f:
        json.dump({'size': current_size}, f)

def pull_exact_flashcards(num_cards):
    master_deck = load_master_deck()
    if len(master_deck) == 0:
        print("Master deck is empty, no flashcards to pull!")
        return []

    num_to_draw = min(num_cards, len(master_deck))
    if num_to_draw < num_cards:
        print(f"Only {num_to_draw} flashcards available in the master deck. Pulling those.")
        # Move the pulled flashcards to the special deck and remove from master deck
    flashcards = random.sample(master_deck, num_to_draw)
    return flashcards

def add_flashcards_to_anki(deck_name, flashcards):
    for flashcard in flashcards:
        note = {
            "deckName": deck_name,
            "modelName": "Basic",
            "fields": {
                "Front": flashcard['front'],
                "Back": flashcard['back']
            },
            "tags": [flashcard['topic'], 'ai-generated']
        }

        #make request to AnkiConnect
        response = requests.post(ANKI_CONNECT_URL, json= {
            "action":"addNote",
            "version": 6,
            "params": {
                "note": note
            }
        })

        result = response.json()
        if result.get('error'):
            print(f"Error adding note: {result['error']}")
        else:
            print(f"Added flashcard for secret topic")

# Main process: Check Special Deck size, compare to previous size, and add new cards accordingly
def add_flashcards_based_on_special_deck_growth():
    # Step 1: Get the current size of the Special Deck
    current_special_size = get_special_deck_size()

    # Step 2: Load the previous size from previous_special_size.json
    previous_special_size = load_previous_special_size()

    # Step 3: Calculate how many new flashcards to add
    if previous_special_size is None:
        # First run: add 5 cards if no previous record exists or if the file has an empty list ([])
        cards_to_add = 5
        print("First run detected. Adding 5 flashcards.")
    else:
        # On subsequent runs, compare the sizes and calculate growth
        cards_to_add = current_special_size - previous_special_size
        print(f"Previous special size: {previous_special_size}, Current special size: {current_special_size}")
        if cards_to_add > 0:
            print(f"Special Deck has grown by {cards_to_add} cards. Adding that many new flashcards.")
        else:
            print("No new cards were moved to the Special Deck. No new flashcards will be added.")
            cards_to_add = 0

    # Step 4: Pull and add new flashcards based on the growth (or 5 on first use)
    if cards_to_add > 0:
        exact_flashcards = pull_exact_flashcards(cards_to_add)
        print(f"Tried to pull {cards_to_add} flashcards. Pulled {len(exact_flashcards)} flashcards to add to Anki.")
        if exact_flashcards:
            # Add the pulled flashcards to the Neuropsychology deck
            add_flashcards_to_anki(LAW_DECK, exact_flashcards)
            print(f"Added {len(exact_flashcards)} flashcards to Anki.")

            # Remove the flashcards from the master deck
            remove_used_cards_from_master(exact_flashcards)
    else:
        print("No flashcards to add to Anki.")

    # Step 5: Save the current size for future comparisons
    save_current_special_size(current_special_size)
    print(f"Saved current special size: {current_special_size}")


# Run the script to add new flashcards based on Special Deck growth
add_flashcards_based_on_special_deck_growth()