import os
import re
import sys
import json
import copy
import shutil
from . import ClaudeFunc, EBXJsonProcess, EBXImportExport
from pathlib import Path



# create instance
sc_decoder = EBXJsonProcess.ScreenDecoder()   
sc_encoder = EBXJsonProcess.ScreenEncoder()


"""LLM使用工具1: 讀取圖片
- Claude 預設吃 Byte
"""
def ReadImageByteData(image_path:str):
    try:
        ext = image_path.split(".")[-1].lower()
        if ext not in ["png", "jpg", "jpeg"]:
            return {
                    "role": "user", 
                    "content":[
                            {
                                "text": "System only accept image file with extenstion of png/jpg/jpeg."
                            }
                        ]
                    }

        with open(image_path, "rb") as f:
            image_bytes = f.read()
            return {
                    "role": "user", 
                    "content":[
                            {
                                "image": {
                                    "format": ext,
                                    "source": {
                                        "bytes": image_bytes #no base64 encoding required!
                                    }
                                }
                            }
                        ]
                    }
    except Exception as e:
        error_msg = str(e)
        return f"[Read Image Failed]{error_msg} for file: `{image_path}`. Please STOP and tell user to check"
   
    
"""LLM可以調用的工具2
- 從 Project File 抽出 Screen View OR
- 使用 EBX Socket 功能抽 View

Args:
- screen_name: screen name
- filename: project 檔案名稱 (.json | .ebxprj)
"""
def GetScreenLayout(screen_name:str, filename:str):
    try:
        ext = filename.split(".")[-1]
        if ext.lower() == "json":
            sc_view = sc_decoder.get_screen_view_from_file(filename, screen_name)
        elif ext.lower() == "ebxprj":
            sc_view = sc_encoder.get_screen_view_by_socket_export(filename, screen_name)
        else:
            raise ValueError(f"Incorrect Extension Format: `{filename}`")
        return sc_view
    
    except Exception as e:
        error_msg = str(e)
        return f"[Get Screen Layout Failed]{error_msg} for file: `{filename}` and screen name :`{screen_name}`. Please STOP and tell user to check"


"""LLM使用的工具3 - JSON-to-JSON
- 使用前須備份檔案
- 檔案到檔案的複寫
- 必須先將LLM的美化結果先輸出一個檔案例如 llm-output.json

Args:
- source_filename: 來源檔案名稱 (View JSON Path)
- target_filename: 目標專案檔案名稱 (Project Path .json | .ebxprj)
"""
def OverrideRes2Proj(source_filename:str, target_filename:str) -> str:
    try:
        trg_ext = target_filename.split(".")[-1]
        
        # 先備份 target 以免被改壞掉
        src_file = Path(target_filename)   # 原始檔案路徑
        dst_dir = Path("backup")           # 目標資料夾
        dst_dir.mkdir(parents=True, exist_ok=True)    # 若資料夾不存在就建立
        # 只複製檔案內容與權限
        shutil.copy(src_file, dst_dir)
        # start override
        if trg_ext.lower() == "json":
            sc_encoder.override_project_from_view(source_filename, target_filename)
        elif trg_ext.lower() == "ebxprj":
            sc_encoder.import_project_from_view_by_socket(source_filename, target_filename)
        else:
            raise ValueError(f"Incorrect Extension Format of project: `{target_filename}`")
        
        return f"[Override Success] From `{source_filename}` to `{target_filename}`"
    
    except Exception as e:
        error_msg = str(e)
        return f"[Override Failed]{error_msg} from `{source_filename}` to `{target_filename}`. Please STOP and tell user to check"
    

"""LLM使用工具4
- widget name : 不重複 -> 新增; 重複 -> update

Args:
- objects: LLM 生成的 pseudo json list, 可以是部分物件
- target_filename: project 檔案名稱 ( .json | .ebxprj)
"""
def UpsertWidgets(widget_list:list, screen_name:str, target_filename:str) -> str:
    try:
        ext = target_filename.split(".")[-1]
        if ext.lower() == "json":
            out_msg = sc_encoder.upsert_objects2screen(widget_list, screen_name, target_filename)
        elif ext.lower() == "ebxprj":
            out_msg = sc_encoder.upsert_objects2screen_by_socket(widget_list, screen_name, target_filename)
        else:
            raise ValueError(f"Incorrect Extension Format of project: `{target_filename}`")
        return out_msg
      
    except Exception as e:
        error_msg = str(e)
        return f"[Upsert Widgets Failed]{error_msg} for file: `{target_filename}` and screen: `{screen_name}`. Please STOP and tell user to check"



