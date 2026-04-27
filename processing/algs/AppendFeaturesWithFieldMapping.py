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
from qgis.PyQt.QtCore import (QVariant, QDate, QDateTime, QCoreApplication, QMetaType, NULL)

from qgis.core import (edit,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingOutputVectorLayer,
                       QgsProject,
                       QgsVectorLayerUtils,
                       QgsVectorDataProvider,
                       QgsProcessingOutputNumber,
                       QgsFeatureRequest,
                       QgsProcessingParameterFieldMapping)


class AppendFeaturesWithFieldMapping(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    FIELD_MAPPING = 'FIELD_MAPPING'
    OUTPUT = 'OUTPUT'
    APPENDED_COUNT = 'APPENDED_COUNT'

    def createInstance(self):
        return type(self)()

    def group(self):
        return QCoreApplication.translate("AppendFeaturesWithFieldMapping", 'Vector table')

    def groupId(self):
        return 'vectortable'

    def tags(self):
        return QCoreApplication.translate("AppendFeaturesWithFieldMapping", 'append,copy,field mapping,features').split(',')

    def __init__(self):
        super().__init__()

    def shortHelpString(self):
        return QCoreApplication.translate("AppendFeaturesWithFieldMapping",
            "This algorithm copies features from a source layer into a target layer with custom field mapping.\n\n"
            "You can map source fields to target fields and apply transformations.")

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.INPUT,
            QCoreApplication.translate("AppendFeaturesWithFieldMapping", 'Source layer'),
            [QgsProcessing.TypeVector]))
        self.addParameter(QgsProcessingParameterFieldMapping(self.FIELD_MAPPING,
            QCoreApplication.translate("AppendFeaturesWithFieldMapping", 'Field mapping'),
            self.INPUT))
        self.addParameter(QgsProcessingParameterVectorLayer(self.OUTPUT,
            QCoreApplication.translate("AppendFeaturesWithFieldMapping", 'Target layer'),
            [QgsProcessing.TypeVector]))
        self.addOutput(QgsProcessingOutputVectorLayer('OUTPUT_LAYER',
            QCoreApplication.translate("AppendFeaturesWithFieldMapping", "Target layer")))
        self.addOutput(QgsProcessingOutputNumber(self.APPENDED_COUNT,
            QCoreApplication.translate("AppendFeaturesWithFieldMapping", "Number of features appended")))

    def name(self):
        return 'appendfeatureswithfieldmapping'

    def displayName(self):
        return QCoreApplication.translate("AppendFeaturesWithFieldMapping", 'Append features with field mapping')

    def convertValue(self, value, target_type, field_name=''):
        if value is NULL or value is None or value == '':
            return QVariant(target_type)

        force_datetime = any(dt_name in field_name.lower() for dt_name in ['date', 'datetime', 'time'])

        if target_type == QVariant.DateTime or target_type == 16 or force_datetime:
            if isinstance(value, QDateTime):
                return value
            if isinstance(value, QDate):
                return QDateTime(value)
            if isinstance(value, (int, float)):
                try:
                    import datetime
                    return QDateTime.fromSecsSinceEpoch(int(value))
                except:
                    pass
            if isinstance(value, str) and value:
                from datetime import datetime
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        dt = datetime.strptime(value, fmt)
                        return QDateTime(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
                    except:
                        pass
            return QDateTime()

        if target_type == QVariant.Date or target_type == 14:
            if isinstance(value, QDate):
                return value
            if isinstance(value, QDateTime):
                return value.date()
            if isinstance(value, (int, float)):
                try:
                    import datetime
                    dt = datetime.datetime.fromtimestamp(int(value))
                    return QDate(dt.year, dt.month, dt.day)
                except:
                    pass
            if isinstance(value, str) and value:
                from datetime import datetime
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                    try:
                        d = datetime.strptime(value, fmt)
                        return QDate(d.year, d.month, d.day)
                    except:
                        pass
            return QDate()

        if target_type == QVariant.Int or target_type == QVariant.LongLong or target_type == 2 or target_type == 4:
            try:
                return int(value)
            except:
                return QVariant(target_type)

        if target_type == QVariant.Double or target_type == 6:
            try:
                return float(value)
            except:
                return QVariant(target_type)

        return value

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT, context)
        target = self.parameterAsVectorLayer(parameters, self.OUTPUT, context)
        field_mapping = parameters[self.FIELD_MAPPING]

        results = {
            'OUTPUT_LAYER': None,
            self.APPENDED_COUNT: 0
        }

        if target.isEditable():
            feedback.reportError("\nWARNING: Close the edit session on layer '{}' before running.".format(target.name()))
            return results

        caps = target.dataProvider().capabilities()
        if not (caps & QgsVectorDataProvider.AddFeatures):
            feedback.reportError("\nWARNING: The target layer does not support appending features!")
            return results

        destType = target.geometryType()
        destIsMulti = QgsWkbTypes.isMultiType(target.wkbType())
        new_features = []

        mapping = dict()
        datetime_field_names = ['date', 'datetime', 'time']
        for target_idx in target.fields().allAttributesList():

            target_field = target.fields().field(target_idx)
            target_field_name_lower = target_field.name().lower()

            if target_idx in target.primaryKeyAttributes():
                if target.dataProvider().storageType() == 'GPKG' and target_field.name() == 'fid':
                    continue
                if target.dataProvider().defaultValueClause(target_idx) not in ['', 'nextval(NULL)']:
                    continue

            source_idx = -1
            force_datetime = any(dt_name in target_field_name_lower for dt_name in datetime_field_names)

            if field_mapping:
                for config in field_mapping:
                    if isinstance(config, dict):
                        target_name = config.get('name', '')
                        if target_name == target_field.name():
                            expr = config.get('expression', '')
                            source_field_name = expr.replace('"', '').strip()
                            source_idx = source.fields().indexOf(source_field_name)
                            break

            if source_idx == -1:
                source_idx = source.fields().indexOf(target_field.name())

            if source_idx != -1:
                target_type = target_field.type()
                field_name = target_field.name()
                if any(dt_name in field_name.lower() for dt_name in datetime_field_names):
                    target_type = QVariant.DateTime
                mapping[target_idx] = {'source_idx': source_idx, 'target_type': target_type, 'field_name': field_name}

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        for current, feature in enumerate(source.getFeatures()):
            if feedback.isCanceled():
                break

            geom = QgsGeometry()
            if QgsWkbTypes.geometryType(source.wkbType()) != QgsWkbTypes.NullGeometry and feature.hasGeometry() and target.isSpatial():
                geom = feature.geometry()
                if not geom.isNull():
                    if destType != QgsWkbTypes.UnknownGeometry:
                        newGeometry = geom.convertToType(destType, destIsMulti)
                        if not newGeometry.isNull():
                            geom = newGeometry
                    geom.avoidIntersections(QgsProject.instance().avoidIntersectionsLayers())

            attrs = {}
            for target_idx, info in mapping.items():
                source_idx = info['source_idx']
                target_type = info['target_type']
                raw_value = feature[source_idx]
                field_name = info.get('field_name', '')
                attrs[target_idx] = self.convertValue(raw_value, target_type, field_name)

            new_feature = QgsVectorLayerUtils().createFeature(target, geom, attrs)
            new_features.append(new_feature)

            feedback.setProgress(int(current * total))

        if not new_features:
            feedback.pushInfo("\nNo features to append.")
            return results

        with edit(target):
            target.beginEditCommand("Appending features...")
            res = target.addFeatures(new_features)
            target.endEditCommand()

        if res:
            feedback.pushInfo("\n{} features appended to '{}'.".format(len(new_features), target.name()))
            results[self.APPENDED_COUNT] = len(new_features)
            target.triggerRepaint()
        else:
            feedback.reportError("\nERROR: Features could not be appended.")

        results['OUTPUT_LAYER'] = target
        return results