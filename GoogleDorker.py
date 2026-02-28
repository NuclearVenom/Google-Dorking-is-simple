"""
Google Dork Query Builder  -  PyQt5  (smart operators)
======================================================
Install:  pip install PyQt5
Run:      python google_dorker.py

How operators work
------------------
Every filter row has its own mini-toolbar that modifies THAT token:

  [-]  Exclude   → -site:google.com        (prepend minus to whole token)
  [+]  Require   → +intext:password        (prepend plus  to whole token)
  [" ] Exact     → intitle:"index of"      (wrap value in quotes)
  [~]  Synonym   → intext:~hack            (prepend ~ to value)
  [*]  Wildcard  → site:*.com              (append * to value / value becomes *)

Per-row GROUP selector  (radio: None / A / B)
  Active rows in Group A are wrapped together:  (token1 token2)
  Active rows in Group B are wrapped together:  (token3 token4)
  Groups are joined by the Group Join operator (AND / OR).
  Un-grouped tokens are joined by the Default Join (AND / OR).

Base query is always prepended as-is.
"""

import sys, webbrowser, urllib.parse
from PyQt5.QtCore    import Qt, QTimer, pyqtSignal
from PyQt5.QtGui     import QFont, QColor, QPalette, QCursor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QFrame,
    QStatusBar, QSplitter, QButtonGroup, QRadioButton,
    QSizePolicy, QToolTip, QComboBox,
)

# ── Palette ────────────────────────────────────────────────────────────────────
C = {
    "bg":           "#11111b",
    "bg2":          "#1e1e2e",
    "bg3":          "#2a2a3d",
    "bg4":          "#313244",
    "border":       "#585b70",
    "border_hi":    "#7c6af7",
    "accent":       "#7c6af7",
    "accent_dk":    "#5a4fcf",
    "accent_lt":    "#9d8fff",
    "fg":           "#ffffff",
    "fg2":          "#cdd6f4",
    "fg3":          "#a6adc8",
    "green":        "#a6e3a1",
    "green_bg":     "#1a3d2e",
    "red":          "#f38ba8",
    "red_bg":       "#3d1a23",
    "yellow":       "#f9e2af",
    "yellow_bg":    "#3d3217",
    "prefix":       "#cba6f7",
    "grp_a":        "#89dceb",   # teal
    "grp_a_bg":     "#0d2d33",
    "grp_b":        "#fab387",   # peach
    "grp_b_bg":     "#33200d",
}

GLOBAL_SS = f"""
QWidget {{
    background: {C['bg']};
    color: {C['fg']};
    font-family: "Segoe UI","SF Pro Display","Helvetica Neue",Arial,sans-serif;
    font-size: 13px;
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {C['bg2']}; width: 8px; border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C['border']}; border-radius: 4px; min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QLineEdit {{
    background: {C['bg4']}; color: {C['fg']};
    border: 1.5px solid {C['border']}; border-radius: 6px;
    padding: 5px 10px; font-size: 13px;
    selection-background-color: {C['accent']};
}}
QLineEdit:focus  {{ border: 1.5px solid {C['border_hi']}; background: #2e2e47; }}
QLineEdit:hover  {{ border: 1.5px solid {C['fg3']}; }}
QLineEdit[readOnly="true"] {{
    background: {C['green_bg']}; color: {C['green']};
    border: 1.5px solid #2a5c42;
    font-family: "Cascadia Code","Fira Code","Consolas",monospace;
    font-weight: bold; font-size: 13px;
}}
QToolTip {{
    background: #2a2a3d; color: {C['fg']};
    border: 1px solid {C['border_hi']};
    border-radius: 5px; padding: 6px 10px; font-size: 12px;
}}
QStatusBar {{
    background: {C['bg2']}; color: {C['fg3']};
    font-size: 12px; border-top: 1px solid {C['border']};
}}
QSplitter::handle {{ background: {C['border']}; }}
QComboBox {{
    background: {C['bg3']}; color: {C['fg']};
    border: 1px solid {C['border']}; border-radius: 5px;
    padding: 3px 8px; font-size: 12px;
}}
QComboBox:hover {{ border-color: {C['accent_lt']}; }}
QComboBox QAbstractItemView {{
    background: {C['bg3']}; color: {C['fg']};
    selection-background-color: {C['accent_dk']};
    border: 1px solid {C['border_hi']};
}}
"""

