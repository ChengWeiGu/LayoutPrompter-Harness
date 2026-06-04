import os
import copy
import json
from . import EBXImportExport


ObjectMap_ebx2view = {
    "objectSwitch":"Switch",
    "objectLamp":"Lamp",
    "objectButton":"Button",
    "objectOptionList":"OptionList",
    "objectSlider":"Slider",
    "objectNumeric":"NumericInput",
    "objectTextInput":"TextInput",
    "objectDrawingRectangle":"DrawingRectangle",
    "objectText":"Text",
    "objectPicture":"Picture",
    "objectDrawingLine":"DrawingLine",
    "objectDrawingEllipse":"DrawingEllipse",
    "objectDrawingArc":"DrawingArc",
    "objectDrawingPolygon":"DrawingPolygon",
    "objectDrawingLinkLine":"DrawingLinkLine",
    "objectDrawingScale":"DrawingScale",
    "objectBarGraph":"BarGraph", # TBD
    "objectEmbeddedWindow":"EmbeddedWindow",
    "objectMatrixBarcode":"2DBarcode",
    "objectPdfReader":"PdfReader", # TBD
    "objectComposite":"CompositeWidget"
}

ObjectMap_view2ebx = {}
for k,v in ObjectMap_ebx2view.items():
    ObjectMap_view2ebx[v] = k
# Lamp is actually a `objectSwitch`
ObjectMap_view2ebx["Lamp"] = "objectSwitch"


"""used for add_entity via socket"""
ObjectMap_view2socket = {
    "Switch":"Switch",
    "Lamp":"Lamp",
    "Button":"Button",
    "OptionList":"OptionList",
    "Slider":"Slider",
    "NumericInput":"Numeric",
    "TextInput":"TextInput",
    "DrawingRectangle":"Rectangle",
    "Text":"Text",
    "DrawingLine":"Line",
    "DrawingArc":"Arc",
    "DrawingEllipse":"Ellipse",
    "DrawingPolygon":"Polygon",
}


