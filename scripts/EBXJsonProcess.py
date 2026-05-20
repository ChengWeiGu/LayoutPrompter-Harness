import os
import copy
import json
import shutil
from pathlib import Path


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
    "objectComposite":"CompositeWidget"
}

ObjectMap_view2ebx = {}
for k,v in ObjectMap_ebx2view.items():
    ObjectMap_view2ebx[v] = k
# Lamp is actually a `objectSwitch`
ObjectMap_view2ebx["Lamp"] = "objectSwitch"


"""transform original json into view json"""
class ScreenDecoder:
    
    supported_input_objects = ["NumericInput", "TextInput"]
    supported_general_objects = ["Lamp", "Switch","Button","Text"]
    
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
            _bg_color = _properties["fill"]["subjectColor"] # default #00000000 => 八碼代表透明, 另外 fill 中的 `pattern` is always 0
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
            
            # use short name
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
            
            # use short name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "Slider":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not a `Slider`.")
            
            # outline section
            _style =  _properties["style"] # default 0 => 0/1/2: default/crystal/flat
            _direction = _properties["direction"] # default 0 => 0/1/2/3: right/up/left/down
            _blockStyle = _properties["blockStyle"] # default "big_rect" => 0/1/2/3: Big rect/Small rect/Up arrow/Down arrow
            if _blockStyle == "big_rect":
                _blockStyle = 0
            elif _blockStyle == "small_rect":
                _blockStyle = 1
            elif _blockStyle == "up_arrow":
                _blockStyle = 2
            elif _blockStyle == "down_arrow":
                _blockStyle = 3
            
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
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use short name
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
            _bg_color = _properties["fill"]["subjectColor"] # default #00000000 => transparent
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
    def get_rectangle_view(cls, object_json:dict) -> dict:
        """DrawingRectangle"""
        try:
            _name = object_json["name"]
            _objectTypeName = object_json["objectTypeName"]
            _properties = object_json["properties"]
            
            # use short name
            _view_object_type = cls.get_object_type(object_json)
            if _view_object_type != "DrawingRectangle":
                raise ValueError(f"Type of object:`{_objectTypeName}` is not a `Rectangle`.")
            
            # Frame Section
            _frameColor = _properties["frameColor"] # default "#000000"
            
            _frameWidth = _properties["frameWidth"] # default "width_1px"
            _frameWidth = int(_frameWidth.split("_")[-1][0]) # 變成整數
            
            _style =  _properties["style"] # default "solid_line" => solid_line/dash_line/dot_line/dash_dot_line/dash_dot_dot_line
            if _style == "solid_line":
                _style = 0
            elif _style == "dash_line":
                _style = 1
            elif _style == "dot_line":
                _style = 2
            elif _style == "dash_dot_line":
                _style = 3
            elif _style == "dash_dot_dot_line":
                _style = 4
            else:
                _style = 0 # 沒有 "5" => 直接變成預設
            
            _frameRadius = _properties["frameRadius"] # default 0
            
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
                    "style":_style,
                    "frameRadius":_frameRadius
                },
                "interior":{
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
            
            return _view
        
        except ValueError as e:
            error_msg = f"[Get Rectangle View Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Get Rectangle View Failed] {str(e)} for name:{_name} and type:{_objectTypeName}"
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
        elif _obj_type == "DrawingRectangle":
            _obj_view = cls.get_rectangle_view(object_json)
        else:
            _obj_view = cls.get_other_object_view(object_json) # None
        
        return _obj_view
    
    def __init__(self):
        self.descr="transform original json into view json"
        
    def get_screen_view_from_file(self, project_path:str, screen_name:str, **kwargs) -> dict:
        """transform whole screen json to the view that LLM understands
            Args:
            - project_path: EBX export 檔案路徑
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
        
        else:
            raise Exception(f"[Get Token Failed] Type of object:`{objectType}` is not supported.")
        
        if not galleryNo:
            raise Exception(f"[Get Token Failed] for `{objectType}` and `{galleryName}`")
        
        return f"v1|1|{index}|0:|{galleryNo}:{galleryName}"         
    
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
    def override_general_object(cls, obj_json:dict, obj_view_json:dict):
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
            _properties["fill"]["pattern"] = 0 # always 0
            _properties["fill"]["subjectColor"] = obj_view_json["background"]["color"]
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
            
            blockStyle = obj_view_json["outline"]["blockStyle"] # int
            if blockStyle == 0:
                _blockStyle = "big_rect"
            elif blockStyle == 1:
                _blockStyle = "small_rect"
            elif blockStyle == 2:
                _blockStyle = "up_arrow"
            elif blockStyle == 3:
                _blockStyle = "down_arrow"
            else:
                _blockStyle = "big_rect" # default
            
            _properties["blockStyle"] = _blockStyle
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
            _properties["fill"]["subjectColor"] = obj_view_json["background"]["color"]
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
    def override_rectangle(cls, obj_json:dict, obj_view_json:dict):
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            # filter
            view_obj_type = obj_view_json["objectType"]
            if view_obj_type != "DrawingRectangle":
                raise ValueError(f"View Type of object:`{view_obj_type}` is not a `Rectangle`.")
            
            # type mapping
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                objectTypeName = view_obj_type
            # type    
            obj_json["objectTypeName"] = objectTypeName
            
            _properties = obj_json["properties"]            
            
            # Frame Section
            _properties["frameColor"] = obj_view_json["frame"]["frameColor"]
            
            frameWidth = obj_view_json["frame"]["frameWidth"] # int
            _properties["frameWidth"] = f"width_{frameWidth}px"

            style = obj_view_json["frame"]["style"] # int
            if style == 0:
                _style = "solid_line"
            elif style == 1:
                _style = "dash_line"
            elif style == 2:
                _style = "dot_line"
            elif style == 3:
                _style = "dash_dot_line"
            elif style == 4:
                _style = "dash_dot_dot_line"
            else:
                _style = "solid_line" # default
            
            _properties["style"] = _style
            _properties["frameRadius"] = obj_view_json["frame"]["frameRadius"]

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
            error_msg = f"[Override Rectangle Failed] {str(e)}"
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"[Override Rectangle Failed] {str(e)} for name:{name} and view_obj_type:{view_obj_type}"
            raise Exception(error_msg)
    
    @classmethod
    def override_other_object(cls, obj_json:dict, obj_view_json:dict):
        try:
            name = obj_view_json["name"]
            obj_json["name"] = name
            
            view_obj_type = obj_view_json["objectType"]
            objectTypeName = ObjectMap_view2ebx.get(view_obj_type, None)
            if not objectTypeName:
                obj_json["objectTypeName"] = objectTypeName # e.g. CompositeWidget
            else:
                obj_json["objectTypeName"] = view_obj_type
            
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
        elif _obj_view_type == "DrawingRectangle":
            cls.override_rectangle(obj_json, obj_view_json)
        else:
            cls.override_other_object(obj_json, obj_view_json)
    
    
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
            for idx, obj in enumerate(objects):
                obj_name = obj["name"]
                obj_type = obj["objectType"]
                # 若物件不存在則 insert
                if obj_name not in _obj_names:
                    _obj = copy.deepcopy(self.ebx_object_default_json[obj_type]) # 抓對應的原始物件, 使用 copy 避免共用 reference
                    self.override_object_router(_obj, obj) # 更改該物件
                    _objects.insert(idx, _obj) # 插入該物件
                else:
                    # 物件存在則找尋該物件
                    for _idx, _obj in enumerate(_objects):
                        _name = _obj["name"]
                        _type = self.get_object_type(_obj) # 轉為 view obj type
                        # 存在就 update
                        if _name == obj_name and _type == obj_type:
                            # 依照物件型態修改
                            self.override_object_router(_obj, obj)
                            break
            
            # override org project file
            with open(project_path, 'w', encoding='utf-8') as f:
                json.dump(_ebx_proj, f, ensure_ascii=False, indent=4)
        
        except:
            raise
            
    def upsert_objects2screen(self, widget_list:list, screen_name:str, project_path:str, **kwargs) -> str:
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
            
            # scan objects list
            for idx, obj in enumerate(widget_list):
                obj_name = obj["name"]
                obj_type = obj["objectType"]
                # 若物件不存在則 insert
                if obj_name not in _obj_names:
                    _obj = copy.deepcopy(self.ebx_object_default_json[obj_type]) # 抓對應的原始物件, 使用 copy 避免共用 reference
                    self.override_object_router(_obj, obj) # 更改該物件
                    _objects.append(_obj) # 插入該物件(加入到最後)
                    out_msg += f"Create Object `{obj_name}` success\n"
                else:
                    # 物件存在則找尋該物件
                    for _idx, _obj in enumerate(_objects):
                        _name = _obj["name"]
                        _type = self.get_object_type(_obj) # 轉為 view obj type
                        # 存在就 update
                        if _name == obj_name and _type == obj_type:
                            # 依照物件型態修改
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
    project_path = "Project800_480.json" # 測試用 json
    save_view_path = "./EXP-view.json"
    screen_name = "demo5"
    
    sc_decoder = ScreenDecoder()
    sc_view = sc_decoder.get_screen_view_from_file(project_path, screen_name)
    print(sc_view)
    
    with open(save_view_path, "w", encoding='utf-8') as f:
        json.dump(sc_view, f, ensure_ascii=False, indent=4)
    
    # sc_encoder = ScreenEncoder()
    # sc_encoder.override_project_from_view(save_view_path, project_path)
    
    pass