# ── Filter data ────────────────────────────────────────────────────────────────
FILTERS = [
    ("allintext",       "allintext:",       "All keywords must appear in page body text",           '"login password"'),
    ("intext",          "intext:",          "At least one keyword appears in page text",             '"admin panel"'),
    ("inurl",           "inurl:",           "Keyword appears somewhere in the URL",                  "login"),
    ("allinurl",        "allinurl:",        "All keywords must appear in the URL",                   "admin login"),
    ("intitle",         "intitle:",         "Keyword appears in the page title tag",                 '"index of"'),
    ("allintitle",      "allintitle:",      "All keywords must appear in the title",                 "admin login panel"),
    ("site",            "site:",            "Restrict results to a specific domain / site",          "example.com"),
    ("filetype",        "filetype:",        "Match a specific file type extension",                  "pdf"),
    ("ext",             "ext:",             "Alternative to filetype — matches file extension",      "sql"),
    ("link",            "link:",            "Pages that have an external link to this URL",          "example.com"),
    ("numrange",        "numrange:",        "Search within a numeric range",                         "1000-9999"),
    ("before",          "before:",          "Results published before this date (YYYY-MM-DD)",       "2023-01-01"),
    ("after",           "after:",           "Results published after this date (YYYY-MM-DD)",        "2020-01-01"),
    ("inanchor",        "inanchor:",        "Keyword appears in anchor/link text pointing to page",  '"click here"'),
    ("allinanchor",     "allinanchor:",     "All keywords appear in anchor texts",                   "free download"),
    ("inpostauthor",    "inpostauthor:",    "Blog posts written by a specific author",               '"John Doe"'),
    ("allinpostauthor", "allinpostauthor:", "All keywords in the blog post-author field",            "security researcher"),
    ("related",         "related:",         "Find pages similar / related to the given URL",         "nytimes.com"),
    ("cache",           "cache:",           "View Google's cached snapshot of a page",               "example.com"),
]

# Preset format:
#   (display_name, description, default_join, group_join, row_states_dict)
#   row_states_dict keys: filter name or "base"
#   row value tuple: (value, exclude, require, exact, wildcard, group)
#   default_join / group_join: "AND" or "OR"
PRESETS = [
    # ── Basic ────────────────────────────────────────────────────────────────
    ("📂 Open Directories",
     "Find open directory listings — classic entry point for exposed files.",
     "AND", "AND",
     {"intitle": ("index of", False, False, True,  False, "N"),
      "base":    "parent directory"}),

    ("⚙️  Config Files",
     "Exposed web server config files with FTP credentials.",
     "AND", "AND",
     {"filetype": ("config", False, False, False, False, "N"),
      "inurl":    ("web.config", False, False, True, False, "N")}),

    ("📄 Exposed PDFs on .gov",
     "Confidential PDFs hosted on government domains.",
     "AND", "AND",
     {"filetype": ("pdf",          False, False, False, False, "N"),
      "intext":   ("confidential", False, False, True,  False, "N"),
      "site":     ("gov",          False, False, False, False, "N")}),

    ("🔐 Login Panels",
     "Find admin / login pages exposed on the web.",
     "AND", "AND",
     {"intitle": ("admin login",  False, False, True,  False, "N"),
      "inurl":   ("admin",        False, False, False, False, "N")}),

    ("🗄️  SQL Backup Files",
     "Exposed SQL dump or backup files.",
     "AND", "AND",
     {"ext":   ("sql",    False, False, False, False, "N"),
      "inurl": ("backup", False, False, False, False, "N")}),

    ("📊 Excel Sheets with Passwords",
     "Excel files containing the word 'password'.",
     "AND", "AND",
     {"filetype": ("xlsx",     False, False, False, False, "N"),
      "intext":   ("password", False, False, True,  False, "N")}),

    ("📸 Exposed Webcams",
     "Publicly accessible webcam interfaces.",
     "AND", "AND",
     {"intitle": ("webcam",         False, False, True,  False, "N"),
      "inurl":   ("view/index.shtml", False, False, True, False, "N")}),

    ("🔑 Private SSH Keys",
     "Accidentally published RSA/SSH private key files.",
     "AND", "AND",
     {"ext":    ("pem",              False, False, False, False, "N"),
      "intext": ("PRIVATE KEY", False, False, True,  False, "N")}),

    ("📰 Recent Security Research",
     "Blog posts or papers about vulnerabilities published after 2023.",
     "AND", "AND",
     {"base":  "vulnerability research",
      "inurl": ("blog", False, False, False, False, "N"),
      "after": ("2023-01-01", False, False, False, False, "N")}),

    ("🧑‍💻 GitHub Exposed Tokens",
     "Find pages referencing API tokens or secrets on GitHub-related sites.",
     "AND", "AND",
     {"site":   ("github.com",  False, False, False, False, "N"),
      "intext": ("api_key",     False, False, True,  False, "N")}),

    # ── Intermediate ─────────────────────────────────────────────────────────
    ("📁 Docs with Salary Info",
     "Office documents containing salary or budget data — marked confidential.",
     "AND", "AND",
     {"ext":    ("doc",         False, False, False, False, "N"),
      "intext": ("salary",      False, False, True,  False, "N"),
      "inurl":  ("confidential",False, False, False, False, "N")}),

    ("🌐 WordPress Login Pages",
     "Exposed WordPress admin login pages (excluding wp.com itself).",
     "AND", "AND",
     {"inurl":  ("wp-login.php", False, False, False, False, "N"),
      "site":   ("wordpress.com", True, False, False, False, "N")}),

    ("🗂️  Exposed ENV Files",
     ".env files that may contain DB passwords or API secrets.",
     "AND", "AND",
     {"ext":    ("env",      False, False, False, False, "N"),
      "intext": ("DB_PASS",  False, False, True,  False, "N")}),

    ("📋 phpMyAdmin Panels",
     "Exposed phpMyAdmin database management interfaces.",
     "AND", "AND",
     {"intitle": ("phpMyAdmin",      False, False, True,  False, "N"),
      "inurl":   ("phpmyadmin/index", False, False, False, False, "N")}),

    ("🎵 Open Music Directories",
     "Open directory listings with audio files — no indexing sites.",
     "AND", "AND",
     {"intitle":  ("index of",  False, False, True,  False, "N"),
      "inurl":    ("mp3",        False, False, False, False, "N"),
      "site":     ("info",       True,  False, False, False, "N")}),

    # ── Complex — grouped with OR / AND between groups ────────────────────────
    ("🔀 Login OR Register pages  [OR group]",
     "Pages that are either login OR registration panels — uses OR to combine "
     "two title variants into one group.",
     "AND", "OR",
     {"intitle": ("login",    False, False, True,  False, "A"),
      "inurl":   ("register", False, False, False, False, "A"),
      "site":    ("php",      False, False, False, False, "N")}),

    ("🏛️  Gov OR Edu confidential PDFs  [OR groups]",
     "Confidential PDFs on either .gov OR .edu domains — Group A holds the "
     "domain alternatives joined by OR; ungrouped filetype applies to both.",
     "AND", "OR",
     {"filetype": ("pdf",          False, False, False, False, "N"),
      "intext":   ("confidential", False, False, True,  False, "N"),
      "site":     ("gov",          False, False, False, False, "A"),
      "related":  ("edu",          False, False, False, False, "A")}),

    ("🔍 Exposed DB on Any TLD  [wildcard + group]",
     "Database backup files on any .com / .net / .org TLD — uses wildcard "
     "on site and OR-groups the file extensions.",
     "AND", "OR",
     {"site":     ("",      False, False, False, True,  "N"),
      "ext":      ("sql",   False, False, False, False, "A"),
      "filetype": ("db",    False, False, False, False, "A"),
      "inurl":    ("backup",False, False, False, False, "N")}),

    ("🧩 Admin Panel — Title OR URL  [OR group]",
     "Admin panels detected by EITHER a matching title OR a matching URL path — "
     "both detection methods grouped with OR, then AND-joined with site exclusion.",
     "AND", "OR",
     {"intitle": ("admin",        False, False, True,  False, "A"),
      "inurl":   ("admin/login",  False, False, False, False, "A"),
      "site":    ("example.com",  True,  False, False, False, "N")}),

    ("📦 Leaked Archives  [ext OR filetype group]",
     "Compressed archives that may contain leaked data — ext and filetype "
     "variants ORed together in Group A, content keyword ungrouped.",
     "AND", "OR",
     {"ext":      ("zip",      False, False, False, False, "A"),
      "filetype": ("tar.gz",   False, False, False, False, "A"),
      "intext":   ("password", False, False, True,  False, "N"),
      "inurl":    ("backup",   False, False, False, False, "N")}),

    ("🕵️  OSINT: Person on Social  [OR groups]",
     "Find a person mentioned across multiple social platforms — "
     "Group A = social sites (OR), Group B = professional sites (OR), "
     "groups joined by OR.",
     "AND", "OR",
     {"base":    "John Doe",
      "site":    ("twitter.com",  False, False, False, False, "A"),
      "inurl":   ("linkedin.com", False, False, False, False, "A"),
      "related": ("facebook.com", False, False, False, False, "B"),
      "intext":  ("profile",      False, False, False, False, "B")}),

    ("📡 IoT Device Panels  [title OR url, grouped]",
     "Exposed IoT / router admin interfaces — match either title keywords OR "
     "URL patterns, excluding major ISP homepages.",
     "AND", "OR",
     {"intitle":  ("router",          False, False, False, False, "A"),
      "intitle":  ("network camera",  False, False, True,  False, "A"),
      "inurl":    ("setup.cgi",        False, False, False, False, "B"),
      "inurl":    ("cgi-bin/webproc",  False, False, False, False, "B"),
      "site":     ("comcast.net",      True,  False, False, False, "N")}),

    ("📜 Sensitive Docs Excluding Known Sites  [exclude + exact]",
     "Exact-phrase confidential documents, excluding result noise from "
     "scribd and slideshare.",
     "AND", "AND",
     {"intext":   ("confidential salary", False, False, True,  False, "N"),
      "filetype": ("pdf",                 False, False, False, False, "N"),
      "site":     ("scribd.com",          True,  False, False, False, "N"),
      "related":  ("slideshare.net",      True,  False, False, False, "N")}),
]


