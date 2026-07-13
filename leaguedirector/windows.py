import os
import functools
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from leaguedirector.widgets import *
from leaguedirector.sequencer import *


class SkyboxCombo(QComboBox):
    def showPopup(self):
        appDir = respath('skyboxes')
        userDir = userpath('skyboxes')
        paths = ['']
        paths += [os.path.join(appDir, f) for f in os.listdir(appDir) if f.endswith('.dds')]
        paths += [os.path.join(userDir, f) for f in os.listdir(userDir) if f.endswith('.dds')]
        self.clear()
        for path in sorted(paths):
            self.addItem(os.path.basename(path), path)
        QComboBox.showPopup(self)


class VisibleWindow(QScrollArea):
    options = [
        ('fogOfWar', 'show_fog_of_war', 'Show Fog Of War?'),
        ('outlineSelect', 'show_selected_outline', 'Show Selected Outline?'),
        ('outlineHover', 'show_hover_outline', 'Show Hover Outline?'),
        ('floatingText', 'show_floating_text', 'Show Floating Text?'),
        ('interfaceAll', 'show_interface_all', 'Show UI?'),
        ('interfaceReplay', 'show_interface_replay', 'Show UI Replay?'),
        ('interfaceScore', 'show_interface_score', 'Show UI Score?'),
        ('interfaceScoreboard', 'show_interface_scoreboard', 'Show UI Scoreboard?'),
        ('interfaceFrames', 'show_interface_frames', 'Show UI Frames?'),
        ('interfaceMinimap', 'show_interface_minimap', 'Show UI Minimap?'),
        ('interfaceTimeline', 'show_interface_timeline', 'Show UI Timeline?'),
        ('interfaceChat', 'show_interface_chat', 'Show UI Chat?'),
        ('interfaceTarget', 'show_interface_target', 'Show UI Target?'),
        ('interfaceQuests', 'show_interface_quests', 'Show UI Quests?'),
        ('interfaceAnnounce', 'show_interface_announce', 'Show UI Announcements?'),
        ('interfaceKillCallouts', 'show_interface_killcallouts', 'Show Kill Callouts?'),
        ('interfaceNeutralTimers', 'show_interface_neutraltimers', 'Show Neutral Timers?'),
        ('healthBarChampions', 'show_healthbar_champions', 'Show Health Champions?'),
        ('healthBarStructures', 'show_healthbar_structures', 'Show Health Structures?'),
        ('healthBarWards', 'show_healthbar_wards', 'Show Health Wards?'),
        ('healthBarPets', 'show_healthbar_pets', 'Show Health Pets?'),
        ('healthBarMinions', 'show_healthbar_minions', 'Show Health Minions?'),
        ('environment', 'show_environment', 'Show Environment?'),
        ('characters', 'show_characters', 'Show Characters?'),
        ('champions', 'show_champions', 'Show Champions?'),
        ('minions', 'show_minions', 'Show Minions?'),
        ('particles', 'show_particles', 'Show Particles?'),
        ('banners', 'show_banners', 'Show Banners?'),
    ]

    def __init__(self, api):
        QScrollArea.__init__(self)
        self.api = api
        self.api.render.updated.connect(self.update)
        self.api.connected.connect(self.connect)
        self.inputs = {}
        self.bindings = {}
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWindowTitle('Visibility')
        widget = QWidget()
        layout = QFormLayout()
        for name, binding, label in self.options:
            self.inputs[name] = BooleanInput()
            self.inputs[name].setValue(True)
            self.inputs[name].valueChanged.connect(functools.partial(self.api.render.set, name))
            self.bindings[binding] = name
            layout.addRow(label, self.inputs[name])
        widget.setLayout(layout)
        self.setWidget(widget)

    def connect(self):
        for name, field in self.inputs.items():
            self.api.render.set(name, field.value())

    def update(self):
        for name, field in self.inputs.items():
            field.setValue(self.api.render.get(name))

    def restoreSettings(self, data):
        for name, value in data.items():
            if name in self.inputs:
                self.inputs[name].update(value)
                self.api.render.set(name, value)

    def saveSettings(self):
        return {name:self.api.render.get(name) for name in self.inputs}

    def onKeybinding(self, name):
        if name in self.bindings:
            self.inputs[self.bindings[name]].toggle()


