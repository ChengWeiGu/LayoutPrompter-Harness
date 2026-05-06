import os
import copy
import json


object_map = {
    0x0000: "Undefined",

    # test
    0x6F6D: "MockObject",
    0x6F43: "CollaborativeMockObject",

    # widget
    0x6261: "AlarmBar",
    0x6461: "AlarmDisplay",
    0x6762: "BarGraph",
    0x7462: "Button",
    0x7063: "CompositeObject",
    0x6463: "ConditionObject",
    0x6464: "DataDisplay",
    0x7765: "EmbeddedWindow",
    0x626D: "MatrixBarcode",
    0x656E: "Numeric",
    0x6C6F: "OptionList",
    0x5250: "PdfReaderObject",
    0x6970: "PictureObject",
    0x6C73: "Slider",
    0x7773: "Switch",
    0x7474: "Text",
    0x7874: "TextInput",
    0x6474: "TrendDisplay",
    0x7672: "RecipeView",

    # background object
    0x6F61: "Alarm",
    0x6D61: "AlarmManager",
    0x6264: "DatabaseServer",
    0x7364: "DataSampling",
    0x6572: "Recipe",
    0x7274: "RecipeEntity",
    0x6D72: "RecipeManager",
    0x656D: "MacroEntity",
    0x666D: "MacroFunctionEntity",
    0x7473: "StringLibrary",
    0x6F73: "SystemObject",
    0x6175: "UacObject",
    0x7761: "WindowAssistant",
    0x7764: "Dashboard",
    0x7377: "WeincloudSetting",
    0x6E64: "DashboardEdgeNode",
    0x6165: "EasyAccess",
    0x6364: "DeviceConfig",
    0x6373: "ServerConfig",

    # drawing object
    0x6C64: "DrawingLine",
    0x6C61: "DrawingArbitraryLine",
    0x6C6C: "DrawingLinkLine",
    0x7261: "DrawingArc",
    0x6564: "DrawingEllipse",
    0x7264: "DrawingRectangle",
    0x7064: "DrawingPolygon",
    0x6373: "DrawingScale",

    # window
    0x776F: "ObjectWindow",
    0x6D63: "CompsiteModel"
}


ebx_object_default_json = {}


"""抓取EBX預設物件JSON格式
- 檔案名稱要與 object_map value 名稱一致
"""
def getEBXObjDefaultJSON(folder="./EBXDefaultJSON"):
    # scan files under folder
    files = os.listdir(folder)
    for file in files:
        key = file.split(".")[0]
        filename = os.path.join(folder, file)
        with open(filename, 'r', encoding='utf-8') as f:
            obj_json = json.load(f)
            ebx_object_default_json[key] = obj_json

# 執行
getEBXObjDefaultJSON()


def getProjectSize(project_json:dict) -> dict:
    size = {
        "width":0,
        "height":0
    }
    screenInfo = project_json["body"]["dataSections"]["info"]
    width, height = screenInfo["resolutionWidth"], screenInfo["resolutionHeight"]
    size.update({
        "width":width,
        "height":height
    })
        
    return size



def getScreenNames(project_json:dict) -> dict:
    screens = {}
    _screens = project_json["body"]["dataSections"]["windowSection"]["screens"]["children"]["$elements"]
    for idx, s in enumerate(_screens):
        name = s["data"]["name"]
        screens.update({
            name: idx
            })
    return screens



def getObjNames(sc_objs:list) -> list:
    names = []
    for sc_obj in sc_objs:
        name = sc_obj["name"]
        names.append(name)
    return names
    


def decodeScreenBG(screen_json:dict) -> dict:
    data = {
        "color":{
            "r":"255",
            "g":"255",
            "b":"255",
            "a":"255"
        },
        "border":{
            "color":{
                "a":"255"
            },
            "style":"5"
        }
    }
    
    # get bg widget
    _bg = screen_json["data"]["properties"]["background"]
    # get bg color
    subjectColor = _bg["fill"]["value"]["value"]["subjectColor"]
    # border style
    borderVal = _bg["border"]["value"]["value"]
    
    data["color"] = subjectColor
    data["border"] = borderVal
    
    return data


"""例外
- Switch/Lamp 的 value 皆相同 (都叫做 "30579")
- 需額外透過 read-only來判斷
read-only
"value": {
    "value": "0",
    "#dataType": 4117
}

這是switch

read-only
"value": {
    "value": "1",
    "#dataType": 4117
}

這是lamp
"""
def getObjType(obj_json:dict) -> int:
    objTypeStr = obj_json["properties"]["general"]["widgetType"]["value"]["value"]
    objTypeInt = int(objTypeStr)
    objType = object_map.get(objTypeInt, "Undefined")
    if objType == "Switch":
        readOnly = obj_json["properties"]["general"]["readOnly"]["value"]["value"]
        if readOnly == "1":
            objType = "Lamp"
    return objType


def getObjTypeStr(objType:str) -> str:
    result = "0"
    if objType == "Lamp":
        objType = "Switch"
    # scan
    for k, v in object_map.items():
        if v==objType:
            result = str(k)
            break
    return result


