import os
import re
from typing import List, Dict, Optional


def read_text_file(file_path: str) -> str:
    """讀取文字檔內容"""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def parse_skill_header(text: str) -> Optional[Dict[str, str]]:
    """
    解析 skill 檔案最上方的 YAML front matter。

    Expected format:
    ---
    name: design-color-systems
    version: "1.0.0"
    description: >-
      description text...
    ---
    """

    # 只抓檔案最前面的 --- ... ---
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)

    if not match:
        return None

    header = match.group(1)

    result = {}

    # name
    name_match = re.search(r"^name:\s*(.+)$", header, re.MULTILINE)
    if name_match:
        result["name"] = name_match.group(1).strip().strip('"').strip("'")

    # version
    version_match = re.search(r"^version:\s*(.+)$", header, re.MULTILINE)
    if version_match:
        result["version"] = version_match.group(1).strip().strip('"').strip("'")

    # description: >- 多行格式
    description_match = re.search(
        r"^description:\s*(?:>[-+]?)?\s*\n((?:[ \t]+.*\n?)*)",
        header,
        re.MULTILINE
    )

    if description_match:
        description_lines = description_match.group(1).splitlines()

        description = "\n".join(
            line.strip()
            for line in description_lines
            if line.strip()
        )

        result["description"] = description

    else:
        # description: 單行格式
        description_single_match = re.search(
            r"^description:\s*(.+)$",
            header,
            re.MULTILINE
        )

        if description_single_match:
            result["description"] = (
                description_single_match
                .group(1)
                .strip()
                .strip('"')
                .strip("'")
            )

    return result


def load_all_skill_headers(skill_dir: str = "./skills") -> List[Dict[str, str]]:
    """
    從 .skill/* 讀取全部 skill 檔案，
    回傳包含 name、version、description 的 list of dict。
    """

    skills = []

    if not os.path.exists(skill_dir):
        return skills

    for file_name in os.listdir(skill_dir):
        file_path = os.path.join(skill_dir, file_name)

        if not os.path.isfile(file_path):
            continue

        try:
            text = read_text_file(file_path)
            skill_info = parse_skill_header(text)

            if skill_info:
                skill_info["file_path"] = file_path
                skills.append(skill_info)

        except Exception as e:
            skills.append({
                "file_path": file_path,
                "error": str(e)
            })

    return skills


if __name__ == "__main__":
    
    skills = load_all_skill_headers("./skills")

    for skill in skills:
        print(skill)