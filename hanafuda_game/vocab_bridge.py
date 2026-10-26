"""
vocab_bridge.py — vocab challenges with session-based card tracking,
and recording answers back into Anki's scheduler.

Notes on compatibility: keep this file free of Python 3.9+ only syntax
(no list[int] / X | None annotations) so it loads on older Anki builds.
"""

import html
import random
import re

QUESTION_PREFERRED = [
    'hanzi', 'chinese', 'japanese', 'kanji', 'tibetan', 'arabic', 'korean',
    'russian', 'german', 'french', 'spanish', 'italian', 'portuguese', 'dutch',
    'hebrew', 'turkish', 'hindi', 'thai', 'vietnamese', 'latin', 'greek',
    'word', 'term', 'front', 'target', 'vocab', 'vocabulary', 'expression',
    'phrase', 'character', 'kana', 'foreign', 'question',
]
ANSWER_PREFERRED = [
    'definition', 'meaning', 'translation', 'english', 'back', 'answer',
    'gloss', 'explanation', 'notes', 'note', 'description', 'native',
    'deutsch', 'français', 'español', 'italiano', 'português', 'usage', 'sense',
]

# Shuffle modes
SHUFFLE_OFF = 0        # pool follows deck order, asked in sequence
SHUFFLE_IN_POOL = 1    # pool follows deck order, asked in random order
SHUFFLE_DECK = 2       # pool drawn at random from the whole deck

# Focus levels: chance that the next question is a card you missed / rated
# Hard (when there are any), instead of a new card from the pool
FOCUS_MISSED_CHANCE = [0.0, 0.15, 0.35, 0.55, 0.8]

# Record-to-Anki modes
RECORD_OFF = 0
RECORD_DUE_ONLY = 1
RECORD_ALL = 2


def _strip_html(text):
    # Line breaks and block ends become spaces so words don't run together
    text = re.sub(r'(?i)<br\s*/?>|</(div|p|li|tr|h[1-6])>', ' ', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[sound:[^\]]+\]', '', text)
    text = html.unescape(text)
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _is_usable(text):
    if not text:
        return False
    if re.match(r'^\d+$', text):
        return False
    return True


def auto_detect_fields(field_names):
    """Positive keyword matching only. Returns (q_idx, a_idx)."""
    if len(field_names) < 2:
        return 0, 1
    lower = [f.lower() for f in field_names]
    q_idx = next(
        (i for pref in QUESTION_PREFERRED
         for i, f in enumerate(lower) if pref in f), 0)
    a_idx = next(
        (i for pref in ANSWER_PREFERRED
         for i, f in enumerate(lower) if pref in f and i != q_idx),
        next((i for i in range(len(field_names)) if i != q_idx), 1))
    return q_idx, a_idx


class FieldResolver:
    """
    Works out which field is the question and which is the answer for any
    note. Fields are matched by NAME, so mixed decks / "All decks" work even
    when note types put their fields in different positions. If a note type
    lacks the chosen field name, that note type falls back to auto-detection.
    """
    def __init__(self, q_name=None, a_name=None):
        self.q_name = q_name
        self.a_name = a_name
        self._cache = {}  # note type id -> (q_idx, a_idx)

    def indices(self, note):
        mid = note.mid
        if mid in self._cache:
            return self._cache[mid]
        keys = list(note.keys())
        auto_q, auto_a = auto_detect_fields(keys)
        q = keys.index(self.q_name) if self.q_name in keys else auto_q
        a = keys.index(self.a_name) if self.a_name in keys else auto_a
        if q == a:
            q, a = auto_q, auto_a
        self._cache[mid] = (q, a)
        return q, a

    def qa(self, note):
        q, a = self.indices(note)
        fields = note.fields
        if q < 0 or q >= len(fields) or a < 0 or a >= len(fields):
            return '', ''
        return _strip_html(fields[q]), _strip_html(fields[a])