"""Descr
- 共用物件: Lamp/Switch/Button/Text
- Text 有別於 TextInput，為 Draw 物件
- stringLib 只讀第一個狀態 (忽略多狀態)
"""
def decodeGeneralObject(obj_json:dict, stringLibTables:list) -> dict:
    data = {}
    name= obj_json["name"] # Object ID
    objectTypeName = getObjType(obj_json)
    
    """Outline Section"""
    outline = obj_json["properties"]["outline"]
    pciture = obj_json["properties"]["outline"]["picture"]
    
    galleryName = pciture["value"]["info"]["galleryName"]
    index = pciture["value"]["info"]["index"]
    pictureColor = outline["pictureColor"]["value"]["value"]
    pictureHorizontalFlipped  = outline["pictureHorizontalFlipped"]["value"]["value"]
    pictureVerticalFlipped  = outline["pictureVerticalFlipped"]["value"]["value"]
    
    """Background Section"""
    bg = obj_json["properties"]["background"]
    bg_fill = bg["fill"]["value"]["value"] # 預設是 {} => 即為 None
    bg_radius = bg["radius"]["value"]["value"]
    bg_border = bg["border"]["value"]["value"]
    
    bg_color = {}
    if "subjectColor" in bg_fill:
        bg_color = bg_fill["subjectColor"]

    
    """label section"""
    label = obj_json["properties"]["label"]
    
    # Text 物件的 text 藏在 general 中
    if objectTypeName == "Text":
        general = obj_json["properties"]["general"]
        textVal = general["text"]["value"]["value"]
    else:
        textVal = label["text"]["value"]["value"]
    
    # print(textVal)
    _type = textVal.get("type",{}).get("$value", None) # string
    text = ""
    if _type == 'string':
        stringTableId = int(textVal["reference"]["stringTableId"])
        stringId = int(textVal["reference"]["stringId"])
        el = stringLibTables[stringTableId]["lingualStrings"]["$elements"][stringId]
        text = el["strings"]["$elements"][0]["text"] # 只讀第一個狀態
    
    # Font
    fontStyle = label["font"]["value"]["family"] 
    fontSize = label["fontSize"]["value"]["value"]
    fontBold = label["fontBold"]["value"]["value"]
    fontItalic = label["fontItalic"]["value"]["value"]
    fontUnderline = label["fontUnderline"]["value"]["value"]
    fontColor = label["fontColor"]["value"]["value"]
    
    # alignment, default: "4"
    alignment = label["alignment"]["value"]["value"]
    # padding, default: {}
    padding = label["padding"]["value"]["value"]
    # blinking, 0/500/1000
    blinking = label["blinking"]["value"]["value"]
    # scrolling, default: {}, direction: "1"~"4", repeated: "0"/"1". e.g. {'direction': '4', 'repeated': '1', 'speed': '5'}
    scrolling = label["scrolling"]["value"]["value"]
    
    # BBOX
    profile = obj_json["properties"]["profile"]
    x = profile["x"]["value"]["value"]
    y = profile["y"]["value"]["value"]
    width = profile["width"]["value"]["value"]
    height = profile["height"]["value"]["value"]
    rotation = profile["rotation"]["value"]["value"]
    
    
    data = {
        "objectTypeName": objectTypeName,
        "name":name,
        "outline":{
            "galleryName":galleryName,
            "index":index,
            "color":pictureColor
        },
        "background":{
            "color":bg_color,
            "radius":bg_radius,
            "border":bg_border
        },
        "label":{
            "text":text,
            "fontStyle":fontStyle,
            "fontSize":fontSize,
            "fontBold":fontBold,
            "fontItalic":fontItalic,
            "fontUnderline":fontUnderline,
            "fontColor":fontColor,
            "alignment":alignment,
            "padding":padding,
            "blinking":blinking,
            "scrolling":scrolling
        },
        "profile":{
            "x":x,
            "y":y,
            "width":width,
            "height":height,
            "rotation":rotation
        }
    }
    
    # data = json.dumps(data, ensure_ascii=False)
    
    return data


""" OptionList"""
def decodeOptionList(obj_json:dict) -> dict:
    data = {}
    name= obj_json["name"] # Object ID
    objectTypeName = getObjType(obj_json)
    
    """General Section"""
    general = obj_json["properties"]["general"]
    style = general["style"]["value"]["value"] # Int: 1 (classic, default) / 0 (Standard)
    
    """Outline Section"""
    outline = obj_json["properties"]["outline"]
    backgroundColor = outline["backgroundColor"]["value"]["value"] # 直接影響選項中每個 item 底色
    selectionColor = outline["selectionColor"]["value"]["value"] # 只有影響已被選擇的 item 底色
    
    
    """label section"""
    label = obj_json["properties"]["label"]
        
    # Font
    fontStyle = label["font"]["value"]["family"] 
    fontSize = label["fontSize"]["value"]["value"]
    fontBold = label["fontBold"]["value"]["value"]
    fontItalic = label["fontItalic"]["value"]["value"]
    fontUnderline = label["fontUnderline"]["value"]["value"]
    fontColor = label["fontColor"]["value"]["value"]
    
    # BBOX
    profile = obj_json["properties"]["profile"]
    x = profile["x"]["value"]["value"]
    y = profile["y"]["value"]["value"]
    width = profile["width"]["value"]["value"]
    height = profile["height"]["value"]["value"]
    rotation = profile["rotation"]["value"]["value"]
    
    
    data = {
        "objectTypeName": objectTypeName,
        "name":name,
        "style":style,
        "outline":{
            "backgroundColor":backgroundColor,
            "selectionColor":selectionColor
        },
        "label":{
            "fontStyle":fontStyle,
            "fontSize":fontSize,
            "fontBold":fontBold,
            "fontItalic":fontItalic,
            "fontUnderline":fontUnderline,
            "fontColor":fontColor
        },
        "profile":{
            "x":x,
            "y":y,
            "width":width,
            "height":height,
            "rotation":rotation
        }
    }
    
    # data = json.dumps(data, ensure_ascii=False)
    
    return data


