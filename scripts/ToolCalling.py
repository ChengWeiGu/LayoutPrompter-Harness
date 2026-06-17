import os
import re
import sys
import json
import copy
import shutil
from . import ClaudeFunc, EBXImportExport, EBXViewProcess, ConfigReader
from pathlib import Path



# create instance
sc_decoder = EBXViewProcess.ScreenDecoder()   
sc_encoder = EBXViewProcess.ScreenEncoder()


"""LLM使用工具1: 讀取圖片
- Claude 預設吃 Byte
"""
def ReadImageByteData(image_path:str):
    try:
        _, ext = os.path.splitext(image_path)
        if ext not in [".png", ".jpeg"]:
            return {
                    "role": "user", 
                    "content":[
                            {
                                "text": f"System only accept image file with extenstion of png/jpeg. got `{ext}`"
                            }
                        ]
                    }

        with open(image_path, "rb") as f:
            # delete "." inside ".md"
            ext = ext.strip(".").lower()
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
- project_path: project 檔案名稱 (.json | .ebxprj)
"""
def GetScreenLayout(screen_name:str, project_path:str):
    try:
        _, ext = os.path.splitext(project_path)
        if ext.lower() == ".json":
            sc_view = sc_decoder.get_screen_view_from_file(project_path, screen_name)
        elif ext.lower() == ".ebxprj":
            sc_view = sc_encoder.get_screen_view_by_socket_export(project_path, screen_name)
        else:
            raise ValueError(f"Incorrect Extension Format: `{project_path}`")
        return sc_view
    
    except Exception as e:
        error_msg = str(e)
        return f"[Get Screen Layout Failed]{error_msg} for file: `{project_path}` and screen name :`{screen_name}`. Please STOP and tell user to check"


"""LLM使用的工具3 - JSON-to-JSON
- 使用前須備份檔案
- 檔案到檔案的複寫
- 必須先將LLM的美化結果先輸出一個檔案例如 llm-output.json

Args:
- source_view_path: 來源檔案名稱 (View JSON Path)
- target_project_path: 目標專案檔案名稱 (Project Path .json | .ebxprj)
"""
def OverrideRes2Proj(source_view_path:str, target_project_path:str) -> str:
    try:
        _, trg_ext = os.path.splitext(target_project_path)
        # 先備份 target 以免被改壞掉
        src_file = Path(target_project_path)   # 原始檔案路徑
        dst_dir = Path("backup")           # 目標資料夾
        dst_dir.mkdir(parents=True, exist_ok=True)    # 若資料夾不存在就建立
        # 只複製檔案內容與權限
        shutil.copy(src_file, dst_dir)
        # start override
        if trg_ext.lower() == ".json":
            sc_encoder.override_project_from_view(source_view_path, target_project_path)
        elif trg_ext.lower() == ".ebxprj":
            sc_encoder.import_project_from_view_by_socket(source_view_path, target_project_path)
        else:
            raise ValueError(f"Incorrect Extension Format of project: `{target_project_path}`")
        
        return f"[Override Success] From `{source_view_path}` to `{target_project_path}`"
    
    except Exception as e:
        error_msg = str(e)
        return f"[Override Failed]{error_msg} from `{source_view_path}` to `{target_project_path}`. Please STOP and tell user to check"
    

"""LLM使用工具4
- widget name : 不重複 -> 新增; 重複 -> update
- 允許同時修改背景

Args:
- widget_list: LLM 生成的 pseudo json list, 可以是部分物件
- screen_name: Target Screen Name
- target_project_path: project 檔案名稱 ( .json | .ebxprj)
- screen_properties: 生成的 screen properties json, 預設空 {}
"""
def UpsertWidgets(widget_list:list ,screen_name:str, target_project_path:str, screen_properties:dict={}) -> str:
    try:
        _, ext = os.path.splitext(target_project_path)
        if ext.lower() == ".json":
            out_msg = sc_encoder.upsert_objects2screen(widget_list, screen_name, target_project_path, screen_properties)
        elif ext.lower() == ".ebxprj":
            out_msg = sc_encoder.upsert_objects2screen_by_socket(widget_list, screen_name, target_project_path, screen_properties)
        else:
            raise ValueError(f"Incorrect Extension Format of project: `{target_project_path}`")
        return out_msg
      
    except Exception as e:
        error_msg = str(e)
        return f"[Upsert Widgets Failed]{error_msg} for file: `{target_project_path}` and screen: `{screen_name}`. Please STOP and tell user to check"


"""LLM使用工具5

Args:
- project_path: project 檔案名稱 (.ebxprj)
"""
def ReadScreenShot(project_path:str, screen_name:str):
    try:
        # check ext
        _, ext = os.path.splitext(project_path)
        if ext.lower() != ".ebxprj":
            out_msg = f"[Get Screen Shot Failed] only support extension of project for `.ebxprj` instead of `{ext}`, please check"
        screenshot_path = EBXImportExport.get_screen_snapshot(project_path, screen_name)
        return ReadImageByteData(screenshot_path)
    
    except Exception as e:
        error_msg = str(e)
        return f"[Get Screen Shot Failed]{error_msg} for file: `{project_path}` and screen: `{screen_name}`. Please STOP and tell user to check"


"""LLM使用工具6