"""transform original json into view json"""
class ScreenDecoder:
    
    supported_input_objects = ["NumericInput", "TextInput"]
    supported_general_objects = ["Lamp", "Switch","Button","Text"]
    supported_draw_objects = ["DrawingRectangle", "DrawingEllipse", "DrawingPolygon"]
    
    @staticmethod
    def load_json_file(project_path:str) -> dict:
        try:
            with open(project_path, 'r', encoding='utf-8') as f:
                _json = json.load(f)
                return _json
        except Exception as e:
            error_msg = f"[Load Project File Failed] {str(e)}"
            raise Exception(error_msg)
    
    @staticmethod
    def get_screen_from_project(project_json:dict, screen_name:str) -> tuple:
        try:
            _screens = project_json["body"]["screens"]
            for _idx, _sc in enumerate(_screens):
                _name = _sc["name"]
                if _name == screen_name: # 區分大小寫
                    return _idx, _sc
            return -1, {}
        
        except Exception as e:
            error_msg = f"[Get Screen Name Failed] {str(e)}"
            raise Exception(error_msg)
    
    @staticmethod
    def get_screen_size(screen_json:dict) -> dict:
        try:
            size = {
                "width":0,
                "height":0
            }
            
            screenInfo = screen_json["properties"]
            width, height = screenInfo["width"], screenInfo["height"]
            
            size.update({
                "width":width,
                "height":height
            })
                
            return size
        except Exception as e:
            error_msg = f"[Get Screen Size Failed] {str(e)}"
            raise Exception(error_msg)
    
    @staticmethod
    def get_screen_properties(screen_json:dict) -> dict:
        """background transform"""
        try: 
            data = {
                "facecolor":"#ffffff",
                "border":{
                    "style":5,
                    "color":"#000000",
                    "width":0
                }
            }
                
            # get bg widget
            _properties = screen_json["properties"]
            # get bg color
            _facecolor = _properties["fill"]["subjectColor"]
            # border style
            _border = _properties["border"]
            
            data["facecolor"] = _facecolor
            data["border"] = _border
            
            return data
        
        except Exception as e:
            error_msg = f"[Get Background View Failed] {str(e)}"
            raise Exception(error_msg)      
    
    @staticmethod
    def get_screen_object_names(screen_objects:list) -> list:
        try:
            _names = []
            for sc_obj in screen_objects:
                _names.append(sc_obj["name"])
            return _names
        
        except Exception as e:
            error_msg = f"[Get Screen Object Names Failed] {str(e)}"
            raise Exception(error_msg)
            
    @staticmethod
    def get_object_type(object_json:dict):
        try:
            _obj_type = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            if _obj_type == "objectSwitch":
                _read_only = _properties["readOnly"]
                if _read_only:
                    _obj_type = "objectLamp"
            
            return ObjectMap_ebx2view.get(_obj_type, None)
        
        except Exception as e:
            error_msg = f"[Get Object Type Failed] {str(e)}"
            raise Exception(error_msg)
    
    @staticmethod
    def get_picture_index(pciture_path:str) -> int:
        """v1|1|<index>|0:|<galleryNo>:<galleryName> 需取出 <index>
        e.g. v1|1|0|0:|25:System Lamp - Ribbon.flbx
        """
        try:
            index = pciture_path.split("|")[2]
            return int(index)
        except Exception as e:
            error_msg = f"[Get Picture Index Failed] {str(e)}"
            raise Exception(error_msg)
    
    @staticmethod
    def get_picture_path(objectType:str, galleryName:str, index:int) -> str:
        """objectType: view type rather than ebx type
        - return : v1|1|<index>|0:|<galleryNo>:<galleryName>
        """
        galleryNo = 0
        if objectType == "Lamp":
            if galleryName == "System Lamp - Ribbon.flbx":
                galleryNo=25
            elif galleryName == "System Lamp - Crystal.flbx":
                galleryNo=26
            elif galleryName == "System Lamp - Flat.flbx":
                galleryNo=23
            elif galleryName == "System Lamp - Standard.flbx":
                galleryNo=27
            else:
                # default
                galleryName = "System Lamp - Ribbon.flbx"
                galleryNo=25
                
        elif objectType == "Switch":
            if galleryName == "System Switch - Ribbon.flbx":
                galleryNo=27
            elif galleryName == "System Switch - Crystal.flbx":
                galleryNo=28
            elif galleryName == "System Switch - Flat.flbx":
                galleryNo=25
            elif galleryName == "System Switch - Standard.flbx":
                galleryNo=29
            else:
                # default
                galleryName = "System Switch - Ribbon.flbx"
                galleryNo=27   
                
        elif objectType == "Button":
            if galleryName == "System Button - Ribbon.flbx":
                galleryNo=27
            elif galleryName == "System Button - Crystal.flbx":
                galleryNo=28
            elif galleryName == "System Button - Flat.flbx":
                galleryNo=25
            elif galleryName == "System Button - Standard.flbx":
                galleryNo=29
            else:
                # default
                galleryName = "System Button - Ribbon.flbx"
                galleryNo=27
                
        elif objectType == "NumericInput":
            if galleryName == "System Input Box - Ribbon.flbx":
                galleryNo=30
            elif galleryName == "System Input Box - Crystal.flbx":
                galleryNo=31
            elif galleryName == "System Input Box - Flat.flbx":
                galleryNo=28
            elif galleryName == "System Input Box - Standard.flbx":
                galleryNo=32
            else:
                # default
                galleryName = "System Input Box - Ribbon.flbx"
                galleryNo=30
        
        elif objectType == "TextInput":
            if galleryName == "System Input Box - Ribbon.flbx":
                galleryNo=30
            elif galleryName == "System Input Box - Crystal.flbx":
                galleryNo=31
            elif galleryName == "System Input Box - Flat.flbx":
                galleryNo=28
            elif galleryName == "System Input Box - Standard.flbx":
                galleryNo=32
            else:
                # default
                galleryName = "System Input Box - Ribbon.flbx"
                galleryNo=30
        elif objectType == "BarGraph":
            # fixed, only `Ribbon` available
            galleryName = "System Bar Graph - Ribbon.flbx"
            galleryNo=30
        else:
            raise Exception(f"[Get Token Failed] Type of object:`{objectType}` is not supported.")
        
        if not galleryNo:
            raise Exception(f"[Get Token Failed] for `{objectType}` and `{galleryName}`")
        
        return f"v1|1|{index}|0:|{galleryNo}:{galleryName}"    
         
    @staticmethod
    def convert_lineStyle2Num(style_name:str) -> int:
        """2026/6/1 已修正問題不再採用"""
        _style = 0 # 預設
        if style_name == "solid_line":
            _style = 0
        elif style_name == "dash_line":
            _style = 1
        elif style_name == "dot_line":
            _style = 2
        elif style_name == "dash_dot_line":
            _style = 3
        elif style_name == "dash_dot_dot_line":
            _style = 4
        return _style
    
    @classmethod
    def get_general_object_view(cls, object_json:dict) -> dict:
        """this func extract view of the following objects only:
        - Lamp/Switch/Button/Text
        """
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use view object type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type not in cls.supported_general_objects:
                raise ValueError(f"Type of object:`{_objectTypeName}` is not supported.")
            
            # bg section
            _bg_pattern = _properties["fill"]["pattern"]
            _bg_color = _properties["fill"]["subjectColor"] # default #00000000 => 八碼代表透明, 另外 fill 中的 `pattern` = 0 代表要填色 = 255 代表全透明
            if _bg_pattern == 255:
                _bg_color = "#00000000" # if pattern = 255, then force bg_color is #00000000
            _bg_radius = _properties["radius"] # default 0
            _bg_border = _properties["border"] # default {"style": 5,"color": "#000000","width": 1}
            
            # label section
            _text = _properties["text"] # default ""
            _fontStyle = _properties["font"] # default "Calibri"
            _fontSize = _properties["fontSize"] # default 16
            _fontBold = 1 if _properties["fontBold"] else 0 # default false => 0
            _fontItalic = 1 if _properties["fontItalic"] else 0 # default false => 0
            _fontUnderline = 1 if _properties["fontUnderline"] else 0 # default false => 0
            _fontColor = _properties["fontColor"] # default #000000
            _alignment = _properties["alignment"] # default 4
            _padding = _properties["padding"] # default {}
            _blinking = _properties["blinking"] # default 0
            _scrolling = _properties["scrolling"] # default {} 
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "background":{
                    "color":_bg_color,
                    "radius":_bg_radius,
                    "border":_bg_border
                },
                "label":{
                    "text":_text,
                    "fontStyle":_fontStyle,
                    "fontSize":_fontSize,
                    "fontBold":_fontBold,
                    "fontItalic":_fontItalic,
                    "fontUnderline":_fontUnderline,
                    "fontColor":_fontColor,
                    "alignment":_alignment,
                    "padding":_padding,
                    "blinking":_blinking,
                    "scrolling":_scrolling
                },
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            # outline section
            """v1|1|<index>|0:|<galleryNo>:<galleryName>
            - for lamp: "v1|1|0|0:|25:System Lamp - Ribbon.flbx"
            - for text: _properties["picture"] is "none" string. we don't let LLM to change it as well as its color => remove outline section
            - so far, only changing the gallery name wihtout changing `pictureIndex` is OK
            """
            if _view_object_type not in ["Text"]:   
                _picture_path = _properties["picture"]["path"]  
                _galleryName = _picture_path.split(":")[-1]
                _index = cls.get_picture_index(_picture_path)
                _pictureColor = _properties["pictureColor"] # default at #00000000 which means transparent
                
                _view["outline"] = {
                    "galleryName":_galleryName,
                    "index":_index,
                    "color":_pictureColor
                }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get General Object View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get General Object View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
            raise Exception(error_msg)
    
    @classmethod
    def get_option_list_view(cls,object_json:dict) -> dict:
        """ OptionList"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # view type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "OptionList":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not an `OptionList`.")
            
            
            _style = _properties["style"] # default 1 => 1 (classic, default) / 0 (Standard)
            
            # outline section
            _backgroundColor = _properties["backgroundColor"] # "#deefff", 直接影響選項中每個 item 底色
            _selectionColor = _properties["selectionColor"] # "#57bfff", 只有影響已被選擇的 item 底色
    
            # label section
            _fontStyle = _properties["font"] # default "Calibri"
            _fontSize = _properties["fontSize"] # default 16
            _fontBold = 1 if _properties["fontBold"] else 0 # default false => 0
            _fontItalic = 1 if _properties["fontItalic"] else 0 # default false => 0
            _fontUnderline = 1 if _properties["fontUnderline"] else 0 # default false => 0
            _fontColor = _properties["fontColor"] # default #000000
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "style":_style,
                "outline":{
                    "backgroundColor":_backgroundColor,
                    "selectionColor":_selectionColor
                },
                "label":{
                    "fontStyle":_fontStyle,
                    "fontSize":_fontSize,
                    "fontBold":_fontBold,
                    "fontItalic":_fontItalic,
                    "fontUnderline":_fontUnderline,
                    "fontColor":_fontColor
                },
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get OptionList View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get OptionList View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
            raise Exception(error_msg)
    
    @classmethod
    def get_slider_view(cls, object_json:dict) -> dict:
        """Slider"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # view type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "Slider":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not a `Slider`.")
            
            # outline section
            _style =  _properties["style"] # default 0 => 0/1/2: default/crystal/flat
            _direction = _properties["direction"] # default 0 => 0/1/2/3: right/up/left/down
            _blockStyle = _properties["blockStyle"] # default 0 => 0/1/2/3: Big rect/Small rect/Up arrow/Down arrow            
            _blockWidth = _properties["blockWidth"] # default 20
            _blockColor = _properties["blockColor"] # default "#000080"
            _frameColor = _properties["frameColor"] # default "#00000000" => transparent
            _backgroundColor = _properties["backgroundColor"] # default "#00000000" => transparent
            _slotColor = _properties["slotColor"] # default "#c0c0c0"
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "outline":{
                    "style":_style,
                    "direction":_direction,
                    "blockStyle":_blockStyle,
                    "blockWidth":_blockWidth,
                    "blockColor":_blockColor,
                    "frameColor":_frameColor,
                    "backgroundColor":_backgroundColor,
                    "slotColor":_slotColor
                },
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get Slider View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get Slider View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
            raise Exception(error_msg)
    
    @classmethod
    def get_input_object_view(cls, object_json:dict) -> dict:
        """NumericInput | TextInput"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # view type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type not in cls.supported_input_objects:
                raise ValueError(f"Type of object:`{_objectTypeName}` is not supported.")
            
            # outline section
            """v1|1|<index>|0:|<galleryNo>:<galleryName>
            - for both Input: "v1|1|0|0:|30:System Input Box - Ribbon.flbx"
            - so far, only changing the gallery name wihtout changing `pictureIndex` is OK
            """
            _picture_path = _properties["picture"]["path"] 
            _galleryName = _picture_path.split(":")[-1]
            _index = cls.get_picture_index(_picture_path)
            _pictureColor = _properties["pictureColor"] # default #00000000 => transparent
            
            # bg section
            _bg_pattern = _properties["fill"]["pattern"]
            _bg_color = _properties["fill"]["subjectColor"] # default #00000000 => transparent
            if _bg_pattern == 255:
                _bg_color = "#00000000" # if pattern = 255, then force bg_color is #00000000
            _bg_radius = _properties["radius"] # default 0
            _bg_border = _properties["border"] # default {"style": 5,"color": "#000000","width": 1}
            
            # label section
            _fontStyle = _properties["font"] # default "Calibri"
            _fontSize = _properties["fontSize"] # default 16
            _fontBold = 1 if _properties["fontBold"] else 0 # default false => 0
            _fontColor = _properties["fontColor"] # default #000000
            _alignment = _properties["alignment"] # default 4
            _padding = _properties["padding"] # default {}
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "outline":{
                    "galleryName":_galleryName,
                    "index":_index,
                    "color":_pictureColor
                },
                "background":{
                    "color":_bg_color,
                    "radius":_bg_radius,
                    "border":_bg_border
                },
                "label":{
                    "fontStyle":_fontStyle,
                    "fontSize":_fontSize,
                    "fontBold":_fontBold,
                    "fontColor":_fontColor,
                    "alignment":_alignment,
                    "padding":_padding
                },
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get Input Object View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get Input Object View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
            raise Exception(error_msg)
        
    @classmethod
    def get_draw_object_view(cls, object_json:dict) -> dict:
        """DrawingRectangle | DrawingEllipse | DrawingPolygon"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # view type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type not in cls.supported_draw_objects:
                raise ValueError(f"Type of object:`{_objectTypeName}` is not a `Rectangle` | `Ellipse` | `Plygon`")
            
            # Frame Section
            _frameColor = _properties["frameColor"] # default "#000000"
            _frameWidth = _properties["frameWidth"] # default 1 for rectangle/ellipse/polygon/LinkLine
            
            """STYLE: solid_line/dash_line/dot_line/dash_dot_line/dash_dot_dot_line (0-4)
            - rectangle/ellipse/polygon/LinkLine: default at 0
            """
            _style =  _properties["style"] # int
            
            # Interior section
            _pattern = _properties["fill"]["pattern"] # default 255, no facecolor
            _subjectColor = _properties["fill"]["subjectColor"] # default "#ffffff", 搭配 pattern = 0 才是代表有填滿，否則只設此值無意義
            if _pattern == 255:
                _subjectColor = "#00000000"            
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "frame":{
                    "frameColor":_frameColor,
                    "frameWidth":_frameWidth,
                    "style":_style
                },
                "interior": {
                    "color":_subjectColor
                },   
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            
            # Only DrawingRectangle has `frameRadius`
            if _view_object_type == "DrawingRectangle":
                _frameRadius = _properties["frameRadius"] # default 0
                _view["frame"]["frameRadius"] = _frameRadius
            
            # For DrawingPolygon, we need points section
            if _view_object_type == "DrawingPolygon":
                _points = _properties["points"]
                _view["points"] = _points
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get {_view_object_type} View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get {_view_object_type} View Failed] {str(e)} for name: `{_name}` and type: `{_objectTypeName}`"
            raise Exception(error_msg)
    
    @classmethod
    def get_line_view(cls, object_json:dict) -> dict:
        """DrawingLine"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use view type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "DrawingLine":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not a `Line Widget`.")
            
            # Pattern Section
            _lineColor = _properties["lineColor"] # default "#000000"
            _lineWidth = _properties["lineWidth"] # 1-8, default 1
            _style = _properties["style"] # default = 0 (solid_line)
            
            # Arrow Section
            _arrowType = _properties["arrowType"] # default {}, formated as {"end": "5","start": "1"}, range of "0"-"5"
            _arrowSize = _properties["arrowSize"] # default at {"end": "1","start": "1"}, range of "1" - "8"
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            # points
            _points = _properties["points"]
            _p1, _p2 = _points[0], _points[1]
            # using start-to-end point to describe a arrow line
            if _p1 == {"x": 0.0,"y": 0.0} and _p2 == {"x": 1.0,"y": 0.0}:
                """arrow right (→), actual height = 1"""
                _start = {"x":_x, "y":_y}
                _end = {"x":_x+_width, "y":_y}
            elif _p1 == {"x": 0.0,"y": 1.0} and _p2 == {"x": 1.0,"y": 0.0}:
                """arrow from left-lower to right-top (↗)"""
                _start = {"x":_x, "y":_y+_height}
                _end = {"x":_x+_width, "y":_y}
            elif _p1 == {"x": 0.0,"y": 1.0} and _p2 == {"x": 0.0,"y": 0.0}:
                """arrow up (↑), actual width = 1"""
                _start = {"x":_x, "y":_y+_height}
                _end = {"x":_x, "y":_y}
            elif _p1 == {"x": 1.0,"y": 1.0} and _p2 == {"x": 0.0,"y": 0.0}:
                """arrow from lower-right to upper-left (↖)"""
                _start = {"x":_x + _width, "y":_y+_height}
                _end = {"x":_x, "y":_y}
            elif _p1 == {"x": 1.0,"y": 0.0} and _p2 == {"x": 0.0,"y": 0.0}:
                """arrow left (←), actual height = 1"""
                _start = {"x":_x + _width, "y":_y}
                _end = {"x":_x, "y":_y}
            elif _p1 == {"x": 1.0,"y": 0.0} and _p2 == {"x": 0.0,"y": 1.0}:
                """arrow from upper-right to lower-left (↙)"""
                _start = {"x":_x + _width, "y":_y}
                _end = {"x":_x, "y":_y+_height}
            elif _p1 == {"x": 0.0,"y": 0.0} and _p2 == {"x": 0.0,"y": 1.0}:
                """arrow down (↓), actual width = 1"""
                _start = {"x":_x, "y":_y}
                _end = {"x":_x, "y":_y+_height}
            elif _p1 == {"x": 0.0,"y": 0.0} and _p2 == {"x": 1.0,"y": 1.0}:
                """arrow from upper-ledft to lower-right (↘)"""
                _start = {"x":_x, "y":_y}
                _end = {"x":_x+_width, "y":_y+_height}
            else:
                raise ValueError(f"[Get Line View Error] Get unknown start and end point, please check")
            
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "pattern":{
                    "lineColor":_lineColor,
                    "lineWidth":_lineWidth,
                    "style":_style
                },
                "arrow":{
                    "arrowType":_arrowType,
                    "arrowSize":_arrowSize
                },        
                "start_pt":_start,
                "end_pt":_end
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get Line View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get Line View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
            raise Exception(error_msg)    
    
    @classmethod
    def get_link_line_view(cls, object_json:dict) -> dict:
        """DrawingLinkLine"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use view type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "DrawingLinkLine":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not a `Link Line`.")
            
            # Pattern Section
            _lineColor = _properties["lineColor"] # default "#000000"
            _lineWidth = _properties["lineWidth"] # 1-8, default 1
            _style = _properties["style"] # default 0
            
            # Arrow Section
            _arrowType = _properties["arrowType"] # default {}, formated as {"end": "5","start": "1"}, range of "0"-"5"
            _arrowSize = _properties["arrowSize"] # default at {"end": "1","start": "1"}, range of "1" - "8"
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            # points section
            _points = _properties["points"]
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "pattern":{
                    "lineColor":_lineColor,
                    "lineWidth":_lineWidth,
                    "style":_style
                },
                "arrow":{
                    "arrowType":_arrowType,
                    "arrowSize":_arrowSize
                },   
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                },
                "points": _points
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get Link Line View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get Link Line View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
            raise Exception(error_msg)    
    
    @classmethod
    def get_arc_view(cls, object_json:dict) -> dict:
        """DrawingArc"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # view type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "DrawingArc":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not a `Arc`.")
            
            # Pattern Section
            _lineColor = _properties["lineColor"] # default "#000000"
            _lineWidth = _properties["lineWidth"] # default = 1
            _style =  _properties["style"] # default at 0 (solid_line) => solid_line/dash_line/dot_line/dash_dot_line/dash_dot_dot_line
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "pattern":{
                    "lineColor":_lineColor,
                    "lineWidth":_lineWidth,
                    "style":_style
                },      
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get Arc View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get Arc View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
            raise Exception(error_msg)
    
    @classmethod
    def get_picture_view(cls, object_json:dict) -> dict:
        """Picture"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use view object type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "Picture":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not supported.")

            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            # outline section
            """v1|1|<index>|0:|<galleryNo>:<galleryName>
            - for picture: 
                - example: "v1|1|0|0:|25:System Lamp - Ribbon.flbx"
                - In default: _properties["picture"] is "none" string.
            - so far, only changing the gallery name wihtout changing `pictureIndex` is OK
            """
            _picture = _properties["picture"]
            _view["outline"] = _picture # default
            if _picture != "none": 
                _picture_path = _properties["picture"]["path"]  
                _galleryName = _picture_path.split(":")[-1]
                _index = cls.get_picture_index(_picture_path)
                _pictureColor = _properties["pictureColor"] # default at #00000000 which means transparent
                
                _view["outline"] = {
                    "galleryName":_galleryName,
                    "index":_index,
                    "color":_pictureColor
                }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get Picture Object View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get Picture Object View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
            raise Exception(error_msg)
    
    @classmethod
    def get_scale_view(cls, object_json:dict) -> dict:
        """DrawingScale"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use view object type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "DrawingScale":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not supported.")

            # general section
            _type = _properties["type"] # int, 0: Circular; 1: Linear
            _angleSetting = _properties["angleSetting"] # default {"spanAngle": "360"}; example {"clockwise": "1","spanAngle": "270","startAngle": "45"}
            _alignment = _properties["alignment"] # Linear will use
            
            """
            1: right to left
            2: left to right
            3: top to bottom
            4: bottom to top
            """
            _direction = _properties["direction"] # int, 2 (linear 才可設定)
            
            # Tick Mark Section
            _tickWidth = _properties["tickWidth"] # int, 1 - 8
            _tickStyle = _properties["tickStyle"] # int, 0 - 4
            _tickColor = _properties["tickColor"] # hex string default at #000000
            _tickRadius = _properties["tickRadius"] # default 100 (單位 %), don't change it
            _tickMainDivision = _properties["tickMainDivision"] # int, 5, 2-100
            _mainScaleLength = _properties["mainScaleLength"] # int, -10
            _tickSubDivision = _properties["tickSubDivision"] # int, 2, 2-100
            _subScaleLength = _properties["subScaleLength"] # int, -10
            
            # Scale Label Section
            _showScaleLabel = _properties["showScaleLabel"] # Default : False
            _showScaleLabel = 1 if _showScaleLabel else 0
            
            _fontStyle = _properties["font"] # default "Calibri"
            _fontSize = _properties["fontSize"] # default 12
            _fontColor = _properties["fontColor"] # default #000000
            _rightDecimalPt = _properties["rightDecimalPt"] # default 0
            _leftDecimalPt = _properties["leftDecimalPt"] # default 0
            _labelRadius = _properties["labelRadius"] # default 80 (單位 %), don't change it
            _limit = _properties["limit"] # default {"high": "100"}, example : {"high": "100","low": "30"}
            
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "general":{
                    "type":_type,
                    "angleSetting":_angleSetting,
                    "direction":_direction,
                    "alignment":_alignment
                },
                "tick_mark":{
                    "tickWidth":_tickWidth,
                    "tickStyle":_tickStyle,
                    "tickColor":_tickColor,
                    "tickMainDivision":_tickMainDivision,
                    "mainScaleLength":_mainScaleLength,
                    "tickSubDivision":_tickSubDivision,
                    "subScaleLength":_subScaleLength,
                },
                "scale_label":{
                    "showScaleLabel":_showScaleLabel,
                    "fontStyle":_fontStyle,
                    "fontSize":_fontSize,
                    "fontColor":_fontColor,
                    "rightDecimalPt":_rightDecimalPt,
                    "leftDecimalPt":_leftDecimalPt,
                    "limit":_limit,
                },
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get Scale Object View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get Scale Object View Failed] {str(e)} for name: `{_name}` and type: `{_objectTypeName}`"
            raise Exception(error_msg)
    
    @classmethod
    def get_bar_graph_view(cls, object_json:dict) -> dict:
        """BarGraph
        - BarColor 有問題
        """
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use view object type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "BarGraph":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not supported.")

            # outline section
            _type =  _properties["type"] # default 0, 0 (Straight) | 1 (Circle)
            _style = _properties["style"] # default 0, 0 (Default) | 1 (Crystal) | 2 (Flat)
            _direction = _properties["direction"] # default 0, 0-3 (Up/Down/Left/Right)
            _angleSetting = _properties["angleSetting"] # default {"spanAngle": "360"}; example {"clockwise": "1","spanAngle": "270","startAngle": "45"}
            _circularHoleRatio = _properties["circularHoleRatio"] # 40, 0 - 90
            _barBackgroundColor= _properties["barBackgroundColor"] # "#a0a0a4", chageable for circular only
            _barFrameColor = _properties["barFrameColor"] # "#00000000", changeable for circular, Default Style for Straight        
                
            # when using `Default` style, barColor should come from barFill
            _barColor = _properties["barColor"]
            if _style == 0:
                _barColor = _properties["barColor"]
                
            """v1|1|<index>|0:|<galleryNo>:<galleryName>
            - for BarGraph: "v1|1|1|0:|30:System Bar Graph - Ribbon.flbx" (only `Ribbon` is availabe, galleryNo = 30, fixed)
            - currently, changing picture of it does not matter for beautification task
            - no picture color for this widget
            """
            _picture_path = _properties["picture"]["path"]  
            _galleryName = _picture_path.split(":")[-1]
            _index = cls.get_picture_index(_picture_path) # 0 - 4 
            
            
            # bg section
            _bg_pattern = _properties["fill"]["pattern"]
            _bg_color = _properties["fill"]["subjectColor"] # default #00000000 => 八碼代表透明, 另外 fill 中的 `pattern` = 0 代表要填色 = 255 代表全透明
            if _bg_pattern == 255:
                _bg_color = "#00000000" # if pattern = 255, then force bg_color is #00000000
            _bg_radius = _properties["radius"] # default 0
            _bg_border = _properties["border"] # default {"style": 5,"color": "#000000","width": 1}
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "outline":{
                    "type":_type,
                    "style":_style,
                    "direction":_direction,
                    "angleSetting":_angleSetting,
                    "circularHoleRatio":_circularHoleRatio,
                    "barBackgroundColor":_barBackgroundColor,
                    "barFrameColor":_barFrameColor
                },
                "background":{
                    "color":_bg_color,
                    "radius":_bg_radius,
                    "border":_bg_border
                },
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get BarGraph View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get BarGraph View Failed] {str(e)} for name: `{_name}` and type: `{_objectTypeName}`"
            raise Exception(error_msg)
    
    @classmethod
    def get_embed_window_view(cls, object_json:dict) -> dict:
        """EmbeddedWindow"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use view object type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "EmbeddedWindow":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not supported.")

            # display section
            _mode = _properties["containerMode"] # 0 (default) | 1, embedded in screen | popup window
            _titleEnabled= _properties["titleEnabled"] # true | false (default)
            _title = _properties["titleString"] # ""
            _displayAnchor = _properties["displayAnchor"] # 0 - 8
            
            """an `effect` will have lots of diff `direction`, so we ignore the attri for simplicity"""
            _entranceAnimation = _properties["entranceAnimation"] # default at {"duration": "100"} means no animation, example: {"direction": "2","duration": "100","effect": "2"} 
            _exitAnimation = _properties["exitAnimation"] # default at {"duration": "100"} means no animation, example: {"direction": "2","duration": "100","effect": "2"}
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "display":{
                    "mode":_mode,
                    "title":_title,
                    "displayAnchor":_displayAnchor
                },
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get EmbeddedWindow View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get EmbeddedWindow View Failed] {str(e)} for name: `{_name}` and type: `{_objectTypeName}`"
            raise Exception(error_msg)
    
    @classmethod
    def get_2d_barcode_view(cls, object_json:dict) -> dict:
        """2DBarcode"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use view object type name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "2DBarcode":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not supported.")

            # general section
            _readValue = _properties["readValue"] # www.weintek.com
            _barcodeType = _properties["barcodeType"] # int, 0 - 2
            _barcodeColor = _properties["cellColor"] # hex string
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            _view = {
                "objectType": _view_object_type,
                "name":_name,
                "general":{
                    "readValue":_readValue,
                    "barcodeType":_barcodeType,
                    "barcodeColor":_barcodeColor
                },
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get 2DBarcode View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get 2DBarcode View Failed] {str(e)} for name: `{_name}` and type: `{_objectTypeName}`"
            raise Exception(error_msg)
    
    @staticmethod
    def get_other_object_view(object_json:dict) -> dict:
        """For undefined object, we only extract profile info"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # 假如 object name 有定義，則使用定義的 objectTypeName
            if _objectTypeName in ObjectMap_ebx2view.keys():
                _objectTypeName = ObjectMap_ebx2view[_objectTypeName]
            
            # profile section
            _x = _properties["x"]
            _y = _properties["y"]
            _width = _properties["width"]
            _height = _properties["height"]
            _rotation = _properties["rotation"]
            
            _view = {
                "objectType": _objectTypeName,
                "name":_name,
                "profile":{
                    "x":_x,
                    "y":_y,
                    "width":_width,
                    "height":_height,
                    "rotation":_rotation
                }
            }
            
            return _view
        
        except Exception as e:
            error_msg = f"[Get Other Object View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
            raise Exception(error_msg)
    
    @classmethod
    def get_object_view_router(cls, object_json:dict) -> dict:
        """a router for get_object_view func"""
        _obj_type = cls.get_object_type(object_json) # None if undefined
        
        _obj_view = {}
        if _obj_type in cls.supported_general_objects:
            _obj_view = cls.get_general_object_view(object_json)
        elif _obj_type == "OptionList":
            _obj_view = cls.get_option_list_view(object_json)
        elif _obj_type == "Slider":
            _obj_view = cls.get_slider_view(object_json)
        elif _obj_type in cls.supported_input_objects:
            _obj_view = cls.get_input_object_view(object_json)
        elif _obj_type in cls.supported_draw_objects:
            _obj_view = cls.get_draw_object_view(object_json)
        elif _obj_type == "DrawingLine":
            _obj_view = cls.get_line_view(object_json)
        elif _obj_type == "DrawingLinkLine":
            _obj_view = cls.get_link_line_view(object_json)
        elif _obj_type == "DrawingArc":
            _obj_view = cls.get_arc_view(object_json)
        elif _obj_type == "Picture":
            _obj_view = cls.get_picture_view(object_json)
        elif _obj_type == "DrawingScale":
            _obj_view = cls.get_scale_view(object_json)
        elif _obj_type == "EmbeddedWindow":
            _obj_view = cls.get_embed_window_view(object_json)
        elif _obj_type == "2DBarcode":
            _obj_view = cls.get_2d_barcode_view(object_json)
        else:
            _obj_view = cls.get_other_object_view(object_json) # CompositeWidget
        
        return _obj_view
    
    def __init__(self):
        self.descr="transform original json into view json"
        
    def get_screen_view_by_socket_export(self, project_path:str, screen_name:str, **kwargs) -> dict:
        """transform whole screen json to the view that LLM understands
            Args:
            - project_path: EBX export 檔案路徑 (.ebxprj)
            - screen_name: 待美化的 screen 名稱
        """
        try:
            # get project json by socket
            _proj_json = EBXImportExport.export_project(project_path, screen_name)   
            # find screen         
            _idx, _sc_json = self.get_screen_from_project(_proj_json, screen_name)
            if _idx < 0 or not _sc_json:
                raise Exception(f"[Get Screen View Failed] screen name :`{screen_name}` not found in project file: `{project_path}`.")
            
            _sc_size = self.get_screen_size(_sc_json)
            _sc_properties = self.get_screen_properties(_sc_json)
            
            _objs = _sc_json["objects"]
            
            _objects = []
            
            # scan objs
            for _obj in _objs:
                _view = self.get_object_view_router(_obj)
                _objects.append(_view)
            
            _sc_view = {
                "screen_name":screen_name,
                "screen_size":_sc_size,
                "screen_properties":_sc_properties,
                "objects":_objects
            }
            return _sc_view
        
        except:
            raise
    
    def get_screen_view_from_file(self, project_path:str, screen_name:str, **kwargs) -> dict:
        """transform whole screen json to the view that LLM understands
            Args:
            - project_path: EBX export 檔案路徑 (.json)
            - screen_name: 待美化的 screen 名稱
        """
        try:
            _proj_json = self.load_json_file(project_path)
            _idx, _sc_json = self.get_screen_from_project(_proj_json, screen_name)
            if _idx < 0 or not _sc_json:
                raise Exception(f"[Get Screen View Failed] screen name :`{screen_name}` not found in project file: `{project_path}`.")
            
            _sc_size = self.get_screen_size(_sc_json)
            _sc_properties = self.get_screen_properties(_sc_json)
            
            _objs = _sc_json["objects"]
            
            _objects = []
            
            # scan objs
            for _obj in _objs:
                _view = self.get_object_view_router(_obj)
                _objects.append(_view)
            
            _sc_view = {
                "screen_name":screen_name,
                "screen_size":_sc_size,
                "screen_properties":_sc_properties,
                "objects":_objects
            }
            return _sc_view
        
        except:
            raise
        