"""Slider"""
def decodeSlider(obj_json:dict) -> dict:
    data = {}
    name= obj_json["name"] # Object ID
    objectTypeName = getObjType(obj_json)
    
    """Outline Section"""
    outline = obj_json["properties"]["outline"]
    style = outline["style"]["value"]["value"] # 0/1/2: default/crystal/flat
    direction = outline["direction"]["value"]["value"] # 0/1/2/3: right/up/left/down
    blockStyle = outline["blockStyle"]["value"]["value"] # 0/1/2/3: Big rect/Small rect/Up arrow/Down arrow
    blockWidth = outline["blockWidth"]["value"]["value"]
    blockColor = outline["blockColor"]["value"]["value"]
    frameColor = outline["frameColor"]["value"]["value"] # default: {}
    backgroundColor = outline["backgroundColor"]["value"]["value"] # default: {}
    slotColor = outline["slotColor"]["value"]["value"] # default: {}
    
    # BBOX
    profile = obj_json["properties"]["profile"]
    x = profile["x"]["value"]["value"]
    y = profile["y"]["value"]["value"]
    width = profile["width"]["value"]["value"]
    height = profile["height"]["value"]["value"]
    rotation = profile["rotation"]["value"]["value"]
    
    
    data = {
        "objectTypeName": objectTypeName,
        "name":name,
        "outline":{
            "style":style,
            "direction":direction,
            "blockStyle":blockStyle,
            "blockWidth":blockWidth,
            "blockColor":blockColor,
            "frameColor":frameColor,
            "backgroundColor":backgroundColor,
            "slotColor":slotColor
        },
        "profile":{
            "x":x,
            "y":y,
            "width":width,
            "height":height,
            "rotation":rotation
        }
    }
    
    # data = json.dumps(data, ensure_ascii=False)
    
    return data


"""Descr
- 共用物件: Numeric/TextInput
"""
def decodeInputObject(obj_json:dict) -> dict:
    data = {}
    name= obj_json["name"] # Object ID
    objectTypeName = getObjType(obj_json)
    
    """Outline Section"""
    outline = obj_json["properties"]["outline"]
    pciture = obj_json["properties"]["outline"]["picture"]
    
    galleryName = pciture["value"]["info"]["galleryName"]
    index = pciture["value"]["info"]["index"]
    pictureColor = outline["pictureColor"]["value"]["value"]
    pictureHorizontalFlipped  = outline["pictureHorizontalFlipped"]["value"]["value"]
    pictureVerticalFlipped  = outline["pictureVerticalFlipped"]["value"]["value"]
    
    """Background Section"""
    bg = obj_json["properties"]["background"]
    bg_fill = bg["fill"]["value"]["value"] # 預設是 {} => 即為 None
    bg_radius = bg["radius"]["value"]["value"]
    bg_border = bg["border"]["value"]["value"]
    
    bg_color = {}
    if bg_fill:
        bg_color = bg_fill["subjectColor"]
    
    """label section"""
    label = obj_json["properties"]["label"]
    
    # Font
    fontStyle = label["font"]["value"]["family"] 
    fontSize = label["fontSize"]["value"]["value"]
    fontBold = label["fontBold"]["value"]["value"]
    fontColor = label["fontColor"]["value"]["value"]
    
    # alignment, default: "4"
    alignment = label["alignment"]["value"]["value"]
    # padding, default: {}
    padding = label["padding"]["value"]["value"]
    
    # BBOX
    profile = obj_json["properties"]["profile"]
    x = profile["x"]["value"]["value"]
    y = profile["y"]["value"]["value"]
    width = profile["width"]["value"]["value"]
    height = profile["height"]["value"]["value"]
    rotation = profile["rotation"]["value"]["value"]
    
    
    data = {
        "objectTypeName": objectTypeName,
        "name":name,
        "outline":{
            "galleryName":galleryName,
            "index":index,
            "color":pictureColor
        },
        "background":{
            "color":bg_color,
            "radius":bg_radius,
            "border":bg_border
        },
        "label":{
            "fontStyle":fontStyle,
            "fontSize":fontSize,
            "fontBold":fontBold,
            "fontColor":fontColor,
            "alignment":alignment,
            "padding":padding
        },
        "profile":{
            "x":x,
            "y":y,
            "width":width,
            "height":height,
            "rotation":rotation
        }
    }
    
    # data = json.dumps(data, ensure_ascii=False)
    
    return data



