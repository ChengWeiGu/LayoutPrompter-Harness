import configparser
from pathlib import Path
from .SkillFunc import load_all_skill_headers



CONFIG_PATH = Path("./Config.ini")
BEDROCK_CONFIG_SECTION = "BEDROCK_EU"
PROMPT_CONFIG_SECTION = "PROMPT"

if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

parser = configparser.ConfigParser()
parser.read(CONFIG_PATH, encoding="utf-8")



def load_bedrock_config(section: str = BEDROCK_CONFIG_SECTION) -> dict:
    """
    Load Bedrock settings from config.ini.
    """
    if section not in parser:
        raise KeyError(f"Section [{section}] not found in {CONFIG_PATH}")

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
    
    
"""build system prompt from CONFIG_PATH
- system_prompt_file: the original system prompt
"""
def read_sys_prompt(section: str = PROMPT_CONFIG_SECTION) -> str:

    _file=parser[section]["system_prompt_file"]
    _prompt = "I'm an ai assistant to help you find answer"
    with open(_file, 'r', encoding='utf-8') as f:
        _prompt = f.read()
        
    return _prompt


"""Skill Headers
- skills_folder : additional skill prompts
"""
def read_skill_headers(section: str = PROMPT_CONFIG_SECTION) -> str:
    _folder = parser[section]["skills_folder"]
    skills = load_all_skill_headers(_folder)
    _prompt = ""
    for skill in skills:
        _prompt += f"{skill}\n"
    
    return _prompt


# init sys prompt
DEFAULT_SYSTEM_PROMPT = read_sys_prompt()