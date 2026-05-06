import os
import re
import sys
import json
import boto3
import time
import configparser
import jsonProcess
from pathlib import Path
from botocore.exceptions import ClientError, BotoCoreError


CONFIG_PATH = Path("./Config.ini")
CONFIG_SECTION = "BEDROCK_EU"
max_tokens=32768
temperature=0.7



"""read system prompt from CONFIG_PATH"""
def read_sys_prompt(config_path: Path = CONFIG_PATH, section: str = "PROMPT") -> str:
    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")
    _file=parser[section]["system_prompt_file"]
    _prompt = "I'm an ai assistant to help you find answer"
    with open(_file, 'r', encoding='utf-8') as f:
        _prompt = f.read()
    return _prompt

DEFAULT_SYSTEM_PROMPT = read_sys_prompt()


"""讀取圖片
- Claude 預設吃 Byte
"""
def ReadImageByteData(image_path:str) -> dict:
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


"""工具檢測"""
def catch_tool_output(text:str) -> tuple:
    pattern = r"```tool_use\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        tool_name, raw_kwargs = content.split(":", 1) # maxsplit=1 代表只切第一個冒號
        kwargs = json.loads(raw_kwargs)
        if tool_name == "decodeScreenLayoutFromJSON":
            screen_name = kwargs["screen_name"]
            filename = kwargs["filename"]
            # 找尋file存不存在
            _is_exist = os.path.exists(filename)
            if not _is_exist:
                return False ,f"[Fail] {filename} does not exist. please check"
            screen = jsonProcess.decodeScreenLayoutFromJSON(**kwargs)
            return True, "[Success] get screen json as follows:\n" + json.dumps(screen, ensure_ascii=False)
        elif tool_name == "overrideScreenLayout2JSON":
            source_filename = kwargs["source_filename"]
            target_filename = kwargs["target_filename"]
            # 找尋file存不存在
            _is_src_exist = os.path.exists(source_filename)
            _is_trg_exist = os.path.exists(target_filename)
            if not _is_src_exist:
                return False ,f"[Fail] {source_filename} does not exist. please check"
            if not _is_trg_exist:
                return False ,f"[Fail] {target_filename} does not exist. please check"
            return True, jsonProcess.overrideScreenLayout2JSON(**kwargs)
        elif tool_name == "createNewObjects":
            target_filename = kwargs["target_filename"]
            # 找尋file存不存在
            _is_trg_exist = os.path.exists(target_filename)
            if not _is_trg_exist:
                return False ,f"[Fail] {target_filename} does not exist. please check"
            out = jsonProcess.createNewObjects(**kwargs)
            return True, out
        elif tool_name == "ReadImageByteData":
            image_path = kwargs["image_path"]
            _is_trg_exist = os.path.exists(image_path)
            if not _is_trg_exist:
                return False, { "role": "user", "content":[{"text": "The image cannot be found, please check"}]}
            return True, ReadImageByteData(image_path)
        else:
            return False, f"[Fail] This tool cannot be found, please check"
    return False, None


"""JSON生成檢測"""
def catch_json_output(text:str) -> tuple:
    pattern = r"```json\s*\n(.*?)\n```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        content = match.group(1)
        return True, content
    
    return False, None



