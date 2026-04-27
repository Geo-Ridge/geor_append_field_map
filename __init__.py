# -*- coding: utf-8 -*-
def classFactory(iface):
    from .append_features_with_field_mapping_plugin import AppendFeaturesWithFieldMappingPlugin
    return AppendFeaturesWithFieldMappingPlugin(iface)