"""Rectangle"""
def decodeRectangle(obj_json:dict) -> dict:
    data = {}
    name= obj_json["name"] # Object ID
    objectTypeName = getObjType(obj_json)
    
    """Frame Section"""
    frame = obj_json["properties"]["frame"]
    frameColor = frame["frameColor"]["value"]["value"]
    frameWidth = frame["frameWidth"]["value"]["value"]
    style = frame["style"]["value"]["value"] # 沒有 "5"
    frameRadius = frame["frameRadius"]["value"]["value"]
    
    """Interior Section"""
    interior = obj_json["properties"]["interior"]
    subjectColor = interior["fill"]["value"]["value"]["subjectColor"]
    
    
    # BBOX
    profile = obj_json["properties"]["profile"]
    x = profile["x"]["value"]["value"]
    y = profile["y"]["value"]["value"]
    width = profile["width"]["value"]["value"]
    height = profile["height"]["value"]["value"]
    rotation = profile["rotation"]["value"]["value"]
    
    data = {
        "objectTypeName": objectTypeName,
        "name":name,
        "frame":{
            "frameColor":frameColor,
            "frameWidth":frameWidth,
            "style":style,
            "frameRadius":frameRadius
        },
        "interior":{
            "color":subjectColor
        },        
        "profile":{
            "x":x,
            "y":y,
            "width":width,
            "height":height,
            "rotation":rotation
        }
    }
    # data = json.dumps(data, ensure_ascii=False)
    
    return data


"""Others
- 如: CompositeObject
"""
def decodeOthers(obj_json:dict) -> dict:
    data = {}
    name= obj_json["name"] # Object ID
    objectTypeName = getObjType(obj_json)
    
    # BBOX
    profile = obj_json["properties"]["profile"]
    x = profile["x"]["value"]["value"]
    y = profile["y"]["value"]["value"]
    width = profile["width"]["value"]["value"]
    height = profile["height"]["value"]["value"]
    rotation = profile["rotation"]["value"]["value"]
    
    data = {
        "objectTypeName": objectTypeName,
        "name":name,
        "profile":{
            "x":x,
            "y":y,
            "width":width,
            "height":height,
            "rotation":rotation
        }
    }
    
    # data = json.dumps(data, ensure_ascii=False)
    
    return data




def encodeScreenBG(sc_json:dict, sc_pseudo_json:dict):
    sc_name = sc_pseudo_json["screen_name"]
    sc_size = sc_pseudo_json["screen_size"]
    screen_properties = sc_pseudo_json["screen_properties"]
    
    _bg = sc_json["data"]["properties"]["background"]
    
    _bg["fill"]["value"]["value"]["subjectColor"] = screen_properties["color"]
    _bg["border"]["value"]["value"] = screen_properties["border"]
    


"""Descr
- 對應 `decodeGeneralObject`, 共用物件: Lamp/Switch/Button/Text
- 將修改後的 pseudo json 轉回原生 JSON 格式
- one-to-one 的轉換
- 只改物件第一個狀態對應的 stringLib | 新增第一個 stringTable 的 stringLib
- [暫時忽略] 需要確保 Object Name 一致: obj → properties → general → task → value → statements → $elements
"""
def encodeGeneralObject(obj_json:dict, stringLibTables:list, obj_pseudo_json:dict):
    """讀 Pseudo JSON"""
    objectTypeName = obj_pseudo_json["objectTypeName"] 
    name = obj_pseudo_json["name"]
    outline = obj_pseudo_json["outline"]
    background = obj_pseudo_json["background"]
    label = obj_pseudo_json["label"]
    profile = obj_pseudo_json["profile"]
    
    # Object ID
    obj_json["name"] = name
    # Lamp/Switch Task 中的 ID 也要確保一致, 對於Button 等物件 element 是 null
    # _taskVal = obj_json.get("properties",{}).get("general",{}).get("task",{}).get("value",{}).get("statements",{}).get("$elements",[])
    # if not _taskVal: # 確保不是 null
    #     for _task in _taskVal:
    #         _task["methodReference"]["reference"]["objectName"] = name
    
    """Outline Section"""
    _outline = obj_json["properties"]["outline"]
    _pciture = obj_json["properties"]["outline"]["picture"]
    
    _outline["pictureColor"]["value"]["value"] = outline["color"]
    _pciture["value"]["info"]["galleryName"] = outline["galleryName"]
    _pciture["value"]["info"]["index"] = int(outline["index"]) # LLM 會犯錯生成 "4"
    
    
    """Background Section"""
    _bg = obj_json["properties"]["background"]
    if background["color"]:
        _bg["fill"]["value"]["value"]["subjectColor"] = background["color"]
    else:
        _bg["fill"]["value"]["value"].pop("subjectColor", None)
    _bg["radius"]["value"]["value"] = background["radius"]
    _bg["border"]["value"]["value"] = background["border"]

    
    """label section"""
    _label = obj_json["properties"]["label"]
    
    # Text 物件的 text 藏在 general 中
    if objectTypeName == "Text":
        _general = obj_json["properties"]["general"]
        _textVal = _general["text"]["value"]["value"]        
    else:
        _textVal = _label["text"]["value"]["value"]
    
    if label["text"]:
        # 若 string lib 已經存在 → 改 string lib
        if "type" in _textVal:
            _stringTableId = int(_textVal["reference"]["stringTableId"])
            _stringId = int(_textVal["reference"]["stringId"])
            _el = stringLibTables[_stringTableId]["lingualStrings"]["$elements"][_stringId]
            _el["strings"]["$elements"][0]["text"] = label["text"] # 只改第一個狀態
        else:
            # 在第一個 StringTable, create 新的 string lib
            _first_stringLibTable_elements = stringLibTables[0]["lingualStrings"]["$elements"]
            _stringId = len(_first_stringLibTable_elements)
            _first_stringLibTable_elements.append({
                                            "name": str(_stringId),
                                            "comment": "",
                                            "strings": {
                                                "$elements": [
                                                    {
                                                        "text": label["text"]
                                                    }
                                                ],
                                                "#elementDataType": 4184
                                            },
                                            "formatArguments": {
                                                "$elements": None,
                                                "#elementDataType": 4096
                                            }
                                        })
            # 寫入對應的 _textVal
            _textVal.clear()
            _textVal.update({
                        "type": {
                            "$value": "string",
                            "#enumType": 3
                        },
                        "reference": {
                            "stringTableId": 0,
                            "stringId": str(_stringId),
                            "#dataType": 4139
                        },
                        "#dataType": 4114
                    })
    else:
        _textVal.clear()
        _textVal.update({"$value": "", "#dataType": 75}) # default, empty
    
    # Font
    _label["font"]["value"]["family"] = label["fontStyle"]
    _label["fontSize"]["value"]["value"] = label["fontSize"]
    _label["fontBold"]["value"]["value"] = label["fontBold"]
    _label["fontItalic"]["value"]["value"] = label["fontItalic"]
    _label["fontUnderline"]["value"]["value"] = label["fontUnderline"]
    _label["fontColor"]["value"]["value"] = label["fontColor"]
    
    
    # alignment, default: "4"
    _label["alignment"]["value"]["value"] = label["alignment"]
    # padding, default: {}
    _label["padding"]["value"]["value"] = label["padding"]
    # blinking, 0/500/1000
    _label["blinking"]["value"]["value"] = label["blinking"]
    # scrolling, default: {}, direction: "1"~"4", repeated: "0"/"1". e.g. {'direction': '4', 'repeated': '1', 'speed': '5'}
    _label["scrolling"]["value"]["value"] = label["scrolling"]
    
    # BBOX
    _profile = obj_json["properties"]["profile"]
    _profile["x"]["value"]["value"] = profile["x"]
    _profile["y"]["value"]["value"] = profile["y"]
    _profile["width"]["value"]["value"] = profile["width"]
    _profile["height"]["value"]["value"] = profile["height"]
    _profile["rotation"]["value"]["value"] = profile["rotation"]



