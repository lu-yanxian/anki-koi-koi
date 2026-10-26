"""
game_window.py — PyQt6/5 QDialog hosting the Hanafuda game via QWebEngineView.

Bridge rule of thumb: every ankiBridge.X() call in index.html must have a
matching @pyqtSlot here, or the whole QWebChannel silently fails.
"""

import json
import os
import time

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLabel,
    QWidget, pyqtSlot, Qt
)

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEngineScript
    from PyQt6.QtWebChannel import QWebChannel
    from PyQt6.QtCore import QObject, pyqtSignal, QUrl, QFile, QIODevice
    PYQT6 = True
except ImportError:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineScript
    from PyQt5.QtWebChannel import QWebChannel
    from PyQt5.QtCore import QObject, pyqtSignal, QUrl, QFile, QIODevice
    PYQT6 = False

from .vocab_bridge import (
    get_decks, get_challenge, get_field_names, build_session,
    auto_detect_fields, record_answer, FieldResolver, RECORD_DUE_ONLY,
    deck_card_rows,
)

ADDON_DIR = os.path.dirname(__file__)
WEB_DIR = os.path.join(ADDON_DIR, "web")

DEFAULT_CONFIG = {"settings": {}, "last_deck": None, "field_overrides": {}}


class AnkiBridge(QObject):
    challengeReady = pyqtSignal(str)
    decksReady     = pyqtSignal(str)
    answerRecorded = pyqtSignal(bool)
    fieldsReady    = pyqtSignal(str)

    def __init__(self, mw, parent=None):
        super().__init__(parent)
        self._mw = mw
        self._col = mw.col
        self._deck_id = None
        self._field_names = []
        self._resolver = FieldResolver()
        self._session = None
        self._shown_at = {}
        self.recorded_any = False
        self._addon = None
        try:
            self._addon = mw.addonManager.addonFromModule(__name__)
        except Exception:
            pass
        self._config = self._load_config()

    # ── Config persistence ───────────────────────────────────────────────
    def _load_config(self):
        conf = None
        try:
            if self._addon:
                conf = self._mw.addonManager.getConfig(self._addon)
        except Exception as e:
            print("[Hanafuda] getConfig error: %s" % e)
        conf = dict(conf or {})
        for k, v in DEFAULT_CONFIG.items():
            if k not in conf or conf[k] is None and v is not None:
                conf[k] = json.loads(json.dumps(v))
        if not isinstance(conf.get("settings"), dict):
            conf["settings"] = {}
        if not isinstance(conf.get("field_overrides"), dict):
            conf["field_overrides"] = {}
        return conf

    def _write_config(self):
        try:
            if self._addon:
                self._mw.addonManager.writeConfig(self._addon, self._config)
        except Exception as e:
            print("[Hanafuda] writeConfig error: %s" % e)

    def _setting(self, key, default):
        return self._config["settings"].get(key, default)

    def _shuffle_mode(self):
        s = self._config["settings"]
        if "shuffleMode" in s:
            return max(0, min(2, int(s["shuffleMode"])))
        if "shufflePool" in s:  # older on/off setting: on = random from deck
            return 2 if s["shufflePool"] else 0
        return 1

    def _focus_level(self):
        s = self._config["settings"]
        if "focusLevel" in s:
            return max(0, min(4, int(s["focusLevel"])))
        if "focus" in s:        # older 3-step slider: New/Balanced/Review
            return {0: 0, 1: 2, 2: 4}.get(int(s["focus"]), 2)
        return 2

    def last_deck(self):
        return self._config.get("last_deck")

    def _deck_key(self):
        return str(self._deck_id) if self._deck_id is not None else "all"

    # ── Session ──────────────────────────────────────────────────────────
    def _reset_session(self):
        self._session = build_session(
            self._col, self._deck_id,
            shuffle_mode=self._shuffle_mode(),
            focus=self._focus_level(),
            pool_size=int(self._setting("poolSize", 20)),
        )
        self._shown_at = {}

    def _apply_session_settings(self):
        """Push saved pool settings into the live session without rebuilding."""
        if not self._session:
            return
        self._session.focus = self._focus_level()
        size = int(self._setting("poolSize", 20))
        self._session.pool_size = max(5, min(size, len(self._session.all_ids)))

    # ── Slots called from JS ─────────────────────────────────────────────
    @pyqtSlot()
    def requestDecks(self):
        try:
            self.decksReady.emit(json.dumps(get_decks(self._col)))
        except Exception as e:
            print("[Hanafuda] requestDecks error: %s" % e)
            self.decksReady.emit(json.dumps([]))

    @pyqtSlot(int)
    def setDeck(self, deck_id):
        self._deck_id = deck_id if deck_id != -1 else None
        self._config["last_deck"] = deck_id
        self._write_config()
        self._field_names = get_field_names(self._col, self._deck_id)
        self._build_resolver()
        self._reset_session()
        self._emit_fields()

    @pyqtSlot()
    def newGameStarted(self):
        self._reset_session()
        print("[Hanafuda] Session reset for new game")

    @pyqtSlot()
    def requestFields(self):
        self._emit_fields()

    @pyqtSlot(result=str)
    def getSettings(self):
        return json.dumps(self._config.get("settings", {}))

    @pyqtSlot(str)
    def saveSettings(self, json_str):
        try:
            data = json.loads(json_str)
            if not isinstance(data, dict):
                return
            old_mode = self._shuffle_mode()
            self._config["settings"].update(data)
            self._write_config()
            # Shuffle changes the pool order itself, so rebuild; other pool
            # settings apply to the current session immediately
            if old_mode != self._shuffle_mode():
                self._reset_session()
            else:
                self._apply_session_settings()
        except Exception as e:
            print("[Hanafuda] saveSettings error: %s" % e)

    @pyqtSlot(int, int)
    def setFieldConfig(self, q_idx, a_idx):
        """Manual field override for the current deck (-1, -1 = auto)."""
        key = self._deck_key()
        names = self._field_names
        if q_idx < 0 or a_idx < 0 or q_idx >= len(names) or a_idx >= len(names):
            self._config["field_overrides"].pop(key, None)
        else:
            self._config["field_overrides"][key] = {"q": names[q_idx], "a": names[a_idx]}
        self._write_config()
        self._build_resolver()
        print("[Hanafuda] Field config for %s: %s" % (key, self._config["field_overrides"].get(key, "auto")))

    @pyqtSlot(int)
    def setSessionFocus(self, focus):
        self._config["settings"]["focusLevel"] = int(focus)
        self._apply_session_settings()

    @pyqtSlot(int)
    def setPoolSize(self, size):
        self._config["settings"]["poolSize"] = int(size)
        self._apply_session_settings()

    @pyqtSlot()
    def requestChallenge(self):
        try:
            if self._session is None:
                self._reset_session()
            challenge = get_challenge(self._col, self._session, self._resolver)
            if challenge is None:
                self.challengeReady.emit(json.dumps({'error': 'not_enough_cards'}))
            else:
                self._shown_at[challenge['card_id']] = time.time()
                self.challengeReady.emit(json.dumps(challenge))
        except Exception as e:
            print("[Hanafuda] requestChallenge error: %s" % e)
            self.challengeReady.emit(json.dumps({'error': str(e)}))

    @pyqtSlot(int, int)
    def recordAnswer(self, card_id, ease):
        """
        ease 1 = Again (missed), 2 = Hard, 3 = Good, 4 = Easy.
        In-game: Again/Hard bring the card back soon; Good/Easy move on.
        Whether Anki's schedule is touched depends on the Record setting.
        """
        try:
            if self._session:
                if ease in (1, 2):
                    self._session.record_wrong(card_id)
                else:
                    self._session.record_correct(card_id)
            mode = int(self._setting("recordMode", RECORD_DUE_ONLY))
            result = record_answer(self._col, card_id, ease, mode,
                                   self._shown_at.pop(card_id, None))
            if result == 'recorded':
                self.recorded_any = True
            self.answerRecorded.emit(result != 'error')
        except Exception as e:
            print("[Hanafuda] recordAnswer error: %s" % e)
            self.answerRecorded.emit(False)

    # ── Helpers ──────────────────────────────────────────────────────────
    def _build_resolver(self):
        ov = self._config["field_overrides"].get(self._deck_key())
        if ov and ov.get("q") in self._field_names and ov.get("a") in self._field_names:
            self._resolver = FieldResolver(ov["q"], ov["a"])
        else:
            self._resolver = FieldResolver()

    def _emit_fields(self):
        try:
            names = self._field_names
            auto_q, auto_a = auto_detect_fields(names) if names else (-1, -1)
            ov = self._config["field_overrides"].get(self._deck_key())
            override = bool(ov and ov.get("q") in names and ov.get("a") in names)
            q = names.index(ov["q"]) if override else auto_q
            a = names.index(ov["a"]) if override else auto_a
            deck_size = len(self._session.all_ids) if self._session else 0
            self.fieldsReady.emit(json.dumps({
                'fields': names, 'auto_q': auto_q, 'auto_a': auto_a,
                'q': q, 'a': a, 'override': override, 'deck_size': deck_size,
            }))
        except Exception as e:
            print("[Hanafuda] _emit_fields error: %s" % e)
            self.fieldsReady.emit(json.dumps({'fields': []}))


