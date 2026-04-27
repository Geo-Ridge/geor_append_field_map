# -*- coding: utf-8 -*-
"""
/***************************************************************************
                     Append Features With Field Mapping
                      --------------------
        begin                : 2024-01-01
        copyright            : (C) 2024
        email                :
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation.                                        *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import (QgsApplication, Qgis)
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtWidgets import QApplication

from .processing.field_mapping_provider import FieldMappingAlgorithmProvider


STYLESHEET_HIDE_ICONS = """
QToolButton[qgisProcessParameterSelectionButton="true"] { min-width: 0px; max-width: 0px; width: 0px; border: none; background: none; }
"""


class AppendFeaturesWithFieldMappingPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.stylesheet_applied = False

    def applyStylesheet(self):
        if not self.stylesheet_applied:
            QApplication.instance().setStyleSheet(STYLESHEET_HIDE_ICONS)
            self.stylesheet_applied = True
            QTimer.singleShot(100, self.resetStylesheet)

    def resetStylesheet(self):
        QApplication.instance().setStyleSheet("")
        self.stylesheet_applied = False

    def initProcessing(self):
        self.provider = FieldMappingAlgorithmProvider()
        if hasattr(QgsApplication, 'processingRegistry'):
            from qgis.core import (QgsApplication as qgis_app)
            qgis_app.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        QTimer.singleShot(100, self.applyStylesheet)

    def unload(self):
        if hasattr(QgsApplication, 'processingRegistry') and self.provider:
            from qgis.core import (QgsApplication as qgis_app)
            qgis_app.processingRegistry().removeProvider(self.provider)
