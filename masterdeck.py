import os
import openai
import gspread
import json
import requests
from oauth2client.service_account import ServiceAccountCredentials

with open('credentials.json') as f:
    credentials = json.load(f)
openai.api_key = credentials.get("openai_api_key")
ANKI_CONNECT_URL = 'http://localhost:8765'
LAW_DECK = 'Basis' # name of most used deck
SPECIAL_DECK = 'Special Deck'

# Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/macintoshhd/bdayaddon/credentials.json', scope)
client = gspread.authorize(creds)

SHEET_ID = '1cmfuPGo1P9egz8DlP0Nsqcrqd-DAc9erZt8izKmlJdQ'
MASTER_DECK_FILE = '/Users/macintoshhd/bdayaddon/master_deck.json'

# Extract topics from Google Doc
def get_sheet_data(client, sheet_id, range_name ):
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.get_worksheet(0)  # Get the first sheet/tab
    return worksheet.get(range_name)  # Get all data in the specified range

# Generate flashcards from topics

class FlashcardGenerator:
    def __init__(self, client):
        self.client = client

# Updated function
    def _get_openai_response(self, prompt: str, system_prompt: str, temperature: float, max_tokens: int) -> str:
        # Using self.client to match your update context
        completion = self.client.chat.completions.create(
            model="gpt-4o-2024-08-06",  # Updated model name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return completion.choices[0].message.content


    def generate_flashcards_from_topics(self, topics):
        flashcards = []
        for topic in topics:
            prompt = f"Generate a front (question) and back (answer) for a flashcard pertaining to an aspect of {topic}. Return only the question and answer, no headings or extra text."
            system_prompt = "You are a diligent anki flashcard generator. Return only the question and answer, without labels."
            response_content = self._get_openai_response(prompt, system_prompt, temperature=0.7, max_tokens=500)

            try:
                # Split into front and back
                front, back = response_content.split("\n", 1)
                front = front.strip()
                back = back.strip()

                flashcards.append({
                    "topic": topic,  # Overall topic
                    "front": front,  # Question
                    "back": back  # Qnswer
                })

            except ValueError:
                print(f"Unexpected format for topic '{topic}'. Skipping this flashcard.")
                continue

        return flashcards


        # Add to master deck

    def update_master_deck(self, flashcards):
        try:
        # Load existing flashcards
            if os.path.exists(MASTER_DECK_FILE):
                with open(MASTER_DECK_FILE, 'r') as f:
                    master_deck = json.load(f)
            else:
                master_deck = []

            master_deck.extend(flashcards)


        # Save back to the file
            with open(MASTER_DECK_FILE, 'w') as f:
                json.dump(master_deck, f, indent=4)

            print(f"Master deck updated with {len(flashcards)} new flashcards.")
        except Exception as e:
            print(f"An error occurred while updating the master deck: {e}")

    # Remove used topics from Google Sheet
def delete_topic_from_sheet(client, sheet_id, topic):
    """Delete a topic from Google Sheets by finding its row and removing it."""
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.get_worksheet(0)  # If sheet is used

        # Finds cell with topic
    cell = worksheet.find(topic)

    if cell:
        worksheet.delete_rows(cell.row)
        #print(f"Deleted topic '{topic}' from row {cell.row}.")
    else:
        print(f"Topic '{topic}' not found in the sheet.")

# Send a request to AnkiConnect
def anki_connect_request(action, params):
    return requests.post(ANKI_CONNECT_URL, json={
        "action": action,
        "version": 6,
        "params": params
    }).json()

# Find cards with "ai-generated" tag and >= 120 days
def find_cards_to_move():
    query = f"deck:{LAW_DECK} tag:ai-generated prop:ivl>=120"
    response = anki_connect_request('findCards', {"query": query})

    if response.get('error'):
        print(f"Error finding cards: {response['error']}")
        return []

    card_ids = response.get('result', [])
    print(f"Found {len(card_ids)} cards to move.")
    return card_ids

def move_cards_to_special_deck(card_ids):
    if not card_ids:
        print("No cards to move.")
        return

    response = anki_connect_request('changeDeck', {
        "cards": card_ids,
        "deck": SPECIAL_DECK
    })

    if response.get('error'):
        print(f"Error moving cards: {response['error']}")
    else:
        print(f"Moved {len(card_ids)} cards to the Special Deck.")

# Move cards that meet criteria to Special Deck
def move_ai_generated_cards():
    cards_to_move = find_cards_to_move()
    move_cards_to_special_deck(cards_to_move)


# retrieve data from Google Sheet and generate flashcards
flashcard_generator = FlashcardGenerator(openai)  # Pass in the OpenAI client
sheet_data = get_sheet_data(client, SHEET_ID, 'A1:A10')  # Adjust range as needed
topics_from_sheet = [row[0] for row in sheet_data if row]


flashcards = flashcard_generator.generate_flashcards_from_topics(topics_from_sheet)
flashcard_generator.update_master_deck(flashcards)

#for flashcard in flashcards:
    #print(f"Topic: {flashcard['topic']}\nFront: {flashcard['front']}\nBack: {flashcard['back']}\n{'-' * 50}\n")

print(f"Added {len(flashcards)} flashcards to the master deck.")

for topic in topics_from_sheet:
    delete_topic_from_sheet(client, SHEET_ID, topic)

move_ai_generated_cards()