# ── Helper widgets ─────────────────────────────────────────────────────────────
class Divider(QFrame):
    def __init__(self, p=None):
        super().__init__(p)
        self.setFrameShape(QFrame.HLine)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background:{C['border']}; border:none;")


class SecLabel(QLabel):
    def __init__(self, t, p=None):
        super().__init__(t, p)
        self.setStyleSheet(f"color:{C['accent_lt']};font-size:10px;font-weight:700;"
                           f"letter-spacing:1.6px;padding:2px 0;background:transparent;")


def _toggle_btn(text, tip, checked_color, parent=None):
    """Small square toggle button used in per-row operator toolbar."""
    b = QPushButton(text, parent)
    b.setCheckable(True)
    b.setFixedSize(26, 26)
    b.setCursor(QCursor(Qt.PointingHandCursor))
    b.setToolTip(tip)
    b.setStyleSheet(f"""
        QPushButton {{
            background:{C['bg4']}; color:{C['fg3']};
            border:1px solid {C['border']}; border-radius:4px;
            font-size:11px; font-weight:700; padding:0;
        }}
        QPushButton:hover   {{ border-color:{C['accent_lt']}; color:{C['fg']}; }}
        QPushButton:checked {{
            background:{checked_color}22;
            border:1.5px solid {checked_color};
            color:{checked_color};
        }}
    """)
    return b