class ScreenEncoder(ScreenDecoder):     
    
    @staticmethod
    def convert_lineStyle2String(style_num:int) -> str:
        """2026/6/1 修正，不再使用"""
        _style = "solid_line" # default
        if style_num == 0:
            _style = "solid_line"
        elif style_num == 1:
            _style = "dash_line"
        elif style_num == 2:
            _style = "dot_line"
        elif style_num == 3:
            _style = "dash_dot_line"
        elif style_num == 4:
            _style = "dash_dot_dot_line"
        
        return _style
    
    @classmethod
    def override_screen_background(cls, sc_json:dict, sc_view_json:dict):
        try:
            sc_json["name"] = sc_view_json["screen_name"]
            
            sc_json["properties"]["fill"]["pattern"] = 0 # always 0
            sc_json["properties"]["fill"]["subjectColor"] = sc_view_json["screen_properties"]["facecolor"]
            sc_json["properties"]["border"] = sc_view_json["screen_properties"]["border"]

        except Exception as e:
            error_msg = f"[Override BG Screen Failed] {str(e)}"
            raise Exception(error_msg)
    
    @classmethod
    def override_screen_properties(cls, sc_json:dict, sc_view_properties:dict):
        """sc_view_properties:
        {"facecolor": "#0f1923", "border": {"style": 5, "color": "#000000", "width": 0}}
        """
        try:
            sc_json["properties"]["fill"]["pattern"] = 0 # always 0
            sc_json["properties"]["fill"]["subjectColor"] = sc_view_properties["facecolor"]
            sc_json["properties"]["border"] = sc_view_properties["border"]

        except Exception as e:
            error_msg = f"[Override BG Screen Failed] {str(e)}"
            raise Exception(error_msg)
    
    @classmethod
    def override_general_object(cls, obj_json:dict, obj_view_json:dict):
        """Lamp/Switch/Button/Text"""
        try:
            # name
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type not in cls.supported_general_objects:
                raise ValueError(f"View Type of object:`{view_obj_type}` is not supported.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]
            
            # bg section
            obj_bg_color = obj_view_json["background"]["color"]
            _properties["fill"]["subjectColor"] = obj_bg_color
            _properties["fill"]["pattern"] = 0 # 0 => has color
            if obj_bg_color == "#00000000":
                _properties["fill"]["pattern"] = 255 
            
            _properties["radius"] = obj_view_json["background"]["radius"]
            _properties["border"] = obj_view_json["background"]["border"]
            
            # label section
            _properties["text"] = obj_view_json["label"]["text"]
            _properties["font"] = obj_view_json["label"]["fontStyle"]
            _properties["fontSize"] = obj_view_json["label"]["fontSize"]
            _properties["fontBold"] = True if obj_view_json["label"]["fontBold"] else False
            _properties["fontItalic"] = True if obj_view_json["label"]["fontItalic"] else False
            _properties["fontUnderline"] = True if obj_view_json["label"]["fontUnderline"] else False
            _properties["fontColor"] = obj_view_json["label"]["fontColor"]
            _properties["alignment"] = obj_view_json["label"]["alignment"]
            _properties["padding"] = obj_view_json["label"]["padding"]
            _properties["blinking"] = obj_view_json["label"]["blinking"]            
            _properties["scrolling"] = obj_view_json["label"]["scrolling"]
            
            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
            
            # outline section
            """v1|1|<index>|0:|<galleryNo>:<galleryName>
            - for lamp: "v1|1|0|0:|25:System Lamp - Ribbon.flbx"
            - for text: _properties["picture"] is "none" string. we don't let LLM to change it as well as its color => remove outline section
            - so far, only changing the gallery name wihtout changing `pictureIndex` is OK
            """
            if view_obj_type in ["Text"]:
                # force them back to default
                _properties["picture"] = "none"
                _properties["pictureColor"] = "#00000000"
            else:
                galleryName = obj_view_json["outline"]["galleryName"]
                index = obj_view_json["outline"]["index"]
                
                _path = cls.get_picture_path(objectType=view_obj_type, galleryName=galleryName, index=index)
                _properties["picture"]["path"] = _path
                _properties["picture"]["kind"] = "resource" # fixed at resource
                
                _properties["pictureColor"] = obj_view_json["outline"]["color"]
        
        except ValueError as e:
            error_msg = f"[Override General Object Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override General Object Failed] {str(e)} for name:{name} and view_obj_type:{view_obj_type}"
            raise Exception(error_msg)
    
    @classmethod
    def override_option_list(cls, obj_json:dict, obj_view_json:dict):
        """ OptionList"""
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type != "OptionList":
                raise ValueError(f"View Type of object:`{view_obj_type}` is not an `OptionList`.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]
            # style
            _properties["style"] = obj_view_json["style"]
            
            # outline section
            _properties["backgroundColor"] = obj_view_json["outline"]["backgroundColor"]
            _properties["selectionColor"] = obj_view_json["outline"]["selectionColor"]
    
            # label section
            _properties["font"] = obj_view_json["label"]["fontStyle"]
            _properties["fontSize"] = obj_view_json["label"]["fontSize"]
            _properties["fontBold"] = True if obj_view_json["label"]["fontBold"] else False
            _properties["fontItalic"] = True if obj_view_json["label"]["fontItalic"] else False
            _properties["fontUnderline"] = True if obj_view_json["label"]["fontUnderline"] else False
            _properties["fontColor"] = obj_view_json["label"]["fontColor"]
            
            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except ValueError as e:
            error_msg = f"[Override OptionList Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override OptionList Failed] {str(e)} for name:{name} and view_obj_type:{view_obj_type}"
            raise Exception(error_msg)
    
    @classmethod
    def override_slider(cls, obj_json:dict, obj_view_json:dict):
        """Slider"""
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type != "Slider":
                raise ValueError(f"View Type of object:`{view_obj_type}` is not a `Slider`.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]
            
            # outline section
            _properties["style"] = obj_view_json["outline"]["style"]
            _properties["direction"] = obj_view_json["outline"]["direction"]
            
            _properties["blockStyle"] = obj_view_json["outline"]["blockStyle"] # int
            _properties["blockWidth"] = obj_view_json["outline"]["blockWidth"]
            _properties["blockColor"] = obj_view_json["outline"]["blockColor"]
            _properties["frameColor"] = obj_view_json["outline"]["frameColor"]
            _properties["backgroundColor"] = obj_view_json["outline"]["backgroundColor"]
            _properties["slotColor"] = obj_view_json["outline"]["slotColor"]
            
            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except ValueError as e:
            error_msg = f"[Override Slider Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override Slider Failed] {str(e)} for name:{name} and view_obj_type:{view_obj_type}"
            raise Exception(error_msg)
        
    @classmethod
    def override_input_object(cls, obj_json:dict, obj_view_json:dict):
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type not in cls.supported_input_objects:
                raise ValueError(f"View Type of object:`{view_obj_type}` is not supported.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]
            
            # outline section
            """v1|1|<index>|0:|<galleryNo>:<galleryName>
            - for both Input: "v1|1|0|0:|30:System Input Box - Ribbon.flbx"
            - so far, only changing the gallery name wihtout changing `pictureIndex` is OK
            """
            galleryName = obj_view_json["outline"]["galleryName"]
            index = obj_view_json["outline"]["index"]
            
            _path = cls.get_picture_path(objectType=view_obj_type, galleryName=galleryName, index=index)
            _properties["picture"]["path"] = _path
            _properties["picture"]["kind"] = "resource" # fixed at resource
            _properties["pictureColor"] = obj_view_json["outline"]["color"]
            
            # bg section
            obj_bg_color = obj_view_json["background"]["color"]
            _properties["fill"]["subjectColor"] = obj_bg_color
            _properties["fill"]["pattern"] = 0 # 0 => has color
            if obj_bg_color == "#00000000":
                _properties["fill"]["pattern"] = 255 
                
            _properties["radius"] = obj_view_json["background"]["radius"]
            _properties["border"] = obj_view_json["background"]["border"]
            
            # label section
            _properties["font"] = obj_view_json["label"]["fontStyle"]
            _properties["fontSize"] = obj_view_json["label"]["fontSize"]
            _properties["fontBold"] = True if obj_view_json["label"]["fontBold"] else False
            _properties["fontColor"] = obj_view_json["label"]["fontColor"]
            _properties["alignment"] = obj_view_json["label"]["alignment"]
            _properties["padding"] = obj_view_json["label"]["padding"]
            
            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except ValueError as e:
            error_msg = f"[Override Input Object Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override Input Object Failed] {str(e)} for name:{name} and view_obj_type:{view_obj_type}"
            raise Exception(error_msg)
    
    @classmethod
    def override_draw_object(cls, obj_json:dict, obj_view_json:dict):
        """DrawingRectangle | DrawingEllipse | DrawingPolygon"""
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type not in cls.supported_draw_objects:
                raise ValueError(f"View Type of object:`{view_obj_type}` is not a `Rectangle` | `Ellipse` | `Plygon`")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]            
            
            # Frame Section
            _properties["frameColor"] = obj_view_json["frame"]["frameColor"]
            _properties["frameWidth"] = obj_view_json["frame"]["frameWidth"] # int        
            _properties["style"] = obj_view_json["frame"]["style"] # int
            
            # Only DrawingRectangle has `frameRadius`
            if view_obj_type == "DrawingRectangle":
                _properties["frameRadius"] = obj_view_json["frame"]["frameRadius"]
                
            # Points section for polygon
            if view_obj_type == "DrawingPolygon":
                # check points of polygon
                points = obj_view_json["points"]
                num_pts = len(points)
                if num_pts < 3:
                    raise ValueError(f"[Override Polygon Error] name of `{name}` should have points > 3 ea; got {num_pts}")
                # check val 0-1
                for pt in points:
                    x, y = pt["x"], pt["y"]
                    x_rule_ul = x <= 1
                    y_rule_ul = y <= 1
                    x_rule_ll = x >= 0
                    y_rule_ll = y >= 0
                    if not (x_rule_ul and y_rule_ul and x_rule_ll and y_rule_ll):
                        raise ValueError(f"[Override Polygon Error] name of `{name}` has incorrect (x,y) = ({x},{y}); should be a normalized value within 0-1")
                # assign points
                _properties["points"] = points
                

            # Interior section
            _properties["fill"]["pattern"] = 0 # set to 0, default 255
            _properties["fill"]["subjectColor"] = obj_view_json["interior"]["color"] # 搭配 pattern = 0 才是代表有填滿，否則只設此值無意義, 設"#00000000" 表示為空
            
            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except ValueError as e:
            error_msg = f"[Override Draw Widget Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override Draw Widget Failed] {str(e)} for name: `{name}` and view_obj_type: `{view_obj_type}`"
            raise Exception(error_msg)
    
    @classmethod
    def override_line_widget(cls, obj_json:dict, obj_view_json:dict):
        """DrawingLine"""
        def convert_start_end_to_line_properties(_start: dict, _end: dict) -> dict:
            """
            Convert absolute start/end points back to:
            - x
            - y
            - width
            - height
            - points: [_p1, _p2]

            This is the reverse logic of get_line_view().
            """

            sx = _start["x"]
            sy = _start["y"]
            ex = _end["x"]
            ey = _end["y"]

            dx = ex - sx
            dy = ey - sy

            if dx == 0 and dy == 0:
                raise ValueError("[Set Line View Error] start and end point cannot be the same")

            # Bounding box
            _x = min(sx, ex)
            _y = min(sy, ey)

            # Recover width / height
            # For horizontal line, height cannot be 0 in widget definition, so use 1.
            # For vertical line, width cannot be 0 in widget definition, so use 1.
            _width = abs(dx) if dx != 0 else 1
            _height = abs(dy) if dy != 0 else 1

            def normalize_point(pt: dict) -> dict:
                px = pt["x"]
                py = pt["y"]

                if dx == 0:
                    nx = 0.0
                else:
                    nx = 0.0 if px == _x else 1.0

                if dy == 0:
                    ny = 0.0
                else:
                    ny = 0.0 if py == _y else 1.0

                return {
                    "x": nx,
                    "y": ny
                }

            _p1 = normalize_point(_start)
            _p2 = normalize_point(_end)

            return {
                "x": _x,
                "y": _y,
                "width": _width,
                "height": _height,
                "points": [_p1, _p2]
            }
            
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type != "DrawingLine":
                raise ValueError(f"View Type of object:`{view_obj_type}` is not a `Line Widget`.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]            
            
            # Pattern Section
            _properties["lineColor"] = obj_view_json["pattern"]["lineColor"]
            _properties["lineWidth"] = obj_view_json["pattern"]["lineWidth"] # int             
            _properties["style"] = obj_view_json["pattern"]["style"] # int
            
            # Arrow Section
            _properties["arrowType"] = obj_view_json["arrow"]["arrowType"]
            _properties["arrowSize"] = obj_view_json["arrow"]["arrowSize"]
            
            # points
            start_pt = obj_view_json["start_pt"]
            end_pt = obj_view_json["end_pt"]
            _convert_pt = convert_start_end_to_line_properties(start_pt, end_pt)
            
            # profile section
            _properties["x"] = _convert_pt["x"]
            _properties["y"] = _convert_pt["y"]
            _properties["width"] = _convert_pt["width"]
            _properties["height"] = _convert_pt["height"]
            _properties["points"] = _convert_pt["points"]
        
        except ValueError as e:
            error_msg = f"[Override Line Widget Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override Line Widget Failed] {str(e)} for name:{name} and view_obj_type:{view_obj_type}"
            raise Exception(error_msg)
    
    @classmethod
    def override_link_line_widget(cls, obj_json:dict, obj_view_json:dict):
        """DrawingLinkLine"""   
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type != "DrawingLinkLine":
                raise ValueError(f"View Type of object:`{view_obj_type}` is not a `Link Line`.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]            
            
            # Pattern Section
            _properties["lineColor"] = obj_view_json["pattern"]["lineColor"] # hex str
            _properties["lineWidth"] = obj_view_json["pattern"]["lineWidth"] # int
            _properties["style"] = obj_view_json["pattern"]["style"] # int
            
            # Arrow Section
            _properties["arrowType"] = obj_view_json["arrow"]["arrowType"]
            _properties["arrowSize"] = obj_view_json["arrow"]["arrowSize"]
            
            # points section
            points = obj_view_json["points"]
            num_pts = len(points)
            if num_pts < 2:
                raise ValueError(f"[Override Link Line Error] name of `{name}` should have at least 2 points; got {num_pts}")
            # check val 0-1
            for pt in points:
                x, y = pt["x"], pt["y"]
                x_rule_ul = x <= 1
                y_rule_ul = y <= 1
                x_rule_ll = x >= 0
                y_rule_ll = y >= 0
                if not (x_rule_ul and y_rule_ul and x_rule_ll and y_rule_ll):
                    raise ValueError(f"[Override Link Line Error] name of `{name}` has incorrect (x,y) = ({x},{y}); should be a normalized value within 0-1")
            # assign points
            _properties["points"] = points
            
            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except ValueError as e:
            error_msg = f"[Override Link Line Widget Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override Link Line Widget Failed] {str(e)} for name: `{name}` and view_obj_type: `{view_obj_type}`"
            raise Exception(error_msg)
    
    @classmethod
    def override_arc_widget(cls, obj_json:dict, obj_view_json:dict):
        """DrawingArc"""
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type != "DrawingArc":
                raise ValueError(f"View Type of object:`{view_obj_type}` is not a `Arc`.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]            
            
            # Pattern Section
            _properties["lineColor"] = obj_view_json["pattern"]["lineColor"]
            _properties["lineWidth"] = obj_view_json["pattern"]["lineWidth"] # int              
            _properties["style"] = obj_view_json["pattern"]["style"] # int
            
            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except ValueError as e:
            error_msg = f"[Override Arc Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override Arc Failed] {str(e)} for name:{name} and view_obj_type:{view_obj_type}"
            raise Exception(error_msg)
     
    @classmethod
    def override_scale_widget(cls, obj_json:dict, obj_view_json:dict):
        """DrawingScale"""
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type != "DrawingScale":
                raise ValueError(f"View Type of object:`{view_obj_type}` is not a `Scale Widget`.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]      
            
            # general section
            _properties["type"] = obj_view_json["general"]["type"] # int, 0: Circular; 1: Linear
            _properties["angleSetting"] = obj_view_json["general"]["angleSetting"]
            _properties["alignment"] = obj_view_json["general"]["alignment"]
            _properties["direction"] = obj_view_json["general"]["direction"]

            # tick_mark section
            _properties["tickWidth"] = obj_view_json["tick_mark"]["tickWidth"]
            _properties["tickStyle"] = obj_view_json["tick_mark"]["tickStyle"]
            _properties["tickColor"] = obj_view_json["tick_mark"]["tickColor"]   
            _properties["tickMainDivision"] = obj_view_json["tick_mark"]["tickMainDivision"]
            _properties["mainScaleLength"] = obj_view_json["tick_mark"]["mainScaleLength"]
            _properties["tickSubDivision"] = obj_view_json["tick_mark"]["tickSubDivision"]
            _properties["subScaleLength"] = obj_view_json["tick_mark"]["subScaleLength"]
            
            # scale_label section
            showScaleLabel = obj_view_json["scale_label"]["showScaleLabel"]
            _properties["showScaleLabel"] = True if showScaleLabel else False
            
            _properties["font"] = obj_view_json["scale_label"]["fontStyle"]
            _properties["fontSize"] = obj_view_json["scale_label"]["fontSize"]
            _properties["fontColor"] = obj_view_json["scale_label"]["fontColor"]
            _properties["rightDecimalPt"] = obj_view_json["scale_label"]["rightDecimalPt"]
            _properties["leftDecimalPt"] = obj_view_json["scale_label"]["leftDecimalPt"]
            _properties["limit"] = obj_view_json["scale_label"]["limit"]
            
            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except ValueError as e:
            error_msg = f"[Override Scale Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override Scale Failed] {str(e)} for name: `{name}` and view_obj_type: `{view_obj_type}`"
            raise Exception(error_msg) 
        
    @classmethod
    def override_embed_window(cls, obj_json:dict, obj_view_json:dict):
        """EmbeddedWindow"""
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type != "EmbeddedWindow":
                raise ValueError(f"View Type of object:`{view_obj_type}` is not a `EmbeddedWindow`.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]      
            
            # display section
            _properties["containerMode"] = obj_view_json["display"]["mode"]
            
            title = obj_view_json["display"]["title"]
            _properties["titleString"] = title
            _properties["titleEnabled"] = False
            if title:
                _properties["titleEnabled"] = True
            
            _properties["displayAnchor"] = obj_view_json["display"]["displayAnchor"]

            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except ValueError as e:
            error_msg = f"[Override EmbeddedWindow Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override EmbeddedWindow Failed] {str(e)} for name: `{name}` and view_obj_type: `{view_obj_type}`"
            raise Exception(error_msg) 
    
    @classmethod
    def override_2d_barcode(cls, obj_json:dict, obj_view_json:dict):
        """2DBarcode"""
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type != "2DBarcode":
                raise ValueError(f"View Type of object:`{view_obj_type}` is not a `2D Barcode`.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]      
            
            # general section
            _properties["readValue"] = obj_view_json["general"]["readValue"]
            _properties["barcodeType"] = obj_view_json["general"]["barcodeType"]
            _properties["cellColor"] = obj_view_json["general"]["barcodeColor"]            

            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except ValueError as e:
            error_msg = f"[Override 2DBarcode Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override 2DBarcode Failed] {str(e)} for name: `{name}` and view_obj_type: `{view_obj_type}`"
            raise Exception(error_msg) 
    
    @classmethod
    def override_other_object(cls, obj_json:dict, obj_view_json:dict):
        """Picture"""
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            view_obj_type = obj_view_json["objectType"]
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if objectTypeName:
                obj_json["objectTypeName"] = objectTypeName # e.g. Picture → objectPicture
            else:
                obj_json["objectTypeName"] = view_obj_type # e.g. objectDrawingArbitraryLine → objectDrawingArbitraryLine
            
            _properties = obj_json["properties"]
            
            # profile section
            _properties["x"] = obj_view_json["profile"]["x"]
            _properties["y"] = obj_view_json["profile"]["y"]
            _properties["width"] = obj_view_json["profile"]["width"]
            _properties["height"] = obj_view_json["profile"]["height"]
            _properties["rotation"] = obj_view_json["profile"]["rotation"]
        
        except Exception as e:
            error_msg = f"[Override Other Object Failed] {str(e)} for name:{name} and view_obj_type:{view_obj_type}"
            raise Exception(error_msg)
    
    @classmethod
    def override_object_router(cls, obj_json:dict, obj_view_json:dict) -> dict:
        """a router for override"""
        _obj_view_type = obj_view_json["objectType"]
        
        if _obj_view_type in cls.supported_general_objects:
            cls.override_general_object(obj_json, obj_view_json)
        elif _obj_view_type == "OptionList":
            cls.override_option_list(obj_json, obj_view_json)
        elif _obj_view_type == "Slider":
            cls.override_slider(obj_json, obj_view_json)
        elif _obj_view_type in cls.supported_input_objects:
            cls.override_input_object(obj_json, obj_view_json)
        elif _obj_view_type in cls.supported_draw_objects:
            cls.override_draw_object(obj_json, obj_view_json)
        elif _obj_view_type == "DrawingLine":
            cls.override_line_widget(obj_json, obj_view_json)
        elif _obj_view_type == "DrawingLinkLine":
            cls.override_link_line_widget(obj_json, obj_view_json)
        elif _obj_view_type == "DrawingArc":
            cls.override_arc_widget(obj_json, obj_view_json)
        elif _obj_view_type == "DrawingScale":
            cls.override_scale_widget(obj_json, obj_view_json)
        elif _obj_view_type == "EmbeddedWindow":
            cls.override_embed_window(obj_json, obj_view_json)
        elif _obj_view_type == "2DBarcode":
            cls.override_2d_barcode(obj_json, obj_view_json)
        else:
            cls.override_other_object(obj_json, obj_view_json)
    
    @classmethod
    def override_layerIndex(cls, obj_json:dict, new_idx:int):
        """2026/05/25 棄用LayerIndex但保留此func"""
        try:
            name = obj_json["name"]
            objectTypeName = obj_json["objectTypeName"]
            # change layer index
            obj_json["layerIndex"] = new_idx 
            obj_json["properties"]["layerIndex"] = new_idx 
            
        except Exception as e:
            error_msg = f"[Override layerIndex Failed] {str(e)} for name:{name} and objectTypeName:{objectTypeName}"
            raise Exception(error_msg)
    
    def __init__(self):
        self.descr="transform view json to original json"
        self.ebx_object_default_json = self.getEBXObjDefaultJSON()
    
    def getEBXObjDefaultJSON(self, folder:str = "./EBXDefaultJSON") -> dict:
        """EBX default JSON
        - file name: same as object view type, <ObjectType>.json
        """
        ebx_object_default_json = {}
        # scan files under folder
        files = os.listdir(folder)
        for file in files:
            key = file.split(".")[0]
            filename = os.path.join(folder, file)
            with open(filename, 'r', encoding='utf-8') as f:
                obj_json = json.load(f)
                ebx_object_default_json[key] = obj_json
        
        if not ebx_object_default_json:
            raise Exception(f"[Get EBX Default JSON Error] EBX Object Map is None")
        
        return ebx_object_default_json
                
    def import_project_from_view_by_socket(self, view_path:str, project_path:str, **kwargs) -> str:
        """override generated screen view to ebx screen json by socket import
            Args:
            - view_path: LLM 產生的 json view 路徑
            - project_path: EBX export 檔案路徑 (.ebxprj)
        """
        try:
            sc_view = self.load_json_file(view_path)
            sc_name = sc_view["screen_name"]
            
            # get project json by socket
            _ebx_proj = EBXImportExport.export_project(project_path, sc_name)              
            # find the sc
            _idx, _sc_json = self.get_screen_from_project(_ebx_proj, sc_name)
            if _idx < 0 or not _sc_json:
                """後續變成安插新的screen (暫時忽略)"""
                raise Exception(f"[Override Screen Failed] screen name :{sc_name} not found in EBX project: {project_path}.")
            
            # override bg
            self.override_screen_background(_sc_json, sc_view)
            
            objects = sc_view["objects"]
            _objects = _sc_json["objects"]
            _obj_names = self.get_screen_object_names(_objects)
            
            # scan objects in sc_view
            _objects_reorder = []
            for idx, obj in enumerate(objects):
                obj_name = obj["name"]
                obj_type = obj["objectType"]
                # 若物件不存在則 insert
                if obj_name not in _obj_names:
                    _obj = copy.deepcopy(self.ebx_object_default_json[obj_type]) # 抓對應的原始物件, 使用 copy 避免共用 reference
                    self.override_object_router(_obj, obj) # 更改該物件
                    # self.override_layerIndex(_obj, idx) # 更改 layerIndex (已停用)
                    _objects_reorder.insert(idx, _obj) # 插入該物件
                else:
                    # 物件存在則找尋該物件
                    for _idx, _obj in enumerate(_objects):
                        _name = _obj["name"]
                        _type = self.get_object_type(_obj) # 轉為 view obj type
                        # 存在就 update
                        if _name == obj_name and _type == obj_type:
                            # 依照物件型態修改
                            self.override_object_router(_obj, obj) # 更改該物件
                            # self.override_layerIndex(_obj, idx) # 更改 layerIndex (已停用)
                            _objects_reorder.insert(idx, _obj) # 插入該物件
                            break
            
            # override whole obj list
            _sc_json["objects"] = _objects_reorder
            
            # call socket to override org project file
            EBXImportExport.import_project(_ebx_proj, project_path)
        
        except:
            raise    
    
    def upsert_objects2screen_by_socket(self, widget_list:list, screen_name:str, project_path:str, screen_properties:dict={}, **kwargs) -> str:
        """update | insert obj to a view and save it to proj
            Args:
            - widget_list: widgets to update | insert
            - screen_name: user's specified screen
            - project_path: EBX export 檔案路徑 (.ebxprj)
        """
        try:
            # get project json by socket
            _ebx_proj = EBXImportExport.export_project(project_path, screen_name)
            _idx, _sc_json = self.get_screen_from_project(_ebx_proj, screen_name)
            if _idx < 0 or not _sc_json:
                """後續變成安插新的screen (暫時忽略)"""
                raise Exception(f"[Upsert Failed] screen name :{screen_name} not found in EBX project: {project_path}.")        
            
            _objects = _sc_json["objects"]
            _obj_names = self.get_screen_object_names(_objects)
            
            out_msg = ""
            
            # override screen if provided
            if screen_properties:
                self.override_screen_properties(_sc_json, screen_properties)
                out_msg += f"Change BG Window success\n"
            
            # scan objects list
            for idx, obj in enumerate(widget_list):
                obj_name = obj["name"]
                obj_type = obj["objectType"] # view type rather than ebx type
                # 若物件不存在則 insert
                if obj_name not in _obj_names:
                    _obj = copy.deepcopy(self.ebx_object_default_json[obj_type]) # 抓對應的原始物件, 使用 copy 避免共用 reference
                    self.override_object_router(_obj, obj) # 更改該物件
                    _objects.append(_obj) # 插入該物件(加入到最後)，不改 layerIndex
                    out_msg += f"Create Object `{obj_name}` success\n"
                else:
                    # 物件存在則找尋該物件
                    for _idx, _obj in enumerate(_objects):
                        _name = _obj["name"]
                        _type = self.get_object_type(_obj) # 轉為 view obj type
                        # 存在就 update
                        if _name == obj_name and _type == obj_type:
                            # 依照物件型態修改，不改 layerIndex
                            self.override_object_router(_obj, obj)
                            out_msg += f"Update Object `{obj_name}` success.\n"
                            break
                        elif _name == obj_name and _type != obj_type:
                            out_msg += f"Update Object `{obj_name}` failed. The type `{obj_type}` is incorrect\n"
                            break
            
            # call socket to override org project file
            EBXImportExport.import_project(_ebx_proj, project_path)
        
            return out_msg
        
        except:
            raise     
    
    def override_project_from_view(self, view_path:str, project_path:str, **kwargs) -> str:
        """override generated screen view to ebx screen json
            Args:
            - view_path: LLM 產生的 json view 路徑
            - project_path: EBX export 檔案路徑
        """
        try:
            sc_view = self.load_json_file(view_path)
            _ebx_proj = self.load_json_file(project_path)
            
            # find the sc from project
            sc_name = sc_view["screen_name"]
            _idx, _sc_json = self.get_screen_from_project(_ebx_proj, sc_name)
            if _idx < 0 or not _sc_json:
                """後續變成安插新的screen (暫時忽略)"""
                raise Exception(f"[Override Screen Failed] screen name :{sc_name} not found in EBX project: {project_path}.")
            
            # override bg
            self.override_screen_background(_sc_json, sc_view)
            
            objects = sc_view["objects"]
            _objects = _sc_json["objects"]
            _obj_names = self.get_screen_object_names(_objects)
            
            # scan objects in sc_view
            _objects_reorder = []
            for idx, obj in enumerate(objects):
                obj_name = obj["name"]
                obj_type = obj["objectType"]
                # 若物件不存在則 insert
                if obj_name not in _obj_names:
                    _obj = copy.deepcopy(self.ebx_object_default_json[obj_type]) # 抓對應的原始物件, 使用 copy 避免共用 reference
                    self.override_object_router(_obj, obj) # 更改該物件
                    # self.override_layerIndex(_obj, idx) # 更改 layerIndex (已停用)
                    _objects_reorder.insert(idx, _obj) # 插入該物件
                else:
                    # 物件存在則找尋該物件
                    for _idx, _obj in enumerate(_objects):
                        _name = _obj["name"]
                        _type = self.get_object_type(_obj) # 轉為 view obj type
                        # 存在就 update
                        if _name == obj_name and _type == obj_type:
                            # 依照物件型態修改
                            self.override_object_router(_obj, obj) # 更改該物件
                            # self.override_layerIndex(_obj, idx) # 更改 layerIndex (已停用)
                            _objects_reorder.insert(idx, _obj) # 插入該物件
                            break
            
            # override whole obj list
            _sc_json["objects"] = _objects_reorder
            
            # override org project file
            with open(project_path, 'w', encoding='utf-8') as f:
                json.dump(_ebx_proj, f, ensure_ascii=False, indent=4)
        
        except:
            raise
            
    def upsert_objects2screen(self, widget_list:list, screen_name:str, project_path:str, screen_properties:dict={}, **kwargs) -> str:
        """update | insert obj to a view and save it to proj
            Args:
            - widget_list: widgets to update | insert
            - screen_name: user's specified screen
            - project_path: EBX export 檔案路徑
        """
        try:
            _ebx_proj = self.load_json_file(project_path)
            _idx, _sc_json = self.get_screen_from_project(_ebx_proj, screen_name)
            if _idx < 0 or not _sc_json:
                """後續變成安插新的screen (暫時忽略)"""
                raise Exception(f"[Upsert Failed] screen name :{screen_name} not found in EBX project: {project_path}.")        
            
            _objects = _sc_json["objects"]
            _obj_names = self.get_screen_object_names(_objects)
            
            out_msg = ""
            
            # override screen if provided
            if screen_properties:
                self.override_screen_properties(_sc_json, screen_properties)
                out_msg += f"Change BG Window success\n"
            
            # scan objects list
            for idx, obj in enumerate(widget_list):
                obj_name = obj["name"]
                obj_type = obj["objectType"]
                # 若物件不存在則 insert
                if obj_name not in _obj_names:
                    _obj = copy.deepcopy(self.ebx_object_default_json[obj_type]) # 抓對應的原始物件, 使用 copy 避免共用 reference
                    self.override_object_router(_obj, obj) # 更改該物件
                    _objects.append(_obj) # 插入該物件(加入到最後)，不改 layerIndex
                    out_msg += f"Create Object `{obj_name}` success\n"
                else:
                    # 物件存在則找尋該物件
                    for _idx, _obj in enumerate(_objects):
                        _name = _obj["name"]
                        _type = self.get_object_type(_obj) # 轉為 view obj type
                        # 存在就 update
                        if _name == obj_name and _type == obj_type:
                            # 依照物件型態修改，不改 layerIndex
                            self.override_object_router(_obj, obj)
                            out_msg += f"Update Object `{obj_name}` success.\n"
                            break
                        elif _name == obj_name and _type != obj_type:
                            out_msg += f"Update Object `{obj_name}` failed. The type `{obj_type}` is incorrect\n"
                            break
            
            # override org project file
            with open(project_path, 'w', encoding='utf-8') as f:
                json.dump(_ebx_proj, f, ensure_ascii=False, indent=4)
        
            return out_msg
        
        except:
            raise 
        

if __name__ == "__main__":
    project_path = "Project_DrawWidgets.json" # 測試用 json
    save_view_path = "./picture-view.json"
    screen_name = "demo6"
    
    sc_decoder = ScreenDecoder()
    sc_view = sc_decoder.get_screen_view_from_file(project_path, screen_name)
    print(sc_view)
    
    with open(save_view_path, "w", encoding='utf-8') as f:
        json.dump(sc_view, f, ensure_ascii=False, indent=4)
    
    # sc_encoder = ScreenEncoder()
    # sc_encoder.override_project_from_view(save_view_path, project_path)
    
    pass