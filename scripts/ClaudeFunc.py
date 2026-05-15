import os
import boto3
import configparser
from pathlib import Path
from .StreamFilter import ToolCallStreamFilter
from botocore.exceptions import ClientError, BotoCoreError


CONFIG_PATH = Path("./Config.ini")
CONFIG_SECTION = "BEDROCK_EU"
MAX_TOKENS = 65536
TEMPERATURE = 0.7



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
    
    
"""read system prompt from CONFIG_PATH"""
def read_sys_prompt(config_path: Path = CONFIG_PATH, section: str = "PROMPT") -> str:
    parser = configparser.ConfigParser()
    parser.read(config_path, encoding="utf-8")
    _file=parser[section]["system_prompt_file"]
    _prompt = "I'm an ai assistant to help you find answer"
    with open(_file, 'r', encoding='utf-8') as f:
        _prompt = f.read()
    return _prompt

# init sys prompt
DEFAULT_SYSTEM_PROMPT = read_sys_prompt()


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


"""打印 LLM 原始輸出"""
def stream_chat(
    client,
    model_id: str,
    messages: list,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    max_tokens: int = MAX_TOKENS,
    temperature: float = TEMPERATURE,
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



"""將 LLM 原始輸出做以下處理
- tool_call 具體訊息不顯示在 terminal
- tool_call 內容僅簡短顯示在 terminal
"""
def stream_chat_filter(
    client,
    model_id: str,
    messages: list,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    max_tokens: int = MAX_TOKENS,
    temperature: float = TEMPERATURE,
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
        display_filter = ToolCallStreamFilter()
        
        for event in response["stream"]:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"].get("delta", {})
                text = delta.get("text", "")

                if text:
                    # print(text, end="", flush=True)
                    full_reply.append(text)
                    
                    visible_text = display_filter.feed(text)
                    if visible_text:
                        print(visible_text, end="", flush=True)

            elif "messageStop" in event:
                # One assistant message completed.
                pass

            elif "metadata" in event:
                # You can inspect token usage here if needed.
                pass
        
        # 串流結束後補印剩餘安全文字
        remaining = display_filter.flush()
        if remaining:
            print(remaining, end="", flush=True)
        
        print()
        return "".join(full_reply)

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", str(e))
        raise RuntimeError(f"AWS ClientError [{error_code}]: {error_message}") from e

    except BotoCoreError as e:
        raise RuntimeError(f"AWS BotoCoreError: {e}") from e