def _radio_btn(text, color, tip):
    r = QRadioButton(text)
    r.setToolTip(tip)
    r.setCursor(QCursor(Qt.PointingHandCursor))
    r.setStyleSheet(f"""
        QRadioButton {{
            color:{C['fg3']}; font-size:11px; font-weight:700;
            spacing:3px; background:transparent;
        }}
        QRadioButton:hover {{ color:{color}; }}
        QRadioButton::indicator {{
            width:12px; height:12px; border-radius:6px;
            border:1.5px solid {C['border']};
            background:{C['bg4']};
        }}
        QRadioButton::indicator:checked {{
            background:{color}; border:1.5px solid {color};
        }}
    """)
    return r


# ── Per-row filter widget ──────────────────────────────────────────────────────
class FilterRow(QWidget):
    changed = pyqtSignal()

    def __init__(self, name, prefix, description, example, index, parent=None):
        super().__init__(parent)
        self.name   = name
        self.prefix = prefix
        self._bg    = C['bg3'] if index % 2 == 0 else C['bg2']
        self.setStyleSheet(f"background:{self._bg};")
        self.setToolTip(
            f"<span style='color:{C['prefix']};font-weight:700;"
            f"font-family:monospace;'>{prefix}</span>"
            f"<br><span style='color:{C['fg2']};'>{description}</span>"
            f"<br><br><span style='color:{C['yellow']};'>Example: </span>"
            f"<span style='color:{C['green']};font-family:monospace;'>"
            f"{prefix}{example}</span>"
        )

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 5, 10, 5)
        outer.setSpacing(6)

        # ── prefix label ──────────────────────────────────────────────────────
        plbl = QLabel(prefix)
        plbl.setFixedWidth(162)
        plbl.setStyleSheet(f"color:{C['prefix']};font-family:'Cascadia Code',"
                           f"'Fira Code','Consolas',monospace;font-size:11px;"
                           f"font-weight:700;background:transparent;")
        outer.addWidget(plbl)

        # ── text input ────────────────────────────────────────────────────────
        self.field = QLineEdit()
        self.field.setPlaceholderText(example)
        self.field.setFixedHeight(30)
        self.field.textChanged.connect(self.changed)
        outer.addWidget(self.field, 1)

        # ── per-row operator toggles ───────────────────────────────────────────
        # Each toggle directly modifies how THIS token is rendered in the query.

        self.btn_exclude  = _toggle_btn("−",  "EXCLUDE: prepend − so Google omits this token\n"
                                              "  e.g.  -site:facebook.com", C['red'])
        self.btn_require  = _toggle_btn("+",  "REQUIRE: prepend + to force this term\n"
                                              "  e.g.  +intext:password", C['green'])
        self.btn_exact    = _toggle_btn("\" ","EXACT PHRASE: wrap value in quotes\n"
                                              "  e.g.  intitle:\"index of\"", C['yellow'])
        self.btn_synonym  = _toggle_btn("~",  "SYNONYM: prefix ~ so Google also finds synonyms\n"
                                              "  e.g.  intext:~hack  →  also: crack, exploit…", C['accent_lt'])
        self.btn_wildcard = _toggle_btn("∗",  "WILDCARD: replace / append * (unknown word)\n"
                                              "  e.g.  site:*.com  or  intitle:* login", C['yellow'])

        # Exclude and Require are mutually exclusive
        self.btn_exclude.toggled.connect(lambda c: self.btn_require.setChecked(False) if c else None)
        self.btn_require.toggled.connect(lambda c: self.btn_exclude.setChecked(False) if c else None)

        for b in (self.btn_exclude, self.btn_require, self.btn_exact,
                  self.btn_synonym, self.btn_wildcard):
            b.toggled.connect(lambda _: self.changed.emit())
            outer.addWidget(b)

        # ── group selector (None / A / B) ─────────────────────────────────────
        sep = QLabel("|")
        sep.setStyleSheet(f"color:{C['border']};background:transparent;font-size:14px;")
        outer.addWidget(sep)

        self._grp_group = QButtonGroup(self)

        self.r_none = _radio_btn("·",  C['fg3'],    "No group — joins with default AND/OR")
        self.r_a    = _radio_btn("A",  C['grp_a'],  "Add to Group A  (tokens wrapped in parentheses together)")
        self.r_b    = _radio_btn("B",  C['grp_b'],  "Add to Group B  (tokens wrapped in parentheses together)")

        self._grp_group.addButton(self.r_none, 0)
        self._grp_group.addButton(self.r_a,    1)
        self._grp_group.addButton(self.r_b,    2)
        self.r_none.setChecked(True)
        self._grp_group.buttonToggled.connect(lambda *_: self._on_group_change())

        for r in (self.r_none, self.r_a, self.r_b):
            outer.addWidget(r)

    def _on_group_change(self):
        gid = self._grp_group.checkedId()
        if gid == 1:
            self.setStyleSheet(f"background:{C['grp_a_bg']};border-left:3px solid {C['grp_a']};")
        elif gid == 2:
            self.setStyleSheet(f"background:{C['grp_b_bg']};border-left:3px solid {C['grp_b']};")
        else:
            self.setStyleSheet(f"background:{self._bg};")
        self.changed.emit()

    # ── public API ────────────────────────────────────────────────────────────
    def raw_value(self):
        return self.field.text().strip()

    def group(self):
        """Returns 'N', 'A', or 'B'."""
        return {0: "N", 1: "A", 2: "B"}[self._grp_group.checkedId()]

    def build_token(self):
        """
        Returns the fully-modified dork token for this row,
        or '' if the field is empty.
        """
        val = self.field.text().strip()
        if not val:
            return ""

        # 1. Wildcard toggle: if value is blank-ish or user wants full wildcard
        if self.btn_wildcard.isChecked():
            if "*" not in val:
                val = val + "*" if val else "*"

        # 2. Synonym toggle: prepend ~ to value (not to the prefix)
        if self.btn_synonym.isChecked():
            if not val.startswith("~"):
                val = "~" + val

        # 3. Exact toggle: wrap value in quotes (only if not already quoted)
        if self.btn_exact.isChecked():
            if not (val.startswith('"') and val.endswith('"')):
                val = f'"{val}"'
        else:
            # Auto-quote multi-word values that aren't already quoted
            if " " in val and not (val.startswith('"') and val.endswith('"')):
                val = f'"{val}"'

        # 4. Assemble prefix:value
        token = f"{self.prefix}{val}"

        # 5. Exclude / Require prefix on the whole token
        if self.btn_exclude.isChecked():
            token = f"-{token}"
        elif self.btn_require.isChecked():
            token = f"+{token}"

        return token

    def clear(self):
        self.field.clear()
        for b in (self.btn_exclude, self.btn_require, self.btn_exact,
                  self.btn_synonym, self.btn_wildcard):
            b.setChecked(False)
        self.r_none.setChecked(True)

    def set_state(self, val, exclude, require, exact, wildcard, group):
        self.field.setText(val)
        self.btn_exclude.setChecked(exclude)
        self.btn_require.setChecked(require)
        self.btn_exact.setChecked(exact)
        self.btn_wildcard.setChecked(wildcard)
        {"N": self.r_none, "A": self.r_a, "B": self.r_b}[group].setChecked(True)


