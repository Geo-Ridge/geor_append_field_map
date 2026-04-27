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
from qgis.core import (QgsProcessingProvider,)
from qgis.PyQt.QtGui import QIcon

from .algs.AppendFeaturesWithFieldMapping import AppendFeaturesWithFieldMapping


class FieldMappingAlgorithmProvider(QgsProcessingProvider):

    def __init__(self):
        super().__init__()

    def load(self):
        self.refreshAlgorithms()
        return True

    def unload(self):
        pass

    def isActive(self):
        return True

    def id(self):
        return 'field_mapping'

    def name(self):
        return 'Append Features With Field Mapping'

    def icon(self):
        return QIcon()

    def loadAlgorithms(self):
        self.addAlgorithm(AppendFeaturesWithFieldMapping())
