"""
Tokyo Night color theme for the Todoist TUI.

Colors sourced from the Tokyo Night VS Code theme.
"""

# -- Background / surface tones --
BG_DARK = "#1a1b26"
BG_DEFAULT = "#24283b"
BG_HIGHLIGHT = "#292e42"
BG_VISUAL = "#364a82"

# -- Foreground --
FG_DEFAULT = "#c0caf5"
FG_DIM = "#565f89"
FG_BRIGHT = "#c0caf5"

# -- Accent colors --
BLUE = "#7aa2f7"
CYAN = "#7dcfff"
GREEN = "#9ece6a"
MAGENTA = "#bb9af7"
ORANGE = "#ff9e64"
RED = "#f7768e"
YELLOW = "#e0af68"
TEAL = "#73daca"

# -- Todoist priority mapping --
PRIORITY_COLORS = {
    1: FG_DEFAULT,   # p4 (normal) — no highlight
    2: BLUE,         # p3
    3: ORANGE,       # p2
    4: RED,          # p1 (urgent)
}

# -- Semantic aliases --
SIDEBAR_BG = BG_DARK
MAIN_BG = BG_DEFAULT
SELECTED_BG = BG_HIGHLIGHT
ACTIVE_VIEW_FG = BLUE
DIM_TEXT = FG_DIM
STATUS_BAR_BG = BG_DARK
BORDER_COLOR = FG_DIM
MODAL_BG = BG_DEFAULT
MODAL_BORDER = BLUE

# -- TCSS theme string for the app --
APP_CSS = """
Screen {
    background: """ + BG_DEFAULT + """;
    color: """ + FG_DEFAULT + """;
}

#sidebar {
    width: 22%;
    min-width: 20;
    max-width: 40;
    background: """ + BG_DARK + """;
    border-right: tall """ + FG_DIM + """;
    padding: 1 0;
}

#main-pane {
    background: """ + BG_DEFAULT + """;
    padding: 0 1;
}

#status-bar {
    dock: bottom;
    height: 1;
    background: """ + BG_DARK + """;
    color: """ + FG_DIM + """;
    padding: 0 1;
}

.sidebar-item {
    padding: 0 1;
    height: 1;
    color: """ + FG_DIM + """;
}

.sidebar-item.--active {
    color: """ + BLUE + """;
    text-style: bold;
}

.sidebar-item:hover {
    background: """ + BG_HIGHLIGHT + """;
}

.task-row {
    height: 1;
    padding: 0 1;
}

.task-row.--selected {
    background: """ + BG_HIGHLIGHT + """;
}

.task-row.--completed {
    color: """ + FG_DIM + """;
    text-style: strike;
}

.priority-1 {
    color: """ + FG_DEFAULT + """;
}

.priority-2 {
    color: """ + BLUE + """;
}

.priority-3 {
    color: """ + ORANGE + """;
}

.priority-4 {
    color: """ + RED + """;
}

.modal-container {
    align: center middle;
    background: """ + BG_DEFAULT + """ 90%;
    border: tall """ + BLUE + """;
    padding: 1 2;
    max-width: 70;
    max-height: 30;
}

.modal-title {
    text-style: bold;
    color: """ + BLUE + """;
    padding: 0 0 1 0;
}

.help-key {
    color: """ + YELLOW + """;
    text-style: bold;
}

.help-desc {
    color: """ + FG_DEFAULT + """;
}

.snooze-preset {
    padding: 0 1;
    height: 1;
}

.snooze-preset:hover {
    background: """ + BG_HIGHLIGHT + """;
}

.snooze-preset.--selected {
    background: """ + BG_VISUAL + """;
    color: """ + CYAN + """;
}

.search-input {
    background: """ + BG_HIGHLIGHT + """;
    color: """ + FG_DEFAULT + """;
    border: tall """ + FG_DIM + """;
    padding: 0 1;
}

.dim-text {
    color: """ + FG_DIM + """;
}

.label-tag {
    color: """ + TEAL + """;
}

.due-date {
    color: """ + YELLOW + """;
}

.due-date.--overdue {
    color: """ + RED + """;
}

.section-header {
    color: """ + MAGENTA + """;
    text-style: bold;
    padding: 1 0 0 0;
}
"""