def encodeOptionList(obj_json:dict, obj_pseudo_json:dict):
    """讀 Pseudo JSON"""
    objectTypeName = obj_pseudo_json["objectTypeName"] 
    name = obj_pseudo_json["name"]
    outline = obj_pseudo_json["outline"]
    label = obj_pseudo_json["label"]
    profile = obj_pseudo_json["profile"]
    
    # Object ID
    obj_json["name"] = name
    
    """General Section"""
    _general = obj_json["properties"]["general"]
    _general["style"]["value"]["value"] = obj_pseudo_json["style"] # Int: 1 (classic, default) / 0 (Standard)
    
    """Outline Section"""
    _outline = obj_json["properties"]["outline"]
    _outline["backgroundColor"]["value"]["value"] = outline["backgroundColor"] # 直接影響選項中每個 item 底色
    _outline["selectionColor"]["value"]["value"] = outline["selectionColor"] # 只有影響已被選擇的 item 底色
        
    """label section"""
    _label = obj_json["properties"]["label"]
        
    # Font
    _label["font"]["value"]["family"] = label["fontStyle"]
    _label["fontSize"]["value"]["value"] = label["fontSize"]
    _label["fontBold"]["value"]["value"] = label["fontBold"]
    _label["fontItalic"]["value"]["value"] = label["fontItalic"]
    _label["fontUnderline"]["value"]["value"] = label["fontUnderline"]
    _label["fontColor"]["value"]["value"] = label["fontColor"]
    
    # BBOX
    _profile = obj_json["properties"]["profile"]
    _profile["x"]["value"]["value"] = profile["x"]
    _profile["y"]["value"]["value"] = profile["y"]
    _profile["width"]["value"]["value"] = profile["width"]
    _profile["height"]["value"]["value"] = profile["height"]
    _profile["rotation"]["value"]["value"] = profile["rotation"]
    
    
    
def encodeSlider(obj_json:dict, obj_pseudo_json:dict):
    """讀 Pseudo JSON"""
    objectTypeName = obj_pseudo_json["objectTypeName"] 
    name = obj_pseudo_json["name"]
    outline = obj_pseudo_json["outline"]
    profile = obj_pseudo_json["profile"]
    
    # Object ID
    obj_json["name"] = name
    
    """Outline Section"""
    _outline = obj_json["properties"]["outline"]
    _outline["style"]["value"]["value"] = outline["style"] # 0/1/2: default/crystal/flat
    _outline["direction"]["value"]["value"] = outline["direction"] # 0/1/2/3: right/up/left/down
    _outline["blockStyle"]["value"]["value"] = outline["blockStyle"] # 0/1/2/3: Big rect/Small rect/Up arrow/Down arrow
    _outline["blockWidth"]["value"]["value"] = outline["blockWidth"]
    _outline["blockColor"]["value"]["value"] = outline["blockColor"]
    _outline["frameColor"]["value"]["value"] = outline["frameColor"] # default: {}
    _outline["backgroundColor"]["value"]["value"] = outline["backgroundColor"] # default: {}
    _outline["slotColor"]["value"]["value"] = outline["slotColor"] # default: {}

    # BBOX
    _profile = obj_json["properties"]["profile"]
    _profile["x"]["value"]["value"] = profile["x"]
    _profile["y"]["value"]["value"] = profile["y"]
    _profile["width"]["value"]["value"] = profile["width"]
    _profile["height"]["value"]["value"] = profile["height"]
    _profile["rotation"]["value"]["value"] = profile["rotation"]
    