class RenderWindow(QScrollArea):
    def __init__(self, api):
        QScrollArea.__init__(self)
        self.api = api
        self.api.render.updated.connect(self.update)
        self.cameraMode = QLabel('')
        self.cameraLockX = BooleanInput('X')
        self.cameraLockY = BooleanInput('Y')
        self.cameraLockZ = BooleanInput('Z')
        self.cameraMoveBackX = BooleanInput('X')
        self.cameraMoveBackY = BooleanInput('Y')
        self.cameraMoveBackZ = BooleanInput('Z')
        self.cameraPosition = VectorInput()
        self.cameraPosition.setSingleStep(10)
        self.cameraRotation = VectorInput([0, -90, -90], [360, 90, 90])
        self.cameraAttached = BooleanInput()
        self.cameraMoveSpeed = FloatInput(0, 5000)
        self.cameraMoveSpeed.setRelativeStep(0.1)
        self.cameraLookSpeed = FloatInput(0.01, 5)
        self.cameraLookSpeed.setSingleStep(0.01)
        self.fieldOfView = FloatInput(0, 180)
        self.nearClip = FloatInput()
        self.nearClip.setRelativeStep(0.05)
        self.farClip = FloatInput()
        self.farClip.setRelativeStep(0.05)
        self.navGrid = FloatInput(-100, 100)
        self.simulateAllParticlesWhileOffScreen = BooleanInput()
        self.skyboxes = SkyboxCombo()
        self.skyboxRotation = FloatInput(-180, 180)
        self.skyboxOffset = FloatInput(-10000000, 10000000)
        self.skyboxRadius = FloatInput(0, 10000000)
        self.skyboxRadius.setSingleStep(10)
        self.sunDirection = VectorInput()
        self.sunDirection.setSingleStep(0.1)
        self.depthFogEnabled = BooleanInput()
        self.depthFogStart = FloatInput(0, 100000)
        self.depthFogStart.setRelativeStep(0.05)
        self.depthFogEnd = FloatInput(0, 100000)
        self.depthFogEnd.setRelativeStep(0.05)
        self.depthFogIntensity = FloatInput(0, 1)
        self.depthFogIntensity.setSingleStep(0.05)
        self.depthFogColor = ColorInput()
        self.heightFogEnabled = BooleanInput()
        self.heightFogStart = FloatInput(-100000, 100000)
        self.heightFogStart.setSingleStep(100)
        self.heightFogEnd = FloatInput(-100000, 100000)
        self.heightFogEnd.setSingleStep(100)
        self.heightFogIntensity = FloatInput(0, 1)
        self.heightFogIntensity.setSingleStep(0.05)
        self.heightFogColor = ColorInput()
        self.depthOfFieldEnabled = BooleanInput()
        self.depthOfFieldDebug = BooleanInput()
        self.depthOfFieldCircle = FloatInput(0, 300)
        self.depthOfFieldWidth = FloatInput(0, 100000)
        self.depthOfFieldWidth.setSingleStep(100)
        self.depthOfFieldNear = FloatInput(0, 100000)
        self.depthOfFieldNear.setRelativeStep(0.05)
        self.depthOfFieldMid = FloatInput(0, 100000)
        self.depthOfFieldMid.setRelativeStep(0.05)
        self.depthOfFieldFar = FloatInput(0, 100000)
        self.depthOfFieldFar.setRelativeStep(0.05)
        self.cameraLockX.valueChanged.connect(functools.partial(self.api.render.set, 'cameraLockX'))
        self.cameraLockY.valueChanged.connect(functools.partial(self.api.render.set, 'cameraLockY'))
        self.cameraLockZ.valueChanged.connect(functools.partial(self.api.render.set, 'cameraLockZ'))
        self.cameraMoveBackX.valueChanged.connect(self.api.render.toggleCameraMoveBackX)
        self.cameraMoveBackY.valueChanged.connect(self.api.render.toggleCameraMoveBackY)
        self.cameraMoveBackZ.valueChanged.connect(self.api.render.toggleCameraMoveBackZ)
        self.cameraPosition.valueChanged.connect(functools.partial(self.api.render.set, 'cameraPosition'))
        self.cameraRotation.valueChanged.connect(functools.partial(self.api.render.set, 'cameraRotation'))
        self.cameraAttached.valueChanged.connect(functools.partial(self.api.render.set, 'cameraAttached'))
        self.cameraMoveSpeed.valueChanged.connect(functools.partial(self.api.render.set, 'cameraMoveSpeed'))
        self.cameraLookSpeed.valueChanged.connect(functools.partial(self.api.render.set, 'cameraLookSpeed'))
        self.fieldOfView.valueChanged.connect(functools.partial(self.api.render.set, 'fieldOfView'))
        self.nearClip.valueChanged.connect(functools.partial(self.api.render.set, 'nearClip'))
        self.farClip.valueChanged.connect(functools.partial(self.api.render.set, 'farClip'))
        self.navGrid.valueChanged.connect(functools.partial(self.api.render.set, 'navGridOffset'))
        self.simulateAllParticlesWhileOffScreen.valueChanged.connect(functools.partial(self.api.render.set, 'simulateAllParticlesWhileOffScreen'))
        self.skyboxes.activated.connect(lambda index: self.api.render.set('skyboxPath', self.skyboxes.itemData(index)))
        self.skyboxRotation.valueChanged.connect(functools.partial(self.api.render.set, 'skyboxRotation'))
        self.skyboxRadius.valueChanged.connect(functools.partial(self.api.render.set, 'skyboxRadius'))
        self.skyboxOffset.valueChanged.connect(functools.partial(self.api.render.set, 'skyboxOffset'))
        self.sunDirection.valueChanged.connect(functools.partial(self.api.render.set, 'sunDirection'))
        self.depthFogEnabled.valueChanged.connect(functools.partial(self.api.render.set, 'depthFogEnabled'))
        self.depthFogStart.valueChanged.connect(functools.partial(self.api.render.set, 'depthFogStart'))
        self.depthFogEnd.valueChanged.connect(functools.partial(self.api.render.set, 'depthFogEnd'))
        self.depthFogIntensity.valueChanged.connect(functools.partial(self.api.render.set, 'depthFogIntensity'))
        self.depthFogColor.valueChanged.connect(functools.partial(self.api.render.set, 'depthFogColor'))
        self.heightFogEnabled.valueChanged.connect(functools.partial(self.api.render.set, 'heightFogEnabled'))
        self.heightFogStart.valueChanged.connect(functools.partial(self.api.render.set, 'heightFogStart'))
        self.heightFogEnd.valueChanged.connect(functools.partial(self.api.render.set, 'heightFogEnd'))
        self.heightFogIntensity.valueChanged.connect(functools.partial(self.api.render.set, 'heightFogIntensity'))
        self.heightFogColor.valueChanged.connect(functools.partial(self.api.render.set, 'heightFogColor'))
        self.depthOfFieldEnabled.valueChanged.connect(functools.partial(self.api.render.set, 'depthOfFieldEnabled'))
        self.depthOfFieldDebug.valueChanged.connect(functools.partial(self.api.render.set, 'depthOfFieldDebug'))
        self.depthOfFieldCircle.valueChanged.connect(functools.partial(self.api.render.set, 'depthOfFieldCircle'))
        self.depthOfFieldWidth.valueChanged.connect(functools.partial(self.api.render.set, 'depthOfFieldWidth'))
        self.depthOfFieldNear.valueChanged.connect(functools.partial(self.api.render.set, 'depthOfFieldNear'))
        self.depthOfFieldMid.valueChanged.connect(functools.partial(self.api.render.set, 'depthOfFieldMid'))
        self.depthOfFieldFar.valueChanged.connect(functools.partial(self.api.render.set, 'depthOfFieldFar'))

        widget = QWidget()
        layout = QFormLayout()
        layout.addRow('Camera Mode', self.cameraMode)
        layout.addRow('Camera Lock', HBoxWidget(self.cameraLockX, self.cameraLockY, self.cameraLockZ))
        layout.addRow('Camera Move Back To', HBoxWidget(self.cameraMoveBackX, self.cameraMoveBackY, self.cameraMoveBackZ))
        layout.addRow('Camera Position', self.cameraPosition)
        layout.addRow('Camera Position', self.cameraPosition)
        layout.addRow('Camera Rotation', self.cameraRotation)
        layout.addRow('Camera Attached', self.cameraAttached)
        layout.addRow('Camera Move Speed', self.cameraMoveSpeed)
        layout.addRow('Camera Look Speed', self.cameraLookSpeed)
        layout.addRow('Field of View', self.fieldOfView)
        layout.addRow('Near Clip', self.nearClip)
        layout.addRow('Far Clip', self.farClip)
        layout.addRow('Nav Grid Offset', self.navGrid)
        layout.addRow('Simulate All Particles While Offscreen', self.simulateAllParticlesWhileOffScreen)
        layout.addRow(Separator())
        layout.addRow('Skybox', self.skyboxes)
        layout.addRow('Skybox Rotation', self.skyboxRotation)
        layout.addRow('Skybox Offset', self.skyboxOffset)
        layout.addRow('Skybox Radius', self.skyboxRadius)
        layout.addRow('Sun Direction', self.sunDirection)
        layout.addRow(Separator())
        layout.addRow('Depth Fog', self.depthFogEnabled)
        layout.addRow('Depth Fog Start', self.depthFogStart)
        layout.addRow('Depth Fog End', self.depthFogEnd)
        layout.addRow('Depth Fog Intensity', self.depthFogIntensity)
        layout.addRow('Depth Fog Color', self.depthFogColor)
        layout.addRow(Separator())
        layout.addRow('Height Fog', self.heightFogEnabled)
        layout.addRow('Height Fog Start', self.heightFogStart)
        layout.addRow('Height Fog End', self.heightFogEnd)
        layout.addRow('Height Fog Intensity', self.heightFogIntensity)
        layout.addRow('Height Fog Color', self.heightFogColor)
        layout.addRow(Separator())
        layout.addRow('Depth of Field', self.depthOfFieldEnabled)
        layout.addRow('Depth of Field Debug', self.depthOfFieldDebug)
        layout.addRow('Depth of Field Circle', self.depthOfFieldCircle)
        layout.addRow('Depth of Field Width', self.depthOfFieldWidth)
        layout.addRow('Depth of Field Near', self.depthOfFieldNear)
        layout.addRow('Depth of Field Mid', self.depthOfFieldMid)
        layout.addRow('Depth of Field Far', self.depthOfFieldFar)
        widget.setLayout(layout)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(widget)
        self.setWindowTitle('Rendering')

    def update(self):
        self.cameraLockX.update(self.api.render.cameraLockX)
        self.cameraLockY.update(self.api.render.cameraLockY)
        self.cameraLockZ.update(self.api.render.cameraLockZ)
        self.cameraMoveBackX.update(self.api.render.cameraMoveBackX is not None)
        self.cameraMoveBackY.update(self.api.render.cameraMoveBackY is not None)
        self.cameraMoveBackZ.update(self.api.render.cameraMoveBackZ is not None)
        self.cameraMoveBackX.setCheckboxText('{0:.2f}'.format(self.api.render.cameraMoveBackX) if self.api.render.cameraMoveBackX else 'X')
        self.cameraMoveBackY.setCheckboxText('{0:.2f}'.format(self.api.render.cameraMoveBackY) if self.api.render.cameraMoveBackY else 'Y')
        self.cameraMoveBackZ.setCheckboxText('{0:.2f}'.format(self.api.render.cameraMoveBackZ) if self.api.render.cameraMoveBackZ else 'Z')
        self.cameraMode.setText(self.api.render.cameraMode)
        self.cameraPosition.update(self.api.render.cameraPosition)
        self.cameraRotation.update(self.api.render.cameraRotation)
        self.cameraAttached.update(self.api.render.cameraAttached)
        self.cameraMoveSpeed.update(self.api.render.cameraMoveSpeed)
        self.cameraLookSpeed.update(self.api.render.cameraLookSpeed)
        self.fieldOfView.update(self.api.render.fieldOfView)
        self.nearClip.update(self.api.render.nearClip)
        self.farClip.update(self.api.render.farClip)
        self.navGrid.update(self.api.render.navGridOffset)
        self.simulateAllParticlesWhileOffScreen.update(self.api.render.simulateAllParticlesWhileOffScreen)
        self.skyboxRotation.update(self.api.render.skyboxRotation)
        self.skyboxRadius.update(self.api.render.skyboxRadius)
        self.skyboxOffset.update(self.api.render.skyboxOffset)
        self.skyboxOffset.setRange(-self.api.render.skyboxRadius, self.api.render.skyboxRadius)
        self.skyboxOffset.setSingleStep(self.api.render.skyboxRadius / 1000)
        self.sunDirection.update(self.api.render.sunDirection)
        self.depthFogEnabled.update(self.api.render.depthFogEnabled)
        self.depthFogStart.update(self.api.render.depthFogStart)
        self.depthFogEnd.update(self.api.render.depthFogEnd)
        self.depthFogIntensity.update(self.api.render.depthFogIntensity)
        self.depthFogColor.update(self.api.render.depthFogColor)
        self.heightFogEnabled.update(self.api.render.heightFogEnabled)
        self.heightFogStart.update(self.api.render.heightFogStart)
        self.heightFogEnd.update(self.api.render.heightFogEnd)
        self.heightFogIntensity.update(self.api.render.heightFogIntensity)
        self.heightFogColor.update(self.api.render.heightFogColor)
        self.depthOfFieldEnabled.update(self.api.render.depthOfFieldEnabled)
        self.depthOfFieldDebug.update(self.api.render.depthOfFieldDebug)
        self.depthOfFieldCircle.update(self.api.render.depthOfFieldCircle)
        self.depthOfFieldWidth.update(self.api.render.depthOfFieldWidth)
        self.depthOfFieldNear.update(self.api.render.depthOfFieldNear)
        self.depthOfFieldMid.update(self.api.render.depthOfFieldMid)
        self.depthOfFieldFar.update(self.api.render.depthOfFieldFar)


