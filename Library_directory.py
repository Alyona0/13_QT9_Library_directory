from PyQt5.QtSql import *
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QMenu, QAction, QWidget


class Viewing_db(QMainWindow):
    def __init__(self, parent=None):
        super(Viewing_db, self).__init__(parent)
        self.resize(1000, 600)
        self.setWindowTitle("Каталог библиотеки")
        # создаем виджеты
        self.main_widget = QtWidgets.QWidget(self)
        self.labelsearch = QtWidgets.QLabel(self.main_widget)
        self.line_search = QtWidgets.QLineEdit(self.main_widget)
        self.combo_field = QtWidgets.QComboBox(self.main_widget)
        self.tview_dbase = QtWidgets.QTableView(self.main_widget)
        # задаем расположение
        self.gridLayout = QtWidgets.QGridLayout(self.main_widget)
        # минимальная ширина
        self.gridLayout.setColumnMinimumWidth(1, 150)
        self.gridLayout.setColumnMinimumWidth(2, 100)
        # коффициенты растяжения
        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 5)
        self.gridLayout.setColumnStretch(2, 2)
        # расположение на сетке
        self.gridLayout.addWidget(self.labelsearch, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.line_search, 0, 1, 1, 1)
        self.gridLayout.addWidget(self.combo_field, 0, 2, 1, 1)
        self.gridLayout.addWidget(self.tview_dbase, 1, 0, 1, 3)
        self.setCentralWidget(self.main_widget)
        # подписи
        self.labelsearch.setText("Фильтр: столбец содержит  ")
        # задаем события (сигналы)
        self.horizontalHeader = self.tview_dbase.horizontalHeader()
        self.horizontalHeader.sectionClicked.connect(self.tview_dbase_horizontalHeader_sectionClicked)
        self.line_search.textChanged.connect(self.line_search_textChanged)

        self.tview_dbase.clicked.connect(self.updateAct)
        self.tview_dbase.setSelectionBehavior(QtWidgets.QTableView.SelectRows) # поведение при выделении

        self.combo_field.currentIndexChanged.connect(self.combo_field_currentIndexChanged)
        # выбор файла базы данных SQLite
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('books_db.db')
        self.db.open()
        # задаем и выводим в QTableView модель выбранной таблицы
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable('view_books')
        self.model.setEditStrategy(QSqlTableModel.OnManualSubmit )
        self.model.select()
            # модель с поддержкой фильтрации
        self.proxy = QtCore.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.tview_dbase.setModel(self.proxy)
        self.tview_dbase.setColumnHidden(6, True)
        # заполняем QComboBox списком заголовков столбцов модели
        self.combo_field.blockSignals(True)
        self.combo_field.clear()
        self.combo_field.blockSignals(False)
        for col in range(self.model.columnCount()):
            self.combo_field.addItem(str(self.model.headerData(col, QtCore.Qt.Horizontal, 0)))

    # создание QMenu с уникальными значениями по клику на заголовке столбца QTableView
    def tview_dbase_horizontalHeader_sectionClicked(self, logicalIndex):
        self.logicalIndex   = logicalIndex
        self.menu_values    = QMenu(self)
        self.signalMapper   = QtCore.QSignalMapper(self)
        # значение QComboBox и столбца фильтрации заменим на выбранный столбец
        self.combo_field.blockSignals(True)
        self.combo_field.setCurrentIndex(self.logicalIndex)
        self.combo_field.blockSignals(False)
        self.proxy.setFilterKeyColumn(self.logicalIndex)
        # создадим список уникальных значений (используем модель, а не представление)
        # модель выводит не больше 256. Грузить оставшиеся?
        self.model.select()
        values_unique = [   self.model.index(row, self.logicalIndex).data()
                            for row in range(self.model.rowCount())
                            ]
        # первый пункт меню для сброса фильтра
        action_all = QAction("Все", self)
        action_all.triggered.connect(self.action_all_triggered)
        self.menu_values.addAction(action_all)
        self.menu_values.addSeparator()
        # формирование пунктов меню на основе уникальных значений
        for action_num, action_name in enumerate(sorted(list(set(values_unique)))):
            action = QAction(str(action_name), self) # наименование, число -> строка
            self.signalMapper.setMapping(action, action_num)
            action.triggered.connect(self.signalMapper.map)
            self.menu_values.addAction(action)
        self.signalMapper.mapped.connect(self.signalMapper_mapped)
        # позиция для отображения QMenu
        header_pos = self.tview_dbase.mapToGlobal(self.horizontalHeader.pos())
        pos_y = header_pos.y() + self.horizontalHeader.height()
        pos_x = header_pos.x() + self.horizontalHeader.sectionViewportPosition(self.logicalIndex)
        self.menu_values.exec_(QtCore.QPoint(pos_x, pos_y))

    # выбор QAction в QMenu для вывода всех записей
    def action_all_triggered(self):
        self.line_search.setText('')

    # выбор записей содержащих наименовние QAction из QMenu
    def signalMapper_mapped(self, i):
        name_action = self.signalMapper.mapping(i).text()
        self.line_search.setText(str(name_action))

    # выбор записей при изменении текста в QLineEdit
    def line_search_textChanged(self, text):
        self.model.select()
        search = QtCore.QRegExp(    text,
                                    QtCore.Qt.CaseInsensitive,
                                    QtCore.QRegExp.RegExp
                                    )
        self.proxy.setFilterRegExp(search)
        self.rowCount_in_statusBar()

    # выбор столбца для применения фильтрации
    def combo_field_currentIndexChanged(self, index):
        self.proxy.setFilterKeyColumn(index)
        self.rowCount_in_statusBar()

    # подсчет и вывод количества запсей
    def rowCount_in_statusBar(self):
        while self.model.canFetchMore():
            self.model.fetchMore()
        self.statusBar().showMessage('Найдено записей: ' + str(self.proxy.rowCount()))

    def updateAct (self, clickedIndex):
        #print(clickedIndex.row(), clickedIndex.column())
        title = clickedIndex.sibling(clickedIndex.row(), 1).data()
        author = clickedIndex.sibling(clickedIndex.row(), 2).data()
        publishing = clickedIndex.sibling(clickedIndex.row(), 3).data()
        year = clickedIndex.sibling(clickedIndex.row(), 4).data()
        genre  = clickedIndex.sibling(clickedIndex.row(), 5).data()
        file = clickedIndex.sibling(clickedIndex.row(), 6).data()
        self.exPopup = Book_form(title, author, publishing, year, genre, file)
        self.exPopup.show()