def encodeInputObject(obj_json:dict, obj_pseudo_json:dict):
    """讀 Pseudo JSON"""
    objectTypeName = obj_pseudo_json["objectTypeName"] 
    name = obj_pseudo_json["name"]
    outline = obj_pseudo_json["outline"]
    background = obj_pseudo_json["background"]
    label = obj_pseudo_json["label"]
    profile = obj_pseudo_json["profile"]
    
    # Object ID
    obj_json["name"] = name
    
    """Outline Section"""
    _outline = obj_json["properties"]["outline"]
    _outline["pictureColor"]["value"]["value"] = outline["color"]
    
    _pciture = obj_json["properties"]["outline"]["picture"]
    _pciture["value"]["info"]["galleryName"] = outline["galleryName"]
    _pciture["value"]["info"]["index"] = outline["index"]
    
    """Background Section"""
    _bg = obj_json["properties"]["background"]
    if background["color"]:
        _bg["fill"]["value"]["value"] = {"subjectColor": background["color"]}
    else:
        _bg["fill"]["value"]["value"] = {}
        
    _bg["radius"]["value"]["value"] = background["radius"]
    _bg["border"]["value"]["value"] = background["border"]
    
    
    """label section"""
    _label = obj_json["properties"]["label"]
    
    # Font
    _label["font"]["value"]["family"] = label["fontStyle"]
    _label["fontSize"]["value"]["value"] = label["fontSize"]
    _label["fontBold"]["value"]["value"] = label["fontBold"]
    _label["fontColor"]["value"]["value"] = label["fontColor"]
    
    # alignment, default: "4"
    _label["alignment"]["value"]["value"] = label["alignment"]
    # padding, default: {}
    _label["padding"]["value"]["value"] = label["padding"]
    
    # BBOX
    _profile = obj_json["properties"]["profile"]
    _profile["x"]["value"]["value"] = profile["x"]
    _profile["y"]["value"]["value"] = profile["y"]
    _profile["width"]["value"]["value"] = profile["width"]
    _profile["height"]["value"]["value"] = profile["height"]
    _profile["rotation"]["value"]["value"] = profile["rotation"]
    


def encodeRectangle(obj_json:dict, obj_pseudo_json:dict):
    """讀 Pseudo JSON"""
    objectTypeName = obj_pseudo_json["objectTypeName"] 
    name = obj_pseudo_json["name"]
    frame = obj_pseudo_json["frame"]
    interior = obj_pseudo_json["interior"]
    profile = obj_pseudo_json["profile"]
    
    # Object ID
    obj_json["name"] = name
    
    """Frame Section"""
    _frame = obj_json["properties"]["frame"]
    _frame["frameColor"]["value"]["value"] = frame["frameColor"]
    _frame["frameWidth"]["value"]["value"] = frame["frameWidth"]
    _frame["style"]["value"]["value"] = frame["style"] # 沒有 "5"
    _frame["frameRadius"]["value"]["value"] = frame["frameRadius"]
    
    """Interior Section"""
    _interior = obj_json["properties"]["interior"]
    _interior["fill"]["value"]["value"]["subjectColor"] = interior["color"]
    
    # BBOX
    _profile = obj_json["properties"]["profile"]
    _profile["x"]["value"]["value"] = profile["x"]
    _profile["y"]["value"]["value"] = profile["y"]
    _profile["width"]["value"]["value"] = profile["width"]
    _profile["height"]["value"]["value"] = profile["height"]
    _profile["rotation"]["value"]["value"] = profile["rotation"]
    


def encodeOthers(obj_json:dict, obj_pseudo_json:dict):
    """讀 Pseudo JSON"""
    objectTypeName = obj_pseudo_json["objectTypeName"] 
    name = obj_pseudo_json["name"]
    profile = obj_pseudo_json["profile"]
    
    # Object ID
    obj_json["name"] = name
    
    # BBOX
    _profile = obj_json["properties"]["profile"]
    _profile["x"]["value"]["value"] = profile["x"]
    _profile["y"]["value"]["value"] = profile["y"]
    _profile["width"]["value"]["value"] = profile["width"]
    _profile["height"]["value"]["value"] = profile["height"]
    _profile["rotation"]["value"]["value"] = profile["rotation"]
    


"""檢查LLM生成的 JSON 符合格式"""
def isPseudoView(pseudo_json:dict) -> bool:
    standard_format = {
        "screen_name":"demo3",
        "screen_size":{"width": 800, "height": 480},
        "screen_properties":{
            "color": {"a": "255", "b": "185", "g": "110", "r": "100"},
            "border": {"color": {"a": "255"}, "style": "5"}
        },
        "objects":[]
    }
    
    
    if not isinstance(pseudo_json, dict):
        print("[Fail] pseudo_json is not a dict")
        return False
    
    """檢查第一層 Keys"""
    standard_keys = set(standard_format.keys())
    input_keys = set(pseudo_json.keys())
    if input_keys != standard_keys:
        missing_keys = standard_keys - input_keys
        extra_keys = input_keys - standard_keys

        if missing_keys:
            print(f"[Fail] missing keys: {missing_keys}")

        if extra_keys:
            print(f"[Fail] extra keys: {extra_keys}")

        return False
    
    """檢查 objects 是否為list"""
    if not isinstance(pseudo_json["objects"], list):
        print("[Fail] objects is not a list")
        return False
    
    return True