class ParticlesWindow(VBoxWidget):
    def __init__(self, api):
        VBoxWidget.__init__(self)
        self.api = api
        self.api.connected.connect(self.connect)
        self.api.particles.updated.connect(self.update)
        self.items = {}
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search...')
        self.search.textEdited.connect(self.textEdited)
        self.list = QListWidget()
        self.list.setSortingEnabled(True)
        self.list.itemChanged.connect(self.itemChanged)
        self.addWidget(self.search)
        self.addWidget(self.list)
        self.setWindowTitle('Particles')

    def textEdited(self, text):
        search = text.lower()
        for particle, item in self.items.items():
            if len(search) == 0 or search in particle.lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def itemChanged(self, item):
        particle = item.text()
        enabled = item.checkState() == Qt.Checked
        if enabled != self.api.particles.getParticle(particle):
            self.api.particles.setParticle(particle, enabled)

    def update(self):
        for particle, enabled in self.api.particles.items():
            if particle not in self.items:
                item = QListWidgetItem(particle)
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setBackground(QApplication.palette().toolTipBase())
                self.list.addItem(item)
                self.items[particle] = item
            self.items[particle].setCheckState(Qt.Checked if enabled else Qt.Unchecked)
        for particle in list(self.items):
            if not self.api.particles.hasParticle(particle):
                item = self.items.pop(particle)
                self.list.takeItem(self.list.row(item))

    def connect(self):
        self.search.clear()


