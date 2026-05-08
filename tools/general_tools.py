import os


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")
    
    

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
    
    
"""LLM使用工具4: 讀取圖片
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