"""Template strings to simplify code formatting"""

mapfile_layer_template = """
# LAYER: {feature}  LEVEL: {layer}

LAYER
    NAME "{feature}_{layer}"
    GROUP "{group}"
    METADATA
        "ows_title" "{metadata_name} {geomtype_humanreadable}"
        "ows_enable_request"   "*"
        "gml_include_items" "all"
        "wms_feature_mime_type" "text/html"
    END
    PROCESSING "LABEL_NO_CLIP=True"
    TEMPLATE blank.html
    TYPE {type}
    STATUS ON
    MAXSCALEDENOM {max_scale_denom}
    {data}
{classes}
END

# END of  LAYER: {feature}  LEVEL: {layer}
"""

lights_layer_template = """
# LIGHTS features and lines
LAYER
     NAME "Light sector rays"
     TYPE LINE
     DATA '{0}/CL{0}_LIGHTS_LINESTRING_SECTOR'
     MAXSCALEDENOM {3}
     GROUP "{2}"
     TOLERANCE 10
     TEMPLATE dummy.html
     PROJECTION
        "init=epsg:3857"
     END
     CLASS
        EXPRESSION ('[TYPE]'='RAYS')
        STYLE
            COLOR  77 77 77
            PATTERN 5 5 5 5 END
            WIDTH 1
        END
     END
     METADATA
        "ows_title" "Light sector rays"
        "ows_enable_request"   "*"
        "gml_include_items" "all"
        "wms_feature_mime_type" "text/html"
     END
 END
 LAYER
     NAME "Arc light sectors"
     TYPE LINE
     DATA '{0}/CL{0}_LIGHTS_LINESTRING_SECTOR'
     MAXSCALEDENOM {3}
     GROUP "{2}"
     TOLERANCE 10
     TEMPLATE dummy.html
     PROJECTION
        "init=epsg:3857"
     END
     CLASS
         EXPRESSION ('[TYPE]'='ARC' AND [VALNMR]!=0)
         STYLE
            COLOR [COLOURRGB]
            WIDTH 3
         END
         TEXT ('[MEANING]'+'.'+tostring([SIGGRP],"%.2g")+ '.' + '[COLOURCODE]'+tostring([SIGPER],"%.2g")+ 's' + tostring([HEIGHT],"%.2g") + 'm'+ tostring([VALNMR],"%.2g") + 'M')
         LABEL
             TYPE TRUETYPE
             FONT sc
             COLOR 0 0 0
             OUTLINECOLOR 255 255 255
             SIZE 8
             ANTIALIAS TRUE
             #FORCE TRUE
             POSITION AUTO
             ANGLE FOLLOW
             MINFEATURESIZE AUTO
         END
     END
     CLASS
         EXPRESSION ('[TYPE]'='ARC' AND [SIGPER]!=0)
         TEXT ('[MEANING]'+'.'+'[SIGGRP]'+ '.' + '[COLOURCODE]'+tostring([SIGPER],"%.2g")+ 's')
         STYLE
            COLOR [COLOURRGB]
            WIDTH 3
         END
         LABEL
             TYPE TRUETYPE
             FONT sc
             COLOR 0 0 0
             OUTLINECOLOR 255 255 255
             SIZE 8
             ANTIALIAS TRUE
             #FORCE TRUE
             POSITION AUTO
             ANGLE FOLLOW
             MINFEATURESIZE AUTO
         END
     END
     METADATA
        "ows_title" "Arc light sectors"
        "ows_enable_request"   "*"
        "gml_include_items" "all"
        "wms_feature_mime_type" "text/html"
     END
 END
 LAYER
     NAME "Lights signature"
     TYPE POINT
     DATA '{0}/CL{0}_LIGHTS_POINT_SIGNATURE'
     MAXSCALEDENOM {3}
     GROUP "{2}"
     TOLERANCE 10
     TEMPLATE dummy.html
     PROJECTION
        "init=epsg:4326"
     END
     CLASS
         EXPRESSION ([VALNMR]!=0)
         TEXT ('[MEANING]'+'.'+'[SIGGRP]'+ '.' + '[COLOUR_COD]'+tostring([SIGPER],"%.2g")+ 's' + tostring([HEIGHT],"%.2g") + 'm'+ tostring([VALNMR],"%.2g") + 'M')
         LABEL
             TYPE TRUETYPE
             FONT sc
             COLOR 0 0 0
             ##OUTLINECOLOR 255 255 255
             SIZE 8
             ANTIALIAS TRUE
             ##FORCE TRUE
             POSITION cc
             OFFSET 65 12
         END
     END
     CLASS
         EXPRESSION ([SIGPER]!=0)
         TEXT ('[MEANING]'+'.'+tostring([SIGGRP],"%.2g")+ '.' + '[COLOUR_COD]'+tostring([SIGPER],"%.2g")+ 's')
         LABEL
             TYPE TRUETYPE
             FONT sc
             COLOR 0 0 0
             ##OUTLINECOLOR 255 255 255
             SIZE 8
             ANTIALIAS TRUE
             ##FORCE TRUE
             POSITION cc
             OFFSET 65 12
         END
     END
     METADATA
        "ows_title" "Lights signature"
        "ows_enable_request"   "*"
        "gml_include_items" "all"
        "wms_feature_mime_type" "text/html"
     END
  END
{1}
"""  # noqa

ogr_data_instruction = """
    CONNECTIONTYPE OGR
    CONNECTION "{0}/{1}.shp"
    DATA "SELECT * FROM {1}"
"""


dynamic_data_instruction = """
    CONNECTIONTYPE OGR
    CONNECTION "{0}/{1}.shp"
    DATA "SELECT *, 360 - {2} as {2}_CAL FROM {1}"
"""


class_template = """
    CLASS # id: {2}
        {0}
        {1}
    END
"""