def load_config(config_path: Path = CONFIG_PATH, section: str = CONFIG_SECTION) -> dict:
    """
    Load Bedrock settings from config.ini.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")

    if section not in parser:
        raise KeyError(f"Section [{section}] not found in {config_path}")

    cfg = parser[section]

    required_keys = [
        "service_name",
        "chat_model_id",
        "region",
        "aws_access_key_id",
        "aws_secret_access_key",
    ]

    missing = [key for key in required_keys if not cfg.get(key, "").strip()]
    if missing:
        raise ValueError(f"Missing required config value(s): {', '.join(missing)}")

    return {
        "service_name": cfg.get("service_name").strip(),
        "anthropic_version": cfg.get("anthropic_version", "").strip(),
        "chat_model_id": cfg.get("chat_model_id").strip(),
        "region": cfg.get("region").strip(),
        "aws_access_key_id": cfg.get("aws_access_key_id").strip(),
        "aws_secret_access_key": cfg.get("aws_secret_access_key").strip(),
    }


def create_bedrock_client(cfg: dict):
    """
    Create Bedrock Runtime client.
    """
    return boto3.client(
        service_name=cfg["service_name"],
        region_name=cfg["region"],
        aws_access_key_id=cfg["aws_access_key_id"],
        aws_secret_access_key=cfg["aws_secret_access_key"],
    )


def build_user_message(user_text: str) -> dict:
    """
    Bedrock Converse API message format.
    """
    return {
        "role": "user",
        "content": [
            {
                "text": user_text
            }
        ],
    }


def build_assistant_message(assistant_text: str) -> dict:
    """
    Save assistant reply into message history.
    """
    return {
        "role": "assistant",
        "content": [
            {
                "text": assistant_text
            }
        ],
    }


def stream_chat(
    client,
    model_id: str,
    messages: list,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    max_tokens: int = 16384,
    temperature: float = 0.7,
) -> str:
    """
    Send current messages to Bedrock and stream assistant response.
    Return the full assistant reply text.
    """
    try:
        response = client.converse_stream(
            modelId=model_id,
            system=[
                {
                    "text": system_prompt
                }
            ],
            messages=messages,
            inferenceConfig={
                "maxTokens": max_tokens,
                "temperature": temperature,
            },
        )

        full_reply = []

        for event in response["stream"]:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"].get("delta", {})
                text = delta.get("text", "")

                if text:
                    print(text, end="", flush=True)
                    full_reply.append(text)

            elif "messageStop" in event:
                # One assistant message completed.
                pass

            elif "metadata" in event:
                # You can inspect token usage here if needed.
                pass

        print()
        return "".join(full_reply)

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise RuntimeError(f"AWS ClientError [{error_code}]: {error_message}") from e

    except BotoCoreError as e:
        raise RuntimeError(f"AWS BotoCoreError: {e}") from e


def main():
    try:
        cfg = load_config()
        client = create_bedrock_client(cfg)
        model_id = cfg["chat_model_id"]

        messages = []

        save_file_name = "llm-output.json"
        save_msg = (
                f"[Success] File has been saved to ./{save_file_name}\n"
                "If you have not yet to update the original project file, please call tool_use with:\n"
                "```tool_use\n"
                "overrideScreenLayout2JSON:./llm-output.json,<target_filename>\n"
                "```"
            )
        
        print("Bedrock Claude chat started.")
        print(f"Model: {model_id}")
        print("Type 'exit', 'quit', or Ctrl+C to leave.")
        print("-" * 60)

        # user-robot QA loop
        while True:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit", "q"}:
                print("Bye.")
                break
            
            t_start = time.time()
            messages.append(build_user_message(user_input))

            # Tool use loop
            while True:
                
                print("\nAssistant: ", end="", flush=True)

                assistant_reply = stream_chat(
                    client=client,
                    model_id=model_id,
                    messages=messages,
                    system_prompt=DEFAULT_SYSTEM_PROMPT,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                
                # 新增LLM輸出
                messages.append(build_assistant_message(assistant_reply))
                
                """JSON 生成檢測
                - 有 json 先存 json
                - 要提醒 main agent 記得 call tool 更改 project → 確保 While Loop 可以中斷
                """
                _json_state, _json_str_output = catch_json_output(assistant_reply)
                if _json_state:
                    try:
                        _json_output = json.loads(_json_str_output)
                        # 確保是完整的 json
                        if jsonProcess.isPseudoView(_json_output):
                            with open(save_file_name, "w", encoding="utf-8") as f:
                                json.dump(_json_output, f, ensure_ascii=False, indent=4)
                            messages.append(build_user_message(save_msg))
                            
                    except json.JSONDecodeError as e:
                        save_msg = f"[Fail] Invalid JSON output, cannot save file to `{save_file_name}`: {e}"
                        print(save_msg)
                        break
                
                """執行工具並回傳結果
                - 工具執行必須在 json 之後
                """
                _tool_state, _tool_use_result = catch_tool_output(assistant_reply) # 這一步抓取工具並直接執行 return 執行結果
                if _tool_state:
                    # 檢查 result 格式, dict → 讀圖片
                    if isinstance(_tool_use_result, dict):
                        messages.append(_tool_use_result)
                    else:
                        messages.append(build_user_message(_tool_use_result))
                else:
                    break
            
            t_end = time.time()
            print(f"Task time: {t_end - t_start}s")
            
    except KeyboardInterrupt:
        print("\nBye.")

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()