"""
_obj: 原始 JSON
_strTables: string library table
obj: pseudo json
"""
def autoencodeObj(_obj, _strTables, obj):
    obj_type = obj["objectTypeName"]
    # 依照物件型態修改
    if obj_type in ["Lamp","Button","Switch","Text"]:
        encodeGeneralObject(_obj, _strTables, obj)
    elif obj_type == "OptionList":
        encodeOptionList(_obj, obj)
    elif obj_type == "Slider":
        encodeSlider(_obj, obj)
    elif obj_type in ["Numeric","TextInput"]:
        encodeInputObject(_obj, obj)
    elif obj_type == "DrawingRectangle":
        encodeRectangle(_obj, obj)
    else:
        encodeOthers(_obj, obj)

           
def encodeScreenLayout2JSON(pseudo_json:dict, target_filename:str = "blank.json"):    
    # read screen name from pseudo
    screen_name = pseudo_json["screen_name"]
    screen_size = pseudo_json["screen_size"]
    screen_properties = pseudo_json["screen_properties"]
    objects = pseudo_json["objects"]
    
    with open(target_filename, 'r', encoding='utf-8') as f:
        _project_json = json.load(f)
        _header = _project_json["header"]
        _screen_names = getScreenNames(_project_json)
        _project_size = getProjectSize(_project_json)
        _screen_idx = _screen_names[screen_name]
        
        _strTables = _project_json["body"]["dataSections"]["stringLibrarySection"]["stringTables"]["$elements"]
        _screens = _project_json["body"]["dataSections"]["windowSection"]["screens"]["children"]["$elements"]
        
        _sc = _screens[_screen_idx] # screen json
        _objs = _sc["data"]["rootLayer"]["subLayers"]["$elements"] # obj list, 空白視窗會是 null
        if _objs is None:
            _sc["data"]["rootLayer"]["subLayers"]["$elements"] = []
            _objs = _sc["data"]["rootLayer"]["subLayers"]["$elements"]        
        
        _obj_names = getObjNames(_objs)
        
        # override bg
        encodeScreenBG(_sc, pseudo_json)
        
        # scan psuedo
        for idx, obj in enumerate(objects):
            obj_name = obj["name"]
            obj_type = obj["objectTypeName"]
            # 若物件不存在則 insert
            if obj_name not in _obj_names:
                _obj = copy.deepcopy(ebx_object_default_json[obj_type]) # 抓對應的原始物件, 使用 copy 避免共用 reference
                autoencodeObj(_obj, _strTables, obj) # 更改該物件
                _objs.insert(idx, _obj) # 插入該物件
            else:
                # 物件存在則找尋該物件
                for _idx, _obj in enumerate(_objs):
                    _name = _obj["name"]
                    _type = getObjType(_obj)
                    # 存在就 update
                    if _name == obj_name and _type == obj_type:
                        # 依照物件型態修改
                        autoencodeObj(_obj, _strTables, obj)
                        break
    
    # save project json to original file
    with open(target_filename, 'w', encoding='utf-8') as f:
        json.dump(_project_json, f, ensure_ascii=False, indent=4)



"""LLM可以調用的工具1
- 從 Project File 抽出 Screen View

Args:
- screen_name: screen name
- filename: project 檔案名稱
"""
def decodeScreenLayoutFromJSON(screen_name:str, filename:str = "blank.json") -> dict:
    # open file
    with open(filename, 'r', encoding='utf-8') as f:
        project_json = json.load(f)
        proj_header = project_json["header"]
        
    screen_names = getScreenNames(project_json)
    screen_size = getProjectSize(project_json)
    screen_idx = screen_names[screen_name]
    _screens = project_json["body"]["dataSections"]["windowSection"]["screens"]["children"]["$elements"]
    sc = _screens[screen_idx] # screen json
    bg_widget = decodeScreenBG(sc)

    strTables = project_json["body"]["dataSections"]["stringLibrarySection"]["stringTables"]["$elements"]
    _objs = sc["data"]["rootLayer"]["subLayers"]["$elements"] # _objs 為 null 當畫面為空時
    
    objects = []
    
    # 當畫面有物件時才進行decode
    if _objs:
        for _obj in _objs:
            obj_type = getObjType(_obj)
            if obj_type in ["Lamp","Button","Switch","Text"]:
                objects.append(decodeGeneralObject(_obj, strTables))
            elif obj_type == "OptionList":
                objects.append(decodeOptionList(_obj))
            elif obj_type == "Slider":
                objects.append(decodeSlider(_obj))
            elif obj_type in ["Numeric","TextInput"]:
                objects.append(decodeInputObject(_obj))
            elif obj_type == "DrawingRectangle":
                objects.append(decodeRectangle(_obj))
            else:
                objects.append(decodeOthers(_obj))
    
    data = {
        "screen_name":screen_name,
        "screen_size":screen_size,
        "screen_properties":bg_widget,
        "objects":objects
    }

    # save file
    # save_filename = f"pseudo-{screen_name}.json"
    # with open(save_filename, 'w', encoding='utf-8') as f:
    #     json.dump(data, f, ensure_ascii=False, indent=4)
    
    return data