class Book_form(QWidget):
    def __init__(self, title, author, publishing, year, genre, file):
        super().__init__()
        self.setWindowTitle("Информация о книге")
        self.resize(500, 700)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.gridLayout = QtWidgets.QGridLayout()
        # подписи
        self.lbl_image = QtWidgets.QLabel(self)
        self.lbl_title = QtWidgets.QLabel(self)
        self.lbl_author = QtWidgets.QLabel(self)
        self.lbl_publishing = QtWidgets.QLabel(self)
        self.lbl_year = QtWidgets.QLabel(self)
        self.lbl_genre = QtWidgets.QLabel(self)
        # данные
        self._title = QtWidgets.QLabel(self)
        self._author = QtWidgets.QLabel(self)
        self._publishing = QtWidgets.QLabel(self)
        self._year = QtWidgets.QLabel(self)
        self._genre = QtWidgets.QLabel(self)
        # расположение
        self.gridLayout.addWidget(self.lbl_image, 0, 0, 1, 3, alignment=Qt.AlignCenter)
        self.gridLayout.addWidget(self.lbl_title, 1, 0, 1, 3)
        self.gridLayout.addWidget(self._title, 2, 0, 1, 3)
        self.gridLayout.addWidget(self.lbl_author, 3, 0, 1, 3)
        self.gridLayout.addWidget(self._author, 4, 0, 1, 3)
        self.gridLayout.addWidget(self.lbl_publishing, 5, 0, 1, 2)
        self.gridLayout.addWidget(self._publishing, 6, 0, 1, 2)
        self.gridLayout.addWidget(self.lbl_year, 5, 2, 1, 1)
        self.gridLayout.addWidget(self._year, 6, 2, 1, 1)
        self.gridLayout.addWidget(self.lbl_genre, 7, 0, 1, 3)
        self.gridLayout.addWidget(self._genre, 8, 0, 2, 3)

        self.horizontalLayout.addLayout(self.gridLayout)
        # подписи
        self.lbl_title.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Название</span></p></body></html>")
        self.lbl_author.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Автор</span></p></body></html>")
        self.lbl_publishing.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Издательство</span></p></body></html>")
        self.lbl_year.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Год издания</span></p></body></html>")
        self.lbl_genre.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt; font-weight:600;\">Жанр</span></p></body></html>")

        self._title.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt;\">" +
                            title + "</span></p></body></html>")
        self._author.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt;\">" +
                            author + "</span></p></body></html>")
        self._publishing.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt;\">" +
                                 publishing + "</span></p></body></html>")
        self._year.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt;\">" +
                           str(year) + "</span></p></body></html>")
        self._genre.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:12pt;\">" +
                            genre + "</span></p></body></html>")

        self.lbl_image.setScaledContents(True)
        self.lbl_image.setFixedSize(360, 500)
        if not file:
            self.pixmap = QPixmap('./book_cover/130668950.jpg')
        else:
            self.pixmap = QPixmap('./book_cover/' + file)
        #self.pixmap.scaled(360, 500, QtCore.Qt.KeepAspectRatio)
        self.lbl_image.setPixmap(self.pixmap)



if __name__ == "__main__":
    import sys
    app  = QApplication(sys.argv)
    main = Viewing_db()
    main.show()
    sys.exit(app.exec_())