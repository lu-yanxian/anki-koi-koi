# 花札 Hanafuda Koi-Koi — Anki Add-on

**A fully playable Koi-Koi card game built into Anki, where every card capture is gated behind a vocabulary question from your own decks.**

Created by Z.J. Rubin · Card images by [Louie Mantia](https://commons.wikimedia.org/wiki/User:Louiemantia) (CC BY-SA 4.0)

---

## Table of Contents

1. [What This Add-on Does](#what-this-add-on-does)
2. [Installation](#installation)
3. [Getting Started](#getting-started)
4. [The Game Window](#the-game-window)
5. [Game Options (Pre-Round Settings)](#game-options-pre-round-settings)
6. [Header Controls](#header-controls)
7. [Config Panel](#config-panel)
8. [Appearance Panel](#appearance-panel)
9. [Yaku Guide Panel](#yaku-guide-panel)
10. [Round History Panel](#round-history-panel)
11. [Vocabulary Challenge](#vocabulary-challenge)
12. [Koi-Koi Rules Reference](#koi-koi-rules-reference)

---

## What This Add-on Does

Hanafuda Koi-Koi is a traditional Japanese card game played with a 48-card flower-themed deck. This add-on turns it into a vocabulary learning tool.

Every time you attempt to capture a pair of cards during the game, a multiple-choice vocabulary question appears drawn from your selected Anki deck. Answer correctly and you capture the cards. Answer incorrectly and the penalty depends on your chosen mode.

Answers are recorded back into Anki's spaced repetition scheduler — correct answers advance the card's interval, wrong answers send it back for review — so playing the game counts as a genuine Anki review session.

The game is fully playable without a deck selected (it will skip vocab questions), so you can also use it as a standalone Koi-Koi game.

---

## Installation

### From AnkiWeb

Search for "Hanafuda Koi-Koi" in Anki's add-on browser (Tools → Add-ons → Browse & Install) and enter the add-on code.

### Manual Installation

1. Download `hanafuda_koi_koi.ankiaddon` from the [GitHub Releases page](https://github.com/zjrubin/hanafuda-koi-koi-anki/releases)
2. Open Anki
3. Go to **Tools → Add-ons → Install from file**
4. Select the downloaded `.ankiaddon` file
5. Restart Anki

Alternatively, unzip the file and copy the `hanafuda_game` folder directly into your Anki `addons21` directory:
- **Windows:** `C:\Users\YourName\AppData\Roaming\Anki2\addons21\`
- **Mac:** `~/Library/Application Support/Anki2/addons21/`
- **Linux:** `~/.local/share/Anki2/addons21/`

### Requirements

- Anki 23.10 or later
- Desktop platform (Windows, Mac, or Linux) — not compatible with AnkiDroid or AnkiMobile

---

## Getting Started

1. Launch Anki and go to **Tools → 🌸 Hanafuda Koi-Koi**
2. The game window opens. At the top, select a deck from the dropdown — this is the deck vocab questions will be drawn from. The game remembers this deck next time.
3. Click **New Game**
4. The dealer flip screen appears. Set your game options (see below), then click **Flip Cards** to determine who goes first
5. Play begins — click a card from your hand, then click a matching card on the field to attempt a capture

The indicator in the top-right corner of the log bar shows the connection status:
- **⬤ Anki connected** (accent colour) — vocab questions are active
- **⬤ connecting...** — still establishing the bridge, wait a moment
- **⬤ no bridge (browser)** — running in browser preview mode, no Anki connection

---

## The Game Window

The window is divided into several areas:

**Score boxes** — show each player's current score, name, and an indicator when it is their turn (highlighted border).

**CPU hand** — the CPU's face-down cards.

**Field** — the 8 cards in the centre of the table available for capture. Cards that match a card in your hand glow to indicate a valid play.

**Your hand** — your 8 cards. Click one to select it, then click a matching field card to attempt a capture.

**Deck** — the remaining draw pile shown as a face-down stack with the card count.

**Log bar** — shows the current game state, last action, and connection status.

**Yaku section** — at the bottom of the page, shows all possible yaku (scoring combinations) with those you have currently earned highlighted. A count badge shows how many of each card type you have captured.

---

## Game Options (Pre-Round Settings)

These appear on the dealer flip screen before each game starts. They lock once the game begins and unlock when it ends (or when you start a New Game). Your choices are remembered for next time.

### CPU Difficulty
Determines how the CPU plays.

- **Easy** — plays randomly, never calls Koi-Koi. Good for learning the rules.
- **Normal** — greedy play (prefers higher-value cards), calls Koi-Koi when it has 7+ points or when you have called Koi-Koi first. The default.
- **Hard** — evaluates each possible play by its contribution to yaku progress, calls Koi-Koi aggressively, and will sometimes deliberately discard cards that would help you form a yaku (denial strategy).

### Game Mode
Determines the scoring structure.

- **Count Down** — both players start with 30 points. When a round is won, the winner takes points from the loser (zero-sum). The game ends when a player reaches 0, or after 12 rounds. This is the traditional competitive scoring format.
- **Count Up** — both players start at 0 and accumulate points independently over 12 rounds. Points are never stolen. Whoever has more points at the end wins. This format is better for casual play.

### Wrong Answer Mode
Determines what happens when you answer a vocab question incorrectly. In every mode, a wrong answer counts as a miss (Again) for that card — see [How Answers Are Recorded to Anki](#how-answers-are-recorded-to-anki).

- **Learning** — no penalty. You always capture the cards regardless of your answer. The question is shown for learning purposes; a missed card still comes back sooner, but the game is not affected.
- **Full Penalty** — a wrong answer shows the correct answer for a moment, then your hand card goes to the field. You do not capture.
- **Retry (3 strikes)** — a wrong answer fetches a new question. You have three attempts total. Three wrong answers in a row leaves both cards on the field. Each missed question counts as a miss for its own card.
- **Duel Mode** — a wrong answer triggers a mini-duel. Both players draw a card from the deck face-up. The lower month wins. Win the duel and you still capture; lose and your hand card goes to the field.

### Questions per Card
How many vocab questions you must answer correctly to earn each capture. Set to 1 by default. Higher values give more practice per capture but slow the game. Can also be adjusted via the slider in the header during play.

### Hints
Choose your hint system for the game.

- **3 per game** — you get 3 hints for the entire game, refilled at the start of each new game. Using a hint reveals the correct answer highlighted in gold. A correct answer after a hint counts as Hard.
- **Unlimited** — hints are always available, one per question.
- Both options are off by default (no hints).

### Hide Choices
When enabled, the multiple-choice options are hidden when a question first appears. A "Show Choices" button lets you reveal them when you are ready. This prevents you from associating each question with the position of its answer rather than the actual meaning. Can be toggled freely during the game via the header.

---

## Header Controls

The header bar is always visible at the top of the screen. Everything here is saved automatically.

### CPU Speed slider
Controls how long the CPU pauses between actions, from 0.4 seconds to 3.0 seconds. Default is 1.0 second. Increase this if you want more time to read the log between CPU moves.

### Q/card slider
Adjusts how many questions you must answer per capture, from 1 to 3. Can be changed at any time during the game.

### Hide Choices toggle
Toggles the hide-choices setting on or off during play. Synced with the toggle in the pre-game settings screen.

### History button
Opens the Round History panel (see below).

### Config button
Opens the Config panel (see below).

### Appearance button
Opens the Appearance panel (see below).

---

## Config Panel

The Config panel lets you fine-tune how vocab questions are drawn from your deck and whether they count as Anki reviews. Open it at any time by clicking **Config** in the header, make your changes, and click **Save & Apply**. Settings are remembered between sessions.

### Field Detection

When you select a deck, the add-on automatically detects which fields to use as the question and answer. It uses the field names — for example, a field called "Hanzi" is recognised as a question field, and a field called "English" or "Definition" is recognised as an answer field.

The **Question Field** and **Answer Field** dropdowns show the auto-detected choice and let you override it manually. The "Auto would pick" label shows what the auto-detection selected for reference.

Manual choices are saved **per deck**: setting fields for your Chinese deck won't affect your Tibetan deck, and each deck remembers its own choice. **Reset to Auto** clears the choice for the current deck.

Fields are matched by name on every card, so decks that mix several note types (and "All decks") pick the right field on each card. If a note type doesn't have the chosen field, that note type falls back to auto-detection.

### Card Pool & Pacing

**Active pool** — how many cards from your deck are in your active study pool at once, from 5 up to 200 (capped at the size of the deck). Default is 20. The game works through these cards before pulling in new ones. Smaller pools mean more repetition and faster mastery of a small set; larger pools give more variety.

For example, with a pool of 10 and a 100-word deck, the game works on 10 words at a time and moves on through the deck as you answer them (see Card order below for exactly how). Once you reach the end of the deck, it starts over from the beginning.

A card you answer correctly won't come back until you've been through the whole deck. Cards you miss (or rate Hard) stay in a "missed" queue and come back soon.

**Card order** — three options:
- **In order** — the pool follows the deck's order (for example HSK word 1, 2, 3…), and cards are asked in exactly that order.
- **Shuffle pool** (default) — the pool still follows the deck's order, but the cards inside it are asked in random order. With a pool of 20, you get words 1–20 in a random order, then words 21–40 in a random order, and so on. This is the best fit for decks meant to be learned in sequence, when you don't want to memorise the order itself.
- **Random from deck** — the pool is drawn at random from the whole deck, and cards are asked in random order.

**Focus slider** — five steps that control how often missed cards come back:
- **New only** — missed cards come back only once the pool runs out of new ones
- **Mostly new** — missed cards come back occasionally
- **Balanced** — missed cards come back now and then (default)
- **Mostly review** — missed cards come back often
- **Review heavy** — missed cards come back most of the time, for drilling what you got wrong

Cards you answered correctly are never affected by Focus. They don't come back until you've been through the whole deck.

### Anki Scheduling

Controls whether your answers in the game count as real Anki reviews:

- **Off** — your Anki schedule is never touched. The game still tracks what you've missed during play.
- **Due only** (default) — answers are recorded only for cards Anki already has due today. The game never pulls new cards into your schedule or reviews cards early.
- **All cards** — every answer is recorded. New cards you answer will enter Anki's learning queue, and cards that aren't due yet are reviewed early.

Anki's main screen refreshes when you close the game, so due counts reflect what you answered.

### Ease Rating Buttons

When enabled, **Hard**, **Good** and **Easy** buttons appear after you answer a question correctly. These are for honest self-assessment — since multiple choice lets you guess, they let you rate how well you actually knew the answer.

- **Easy** — you knew it cold. Longer Anki interval; the card is done for this game.
- **Good** — you knew it. Normal interval.
- **Hard** — you guessed or struggled. Shorter Anki interval, and the card comes back soon in this game.

Wrong answers don't show the buttons; they always count as Again. When the buttons are off, a correct answer counts as Good.

---

## Appearance Panel

Six visual themes are available, each named after a Japanese city:

- **Tokyo** — the default. Dark blue, professional and easy on the eyes.
- **Nara** — warm amber and chestnut, inspired by Nara's cedar forests and deer parks.
- **Hirosaki** — soft pinks and warm whites, inspired by Hirosaki Castle's famous cherry blossoms.
- **Kyoto** — imperial green, gold lacquer, and vermillion — the colours of Heian court culture.
- **Fukuoka** — deep navy, dark teal, and lavender, inspired by Fukuoka's coastal harbour.
- **Sapporo** — near-black background with cream surfaces and icy blue accents, evoking a Hokkaido winter night.

Click any theme to switch instantly. Your theme is remembered the next time you open the game.

---

## Yaku Guide Panel

Click **Yaku Guide** next to the yaku section at the bottom of the screen to open a detailed reference panel listing all 13 yaku with:

- Japanese name and romanisation
- Point value
- Description of what the combination requires
- Which specific cards are involved

This is useful when you are learning which cards to prioritise capturing.

---

## Round History Panel

Click **History** in the header to open a panel showing all completed rounds in the current game, newest first. Each entry shows:

- Round number
- Winner
- Yaku formed
- Points earned (with any multipliers noted)
- Running scores after that round

---

## Vocabulary Challenge

When you attempt to capture a card pair, a challenge overlay appears with:

- The question (drawn from your selected deck's question field)
- Four multiple-choice answers (one correct, three drawn from other cards in the deck)
- A hint button (if hints are enabled)
- Hard / Good / Easy buttons after a correct answer (if enabled in Config)
- A stake description explaining the current penalty mode

### How Answers Are Recorded to Anki

Each answer is given a rating. Whether that rating is sent to Anki depends on the [Anki Scheduling](#anki-scheduling) setting (by default, only for cards that are due).

| Situation | Rating |
|---|---|
| Correct, no hint used | 3 — Good (or your Hard / Good / Easy choice, if the buttons are on) |
| Correct, hint was used | 2 — Hard |
| Wrong answer (any mode, including retry strikes and duels) | 1 — Again |

When ratings are sent to Anki, your card intervals update in real time as you play, and the time you spent on each question is recorded as the review time. Cards you struggle with come back sooner; cards you know well are pushed further out.

### Session Tracking

Within a single game, the add-on tracks which cards you have seen and answered. It will not show you the same card twice in a row, never repeats a card you answered correctly until you've been through the deck, and brings back cards you missed according to the Focus setting. Decks with several cards per note (like a word card and a sentence card from the same note) count each note once. Suspended cards are skipped. When you start a new game or switch decks, the session resets; your pool, focus and card order settings carry over.

---

## Koi-Koi Rules Reference

### The Deck

Hanafuda uses a 48-card deck divided into 12 suits of 4 cards each, one suit per month of the year. Each suit is associated with a flower or plant:

| Month | Plant | Special cards |
|---|---|---|
| January | Pine | Crane (bright) |
| February | Plum | Bush Warbler |
| March | Cherry | Curtain (bright) |
| April | Wisteria | Cuckoo |
| May | Iris | Bridge |
| June | Peony | Butterflies |
| July | Bush Clover | Boar |
| August | Susuki Grass | Moon (bright) |
| September | Chrysanthemum | Sake Cup |
| October | Maple | Deer |
| November | Willow | Rain Man (bright), Swallow |
| December | Paulownia | Phoenix (bright) |

Cards are ranked by type: **Bright** (20 pts) → **Ribbon/Tane** (10 pts) → **Kasu** (plain, 1 pt).

### Setup

Each player is dealt 8 cards. 8 cards are laid face-up on the field. The remaining 24 form the draw pile. The dealer (Oya, marked ★) is determined by a card flip at the start of each game — the player whose flipped card has the lower month number becomes the dealer and goes first.

### A Turn

On your turn you take two actions in sequence:

**1. Play from hand** — select a card from your hand. If it matches the month of a card on the field, you capture both (they go to your captured pile). If it matches two field cards, you choose which one to take. If the other three cards of that month are all on the field, you capture all four. If there is no match, your card is placed on the field.

**2. Draw from deck** — flip the top card of the draw pile. If it matches a field card, you capture both. If not, it stays on the field.

### Forming Yaku

After each capture (hand play or deck draw), the game checks whether your captured cards form any yaku (scoring combinations — see the Yaku Guide in the game for the full list). If you form a new yaku, you must make a decision:

- **Stop (やめ)** — end the round and collect your points
- **Koi-Koi (こいこい)** — continue playing to try to earn more points, but take a risk: if your opponent forms a yaku before you form another, they win the round with double points and you earn nothing

If you form a yaku on your very last play, there's nothing left to continue with, so the game stops for you automatically. The CPU follows the same rule.

### End of Round

The round ends when:
- A player calls Stop after forming a yaku (or is stopped automatically on their last play)
- The cards run out without anyone stopping — this is Oya-Ken (see below)

When a player stops, they score points based on their yaku. In Count Down mode, the loser's score is reduced by the same amount.

### Scoring Multipliers

- **7+ points:** If your total yaku score is 7 or more, it is doubled (×2)
- **Opponent called Koi-Koi:** If your opponent called Koi-Koi earlier in the round and you subsequently form a yaku, your score is doubled (×2)
- **Both conditions:** ×4 total

### Special Deals

If you are dealt any of the following at the start of a round, the round ends immediately:

- **Teshi (手四)** — all four cards of the same month in your opening hand (6 points)
- **Kuttsuki (くっつき)** — four pairs (two cards from four different months) in your opening hand (6 points)

If these appear in the field instead of a hand, the round is void and redealt.

### Oya-Ken (親権) — Dealer's Privilege

If the cards run out without anyone stopping, nobody scores their yaku — even a player holding yaku from before a Koi-Koi earns nothing. Instead, the dealer gains 1 point (taken from the opponent in Count Down mode) and keeps the deal for the next round.

### The Sake Cup

The September Sake Cup is special: it counts as both a seed (tane) card and a kasu card at the same time, so it can help complete Tane and Kasu.

### Full Yaku List

| Yaku | Japanese | Points | Requirement |
|---|---|---|---|
| Goko | 五光 | 10 | All 5 bright cards |
| Shiko | 四光 | 8 | Any 4 brights, excluding Rain Man |
| Ame-Shiko | 雨四光 | 7 | Any 4 brights, including Rain Man |
| Sankou | 三光 | 5 | Any 3 brights, excluding Rain Man |
| Tsukimi-zake | 月見酒 | 5 | Moon + Sake Cup |
| Hanami-zake | 花見酒 | 5 | Cherry Curtain + Sake Cup |
| Inoshikacho | 猪鹿蝶 | 5 | Boar + Deer + Butterflies |
| Akatan | 赤短 | 5 | All 3 red poetry ribbons (Jan/Feb/Mar) |
| Aotan | 青短 | 5 | All 3 blue ribbons (Jun/Sep/Oct) |
| Akatan + Aotan | 赤短·青短 | 10 | All 6 of the above ribbons combined |
| Tane | タネ | 1+extras | Any 5 seed cards (+1 per extra) |
| Tanzaku | 短冊 | 1+extras | Any 5 ribbon cards (+1 per extra) |
| Kasu | 粕 | 1+extras | Any 10 kasu cards, Sake Cup included (+1 per extra) |

---

*Hanafuda card images by Louie Mantia, licensed under CC BY-SA 4.0. This add-on is released under the same license.*