class HanafudaWindow(QDialog):
    def __init__(self, mw):
        super().__init__(mw)
        self.mw = mw
        self.setWindowTitle("🌸 Hanafuda Koi-Koi")
        # Fit within the visible screen area so the taskbar doesn't cover it
        from aqt.qt import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.resize(min(980, geo.width()), min(860, int(geo.height() * 0.95)))
        else:
            self.resize(980, 800)
        self.setMinimumSize(800, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        bar = QWidget()
        bar.setFixedHeight(44)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(12, 6, 12, 6)
        bar_layout.addWidget(QLabel("Deck for vocab challenges:"))
        self.deck_combo = QComboBox()
        self.deck_combo.setMinimumWidth(260)
        bar_layout.addWidget(self.deck_combo)
        bar_layout.addStretch()
        layout.addWidget(bar)

        self.web = QWebEngineView()
        settings = self.web.settings()
        if PYQT6:
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False)
        else:
            settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
            settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

        self._inject_qwebchannel()

        self.channel = QWebChannel()
        self.bridge = AnkiBridge(self.mw)
        self.channel.registerObject("ankiBridge", self.bridge)
        self.web.page().setWebChannel(self.channel)

        self.web.load(QUrl.fromLocalFile(os.path.join(WEB_DIR, "index.html")))
        layout.addWidget(self.web)

        self._populate_decks()
        self.deck_combo.currentIndexChanged.connect(self._on_deck_changed)

    def _inject_qwebchannel(self):
        try:
            f = QFile(":/qtwebchannel/qwebchannel.js")
            open_mode = (QIODevice.OpenModeFlag.ReadOnly if PYQT6 else QIODevice.ReadOnly)
            if f.open(open_mode):
                js_code = bytes(f.readAll()).decode('utf-8')
                f.close()
            else:
                with open(os.path.join(WEB_DIR, "qwebchannel.js"), 'r', encoding='utf-8') as bf:
                    js_code = bf.read()
            script = QWebEngineScript()
            script.setName("qwebchannel")
            script.setSourceCode(js_code)
            if PYQT6:
                script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
                script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
            else:
                script.setInjectionPoint(QWebEngineScript.DocumentCreation)
                script.setWorldId(QWebEngineScript.MainWorld)
            script.setRunsOnSubFrames(False)
            self.web.page().scripts().insert(script)
        except Exception as e:
            print("[Hanafuda] qwebchannel injection error: %s" % e)

    def _populate_decks(self):
        """Fill the deck list and reopen the deck used last time."""
        try:
            self.deck_combo.addItem("All decks", -1)
            for d in get_decks(self.mw.col):
                self.deck_combo.addItem(d["name"], d["id"])
            last = self.bridge.last_deck()
            idx = self.deck_combo.findData(last) if last is not None else -1
            if idx < 0:
                # No saved deck: start on the first deck that has cards
                # (skipping e.g. an empty "Default" deck)
                idx = 0
                for i in range(1, self.deck_combo.count()):
                    if deck_card_rows(self.mw.col, int(self.deck_combo.itemData(i))):
                        idx = i
                        break
            self.deck_combo.setCurrentIndex(idx)
            self.bridge.setDeck(int(self.deck_combo.itemData(idx)))
        except Exception as e:
            print("[Hanafuda] _populate_decks error: %s" % e)

    def _on_deck_changed(self, index):
        deck_id = self.deck_combo.itemData(index)
        if deck_id is not None:
            self.bridge.setDeck(int(deck_id))

    def keyPressEvent(self, event):
        # Don't let Esc close the game mid-round
        esc = Qt.Key.Key_Escape if PYQT6 else Qt.Key_Escape
        if event.key() == esc:
            event.ignore()
            return
        super().keyPressEvent(event)

    def done(self, result):
        # Refresh Anki's main screen so due counts reflect answers made here
        try:
            if self.bridge.recorded_any:
                self.mw.reset()
        except Exception:
            pass
        super().done(result)
