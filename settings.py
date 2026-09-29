import json
from aqt import mw
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget,
    QWidget, QSpinBox, QDoubleSpinBox, QLineEdit, QPushButton,
    QCheckBox, QComboBox, QLabel
)

DEFAULT_CONFIG = {
    "openDelay": 120,
    "closeDelay": 150,
    "gap": 2,
    "viewportMargin": 24,
    "enableInBrowser": True,
    "maxWidth": "65vw",
    "maxHeight": "52vh",
    "minWidth": "320px",
    "borderRadius": "8px",
    "popupPadding": "16px 20px",
    "fontSize": "14px",
    "lineHeight": "1.5",
    "theme": "auto",
    "showFieldBadges": True,
    "showFieldDividers": True,
    "fieldBadgeFontSize": "8.5px",
    "fieldBadgeOpacity": 0.45
}

class PagePreviewSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Note Preview Settings")
        self.setMinimumWidth(440)

        addon_name = __name__.split('.')[0]
        self.config = mw.addonManager.getConfig(addon_name) or DEFAULT_CONFIG.copy()

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()



          # ==========================================
        # TAB 1: Typography & Colors
        # ==========================================
        tab_style = QWidget()
        form_style = QFormLayout(tab_style)

        self.font_size = QLineEdit(str(self.config.get("fontSize", "14px")))
        form_style.addRow("Font Size (e.g. 14px):", self.font_size)

        self.line_height = QLineEdit(str(self.config.get("lineHeight", "1.5")))
        form_style.addRow("Line Spacing (e.g. 1.5):", self.line_height)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Auto (Match Anki)", "Always Dark", "Always Light"])
        current_theme = self.config.get("theme", "auto")
        if current_theme == "dark":
            self.theme_combo.setCurrentIndex(1)
        elif current_theme == "light":
            self.theme_combo.setCurrentIndex(2)
        else:
            self.theme_combo.setCurrentIndex(0)
        form_style.addRow("Theme:", self.theme_combo)

        self.tabs.addTab(tab_style, "Typography/Theme")




        # ==========================================
        # TAB 2: Dimensions & Layout
        # ==========================================
        tab_layout = QWidget()
        form_layout = QFormLayout(tab_layout)

        self.max_width = QLineEdit(str(self.config.get("maxWidth", "65vw")))
        form_layout.addRow("Max Width (e.g. 65vw, 600px):", self.max_width)

        self.max_height = QLineEdit(str(self.config.get("maxHeight", "52vh")))
        form_layout.addRow("Max Height (e.g. 52vh, 400px):", self.max_height)

        self.min_width = QLineEdit(str(self.config.get("minWidth", "320px")))
        form_layout.addRow("Min Width (e.g. 320px):", self.min_width)

        self.border_radius = QLineEdit(str(self.config.get("borderRadius", "8px")))
        form_layout.addRow("Corner Rounding (e.g. 8px):", self.border_radius)

        self.popup_padding = QLineEdit(str(self.config.get("popupPadding", "16px 20px")))
        form_layout.addRow("Inner Padding (e.g. 16px 20px):", self.popup_padding)

        self.tabs.addTab(tab_layout, "Geometry")

        # ==========================================
        # TAB 3: Timing & Interaction
        # ==========================================
        tab_timing = QWidget()
        form_timing = QFormLayout(tab_timing)

        self.open_delay = QSpinBox()
        self.open_delay.setRange(0, 1000)
        self.open_delay.setSingleStep(10)
        self.open_delay.setValue(int(self.config.get("openDelay", 120)))
        form_timing.addRow("Hover Open Delay (ms):", self.open_delay)

        self.close_delay = QSpinBox()
        self.close_delay.setRange(0, 1000)
        self.close_delay.setSingleStep(10)
        self.close_delay.setValue(int(self.config.get("closeDelay", 150)))
        form_timing.addRow("Close Grace Period (ms):", self.close_delay)

        self.gap = QSpinBox()
        self.gap.setRange(0, 50)
        self.gap.setValue(int(self.config.get("gap", 2)))
        form_timing.addRow("Gap from Text (px):", self.gap)

        self.margin = QSpinBox()
        self.margin.setRange(0, 100)
        self.margin.setValue(int(self.config.get("viewportMargin", 24)))
        form_timing.addRow("Screen Escape Margin (px):", self.margin)

        self.enable_browser = QCheckBox("Enable preview in Card Browser")
        self.enable_browser.setChecked(bool(self.config.get("enableInBrowser", True)))
        form_timing.addRow(self.enable_browser)

        self.tabs.addTab(tab_timing, "Interaction")

        self.enable_block_tags = QCheckBox("Enable ^block-tag references (e.g. ^my-image)")
        self.enable_block_tags.setChecked(bool(self.config.get("enableBlockTags", True)))
        form_timing.addRow(self.enable_block_tags)

        
      

        # ==========================================
        # TAB 4: Field Labels (Full Cards)
        # ==========================================
        tab_fields = QWidget()
        form_fields = QFormLayout(tab_fields)

        self.show_badges = QCheckBox("Show FRONT / BACK field badges")
        self.show_badges.setChecked(bool(self.config.get("showFieldBadges", True)))
        form_fields.addRow(self.show_badges)

        self.show_dividers = QCheckBox("Show dividers between fields")
        self.show_dividers.setChecked(bool(self.config.get("showFieldDividers", True)))
        form_fields.addRow(self.show_dividers)

        self.badge_size = QLineEdit(str(self.config.get("fieldBadgeFontSize", "8.5px")))
        form_fields.addRow("Badge Font Size:", self.badge_size)

        self.badge_opacity = QDoubleSpinBox()
        self.badge_opacity.setRange(0.05, 1.0)
        self.badge_opacity.setSingleStep(0.05)
        self.badge_opacity.setValue(float(self.config.get("fieldBadgeOpacity", 0.45)))
        form_fields.addRow("Badge Dimness (Opacity 0.1 - 1.0):", self.badge_opacity)

        self.tabs.addTab(tab_fields, "Field Badges")

        layout.addWidget(self.tabs)

        # Bottom Buttons
        btn_box = QHBoxLayout()
        restore_btn = QPushButton("Restore Defaults")
        restore_btn.clicked.connect(self.restore_defaults)
        btn_box.addWidget(restore_btn)
        btn_box.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.save_settings)
        btn_box.addWidget(save_btn)

        layout.addLayout(btn_box)

    def restore_defaults(self):
        self.open_delay.setValue(DEFAULT_CONFIG["openDelay"])
        self.close_delay.setValue(DEFAULT_CONFIG["closeDelay"])
        self.gap.setValue(DEFAULT_CONFIG["gap"])
        self.margin.setValue(DEFAULT_CONFIG["viewportMargin"])
        self.enable_browser.setChecked(DEFAULT_CONFIG["enableInBrowser"])
        self.max_width.setText(DEFAULT_CONFIG["maxWidth"])
        self.max_height.setText(DEFAULT_CONFIG["maxHeight"])
        self.min_width.setText(DEFAULT_CONFIG["minWidth"])
        self.border_radius.setText(DEFAULT_CONFIG["borderRadius"])
        self.popup_padding.setText(DEFAULT_CONFIG["popupPadding"])
        self.font_size.setText(DEFAULT_CONFIG["fontSize"])
        self.line_height.setText(DEFAULT_CONFIG["lineHeight"])
        self.theme_combo.setCurrentIndex(0)
        self.show_badges.setChecked(DEFAULT_CONFIG["showFieldBadges"])
        self.show_dividers.setChecked(DEFAULT_CONFIG["showFieldDividers"])
        self.badge_size.setText(DEFAULT_CONFIG["fieldBadgeFontSize"])
        self.badge_opacity.setValue(DEFAULT_CONFIG["fieldBadgeOpacity"])

    def save_settings(self):
        theme_val = "auto"
        if self.theme_combo.currentIndex() == 1:
            theme_val = "dark"
        elif self.theme_combo.currentIndex() == 2:
            theme_val = "light"

        new_config = {
            "openDelay": self.open_delay.value(),
            "closeDelay": self.close_delay.value(),
            "gap": self.gap.value(),
            "viewportMargin": self.margin.value(),
            "enableInBrowser": self.enable_browser.isChecked(),
            "maxWidth": self.max_width.text().strip(),
            "maxHeight": self.max_height.text().strip(),
            "minWidth": self.min_width.text().strip(),
            "borderRadius": self.border_radius.text().strip(),
            "popupPadding": self.popup_padding.text().strip(),
            "fontSize": self.font_size.text().strip(),
            "lineHeight": self.line_height.text().strip(),
            "theme": theme_val,
            "showFieldBadges": self.show_badges.isChecked(),
            "showFieldDividers": self.show_dividers.isChecked(),
            "fieldBadgeFontSize": self.badge_size.text().strip(),
            "fieldBadgeOpacity": round(self.badge_opacity.value(), 2)
        }

        addon_name = __name__.split('.')[0]
        mw.addonManager.writeConfig(addon_name, new_config)

        # Real-time push to the webview
        if mw.state == "review" and hasattr(mw, "reviewer") and mw.reviewer.web:
            mw.reviewer.web.eval(f"window.__NOTE_PREVIEW_CONFIG__ = {json.dumps(new_config)};")

        self.accept()

def open_settings_dialog():
    dialog = PagePreviewSettingsDialog(mw)
    dialog.exec()

def setup_menu():
    from aqt.qt import QAction
    action = QAction("Note Preview Settings...", mw)
    action.triggered.connect(open_settings_dialog)
    mw.form.menuTools.addAction(action)