# ── Main window ────────────────────────────────────────────────────────────────
class GoogleDorker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Google Dork Query Builder")
        self.resize(1150, 860)
        self.setMinimumSize(900, 620)
        self.setStyleSheet(GLOBAL_SS)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.addWidget(self._make_left())
        splitter.addWidget(self._make_right())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        root.addWidget(self._make_query_bar())

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready — fill in filters and apply operators per row to build your dork query.")

        self._update_query()

    # ── Header ─────────────────────────────────────────────────────────────────
    def _make_header(self):
        w = QWidget()
        w.setFixedHeight(66)
        w.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                        f"stop:0 {C['accent_dk']},stop:1 #3d1a7a);"
                        f"border-bottom:2px solid {C['accent']};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 8, 20, 6)
        lay.setSpacing(1)
        t1 = QLabel("🔍  Google Dork Query Builder")
        t1.setStyleSheet("color:#fff;font-size:18px;font-weight:700;background:transparent;")
        t2 = QLabel("Per-row operators  ·  Grouping with ( )  ·  OR / AND between groups  ·  Hover anything for help")
        t2.setStyleSheet(f"color:#d0caff;font-size:11px;background:transparent;")
        lay.addWidget(t1); lay.addWidget(t2)
        return w

    # ── Left panel: base query + filter rows ───────────────────────────────────
    def _make_left(self):
        outer = QWidget()
        outer.setStyleSheet(f"background:{C['bg']};")
        vlay = QVBoxLayout(outer)
        vlay.setContentsMargins(12, 12, 6, 12)
        vlay.setSpacing(8)

        # ── Base query ────────────────────────────────────────────────────────
        vlay.addWidget(SecLabel("BASE QUERY"))
        self.base_field = QLineEdit()
        self.base_field.setPlaceholderText("What you'd normally type in Google (free-form text, no operators)")
        self.base_field.setFixedHeight(38)
        self.base_field.setStyleSheet(f"""
            QLineEdit {{
                background:{C['bg4']}; color:{C['fg']};
                border:2px solid {C['border']}; border-radius:7px;
                padding:6px 12px; font-size:14px;
            }}
            QLineEdit:focus  {{ border:2px solid {C['accent']}; background:#252540; }}
            QLineEdit:hover  {{ border:2px solid {C['fg3']}; }}
        """)
        self.base_field.textChanged.connect(self._update_query)
        vlay.addWidget(self.base_field)

        vlay.addWidget(Divider())

        # ── Column headers ────────────────────────────────────────────────────
        hdr = QWidget()
        hdr.setStyleSheet(f"background:{C['bg']};")
        hlay = QHBoxLayout(hdr)
        hlay.setContentsMargins(10, 0, 10, 0)
        hlay.setSpacing(6)

        def _hdr(t, w=None, tip=""):
            l = QLabel(t)
            l.setStyleSheet(f"color:{C['fg3']};font-size:10px;font-weight:700;"
                            f"letter-spacing:1px;background:transparent;")
            l.setToolTip(tip)
            if w: l.setFixedWidth(w)
            return l

        hlay.addWidget(_hdr("FILTER PREFIX", 162))
        hlay.addWidget(_hdr("VALUE", 0), 1)
        hlay.addWidget(_hdr("−  +  \"  ~  ∗",  tip=(
            "Per-row operator toggles:\n"
            "  −  Exclude  → -prefix:value\n"
            "  +  Require  → +prefix:value\n"
            "  \"  Exact    → prefix:\"value\"\n"
            "  ~  Synonym  → prefix:~value\n"
            "  ∗  Wildcard → prefix:value*"
        )))
        hlay.addWidget(QLabel("|"))   # spacer
        hlay.addWidget(_hdr("GRP", tip=(
            "Grouping radio (·  A  B):\n"
            "All rows assigned to A are wrapped in (…) together.\n"
            "All rows assigned to B are wrapped in (…) together.\n"
            "A and B are joined by the Group Join operator (AND/OR).\n"
            "Un-grouped rows join with the Default Join (AND/OR)."
        )))
        vlay.addWidget(hdr)
        vlay.addWidget(Divider())

        # ── Scrollable filter list ────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"background:{C['bg']};border:none;")

        container = QWidget()
        container.setStyleSheet(f"background:{C['bg']};")
        clay = QVBoxLayout(container)
        clay.setContentsMargins(0, 0, 0, 0)
        clay.setSpacing(1)

        self.rows = {}
        for i, (name, prefix, desc, example) in enumerate(FILTERS):
            row = FilterRow(name, prefix, desc, example, i)
            row.changed.connect(self._update_query)
            self.rows[name] = row
            clay.addWidget(row)

        clay.addStretch(1)
        scroll.setWidget(container)
        vlay.addWidget(scroll, 1)
        return outer

    # ── Right panel: join controls + presets ───────────────────────────────────
    def _make_right(self):
        outer = QWidget()
        outer.setStyleSheet(f"background:{C['bg2']};border-left:1px solid {C['border']};")
        outer.setMinimumWidth(220)
        outer.setMaximumWidth(300)
        vlay = QVBoxLayout(outer)
        vlay.setContentsMargins(14, 14, 14, 14)
        vlay.setSpacing(10)

        # ── Default join ──────────────────────────────────────────────────────
        vlay.addWidget(SecLabel("DEFAULT JOIN"))
        vlay.addWidget(Divider())

        dj_info = QLabel(
            "How un-grouped active tokens are joined together."
        )
        dj_info.setWordWrap(True)
        dj_info.setStyleSheet(f"color:{C['fg3']};font-size:11px;background:transparent;")
        vlay.addWidget(dj_info)

        self.combo_default_join = self._join_combo(
            tip="AND (space) = all tokens must match\nOR ( | ) = any token can match"
        )
        vlay.addWidget(self.combo_default_join)

        vlay.addSpacing(6)

        # ── Group A ───────────────────────────────────────────────────────────
        ga_lbl = QLabel("●  Group A")
        ga_lbl.setStyleSheet(f"color:{C['grp_a']};font-size:12px;font-weight:700;background:transparent;")
        vlay.addWidget(ga_lbl)
        vlay.addWidget(Divider())

        ga_info = QLabel("Rows tagged A are wrapped:\n( tokenA1 tokenA2 … )")
        ga_info.setWordWrap(True)
        ga_info.setStyleSheet(f"color:{C['fg3']};font-size:11px;background:transparent;")
        vlay.addWidget(ga_info)

        # ── Group B ───────────────────────────────────────────────────────────
        gb_lbl = QLabel("●  Group B")
        gb_lbl.setStyleSheet(f"color:{C['grp_b']};font-size:12px;font-weight:700;background:transparent;")
        vlay.addWidget(gb_lbl)
        vlay.addWidget(Divider())

        gb_info = QLabel("Rows tagged B are wrapped:\n( tokenB1 tokenB2 … )")
        gb_info.setWordWrap(True)
        gb_info.setStyleSheet(f"color:{C['fg3']};font-size:11px;background:transparent;")
        vlay.addWidget(gb_info)

        # ── Group join ────────────────────────────────────────────────────────
        gj_lbl = QLabel("Group A  ⟷  Group B  Join")
        gj_lbl.setStyleSheet(f"color:{C['fg2']};font-size:11px;font-weight:700;background:transparent;")
        gj_lbl.setToolTip("How Group A and Group B are joined to each other\n"
                           "and to the remaining un-grouped tokens.")
        vlay.addWidget(gj_lbl)

        self.combo_group_join = self._join_combo(
            tip="Operator placed BETWEEN Group A and Group B blocks\n"
                "(and between those blocks and any un-grouped tokens)"
        )
        vlay.addWidget(self.combo_group_join)

        vlay.addSpacing(4)
        vlay.addWidget(Divider())

        # ── Presets header + clear ─────────────────────────────────────────────
        preset_hdr = QHBoxLayout()
        preset_hdr.setContentsMargins(0, 0, 0, 0)
        preset_hdr.addWidget(SecLabel("QUICK PRESETS"))
        preset_hdr.addStretch(1)
        clr = QPushButton("🗑 Clear")
        clr.setCursor(QCursor(Qt.PointingHandCursor))
        clr.setFixedHeight(22)
        clr.setToolTip("Clear all fields and reset operators")
        clr.setStyleSheet(f"""
            QPushButton {{
                background:{C['red_bg']}; color:{C['red']};
                border:1px solid #6b1a2e; border-radius:4px;
                font-weight:700; font-size:11px; padding:0 8px;
            }}
            QPushButton:hover {{ background:#5c1825; color:#fff; border-color:{C['red']}; }}
            QPushButton:pressed {{ background:{C['red']}; color:#11111b; }}
        """)
        clr.clicked.connect(self._clear_all)
        preset_hdr.addWidget(clr)
        hdr_w = QWidget()
        hdr_w.setStyleSheet("background:transparent;")
        hdr_w.setLayout(preset_hdr)
        vlay.addWidget(hdr_w)

        # ── Scrollable preset list ─────────────────────────────────────────────
        pscroll = QScrollArea()
        pscroll.setWidgetResizable(True)
        pscroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        pscroll.setStyleSheet(f"background:{C['bg2']}; border:1px solid {C['border']}; border-radius:6px;")

        pcontainer = QWidget()
        pcontainer.setStyleSheet("background:transparent;")
        play = QVBoxLayout(pcontainer)
        play.setContentsMargins(6, 6, 6, 6)
        play.setSpacing(4)

        _basic_header_done   = False
        _inter_header_done   = False
        _complex_header_done = False

        def _cat_label(text, color=None):
            cl = QLabel(text)
            col = color or C['fg3']
            cl.setStyleSheet(f"color:{col};font-size:10px;font-weight:700;"
                             f"letter-spacing:1px;background:transparent;padding:4px 0 2px 0;")
            return cl

        for pname, pdesc, pdj, pgj, pvals in PRESETS:
            if not _basic_header_done:
                _basic_header_done = True
                play.addWidget(_cat_label("── Basic ──"))

            if not _inter_header_done and pname.startswith("📁"):
                _inter_header_done = True
                play.addWidget(Divider())
                play.addWidget(_cat_label("── Intermediate ──"))

            if not _complex_header_done and "[" in pname:
                _complex_header_done = True
                play.addWidget(Divider())
                play.addWidget(_cat_label("── Complex (Grouped) ──", C['grp_a']))

            pb = QPushButton(f" {pname}")
            pb.setCursor(QCursor(Qt.PointingHandCursor))
            pb.setMinimumHeight(28)
            pb.setToolTip(
                f"<b>{pname}</b><br><br>{pdesc}<br><br>"
                f"<span style='color:{C['yellow']};'>Default join:</span> {pdj}&nbsp;&nbsp;"
                f"<span style='color:{C['yellow']};'>Group join:</span> {pgj}"
            )
            pb.setStyleSheet(f"""
                QPushButton {{
                    background:{C['bg3']}; color:{C['fg2']};
                    border:1px solid {C['border']}; border-radius:5px;
                    font-size:11px; text-align:left; padding:2px 8px;
                }}
                QPushButton:hover {{
                    background:{C['accent_dk']}; color:#fff;
                    border-color:{C['accent']};
                }}
                QPushButton:pressed {{ background:{C['accent']}; color:#fff; }}
            """)
            pb.clicked.connect(lambda _, dj=pdj, gj=pgj, pv=pvals: self._load_preset(dj, gj, pv))
            play.addWidget(pb)

        play.addStretch(1)
        pscroll.setWidget(pcontainer)
        vlay.addWidget(pscroll, 1)
        return outer

    def _join_combo(self, tip=""):
        cb = QComboBox()
        cb.addItem("AND  (space)  — all must match",  "AND")
        cb.addItem("OR   ( | )   — any can match",    "OR")
        cb.setToolTip(tip)
        cb.currentIndexChanged.connect(self._update_query)
        return cb

    # ── Query bar ──────────────────────────────────────────────────────────────
    def _make_query_bar(self):
        bar = QWidget()
        bar.setFixedHeight(70)
        bar.setStyleSheet(f"background:{C['bg2']};border-top:2px solid {C['border']};")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(10)

        lbl = QLabel("Query:")
        lbl.setFixedWidth(52)
        lbl.setStyleSheet(f"color:{C['fg3']};font-weight:700;font-size:12px;background:transparent;")
        lay.addWidget(lbl)

        self.query_field = QLineEdit()
        self.query_field.setReadOnly(True)
        self.query_field.setPlaceholderText("Your assembled dork query appears here…")
        self.query_field.setFixedHeight(44)
        lay.addWidget(self.query_field, 1)

        copy_btn = QPushButton("📋  Copy")
        copy_btn.setFixedSize(104, 44)
        copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        copy_btn.setToolTip("Copy query to clipboard")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background:{C['accent_dk']}; color:#fff;
                border:1.5px solid {C['accent']}; border-radius:7px;
                font-weight:700; font-size:13px;
            }}
            QPushButton:hover  {{ background:{C['accent']}; border-color:{C['accent_lt']}; }}
            QPushButton:pressed {{ background:{C['accent_dk']}; }}
        """)
        copy_btn.clicked.connect(self._copy_query)
        lay.addWidget(copy_btn)

        go_btn = QPushButton("🌐  Search in Browser")
        go_btn.setFixedHeight(44)
        go_btn.setCursor(QCursor(Qt.PointingHandCursor))
        go_btn.setToolTip("Open this dork query directly in Google via your default browser")
        go_btn.setStyleSheet(f"""
            QPushButton {{
                background:#1a4d2e; color:{C['green']};
                border:1.5px solid #2a6642; border-radius:7px;
                font-weight:700; font-size:13px; padding:0 20px;
            }}
            QPushButton:hover  {{ background:#236640; color:#fff; border-color:{C['green']}; }}
            QPushButton:pressed {{ background:#1a4d2e; }}
        """)
        go_btn.clicked.connect(self._open_browser)
        lay.addWidget(go_btn)
        return bar

    # ── Query assembly logic ───────────────────────────────────────────────────
    def _build_query(self):
        """
        Assembly order
        ──────────────
        1. Each row calls build_token() which applies its own per-row modifiers.
        2. Tokens are sorted into three buckets: ungrouped, group_a, group_b.
        3. group_a tokens  →  joined by default_join  →  wrapped in ( … ) if >1
        4. group_b tokens  →  joined by default_join  →  wrapped in ( … ) if >1
        5. All top-level parts (base, ungrouped tokens, group_A_block, group_B_block)
           are joined by group_join if either group exists, else default_join.
        """
        default_join = self.combo_default_join.currentData()   # "AND" or "OR"
        group_join   = self.combo_group_join.currentData()

        dj_sep = " | " if default_join == "OR" else " "
        gj_sep = " | " if group_join   == "OR" else " "

        ungrouped, grp_a, grp_b = [], [], []

        for _, prefix, _, _ in FILTERS:
            name = next(n for n,p,_,_ in FILTERS if p == prefix)
            row  = self.rows[name]
            tok  = row.build_token()
            if not tok:
                continue
            g = row.group()
            if   g == "A": grp_a.append(tok)
            elif g == "B": grp_b.append(tok)
            else:          ungrouped.append(tok)

        parts = []

        base = self.base_field.text().strip()
        if base:
            parts.append(base)

        # Un-grouped tokens join with default_join
        if ungrouped:
            parts.append(dj_sep.join(ungrouped))

        # Group A block
        if grp_a:
            block = dj_sep.join(grp_a)
            parts.append(f"({block})" if len(grp_a) > 1 else block)

        # Group B block
        if grp_b:
            block = dj_sep.join(grp_b)
            parts.append(f"({block})" if len(grp_b) > 1 else block)

        # If both groups exist, join everything with group_join
        # Otherwise use default_join throughout
        if grp_a and grp_b:
            # Re-join all parts with group_join separator
            return gj_sep.join(parts)
        else:
            return dj_sep.join(parts)

    def _update_query(self):
        q = self._build_query()
        self.query_field.setText(q)
        n = len(q)
        self.status.showMessage(
            f"{n} char{'s' if n!=1 else ''}" +
            ("   ⚠  Google may truncate very long queries" if n > 2000 else "")
            if q else "Ready — fill in filters and apply operators per row."
        )

    def _copy_query(self):
        q = self._build_query()
        if not q:
            self.status.showMessage("⚠  Nothing to copy — fill in at least one field.")
            return
        QApplication.clipboard().setText(q)
        self.status.showMessage("✔  Copied to clipboard!")
        QTimer.singleShot(2200, self._update_query)

    def _open_browser(self):
        q = self._build_query()
        if not q:
            self.status.showMessage("⚠  Build a query first.")
            return
        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(q)
        webbrowser.open(url)
        self.status.showMessage(f"🌐  Opened: {url[:90]}…")

    def _clear_all(self):
        self.base_field.clear()
        for row in self.rows.values():
            row.clear()
        self.combo_default_join.setCurrentIndex(0)
        self.combo_group_join.setCurrentIndex(0)
        self.status.showMessage("All fields cleared.")

    def _load_preset(self, default_join, group_join, pvals):
        self._clear_all()
        self.combo_default_join.setCurrentIndex(0 if default_join == "AND" else 1)
        self.combo_group_join.setCurrentIndex(0 if group_join == "AND" else 1)
        self.base_field.setText(pvals.get("base", ""))
        for name, state in pvals.items():
            if name == "base" or name not in self.rows:
                continue
            val, excl, req, exact, wc, grp = state
            self.rows[name].set_state(val, excl, req, exact, wc, grp)
        self._update_query()
        self.status.showMessage("Preset loaded — check the query bar below.")


# ── Entry ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    for role, hex_ in [
        (QPalette.Window,          C['bg']),
        (QPalette.WindowText,      C['fg']),
        (QPalette.Base,            C['bg4']),
        (QPalette.AlternateBase,   C['bg2']),
        (QPalette.ToolTipBase,     C['bg3']),
        (QPalette.ToolTipText,     C['fg']),
        (QPalette.Text,            C['fg']),
        (QPalette.Button,          C['bg3']),
        (QPalette.ButtonText,      C['fg']),
        (QPalette.Highlight,       C['accent']),
        (QPalette.HighlightedText, "#ffffff"),
    ]:
        pal.setColor(role, QColor(hex_))
    app.setPalette(pal)
    app.setFont(QFont("Segoe UI", 10))
    QToolTip.setFont(QFont("Segoe UI", 10))

    win = GoogleDorker()
    win.show()
    sys.exit(app.exec_())