class VocabSession:
    """
    Tracks card exposure within one game.

    - all_ids:       one card per note, in pool order (deck order or shuffled)
    - all_card_ids:  every card in the deck (used for wrong-answer choices)
    - seen:          cards answered Good/Easy this game
    - wrong_queue:   cards missed or rated Hard — they come back soon
    - last_id:       never show the same card twice in a row

    The active pool is the first `pool_size` unseen cards. In "Shuffle pool"
    mode it is a fixed block of the next `pool_size` cards in deck order,
    asked in random order; the next block starts when that one is done. In
    the other modes it is a sliding window. When the whole deck is seen,
    everything resets and starts over.
    """
    def __init__(self, all_ids, due_ids, card_to_note=None, all_card_ids=None,
                 shuffle_mode=SHUFFLE_IN_POOL, focus=2, pool_size=20):
        self.all_ids = list(all_ids)
        self.all_card_ids = list(all_card_ids) if all_card_ids else list(all_ids)
        self.due_ids = due_ids
        self.seen = set()
        self.wrong_queue = []
        self.pending = None
        self.last_id = None
        self.focus = focus          # 0 New only ... 2 Balanced ... 4 Review heavy
        self.pool_size = pool_size  # max unseen cards active at once
        self.shuffle_mode = shuffle_mode
        self.card_to_note = card_to_note or {}
        note_to_cards = {}
        for cid, nid in self.card_to_note.items():
            note_to_cards.setdefault(nid, []).append(cid)
        self.note_to_cards = note_to_cards
        self.block = []             # SHUFFLE_IN_POOL: current deck-order block
        if self.shuffle_mode == SHUFFLE_DECK:
            random.shuffle(self.all_ids)

    def pick(self):
        def exclude(lst):
            return [c for c in lst if c != self.last_id]

        def choose(pool):
            chosen = pool[0] if self.shuffle_mode == SHUFFLE_OFF else random.choice(pool)
            self.pending = chosen
            self.last_id = chosen
            return chosen

        # Cards answered Good/Easy never repeat until the whole deck has been
        # worked through. Focus only controls how often MISSED (or Hard) cards
        # come back, from "New only" (only once the pool's new cards run out)
        # to "Review heavy" (most of the time).
        all_unseen = [c for c in self.all_ids if c not in self.seen]
        if self.shuffle_mode == SHUFFLE_IN_POOL:
            # Work through the deck in blocks: the next pool_size cards in deck
            # order, asked in random order. Missed cards leave the block (they
            # come back through the missed queue), and the next block starts
            # once every card in this one has been answered.
            unseen = [c for c in self.block
                      if c not in self.seen and c not in self.wrong_queue]
            if not unseen:
                self.block = [c for c in all_unseen
                              if c not in self.wrong_queue][:self.pool_size]
                unseen = list(self.block)
        else:
            unseen = all_unseen[:self.pool_size]
        level = max(0, min(int(self.focus), len(FOCUS_MISSED_CHANCE) - 1))
        missed_chance = FOCUS_MISSED_CHANCE[level]
        if missed_chance and random.random() < missed_chance:
            pool = exclude(self.wrong_queue)
            if pool:
                return choose(pool)
        # Anki-due cards first, then the rest of the pool, then misses
        for pool in ([c for c in unseen if c in self.due_ids],
                     unseen,
                     self.wrong_queue):
            pool = exclude(pool)
            if pool:
                return choose(pool)

        if all_unseen:
            pool = exclude(all_unseen[:self.pool_size]) or all_unseen[:self.pool_size]
            return choose(pool)
        # Whole deck seen — start over
        print("[Hanafuda] Full deck seen (%d cards). Restarting." % len(self.all_ids))
        self.seen = set()
        self.wrong_queue = []
        self.block = []
        if self.shuffle_mode == SHUFFLE_DECK:
            random.shuffle(self.all_ids)
        pool = exclude(self.all_ids) or self.all_ids
        return choose(pool) if pool else None

    def record_correct(self, card_id):
        note_id = self.card_to_note.get(card_id)
        siblings = self.note_to_cards.get(note_id, [card_id]) if note_id else [card_id]
        for cid in siblings:
            self.seen.add(cid)
            if cid in self.wrong_queue:
                self.wrong_queue.remove(cid)
        self.pending = None

    def record_wrong(self, card_id):
        if card_id not in self.wrong_queue:
            self.wrong_queue.append(card_id)
        self.pending = None

    @property
    def stats(self):
        return "seen %d/%d, missed queue %d" % (
            len(self.seen), len(self.all_ids), len(self.wrong_queue))


def deck_card_rows(col, deck_id=None):
    """
    One fast DB query for the deck's cards (subdecks included, suspended
    cards excluded). Rows are (card_id, note_id), in deck order.
    Uses deck IDs rather than a name search, so deck names containing
    quotes, underscores or asterisks can't break the lookup.
    """
    if deck_id is not None:
        dids = col.decks.deck_and_child_ids(deck_id)
        if not dids:
            return []
        id_list = ",".join(str(int(d)) for d in dids)
        sql = ("select id, nid from cards where did in (%s) and queue != -1 "
               "order by nid, ord" % id_list)
    else:
        sql = "select id, nid from cards where queue != -1 order by nid, ord"
    return col.db.all(sql)


def get_field_names(col, deck_id=None):
    """Field names of the most common note type in the deck."""
    try:
        if deck_id is not None:
            dids = col.decks.deck_and_child_ids(deck_id)
            id_list = ",".join(str(int(d)) for d in dids) or "0"
            sql = ("select n.mid, count(*) from cards c join notes n on c.nid = n.id "
                   "where c.did in (%s) group by n.mid order by count(*) desc limit 1" % id_list)
        else:
            sql = ("select n.mid, count(*) from cards c join notes n on c.nid = n.id "
                   "group by n.mid order by count(*) desc limit 1")
        row = col.db.first(sql)
        if not row:
            return []
        model = col.models.get(row[0])
        return [f['name'] for f in model['flds']] if model else []
    except Exception as e:
        print("[Hanafuda] get_field_names error: %s" % e)
        return []


