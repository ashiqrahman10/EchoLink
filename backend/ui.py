import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *


class EmergencyDashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Emergency Dashboard")
        self.setGeometry(100, 100, 2400, 1200)

        main_layout = QVBoxLayout()

        top_bar = QHBoxLayout()
        dashboard_btn = self.create_top_button("Dashboard")
        call_history_btn = self.create_top_button("Call History")
        analytics_btn = self.create_top_button("Analytics")
        dispatch_btn = self.create_top_button("Dispatch")

        top_bar.addWidget(dashboard_btn)
        top_bar.addWidget(call_history_btn)
        top_bar.addWidget(analytics_btn)
        top_bar.addWidget(dispatch_btn)

        main_layout.addLayout(top_bar)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)

        content_splitter = QSplitter(Qt.Horizontal)

        left_frame = QFrame(self)
        left_layout = QVBoxLayout()

        current_calls_layout = QVBoxLayout()
        current_calls_label = QLabel("Current Calls")
        current_calls_label.setFont(QFont('Arial', 16, QFont.Bold))

        current_calls_layout.addWidget(current_calls_label)

        calls = [("Heart attack on Maple Drive", "Critical"),
                 ("Multiple people injured on 27th Street", "Critical"),
                 ("Apartment fire on Main Street", "Moderate")]

        for call in calls:
            call_frame = QFrame(self)
            call_frame.setStyleSheet("background-color: white; border: 1px solid lightgray; border-radius: 10px;")
            call_layout = QHBoxLayout()
            call_label = QLabel(call[0])
            call_label.setFont(QFont('Arial', 12))
            
            badge_label = QLabel(call[1])
            badge_label.setFont(QFont('Arial', 12, QFont.Bold))
            badge_label.setAlignment(Qt.AlignCenter)
            badge_label.setStyleSheet(f"background-color: {'red' if call[1] == 'Critical' else 'orange'}; color: white; border-radius: 10px; padding: 5px;")
            
            call_layout.addWidget(call_label)
            call_layout.addWidget(badge_label)
            call_frame.setLayout(call_layout)
            current_calls_layout.addWidget(call_frame)

        dispatch_layout = QVBoxLayout()
        dispatch_label = QLabel("Dispatch first responders:")
        dispatch_layout.addWidget(dispatch_label)

        police_btn = self.create_dispatch_button("Police", "blue")
        firefighters_btn = self.create_dispatch_button("Firefighters", "red")
        paramedics_btn = self.create_dispatch_button("Paramedics", "green")

        dispatch_layout.addWidget(police_btn)
        dispatch_layout.addWidget(firefighters_btn)
        dispatch_layout.addWidget(paramedics_btn)

        left_layout.addLayout(current_calls_layout)
        left_layout.addLayout(dispatch_layout)
        left_frame.setLayout(left_layout)

        map_frame = QFrame(self)
        map_layout = QVBoxLayout()

        self.url = QUrl('https://www.openstreetmap.org/')
        self.web_view = QWebEngineView(self)
        self.web_view.setUrl(self.url)

        map_layout.addWidget(self.web_view)
        map_frame.setLayout(map_layout)

        right_frame = QFrame(self)
        right_layout = QVBoxLayout()

        transcription_label = QLabel("Live Transcription")
        transcription_label.setFont(QFont('Arial', 14, QFont.Bold))
        right_layout.addWidget(transcription_label)

        transcript_box = QTextEdit(self)
        transcript_box.setReadOnly(True)
        transcript_box.setText("Live transcript messages will appear here...")
        transcript_box.setStyleSheet("background-color: white; border: 1px solid gray; padding: 10px;")
        right_layout.addWidget(transcript_box)

        right_frame.setLayout(right_layout)

        content_splitter.addWidget(left_frame)
        content_splitter.addWidget(map_frame)
        content_splitter.addWidget(right_frame)

        main_layout.addWidget(content_splitter)
        self.setLayout(main_layout)

    def create_top_button(self, name):
        btn = QPushButton(name)
        btn.setStyleSheet("""
            QPushButton{
                background-color: lightgray; border-radius: 10px;
            }
            QPushButton:hover{
            }
        """)
        btn.setFixedHeight(80)
        return btn

    def create_dispatch_button(self, name, color):
        btn = QPushButton(name)
        btn.setFixedSize(150, 40)
        btn.setStyleSheet(f"background-color: {color}; color: white; border-radius: 5px;")
        btn.setIcon(QIcon(f'{name.lower()}.png'))  
        return btn

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = EmergencyDashboard()
    window.show()

    sys.exit(app.exec_())