"""工具檢測
    return:
    - dict, 執行結果, 為 claude user message 格式
"""
def catch_tool_execute(text:str) -> dict:
    pattern = r"```tool_call\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(1).strip()

        try:
            tool_name, raw_kwargs = content.split(":", 1) # maxsplit=1 代表只切第一個冒號
        except ValueError:
            return ClaudeFunc.build_user_message(
                "[Fail] Invalid tool_call format. Expected: <tool_name>:<kwargs>"
            )
        
        try:
            kwargs = json.loads(raw_kwargs)
        except json.JSONDecodeError as e:
            return ClaudeFunc.build_user_message(
                f"[Fail] Invalid tool_call JSON arguments: {e}"
            )
        
        if tool_name == "GetScreenLayout":
            # args
            screen_name = kwargs["screen_name"]
            filename = kwargs["filename"]
            # check file exists
            _is_exist = os.path.exists(filename)
            if not _is_exist:
                return ClaudeFunc.build_user_message(f"[Fail] `{filename}` does not exist. please tell user to check")
            # call func
            screen = GetScreenLayout(**kwargs)
            # error message
            if isinstance(screen, str):
                return ClaudeFunc.build_user_message(screen)
            # screen json
            result = "[Success] get screen json as follows:\n" + json.dumps(screen, ensure_ascii=False)
            return ClaudeFunc.build_user_message(result)
        
        elif tool_name == "OverrideRes2Proj":
            # args
            source_filename = kwargs["source_filename"]
            target_filename = kwargs["target_filename"]
            # check file exists
            _is_src_exist = os.path.exists(source_filename)
            _is_trg_exist = os.path.exists(target_filename)
            if not _is_src_exist:
                return ClaudeFunc.build_user_message(f"[Fail] `{source_filename}` does not exist. please tell user to check")
            if not _is_trg_exist:
                return ClaudeFunc.build_user_message(f"[Fail] `{target_filename}` does not exist. please tell user to check")
            # call func
            result = OverrideRes2Proj(**kwargs)
            return ClaudeFunc.build_user_message(result)
        
        elif tool_name == "UpsertWidgets":
            # args
            target_filename = kwargs["target_filename"]
            # check file exists
            _is_trg_exist = os.path.exists(target_filename)
            if not _is_trg_exist:
                return ClaudeFunc.build_user_message(f"[Fail] {target_filename} does not exist. please tell user to check")
            # call func
            result = UpsertWidgets(**kwargs)
            return ClaudeFunc.build_user_message(result)
        
        elif tool_name == "ReadImageByteData":
            # args
            image_path = kwargs["image_path"]
            # check file exists
            _is_trg_exist = os.path.exists(image_path)
            if not _is_trg_exist:
                return ClaudeFunc.build_user_message(f"[Fail] `{image_path}` does not exist. please tell user to check")
            # call func
            result = ReadImageByteData(image_path)
            # error msg
            if isinstance(result, str):
                return  ClaudeFunc.build_user_message(result)
            # image dict
            return result
        
        else:
            return ClaudeFunc.build_user_message(f"[Fail] This tool `{tool_name}` cannot be found, please check you called a right tool.")
        
    return {}


"""JSON生成檢測"""
def catch_json_output(text:str) -> tuple:
    pattern = r"```json\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(1)
        return True, content
    
    return False, None



"""檢查LLM生成格式"""
def _isViewFormat(sc_view_json:dict) -> bool:
    standard_format = {
        "screen_name": "test1",
        "screen_size": {
            "width": 1024,
            "height": 768
        },
        "screen_properties": {
            "facecolor": "#5f706e",
            "border": {
                "style": 5,
                "color": "#000000",
                "width": 0
            }
        },
        "objects": []
    }
    
    if not isinstance(sc_view_json, dict):
        print("[Fail] screen json is not a dict")
        return False
    
    """檢查第一層 Keys"""
    standard_keys = set(standard_format.keys())
    input_keys = set(sc_view_json.keys())
    if input_keys != standard_keys:
        missing_keys = standard_keys - input_keys
        extra_keys = input_keys - standard_keys

        if missing_keys:
            print(f"[Fail] missing keys: {missing_keys}")

        if extra_keys:
            print(f"[Fail] extra keys: {extra_keys}")

        return False
    
    """檢查 objects 是否為list"""
    if not isinstance(sc_view_json["objects"], list):
        print("[Fail] objects is not a list")
        return False
    
    return True