def get_decks(col):
    decks = []
    for deck in col.decks.all_names_and_ids():
        decks.append({'id': deck.id, 'name': deck.name})
    return sorted(decks, key=lambda d: d['name'])


def build_session(col, deck_id=None, shuffle_mode=SHUFFLE_IN_POOL, focus=2, pool_size=20):
    try:
        rows = deck_card_rows(col, deck_id)
        if not rows:
            return None
        all_card_ids = [r[0] for r in rows]
        card_to_note = {r[0]: r[1] for r in rows}
        in_deck = set(all_card_ids)
        due_ids = set(c for c in col.find_cards('is:due') if c in in_deck)
        # One card per note, keeping deck order
        seen_notes = set()
        deduped = []
        for cid, nid in rows:
            if nid not in seen_notes:
                seen_notes.add(nid)
                deduped.append(cid)
        size = max(5, min(int(pool_size), len(deduped))) if deduped else 5
        print("[Hanafuda] New session: %d notes (%d cards), %d due, pool %d, %s"
              % (len(deduped), len(all_card_ids), len(due_ids), size,
                 ["deck order", "deck order, shuffled", "random from deck"][shuffle_mode]))
        return VocabSession(deduped, due_ids, card_to_note, all_card_ids,
                            shuffle_mode=shuffle_mode, focus=focus, pool_size=size)
    except Exception as e:
        print("[Hanafuda] build_session error: %s" % e)
        return None


def get_challenge(col, session, resolver, n_choices=4):
    if session is None or not session.all_card_ids:
        return None
    all_ids = session.all_card_ids
    if len(all_ids) < n_choices:
        print("[Hanafuda] Not enough cards: %d" % len(all_ids))
        return None

    target_id = None
    question = ''
    correct = ''
    tried = set()
    for _ in range(min(25, len(session.all_ids))):
        cid = session.pick()
        if cid is None:
            break
        if cid in tried:
            session.seen.add(cid)
            continue
        tried.add(cid)
        try:
            q, a = resolver.qa(col.get_card(cid).note())
            if _is_usable(q) and _is_usable(a):
                target_id, question, correct = cid, q, a
                break
            print("[Hanafuda] Card %s unusable: q=%r a=%r" % (cid, q[:30], a[:30]))
            session.seen.add(cid)
        except Exception as e:
            print("[Hanafuda] Card %s error: %s" % (cid, e))
            session.seen.add(cid)

    if target_id is None:
        for cid in random.sample(all_ids, min(50, len(all_ids))):
            try:
                q, a = resolver.qa(col.get_card(cid).note())
                if _is_usable(q) and _is_usable(a):
                    target_id, question, correct = cid, q, a
                    session.last_id = cid
                    break
            except Exception:
                continue
    if target_id is None:
        print("[Hanafuda] No usable card found")
        return None

    # Wrong choices from other notes in the deck
    target_nid = session.card_to_note.get(target_id)
    other_ids = [c for c in all_ids
                 if c != target_id and session.card_to_note.get(c) != target_nid]
    random.shuffle(other_ids)
    wrong = []
    for cid in other_ids[:200]:
        if len(wrong) >= n_choices - 1:
            break
        try:
            _, ans = resolver.qa(col.get_card(cid).note())
            if _is_usable(ans) and ans != correct and ans not in wrong:
                wrong.append(ans)
        except Exception:
            continue
    if len(wrong) < n_choices - 1:
        print("[Hanafuda] Not enough distinct answers: %d" % len(wrong))
        return None

    choices = wrong + [correct]
    random.shuffle(choices)
    print("[Hanafuda] Challenge (%s): Q=%r A=%r" % (session.stats, question[:30], correct[:30]))
    return {
        'question': question,
        'answer': correct,
        'choices': choices,
        'card_id': target_id,
        'note_id': target_nid or 0,
        'is_due': target_id in session.due_ids,
    }


def card_is_due(col, card_id):
    try:
        return bool(col.find_cards("cid:%d is:due" % int(card_id)))
    except Exception:
        return False


def record_answer(col, card_id, ease, mode=RECORD_DUE_ONLY, shown_at=None):
    """
    Submit an answer to Anki's scheduler, depending on the record mode:
      0 Off       — never touch Anki
      1 Due only  — only cards Anki already has due today
      2 All       — every card (new cards enter learning, early reviews count)
    Returns 'recorded', 'skipped', or 'error'.
    """
    if mode == RECORD_OFF:
        return 'skipped'
    try:
        if mode == RECORD_DUE_ONLY and not card_is_due(col, card_id):
            return 'skipped'
        card = col.get_card(card_id)
        card.start_timer()
        if shown_at:
            # Count the time since the question appeared as the answer time
            card.timer_started = shown_at
        col.sched.answerCard(card, int(ease))
        print("[Hanafuda] Recorded: card=%s ease=%s" % (card_id, ease))
        return 'recorded'
    except Exception as e:
        print("[Hanafuda] record_answer failed: %s" % e)
        return 'error'