class RecordingWindow(VBoxWidget):
    def __init__(self, api):
        VBoxWidget.__init__(self)
        self.api = api
        self.api.recording.updated.connect(self.update)
        self.recordings = set()

        self.codec = QComboBox()
        self.codec.addItem('webm')
        self.codec.addItem('png')
        self.startTime = FloatInput(0, 100)
        self.endTime = FloatInput(0, 100)
        self.fps = FloatInput(0, 400)
        self.fps.setValue(60)
        self.lossless = BooleanInput()

        self.outputPath = userpath('recordings')
        self.outputLabel = QLabel()
        self.outputLabel.setTextFormat(Qt.RichText)
        self.outputLabel.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.outputLabel.setOpenExternalLinks(True)

        self.outputButton = QPushButton()
        self.outputButton.setToolTip('Change Output Directory')
        self.outputButton.setFixedWidth(30)
        self.outputButton.setIcon(self.style().standardIcon(QStyle.SP_FileDialogStart))
        self.outputButton.clicked.connect(self.selectOutputDirectory)

        self.button = QPushButton('Record')
        self.button.clicked.connect(self.startRecording)
        self.button2 = QPushButton('Record Sequence')
        self.button2.clicked.connect(self.recordSequence)
        self.list = QListWidget()
        self.list.setSortingEnabled(True)
        self.list.itemDoubleClicked.connect(self.openRecording)

        self.form = QWidget(self)
        self.formLayout = QFormLayout(self.form)
        self.formLayout.addRow('Codec', self.codec)
        self.formLayout.addRow('Start Time', self.startTime)
        self.formLayout.addRow('End Time', self.endTime)
        self.formLayout.addRow('Frames Per Second', self.fps)
        self.formLayout.addRow('Lossless Encoding', self.lossless)
        self.formLayout.addRow('Output Directory', HBoxWidget(self.outputButton, self.outputLabel))
        self.formLayout.addRow(HBoxWidget(self.button, self.button2))
        self.formLayout.addRow(self.list)
        self.form.setLayout(self.formLayout)

        self.render = QWidget(self)
        self.progress = QProgressBar()
        self.cancel = QPushButton('Cancel Recording')
        self.cancel.clicked.connect(self.stopRecording)
        self.renderLayout = QFormLayout()
        self.renderLayout.addRow(QLabel('Rendering video...'))
        self.renderLayout.addRow(self.progress)
        self.renderLayout.addRow(self.cancel)
        self.render.setLayout(self.renderLayout)

        self.addWidget(self.form)
        self.addWidget(self.render)
        self.setWindowTitle('Recording')

    def update(self):
        self.startTime.setRange(0, self.api.playback.length)
        self.endTime.setRange(0, self.api.playback.length)
        self.render.setVisible(self.api.recording.recording)
        self.form.setVisible(not self.api.recording.recording)
        if self.api.recording.recording:
            self.progress.setMinimum(self.api.recording.startTime * 1000)
            self.progress.setMaximum(self.api.recording.endTime * 1000)
            self.progress.setValue(self.api.recording.currentTime * 1000)
            if self.api.recording.path not in self.recordings:
                self.list.addItem(self.api.recording.path)
                self.recordings.add(self.api.recording.path)

    def selectOutputDirectory(self):
        self.setOutputDirectory(QFileDialog.getExistingDirectory(self, 'Select Output Directory', self.outputPath))

    def openRecording(self, item):
        QDesktopServices.openUrl(QUrl('file:///{}'.format(item.text())))

    def stopRecording(self):
        self.api.recording.update({'recording' : False})

    def startRecording(self):
        self.api.playback.play()
        self.api.recording.update({
            'recording' : True,
            'codec' : self.codec.currentText(),
            'startTime' : self.startTime.value(),
            'endTime' : self.endTime.value(),
            'framesPerSecond' : self.fps.value(),
            'enforceFrameRate' : True,
            'lossless' : self.lossless.value(),
            'path' : self.outputPath,
        })

    def setOutputDirectory(self, path):
        if os.path.exists(path):
            self.outputPath = path
            self.outputLabel.setText("<a href=\"file:///{}\">{}</a>".format(path, path))

    def recordSequence(self):
        self.api.sequence.setSequencing(True)
        self.startTime.setValue(self.api.sequence.startTime)
        self.endTime.setValue(self.api.sequence.endTime)
        self.startRecording()

    def saveSettings(self):
        return {'output': self.outputPath}

    def restoreSettings(self, data):
        self.setOutputDirectory(data.get('output', self.outputPath))