Args:
- file_path: text file 檔案名稱
- so far, only support txt | md
"""
def ReadTextFile(file_path:str) -> str:
    try:
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in [".txt", ".md"]:
            return f"[Read Text File Error] Cannot support file with extension of `{ext}`. Only support .txt | .md"
        
        context = ""
        with open(file_path, "r", encoding="utf-8") as f:
            context = f.read()
        return context

    except Exception as e:
        error_msg = str(e)
        return f"[Read Text File Error]{error_msg} for file: `{file_path}`. Please STOP and tell user to check"
        


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
            project_path = kwargs["project_path"]
            # check file exists
            _is_exist = os.path.exists(project_path)
            if not _is_exist:
                return ClaudeFunc.build_user_message(f"[Fail] `{project_path}` does not exist. please tell user to check")
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
            source_view_path = kwargs["source_view_path"]
            target_project_path = kwargs["target_project_path"]
            # check file exists
            _is_src_exist = os.path.exists(source_view_path)
            _is_trg_exist = os.path.exists(target_project_path)
            if not _is_src_exist:
                return ClaudeFunc.build_user_message(f"[Fail] `{source_view_path}` does not exist. please tell user to check")
            if not _is_trg_exist:
                return ClaudeFunc.build_user_message(f"[Fail] `{target_project_path}` does not exist. please tell user to check")
            # call func
            result = OverrideRes2Proj(**kwargs)
            return ClaudeFunc.build_user_message(result)
        
        elif tool_name == "UpsertWidgets":
            # args
            target_project_path = kwargs["target_project_path"]
            # check file exists
            _is_trg_exist = os.path.exists(target_project_path)
            if not _is_trg_exist:
                return ClaudeFunc.build_user_message(f"[Fail] {target_project_path} does not exist. please tell user to check")
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
                return ClaudeFunc.build_user_message(result)
            # image dict
            return result
        
        elif tool_name == "ReadScreenShot":
            project_path = kwargs["project_path"]
            # check project file exists
            _is_file_exist = os.path.exists(project_path)
            if not _is_file_exist:
                return ClaudeFunc.build_user_message(f"[Fail] `{project_path}` does not exist. please tell user to check")
            # call func
            result = ReadScreenShot(**kwargs)
            # error msg
            if isinstance(result, str):
                return ClaudeFunc.build_user_message(result)
            # image dict
            return result
        
        elif tool_name == "ReadTextFile":
            # args
            file_path = kwargs["file_path"]
            # check file exists
            _is_file_exist = os.path.exists(file_path)
            if not _is_file_exist:
                return ClaudeFunc.build_user_message(f"[Fail] `{file_path}` does not exist. please tell user to check")
            # call func
            result = ReadTextFile(**kwargs)
            return ClaudeFunc.build_user_message(result)
        
        elif tool_name == "ReadSkills":
            # call func
            result = ConfigReader.read_skill_headers()
            return ClaudeFunc.build_user_message(result)
        
        else:
            return ClaudeFunc.build_user_message(f"[Fail] This tool `{tool_name}` cannot be found, please check you called a right tool.")
        
    return {}


"""JSON生成檢測
- 抓最後一個 json
"""
def catch_json_output(text:str) -> tuple:
    pattern = r"```json\s*\n(.*?)\n```"
    
    # 抓第一個json
    # match = re.search(pattern, text, re.DOTALL)
    # if match:
    #     content = match.group(1)
    #     return True, content
    
    # 抓最後一個json
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        content = matches[-1]
        return True, content
    
    return False, None



"""檢查LLM生成格式"""
def _isViewFormat(sc_view_json:dict) -> bool:
    
    # color
    BEGIN_COLOR = "\033[92m"
    RESET = "\033[0m"
    
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
        print(BEGIN_COLOR+"[Warning] screen json is not a dict"+RESET)
        return False
    
    """檢查第一層 Keys"""
    standard_keys = set(standard_format.keys())
    input_keys = set(sc_view_json.keys())
    if input_keys != standard_keys:
        missing_keys = standard_keys - input_keys
        extra_keys = input_keys - standard_keys

        if missing_keys:
            print(BEGIN_COLOR+f"[Warning] missing keys: {missing_keys}"+RESET)

        if extra_keys:
            print(BEGIN_COLOR+f"[Warning] extra keys: {extra_keys}"+RESET)

        return False
    
    """檢查 objects 是否為list"""
    if not isinstance(sc_view_json["objects"], list):
        print(BEGIN_COLOR+"[Warning] objects is not a list"+RESET)
        return False
    
    return True