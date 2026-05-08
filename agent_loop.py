import os
import re
import sys
import json
import boto3
import time
import configparser
from pathlib import Path
from datetime import datetime
from tools import general_tools
from tools import ebx_json_tools
from botocore.exceptions import ClientError, BotoCoreError


CONFIG_PATH = Path("./Config.ini")
CONFIG_SECTION = "BEDROCK_EU"
max_tokens=65536
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
            return general_tools.build_user_message(
                "[Fail] Invalid tool_call format. Expected: <tool_name>:<kwargs>"
            )
        
        try:
            kwargs = json.loads(raw_kwargs)
        except json.JSONDecodeError as e:
            return general_tools.build_user_message(
                f"[Fail] Invalid tool_call JSON arguments: {e}"
            )        
        
        if tool_name == "decodeScreenLayoutFromJSON":
            screen_name = kwargs["screen_name"]
            filename = kwargs["filename"]
            
            # 找尋 file 存不存在
            _is_exist = os.path.exists(filename)
            if not _is_exist:
                return general_tools.build_user_message(f"[Fail] `{filename}` does not exist. please tell me to check")
            
            screen = ebx_json_tools.decodeScreenLayoutFromJSON(**kwargs)
            if screen is None:
                return general_tools.build_user_message(f"[Fail] the screen name `{screen_name}` cannot be found in `{filename}`. please tell me to check")
            
            result = "[Success] get screen json as follows:\n" + json.dumps(screen, ensure_ascii=False)
            return general_tools.build_user_message(result)
        
        elif tool_name == "overrideScreenLayout2JSON":
            source_filename = kwargs["source_filename"]
            target_filename = kwargs["target_filename"]
            
            # 找尋 file 存不存在
            _is_src_exist = os.path.exists(source_filename)
            _is_trg_exist = os.path.exists(target_filename)
            if not _is_src_exist:
                return general_tools.build_user_message(f"[Fail] `{source_filename}` does not exist. please tell me to check")
            if not _is_trg_exist:
                return general_tools.build_user_message(f"[Fail] `{target_filename}` does not exist. please tell me to check")
            
            result = ebx_json_tools.overrideScreenLayout2JSON(**kwargs)
            return general_tools.build_user_message(result)
        
        elif tool_name == "upsertObjects":
            target_filename = kwargs["target_filename"]
            
            # 找尋 file 存不存在
            _is_trg_exist = os.path.exists(target_filename)
            if not _is_trg_exist:
                return general_tools.build_user_message(f"[Fail] {target_filename} does not exist. please tell me to check")
            
            result = ebx_json_tools.upsertObjects(**kwargs)
            return general_tools.build_user_message(result)
        
        elif tool_name == "ReadImageByteData":
            image_path = kwargs["image_path"]
            _is_trg_exist = os.path.exists(image_path)
            
            # 找尋 file 存不存在
            if not _is_trg_exist:
                return general_tools.build_user_message(f"[Fail] `{image_path}` does not exist. please tell me to check")
            
            return general_tools.ReadImageByteData(image_path)
        
        else:
            return general_tools.build_user_message(f"[Fail] This tool `{tool_name}` cannot be found, please check")
        
    return {}


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
    
    # color
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    
    try:
        cfg = load_config()
        client = create_bedrock_client(cfg)
        model_id = cfg["chat_model_id"]

        messages = []

        # 確認temp存在
        if not os.path.exists("./temp"):
            os.makedirs("./temp")
        
        print(BLUE + "Bedrock Claude chat started.")
        print(f"Model: {model_id}")
        print("Type '/exit', '/quit', or Ctrl+C to leave")
        print("Type '/help' to see all available commands."+ RESET)
        print("-" * 60)
        
        # user-robot QA loop
        while True:
            user_input = input("\nYou: ").strip()

            serial_num = datetime.now().strftime("%Y%m%d%H%M%S")
            save_file_name = f"./temp/llm-output-{serial_num}.json"
            
            save_msg = (
                    f"[System Info] latest complete json has been saved to {save_file_name}\n"
                    "Immediately after that, if the original project file has not been updated yet, please call tool_call with the following:\n"
                    "```tool_call\n"
                    "overrideScreenLayout2JSON:{"
                    f"\"source_filename\":\"{save_file_name}\","
                    "\"target_filename\":\"<target_filename>\""
                    "}\n"
                    "```"
                )
            
            
            if not user_input:
                continue
            
            command = user_input.lower()
            
            if command == "/help":
                print("\n")
                print(
                    YELLOW
                    + "Available commands:\n"
                    + "  /clear  Clear message history\n"
                    + "  /reset  Clear message history\n"
                    + "  /help    Show commands\n"
                    + "  /quit    Exit program\n"
                    + "  /exit    Exit program\n"
                    + "  ctrl + C    Exit program\n"
                    + RESET
                )
                continue
            
            
            if command in {"/exit", "/quit"}:
                print("Bye.")
                break
            
            if command in {"/clear", "/reset"}:
                messages.clear()
                general_tools.clear_terminal()
                print(BLUE + "Bedrock Claude chat started")
                print(f"Model: {model_id}")
                print("Message history has been cleared")
                print("Type '/exit', '/quit', or Ctrl+C to leave")
                print("Type '/help' to see all available commands."+ RESET)
                print("-" * 60)
                continue
            
            
            t_start = time.time()
            messages.append(general_tools.build_user_message(user_input))

            # Tool use loop
            max_agent_steps = 10
            step_count = 0
            while step_count < max_agent_steps:
                
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
                messages.append(general_tools.build_assistant_message(assistant_reply))
                step_count += 1
                
                """完整的 JSON 生成檢測
                - 有 json 先存 json
                - 要提醒 main agent 記得 call tool 更改 project → 確保 While Loop 可以中斷
                """
                _json_state, _json_str_output = catch_json_output(assistant_reply)
                _has_psuedo_view = False
                if _json_state:
                    try:
                        _json_output = json.loads(_json_str_output)
                        # 確保是完整的 json
                        _has_psuedo_view = ebx_json_tools.isPseudoView(_json_output)
                        if _has_psuedo_view:
                            with open(save_file_name, "w", encoding="utf-8") as f:
                                json.dump(_json_output, f, ensure_ascii=False, indent=4)
                            messages.append(general_tools.build_user_message(save_msg))
                            
                    except json.JSONDecodeError as e:
                        error_msg = f"[Fail] Invalid JSON output, cannot save file to `{save_file_name}`: {e}"
                        print(error_msg)
                        messages.append(general_tools.build_user_message(error_msg))
                        continue
                
                """執行工具並回傳結果
                - 工具執行必須在 json 之後
                """
                try:
                    # 抓取工具並直接執行 return 執行結果
                    _tool_call_message = catch_tool_execute(assistant_reply) 
                    if _tool_call_message:
                        messages.append(_tool_call_message)
                    else:
                        # 如果有 psuedo view 但沒有同時使用工具，再給一次使用工具的機會
                        if _has_psuedo_view:
                            continue
                        break
                except Exception as e:
                    error_msg = f"[Tool Use Error] {str(e)}"
                    print(error_msg)
                    messages.append(general_tools.build_user_message(error_msg))
                    continue
                
            else:
                error_msg = "[System Info] Reached max agent steps. Please check whether the tool call format is correct | STOP calling tools"
                print(error_msg)
                messages.append(general_tools.build_user_message(error_msg))
            
            t_end = time.time()
            print(f"Task time: {t_end - t_start}s")
            
    except KeyboardInterrupt:
        print("\nBye.")

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()