"""LLM使用的工具2
- 檔案到檔案的複寫
- 必須先將LLM的美化結果先輸出一個檔案例如 llm-output.json

Args:
- source_filename: 來源檔案名稱
- target_filename: 目標檔案名稱
"""
def overrideScreenLayout2JSON(source_filename:str, target_filename:str):
    state = "[Override Success]"
    try:
        with open(source_filename, 'r', encoding='utf-8') as f:
            pseudo_json = json.load(f)
            
        encodeScreenLayout2JSON(pseudo_json, target_filename)
    except Exception as e:
        error_msg = str(e)
        state = f"[Override Failed] {error_msg}"
        print(state)
    finally:
        return state        



"""LLM使用工具3
- widget name 不能重複

Args:
- objects: LLM 生成的 pseudo json list, 可以是部分物件
- target_filename: project 檔案名稱
"""
def createNewObjects(widget_list:list, screen_name:str, target_filename:str = "blank.json"):
    out = ""  
    with open(target_filename, 'r', encoding='utf-8') as f:
        _project_json = json.load(f)
        _header = _project_json["header"]
        _screen_names = getScreenNames(_project_json)
        _project_size = getProjectSize(_project_json)
        
        # 檢查screen name
        if screen_name not in _screen_names:
            out = f"[failed] screen name `{screen_name}` not found, please check"
            return out
        
        _screen_idx = _screen_names[screen_name]
        
        _strTables = _project_json["body"]["dataSections"]["stringLibrarySection"]["stringTables"]["$elements"]
        _screens = _project_json["body"]["dataSections"]["windowSection"]["screens"]["children"]["$elements"]
        
        _sc = _screens[_screen_idx] # screen json
        _objs = _sc["data"]["rootLayer"]["subLayers"]["$elements"] # obj list, 空白視窗會是 null
        if _objs is None:
            _sc["data"]["rootLayer"]["subLayers"]["$elements"] = []
            _objs = _sc["data"]["rootLayer"]["subLayers"]["$elements"]
        
        _obj_names = getObjNames(_objs)
        
        # scan psuedo
        for idx, obj in enumerate(widget_list):
            obj_name = obj["name"]
            obj_type = obj["objectTypeName"]
            # 若物件不存在則 append
            if obj_name not in _obj_names:
                _obj = copy.deepcopy(ebx_object_default_json[obj_type]) # 抓對應的原始物件, 使用 copy 避免共用 reference
                autoencodeObj(_obj, _strTables, obj) # 更改該物件
                _objs.append(_obj) # 插入該物件(加入到最後)
                out += f"Create Object `{obj_name}` success\n"
            else:
                out += f"Create Object `{obj_name}` failed, the name already exist\n"
    
    # save project json to original file
    with open(target_filename, 'w', encoding='utf-8') as f:
        json.dump(_project_json, f, ensure_ascii=False, indent=4)
    
    return out



if __name__ == "__main__":
    filename = "blank.json"
    screen_name = "test1"
    # screen_name = "default"
    # screen_name = "demo1"
    # print(decodeScreenLayoutFromJSON(screen_name, filename))
    
    # print(getObjTypeStr("Lamp"))
    
    with open(filename, 'r', encoding='utf-8') as f:
        project_json = json.load(f)
        print("[Proj Header]\n",project_json["header"])
        print("[Screen Names]\n",getScreenNames(project_json))
        print("[Proj Size]\n", getProjectSize(project_json))
        
        _screens = project_json["body"]["dataSections"]["windowSection"]["screens"]["children"]["$elements"]
        sc = _screens[0] # screen json
        print("BG Screen:\n", decodeScreenBG(sc))
        
        strTables = project_json["body"]["dataSections"]["stringLibrarySection"]["stringTables"]["$elements"]
        # print(strTables)
        
        _objs = sc["data"]["rootLayer"]["subLayers"]["$elements"] # 空白畫面會是 null
        # _lamp = _objs[0]
        # _lamp2 = _objs[1]
    #     _btn = _objs[2]
    #     _switch = _objs[3]
    #     _option_list = _objs[4]
    #     _slider = _objs[5]
    #     _numeric = _objs[6]
    #     _textInput = _objs[7]
        _rect = _objs[8]
    #     _text = _objs[9]
        

        pseudo_new = {
            'objectTypeName': 'DrawingRectangle', 
            'name': 'Rectangle', 
            'frame': {
                'frameColor': {
                    'a': '255'
                }, 
                'frameWidth': 4, 
                'style': 0, 
                'frameRadius': '15'
            }, 
            'interior': {
                'color': {'a': '255', 'b': '0', 'g': '255', 'r': '255'}
            }, 
            'profile': {'x': '500', 'y': '133', 'width': '129', 'height': '87', 'rotation': '0'}
        }
        
        encodeRectangle(_rect, pseudo_new)
    
    # save project json to original file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(project_json, f, ensure_ascii=False, indent=4)
    
    
    pass
    
    
    