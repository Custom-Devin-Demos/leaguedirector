import sys
import json
import logging
import logging.handlers
import leaguedirector
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtNetwork import *
from leaguedirector.widgets import *
from leaguedirector.api import Game, Playback, Render, Particles, Recording, Sequence
from leaguedirector.bindings import Bindings
from leaguedirector.settings import Settings
from leaguedirector.dialogs import KeybindingsWindow, ConnectWindow
from leaguedirector.windows import RenderWindow, ParticlesWindow, VisibleWindow, TimelineWindow, RecordingWindow


class Api(QObject):
    connected = Signal()

    def __init__(self):
        QObject.__init__(self)
        self.wasConnected = False
        self.game = Game()
        self.render = Render()
        self.particles = Particles()
        self.playback = Playback()
        self.recording = Recording()
        self.sequence = Sequence(self.render, self.playback)
        self.game.updated.connect(self.updated)
        self.render.updated.connect(self.updated)
        self.particles.updated.connect(self.updated)
        self.playback.updated.connect(self.updated)
        self.recording.updated.connect(self.updated)

    def updated(self):
        if not self.wasConnected and self.game.connected:
            self.connected.emit()
        self.wasConnected = self.game.connected

    def update(self):
        self.game.update()
        self.render.update()
        self.particles.update()
        self.playback.update()
        self.recording.update()

    def onKeybinding(self, name):
        if name == 'camera_up':
            self.render.moveCamera(y=7)
        elif name == 'camera_down':
            self.render.moveCamera(y=-7)
        elif name == 'camera_move_speed_up':
            self.render.cameraMoveSpeed = self.render.cameraMoveSpeed * 1.2
        elif name == 'camera_move_speed_down':
            self.render.cameraMoveSpeed = self.render.cameraMoveSpeed * 0.8
        elif name == 'camera_look_speed_up':
            self.render.cameraLookSpeed = self.render.cameraLookSpeed * 1.1
        elif name == 'camera_look_speed_down':
            self.render.cameraLookSpeed = self.render.cameraLookSpeed * 0.9
        elif name == 'camera_yaw_left':
            self.render.rotateCamera(x=-1)
        elif name == 'camera_yaw_right':
            self.render.rotateCamera(x=1)
        elif name == 'camera_pitch_up':
            self.render.rotateCamera(y=-1)
        elif name == 'camera_pitch_down':
            self.render.rotateCamera(y=1)
        elif name == 'camera_roll_left':
            self.render.rotateCamera(z=1)
        elif name == 'camera_roll_right':
            self.render.rotateCamera(z=-1)
        elif name == 'camera_move_back_x':
            self.render.toggleCameraMoveBackX()
        elif name == 'camera_move_back_y':
            self.render.toggleCameraMoveBackY()
        elif name == 'camera_move_back_z':
            self.render.toggleCameraMoveBackZ()
        elif name == 'camera_lock_x':
            self.render.cameraLockX = not self.render.cameraLockX
        elif name == 'camera_lock_y':
            self.render.cameraLockY = not self.render.cameraLockY
        elif name == 'camera_lock_z':
            self.render.cameraLockZ = not self.render.cameraLockZ
        elif name == 'camera_attach':
            self.render.cameraAttached = not self.render.cameraAttached
        elif name == 'camera_fov_up':
            self.render.fieldOfView = self.render.fieldOfView * 1.05
        elif name == 'camera_fov_down':
            self.render.fieldOfView = self.render.fieldOfView * 0.95
        elif name == 'render_dof_near_up':
            self.render.depthOfFieldNear = self.render.depthOfFieldNear * 1.05
        elif name == 'render_dof_near_down':
            self.render.depthOfFieldNear = self.render.depthOfFieldNear * 0.95
        elif name == 'render_dof_mid_up':
            self.render.depthOfFieldMid = self.render.depthOfFieldMid * 1.05
        elif name == 'render_dof_mid_down':
            self.render.depthOfFieldMid = self.render.depthOfFieldMid * 0.95
        elif name == 'render_dof_far_up':
            self.render.depthOfFieldFar = self.render.depthOfFieldFar * 1.05
        elif name == 'render_dof_far_down':
            self.render.depthOfFieldFar = self.render.depthOfFieldFar * 0.95
        elif name == 'play_pause':
            self.playback.paused = not self.playback.paused
        elif name == 'time_minus_120':
            self.playback.adjustTime(-120)
        elif name == 'time_minus_60':
            self.playback.adjustTime(-60)
        elif name == 'time_minus_30':
            self.playback.adjustTime(-30)
        elif name == 'time_minus_10':
            self.playback.adjustTime(-10)
        elif name == 'time_minus_5':
            self.playback.adjustTime(-5)
        elif name == 'time_plus_5':
            self.playback.adjustTime(5)
        elif name == 'time_plus_10':
            self.playback.adjustTime(10)
        elif name == 'time_plus_30':
            self.playback.adjustTime(30)
        elif name == 'time_plus_60':
            self.playback.adjustTime(60)
        elif name == 'time_plus_120':
            self.playback.adjustTime(120)


