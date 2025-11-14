import sys
import sqlite3
import random
from PyQt5 import QtWidgets, QtCore, QtGui

class DinoRunner(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("мячик")
        self.resize(600, 400)
        self.setStyleSheet("background-color: #f0f0f0;")
        self.conn = sqlite3.connect('ball.db')
        self.create_table()

        self.score = 0
        self.is_game_active = False
        self.player_name = ""
        self.obstacles = []
        self.speed = 10
        self.speed_increase_timer = 0
        self.is_jumping = False  
        self.setup_ui()

        self.game_timer = QtCore.QTimer()
        self.game_timer.timeout.connect(self.game_step)
        self.obstacle_timer = QtCore.QTimer()
        self.obstacle_timer.timeout.connect(self.spawn_obstacle)
        self.speed_timer = QtCore.QTimer()
        self.speed_timer.timeout.connect(self.increase_speed)

        self.setup_styles()
        self.prompt_name()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS scores (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            player_name TEXT,
                            score INTEGER,
                            date TEXT)''')
        self.conn.commit()
        
#ввод
    def prompt_name(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Регистрация")
        dialog.setFixedSize(300, 150)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
                border-radius: 10px;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        title = QtWidgets.QLabel("Введите ваш ник")
        title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding: 10px;
            }
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        name_input = QtWidgets.QLineEdit()
        name_input.setPlaceholderText("...")
        name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin: 0 20px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        layout.addWidget(name_input)
        
#Кн
        btn_layout = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("OK")
        cancel_btn = QtWidgets.QPushButton("Продолжить без регистрации")
        
        for btn in [ok_btn, cancel_btn]:
            btn.setFixedHeight(35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    padding: 5px 15px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        def accept_name():
            name = name_input.text().strip()
            if name:
                self.player_name = name
                self.start_btn.setEnabled(True)
            else:
                self.player_name = "Анонимус"
                self.start_btn.setEnabled(True)
            dialog.accept()
        
        def cancel_input():
            self.player_name = "Анонимус"
            self.start_btn.setEnabled(True)
            dialog.reject()
        
        ok_btn.clicked.connect(accept_name)
        cancel_btn.clicked.connect(cancel_input)
        name_input.returnPressed.connect(accept_name)
        
        dialog.exec_()

    def setup_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

#Игра
        self.game_area = QtWidgets.QFrame()
        self.game_area.setFixedHeight(250)
        self.game_area.setStyleSheet("background-color: #ffffff; border: 2px solid #888; border-radius: 10px;")
        layout.addWidget(self.game_area)

        info_layout = QtWidgets.QHBoxLayout()
        self.score_label = QtWidgets.QLabel("Очки: 0")
        self.score_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff0000;")
        self.message_browser = QtWidgets.QTextBrowser()
        self.message_browser.setFixedHeight(80)
        self.message_browser.setStyleSheet("border:1px solid #ccc; border-radius: 5px; padding:4px;")
        info_layout.addWidget(self.score_label)
        info_layout.addWidget(self.message_browser)
        layout.addLayout(info_layout)

#Кн2
        btn_layout = QtWidgets.QHBoxLayout()
        
        self.start_btn = QtWidgets.QPushButton("Играть")
        self.scores_btn = QtWidgets.QPushButton("Рекорды")
        self.exit_btn = QtWidgets.QPushButton("Выход из игры")
        self.start_btn.setEnabled(False)

        btns = [self.start_btn, self.scores_btn, self.exit_btn]
        for btn in btns:
            btn.setFixedHeight(40)
            btn.setMinimumWidth(120)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px 16px;
                    border-radius: 8px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                    color: #666666;
                }
            """)
        
        self.start_btn.clicked.connect(self.start_game)
        self.scores_btn.clicked.connect(self.show_scores)
        self.exit_btn.clicked.connect(self.close) 
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.scores_btn)
        btn_layout.addWidget(self.exit_btn)
        layout.addLayout(btn_layout)
        self.game_area.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.game_area.keyPressEvent = self.key_press_event

#перс
        self.player = QtWidgets.QLabel(self.game_area)
        self.player.setStyleSheet("background-color: #333; border-radius: 10px;")
        self.player.setFixedSize(20, 20)
        self.player.move(50, 230)

    def setup_styles(self):
        pass
#старт и преп
    def start_game(self):
        if self.is_game_active:
            return
        self.is_game_active = True
        self.is_jumping = False  
        self.score = 0
        self.speed = 10
        self.speed_increase_timer = 0
        self.update_score()
        self.message_browser.clear()
        self.player.move(50, 230)
        for child in self.game_area.children():
            if isinstance(child, QtWidgets.QLabel) and hasattr(child, 'is_obstacle'):
                child.deleteLater()
        self.obstacles.clear()

        self.game_timer.start(30)
        self.obstacle_timer.start(1500)
        self.speed_timer.start(10000)
        self.game_area.setFocus()

    def game_step(self):
        for obstacle in self.obstacles[:]:
            x = obstacle.x() - self.speed
            if x + obstacle.width() < 0:
                obstacle.deleteLater()
                self.obstacles.remove(obstacle)
                self.score += 1
                self.update_score()
            else:
                obstacle.move(x, obstacle.y())

#столк
        player_rect = self.player.geometry()
        for obstacle in self.obstacles:
            if obstacle.geometry().intersects(player_rect):
                self.end_game()
                break

#размер и форма
    def spawn_obstacle(self):
        size_choice = random.choice([30, 40, 50, 60, 70, 80, 90, 100, 110])

        
        y_pos = 230
        obstacle = QtWidgets.QLabel(self.game_area)
        obstacle.setStyleSheet("background-color: transparent;")
        obstacle.setFixedSize(size_choice, size_choice)

        pixmap = QtGui.QPixmap(size_choice, size_choice)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#f00")))
        painter.setPen(QtCore.Qt.NoPen) 
        painter.end()

        obstacle.setPixmap(pixmap)
        obstacle.move(600, y_pos)
        obstacle.is_obstacle = True
        obstacle.show()
        self.obstacles.append(obstacle)
        
#пробел
    def key_press_event(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.jump()

    def jump(self):
        if not self.is_game_active or self.is_jumping:
            return
            
        self.is_jumping = True
        max_y = self.player.y()
        if max_y < 80:
            max_y = 80
            
        jump_anim = QtCore.QPropertyAnimation(self.player, b"pos")
        jump_anim.setDuration(300)
        jump_anim.setStartValue(self.player.pos())
        jump_anim.setEndValue(QtCore.QPoint(self.player.x(), max_y - 80))
        jump_anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)

        fall_anim = QtCore.QPropertyAnimation(self.player, b"pos")
        fall_anim.setDuration(300)
        fall_anim.setStartValue(QtCore.QPoint(self.player.x(), max_y - 80))
        fall_anim.setEndValue(QtCore.QPoint(self.player.x(), 230))
        fall_anim.setEasingCurve(QtCore.QEasingCurve.InQuad)

        self.jump_group = QtCore.QSequentialAnimationGroup()
        self.jump_group.addAnimation(jump_anim)
        self.jump_group.addAnimation(fall_anim)
        
        def reset_jump_flag():
            self.is_jumping = False
            
        self.jump_group.finished.connect(reset_jump_flag)
        self.jump_group.start()
#обн рек
    def update_score(self):
        self.score_label.setText(f"Очки: {self.score}")
        
#кон
    def end_game(self):
        self.game_timer.stop()
        self.obstacle_timer.stop()
        self.speed_timer.stop()
        self.is_game_active = False
        self.is_jumping = False
        if not self.player_name:
            self.prompt_name()
        self.save_score(self.player_name, self.score)
        self.message_browser.append(f"Игра завершена. Очки: {self.score}")
        
#сохр рек
    def save_score(self, name, score):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO scores (player_name, score, date) VALUES (?, ?, datetime('now'))",
                       (name, score))
        self.conn.commit()
        
#покз рек
    def show_scores(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT player_name, score, date FROM scores ORDER BY score DESC LIMIT 10")
        records = cursor.fetchall()
        scores_dialog = QtWidgets.QDialog(self)
        scores_dialog.setWindowTitle("Таблица рекордов")
        scores_dialog.setFixedSize(400, 300)
        scores_dialog.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(scores_dialog)
        title = QtWidgets.QLabel("Лучшие игроки")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                padding: 10px;
                text-align: center;
            }
        """)
        layout.addWidget(title)
        
#Таб рек
        table = QtWidgets.QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels([" Игрок ", " Очки ", " Дата "])
        table.setRowCount(len(records))
        
        for i, rec in enumerate(records):
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(rec[0]))
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(rec[1])))
            table.setItem(i, 2, QtWidgets.QTableWidgetItem(rec[2].split()[0]))
        
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
        """)
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
#Кн закрытия рек
        close_btn = QtWidgets.QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        close_btn.clicked.connect(scores_dialog.accept)
        layout.addWidget(close_btn)
        
        scores_dialog.exec_()
        
#скорость
    def increase_speed(self):
        self.speed += 2
        self.speed_increase_timer += 1
        self.obstacle_timer.setInterval(max(800, 1500 - self.speed_increase_timer * 100))

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = DinoRunner()
    window.show()
    sys.exit(app.exec_())