class TimelineWindow(QWidget):
    def __init__(self, api):
        QWidget.__init__(self)
        self.api = api
        self.api.playback.updated.connect(self.update)
        self.api.sequence.updated.connect(self.update)
        self.timer = schedule(10, self.animate)
        self.sequenceHeaders = SequenceHeaderView(self.api)
        self.sequenceTracks = SequenceTrackView(self.api, self.sequenceHeaders)
        layout = QVBoxLayout()
        self.layoutSpeed(layout)
        self.layoutTimeButtons(layout)
        self.layoutSlider(layout)
        self.layoutSequencer(layout)
        self.setWindowTitle('Timeline')
        self.setLayout(layout)

    def saveSettings(self):
        return {'directory': self.api.sequence.directory}

    def restoreSettings(self, data):
        self.api.sequence.setDirectory(data.get('directory', userpath('sequences')))

    def selectDirectory(self):
        self.api.sequence.setDirectory(QFileDialog.getExistingDirectory(self, 'Select Directory', self.api.sequence.directory))

    def layoutSequencer(self, layout):
        self.sequenceCombo = SequenceCombo(self.api)
        self.sequenceButton = QPushButton()
        self.sequenceButton.setToolTip('Open Directory')
        self.sequenceButton.setFixedWidth(30)
        self.sequenceButton.setIcon(self.style().standardIcon(QStyle.SP_FileDialogStart))
        self.sequenceButton.clicked.connect(self.selectDirectory)
        layout.addWidget(HBoxWidget(self.sequenceCombo, self.sequenceButton))

        widget = HBoxWidget()
        self.applySequence = BooleanInput('Apply Sequence?')
        self.applySequence.valueChanged.connect(self.api.sequence.setSequencing)
        widget.addWidget(self.applySequence)
        playSequence = QPushButton('Play Sequence')
        playSequence.setMaximumWidth(150)
        playSequence.clicked.connect(self.playSequence)
        widget.addWidget(playSequence)
        copySequence = QPushButton('Copy Sequence')
        copySequence.setMaximumWidth(150)
        copySequence.clicked.connect(self.copySequence)
        widget.addWidget(copySequence)
        newSequence = QPushButton('New Sequence')
        newSequence.setMaximumWidth(150)
        newSequence.clicked.connect(self.newSequence)
        widget.addWidget(newSequence)
        layout.addWidget(widget)

        widget = HBoxWidget()
        widget.addWidget(self.sequenceHeaders)
        widget.addWidget(self.sequenceTracks)
        layout.addWidget(widget)

        sequenceSelection = SequenceSelectedView(self.api, self.sequenceTracks)
        layout.addWidget(sequenceSelection)

    def layoutSpeed(self, layout):
        widget = HBoxWidget()
        self.play = QPushButton("")
        self.play.clicked.connect(self.api.playback.togglePlay)
        widget.addWidget(self.play)
        self.speed = FloatSlider('Speed')
        self.speed.setRange(0, 8.0)
        self.speed.setSingleStep(0.1)
        self.speed.valueChanged.connect(lambda: self.api.playback.setSpeed(self.speed.value()))
        widget.addWidget(self.speed)
        for speed in [0.5, 1, 2, 4]:
            button = QPushButton("x{}".format(speed))
            button.setMaximumWidth(35)
            button.clicked.connect(functools.partial(self.api.playback.setSpeed, speed))
            widget.addWidget(button)
        layout.addWidget(widget)

    def layoutTimeButtons(self, layout):
        widget = HBoxWidget()
        for delta in [-120, -60, -30, -10, -5, 5, 10, 30, 60, 120]:
            sign = '+' if delta > 0 else ''
            button = QPushButton('{}{}s'.format(sign, delta))
            button.setMinimumWidth(40)
            button.clicked.connect(functools.partial(self.api.playback.adjustTime, delta))
            widget.addWidget(button)
        layout.addWidget(widget)

    def layoutSlider(self, layout):
        widget = VBoxWidget()
        self.timeLabel = QLabel("")
        self.timeSlider = QSlider(Qt.Horizontal)
        self.timeSlider.setTickPosition(QSlider.TicksBelow)
        self.timeSlider.setTickInterval(60000)
        self.timeSlider.setTracking(False)
        self.timeSlider.sliderReleased.connect(self.onTimeline)
        widget.addWidget(self.timeLabel)
        widget.addWidget(self.timeSlider)
        layout.addWidget(widget)

    def onTimeline(self):
        self.api.playback.time = self.timeSlider.sliderPosition() / 1000

    def newSequence(self):
        name, ok = QInputDialog.getText(self, 'Create New Sequence', 'Enter a name for your sequence')
        if ok:
            self.api.sequence.create(name)

    def copySequence(self):
        name, ok = QInputDialog.getText(self, 'Copy Sequence', 'Enter a name to save a new copy of your sequence')
        if ok:
            self.api.sequence.copy(name)

    def playSequence(self):
        self.api.sequence.setSequencing(True)
        self.api.playback.play(self.api.sequence.startTime)

    def onKeybinding(self, name):
        if name == 'sequence_del_kf':
            self.sequenceTracks.deleteSelectedKeyframes()
        elif name == 'sequence_next_kf':
            self.sequenceTracks.selectNextKeyframe()
        elif name == 'sequence_prev_kf':
            self.sequenceTracks.selectPrevKeyframe()
        elif name == 'sequence_adj_kf':
            self.sequenceTracks.selectAdjacentKeyframes()
        elif name == 'sequence_all_kf':
            self.sequenceTracks.selectAllKeyframes()
        elif name == 'sequence_seek_kf':
            self.sequenceTracks.seekSelectedKeyframe()
        elif name == 'sequence_apply':
            self.applySequence.toggle()
        elif name == 'sequence_play':
            self.playSequence()
        elif name == 'sequence_new':
            self.newSequence()
        elif name == 'sequence_copy':
            self.copySequence()
        elif name == 'sequence_clear':
            self.sequenceTracks.clearKeyframes()
        elif name == 'sequence_undo':
            self.api.sequence.undo()
        elif name == 'sequence_redo':
            self.api.sequence.redo()
        elif name == 'kf_position':
            self.sequenceTracks.addKeyframe('cameraPosition')
        elif name == 'kf_rotation':
            self.sequenceTracks.addKeyframe('cameraRotation')
        elif name == 'kf_speed':
            self.sequenceTracks.addKeyframe('playbackSpeed')
        elif name == 'kf_fov':
            self.sequenceTracks.addKeyframe('fieldOfView')
        elif name == 'kf_near_clip':
            self.sequenceTracks.addKeyframe('nearClip')
        elif name == 'kf_far_clip':
            self.sequenceTracks.addKeyframe('farClip')
        elif name == 'kf_nav_grid':
            self.sequenceTracks.addKeyframe('navGridOffset')
        elif name == 'kf_sky_rotation':
            self.sequenceTracks.addKeyframe('skyboxRotation')
        elif name == 'kf_sky_radius':
            self.sequenceTracks.addKeyframe('skyboxRadius')
        elif name == 'kf_sky_offset':
            self.sequenceTracks.addKeyframe('skyboxOffset')
        elif name == 'kf_sun_direction':
            self.sequenceTracks.addKeyframe('sunDirection')
        elif name == 'kf_depth_fog_enable':
            self.sequenceTracks.addKeyframe('depthFogEnabled')
        elif name == 'kf_depth_fog_start':
            self.sequenceTracks.addKeyframe('depthFogStart')
        elif name == 'kf_depth_fog_end':
            self.sequenceTracks.addKeyframe('depthFogEnd')
        elif name == 'kf_depth_fog_intensity':
            self.sequenceTracks.addKeyframe('depthFogIntensity')
        elif name == 'kf_depth_fog_color':
            self.sequenceTracks.addKeyframe('depthFogColor')
        elif name == 'kf_height_fog_enable':
            self.sequenceTracks.addKeyframe('heightFogEnabled')
        elif name == 'kf_height_fog_start':
            self.sequenceTracks.addKeyframe('heightFogStart')
        elif name == 'kf_height_fog_end':
            self.sequenceTracks.addKeyframe('heightFogEnd')
        elif name == 'kf_height_fog_intensity':
            self.sequenceTracks.addKeyframe('heightFogIntensity')
        elif name == 'kf_height_fog_color':
            self.sequenceTracks.addKeyframe('heightFogColor')
        elif name == 'kf_dof_enabled':
            self.sequenceTracks.addKeyframe('depthOfFieldEnabled')
        elif name == 'kf_dof_circle':
            self.sequenceTracks.addKeyframe('depthOfFieldCircle')
        elif name == 'kf_dof_width':
            self.sequenceTracks.addKeyframe('depthOfFieldWidth')
        elif name == 'kf_dof_near':
            self.sequenceTracks.addKeyframe('depthOfFieldNear')
        elif name == 'kf_dof_mid':
            self.sequenceTracks.addKeyframe('depthOfFieldMid')
        elif name == 'kf_dof_far':
            self.sequenceTracks.addKeyframe('depthOfFieldFar')

    def formatTime(self, t):
        minutes, seconds = divmod(t, 60)
        return '{0:02}:{1:05.2f}'.format(int(minutes), seconds)

    def animate(self):
        self.speed.update(self.api.playback.speed)
        self.timeSlider.setRange(0, self.api.playback.length * 1000)
        if self.timeSlider.isSliderDown():
            self.timeLabel.setText(self.formatTime(self.timeSlider.sliderPosition() / 1000))
        else:
            self.timeLabel.setText(self.formatTime(self.api.playback.currentTime))
            self.timeSlider.setValue(self.api.playback.currentTime * 1000)

    def update(self):
        self.applySequence.update(self.api.sequence.sequencing)
        if self.api.playback.seeking:
            self.play.setDisabled(True)
            self.play.setText('Seeking')
        elif self.api.playback.paused:
            self.play.setDisabled(False)
            self.play.setText('Play')
        else:
            self.play.setDisabled(False)
            self.play.setText('Pause')