class LeagueDirector(object):
    def __init__(self):
        self.setupLogging()
        self.app = QApplication()
        self.setup()
        sys.exit(self.app.exec())

    def setup(self):
        self.loadTheme()
        self.window = QMainWindow()
        self.mdi = QMdiArea()
        self.api = Api()
        self.windows = {}
        self.settings = Settings()
        self.bindings = self.setupBindings()
        self.addWindow(RenderWindow(self.api), 'render')
        self.addWindow(ParticlesWindow(self.api), 'particles')
        self.addWindow(VisibleWindow(self.api), 'visible')
        self.addWindow(TimelineWindow(self.api), 'timeline')
        self.addWindow(RecordingWindow(self.api), 'recording')
        self.addWindow(KeybindingsWindow(self.bindings), 'bindings')
        self.addWindow(ConnectWindow(), 'connect')
        self.window.setCentralWidget(self.mdi)
        self.window.setWindowTitle('League Director')
        self.window.setWindowIcon(QIcon(respath('icon.ico')))
        self.window.closeEvent = self.closeEvent
        self.window.show()
        self.restoreSettings()
        self.checkUpdate()
        self.bindings.triggered.connect(self.api.onKeybinding)
        self.bindings.triggered.connect(self.windows['timeline'].onKeybinding)
        self.bindings.triggered.connect(self.windows['visible'].onKeybinding)
        self.timerUpdate = schedule(500, self.update)
        self.timerSave = schedule(5000, self.saveSettings)
        self.update()

    def closeEvent(self, event):
        self.saveSettings()
        QMainWindow.closeEvent(self.window, event)

    def setupLogging(self):
        logger = logging.getLogger()
        formatter = logging.Formatter('%(asctime)s [%(levelname)-8s] %(message)s')
        path = userpath('logs', 'leaguedirector.log')
        handler = logging.handlers.RotatingFileHandler(path, backupCount=20)
        try:
            handler.doRollover()
        except Exception: pass
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logging.info('Started League Director (%s)', leaguedirector.__version__)
        logging.info('Using SSL (%s)', QSslSocket.sslLibraryVersionString())
        qInstallMessageHandler(self.handleMessage)

    def checkUpdate(self):
        self.updateAvailable = False
        request = QNetworkRequest(QUrl('https://api.github.com/repos/riotgames/leaguedirector/releases/latest'))
        response = self.api.game.manager().get(request)
        def callback():
            if response.error() == QNetworkReply.NoError:
                version = json.loads(response.readAll().data().decode()).get('tag_name')
                if version and version != 'v{}'.format(leaguedirector.__version__):
                    self.updateAvailable = True
        response.finished.connect(callback)

    def handleMessage(self, msgType, msgContext, msgString):
        if msgType == QtInfoMsg:
            logging.info('(QT) %s', msgString)
        elif msgType == QtDebugMsg:
            logging.debug('(QT) %s', msgString)
        elif msgType == QtWarningMsg:
            logging.warning('(QT) %s', msgString)
        elif msgType == QtCriticalMsg:
            logging.critical('(QT) %s', msgString)
        elif msgType == QtFatalMsg:
            logging.critical('(QT) %s', msgString)
        elif msgType == QtSystemMsg:
            logging.critical('(QT) %s', msgString)

    def setupBindings(self):
        return Bindings(self.window, self.settings.value('bindings', {}), [
            ('play_pause',                  'Play / Pause',                     'Space'),
            ('camera_up',                   'Camera Up',                        ''),
            ('camera_down',                 'Camera Down',                      ''),
            ('camera_yaw_left',             'Camera Yaw Left',                  ''),
            ('camera_yaw_right',            'Camera Yaw Right',                 ''),
            ('camera_pitch_up',             'Camera Pitch Up',                  ''),
            ('camera_pitch_down',           'Camera Pitch Down',                ''),
            ('camera_roll_left',            'Camera Roll Left',                 ''),
            ('camera_roll_right',           'Camera Roll Right',                ''),
            ('camera_move_speed_up',        'Camera Move Speed Up',             'Ctrl++'),
            ('camera_move_speed_down',      'Camera Move Speed Down',           'Ctrl+-'),
            ('camera_look_speed_up',        'Camera Look Speed Up',             ''),
            ('camera_look_speed_down',      'Camera Look Speed Down',           ''),
            ('camera_lock_x',               'Camera Lock X Axis',               ''),
            ('camera_lock_y',               'Camera Lock Y Axis',               ''),
            ('camera_lock_z',               'Camera Lock Z Axis',               ''),
            ('camera_move_back_x',          'Camera Lock X Axis',               ''),
            ('camera_move_back_y',          'Camera Lock Y Axis',               ''),
            ('camera_move_back_z',          'Camera Lock Z Axis',               ''),
            ('camera_attach',               'Camera Attach',                    ''),
            ('camera_fov_up',               'Camera Increase Field of View',    ''),
            ('camera_fov_down',             'Camera Decrease Field of View',    ''),
            ('render_dof_near_up',          'Increase Depth of Field Near',     ''),
            ('render_dof_near_down',        'Decrease Depth of Field Near',     ''),
            ('render_dof_mid_up',           'Increase Depth of Field Mid',      ''),
            ('render_dof_mid_down',         'Decrease Depth of Field Mid',      ''),
            ('render_dof_far_up',           'Increase Depth of Field Far',      ''),
            ('render_dof_far_down',         'Decrease Depth of Field Far',      ''),
            ('show_fog_of_war',             'Show Fog of War',                  ''),
            ('show_selected_outline',       'Show Selected Outline',            ''),
            ('show_hover_outline',          'Show Hover Outline',               ''),
            ('show_floating_text',          'Show Floating Text',               ''),
            ('show_interface_all',          'Show UI All',                      ''),
            ('show_interface_replay',       'Show UI Replay',                   ''),
            ('show_interface_score',        'Show UI Score',                    ''),
            ('show_interface_scoreboard',   'Show UI Scoreboard',               ''),
            ('show_interface_frames',       'Show UI Frames',                   ''),
            ('show_interface_minimap',      'Show UI Minimap',                  ''),
            ('show_interface_timeline',     'Show UI Timeline',                 ''),
            ('show_interface_chat',         'Show UI Chat',                     ''),
            ('show_interface_target',       'Show UI Target',                   ''),
            ('show_interface_quests',       'Show UI Quests',                   ''),
            ('show_interface_announce',     'Show UI Announcements',            ''),
            ('show_healthbar_champions',    'Show Health Champions',            ''),
            ('show_healthbar_structures',   'Show Health Structures',           ''),
            ('show_healthbar_wards',        'Show Health Wards',                ''),
            ('show_healthbar_pets',         'Show Health Pets',                 ''),
            ('show_healthbar_minions',      'Show Health Minions',              ''),
            ('show_environment',            'Show Environment',                 ''),
            ('show_characters',             'Show Characters',                  ''),
            ('show_champions',             'Show Champions',                  ''),
            ('show_minions',             'Show Minions',                  ''),
            ('show_particles',              'Show Particles',                   ''),
            ('sequence_play',               'Play Sequence',                    'Ctrl+Space'),
            ('sequence_apply',              'Apply Sequence',                   '\\'),
            ('sequence_new',                'New Sequence',                     'Ctrl+N'),
            ('sequence_copy',               'Copy Sequence',                    ''),
            ('sequence_clear',              'Clear Sequence',                   ''),
            ('sequence_del_kf',             'Delete Keyframe',                  'Del'),
            ('sequence_next_kf',            'Select Next Keyframe',             ''),
            ('sequence_prev_kf',            'Select Prev Keyframe',             ''),
            ('sequence_adj_kf',             'Select Adjacent Keyframes',        ''),
            ('sequence_all_kf',             'Select All Keyframes',             'Ctrl+A'),
            ('sequence_seek_kf',            'Seek To Keyframe',                 ''),
            ('sequence_undo',               'Sequence Undo',                    'Ctrl+Z'),
            ('sequence_redo',               'Sequence Redo',                    'Ctrl+Shift+Z'),
            ('time_minus_120',              'Time -120 Seconds',                ''),
            ('time_minus_60',               'Time -60 Seconds',                 ''),
            ('time_minus_30',               'Time -30 Seconds',                 ''),
            ('time_minus_10',               'Time -10 Seconds',                 ''),
            ('time_minus_5',                'Time -5 Seconds',                  ''),
            ('time_plus_5',                 'Time +5 Seconds',                  ''),
            ('time_plus_10',                'Time +10 Seconds',                 ''),
            ('time_plus_30',                'Time +30 Seconds',                 ''),
            ('time_plus_60',                'Time +60 Seconds',                 ''),
            ('time_plus_120',               'Time +120 Seconds',                ''),
            ('kf_position',                 'Keyframe Position',                '+'),
            ('kf_rotation',                 'Keyframe Rotation',                '+'),
            ('kf_speed',                    'Keyframe Speed',                   ''),
            ('kf_fov',                      'Keyframe Field of View',           ''),
            ('kf_near_clip',                'Keyframe Near Clip',               ''),
            ('kf_far_clip',                 'Keyframe Far Clip',                ''),
            ('kf_nav_grid',                 'Keyframe Nav Grid Offset',         ''),
            ('kf_sky_rotation',             'Keyframe Skybox Rotation',         ''),
            ('kf_sky_radius',               'Keyframe Skybox Radius',           ''),
            ('kf_sky_offset',               'Keyframe Skybox Offset',           ''),
            ('kf_sun_direction',            'Keyframe Sun Direction',           ''),
            ('kf_depth_fog_enable',         'Keyframe Depth Fog Enable',        ''),
            ('kf_depth_fog_start',          'Keyframe Depth Fog Start',         ''),
            ('kf_depth_fog_end',            'Keyframe Depth Fog End',           ''),
            ('kf_depth_fog_intensity',      'Keyframe Depth Fog Intensity',     ''),
            ('kf_depth_fog_color',          'Keyframe Depth Fog Color',         ''),
            ('kf_height_fog_enable',        'Keyframe Height Fog Enable',       ''),
            ('kf_height_fog_start',         'Keyframe Height Fog Start',        ''),
            ('kf_height_fog_end',           'Keyframe Height Fog End',          ''),
            ('kf_height_fog_intensity',     'Keyframe Height Fog Intensity',    ''),
            ('kf_height_fog_color',         'Keyframe Height Fog Color',        ''),
            ('kf_dof_enabled',              'Keyframe DOF Enabled',             ''),
            ('kf_dof_circle',               'Keyframe DOF Circle',              ''),
            ('kf_dof_width',                'Keyframe DOF Width',               ''),
            ('kf_dof_near',                 'Keyframe DOF Near',                ''),
            ('kf_dof_mid',                  'Keyframe DOF Mid',                 ''),
            ('kf_dof_far',                  'Keyframe DOF Far',                 ''),
        ])

    def addWindow(self, widget, name):
        self.windows[name] = widget
        flags = Qt.Window | Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint
        self.mdi.addSubWindow(widget, flags)
        widget.update()

    def update(self):
        self.api.update()
        self.bindings.setGamePid(self.api.game.processID)
        for name, window in self.windows.items():
            if name == 'update':
                window.parent().setVisible(self.updateAvailable)
            elif name == 'connect':
                window.parent().setVisible(not self.api.game.connected)
            else:
                window.parent().setVisible(self.api.game.connected)

    def loadGeometry(self, widget, data):
        if data and len(data) == 4:
            widget.setGeometry(*data)

    def loadState(self, widget, data):
        if data is not None:
            widget.setWindowState(Qt.WindowStates(data))

    def restoreSettings(self):
        self.loadState(self.window, Qt.WindowState(self.settings.value('window/state') or 0))
        self.loadGeometry(self.window, self.settings.value('window/geo'))
        for name, widget in self.windows.items():
            parent = widget.parentWidget()
            self.loadState(parent, self.settings.value('{}/state'.format(name)))
            self.loadGeometry(parent, self.settings.value('{}/geo'.format(name)))
            if hasattr(widget, 'restoreSettings'):
                widget.restoreSettings(self.settings.value('{}/settings'.format(name), {}) or {})

    def saveSettings(self):
        self.settings.setValue('bindings', self.bindings.getBindings())
        self.settings.setValue('window/state', self.window.windowState().value)
        self.settings.setValue('window/geo', self.window.geometry().getRect())
        for name, widget in self.windows.items():
            parent = widget.parentWidget()
            self.settings.setValue('{}/state'.format(name), parent.windowState().value)
            self.settings.setValue('{}/geo'.format(name), parent.geometry().getRect())
            if hasattr(widget, 'saveSettings'):
                self.settings.setValue('{}/settings'.format(name), widget.saveSettings())

    def loadTheme(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(180, 180, 180))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.Light, QColor(80, 80, 80))
        palette.setColor(QPalette.ColorRole.Midlight, QColor(80, 80, 80))
        palette.setColor(QPalette.ColorRole.Mid, QColor(44, 44, 44))
        palette.setColor(QPalette.ColorRole.Dark, QColor(35, 35, 35))
        palette.setColor(QPalette.ColorRole.Text, QColor(190, 190, 190))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(180, 180, 180))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(180, 180, 180))
        palette.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.Shadow, QColor(20, 20, 20))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(110, 125, 190))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(180, 180, 180))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(180, 180, 180))
        palette.setColor(QPalette.ColorRole.Link, QColor(56, 252, 196))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(180, 180, 180))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(127, 127, 127))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, QColor(127, 127, 127))
        self.app.setPalette(palette)
        self.app.setStyle('Fusion')
