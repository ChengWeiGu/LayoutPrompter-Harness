import os
import re
import sys
import json
import time
from datetime import datetime
import scripts.ClaudeFunc as cf_layer
import scripts.ToolCalling as tc_layer


def clear_terminal():
    os.system("cls" if os.name == "nt" else "clear")
    

def main():
    
    # color
    RED = "\033[31m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_MAGENTA = "\033[95m"
    RESET = "\033[0m"
    
    try:
        cfg = cf_layer.load_config()
        client = cf_layer.create_bedrock_client(cfg)
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
            user_input = input(f"\n{BRIGHT_CYAN}You: {RESET}").strip()

            serial_num = datetime.now().strftime("%Y%m%d%H%M%S")
            save_file_name = f"./temp/llm-output-{serial_num}.json"
            
            save_msg = (
                    f"[System Info] latest complete json has been saved to {save_file_name}\n"
                    "Immediately after that, if the original project file has not been updated yet, please override it to user's project with:\n"
                    "```tool_call\n"
                    "OverrideRes2Proj:{"
                    f"\"source_view_path\":\"{save_file_name}\","
                    "\"target_project_path\":\"<target_filename>\""
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
                print(RED+"Bye."+RESET)
                break
            
            if command in {"/clear", "/reset"}:
                messages.clear()
                clear_terminal()
                print(BLUE + "Bedrock Claude chat started")
                print(f"Model: {model_id}")
                print("Message history has been cleared")
                print("Type '/exit', '/quit', or Ctrl+C to leave")
                print("Type '/help' to see all available commands."+ RESET)
                print("-" * 60)
                continue
            
            
            t_start = time.time()
            messages.append(cf_layer.build_user_message(user_input))

            # Tool use loop
            max_agent_steps = 10
            step_count = 0
            while step_count < max_agent_steps:
                
                print(f"\n\n{BRIGHT_MAGENTA}Assistant:{RESET} ", end="", flush=True)

                assistant_reply = cf_layer.stream_chat_filter(
                    client=client,
                    model_id=model_id,
                    messages=messages
                )
                
                # 新增LLM輸出
                messages.append(cf_layer.build_assistant_message(assistant_reply))
                step_count += 1
                
                """完整的 JSON 生成檢測
                - 有 json 先存 json
                - 要提醒 main agent 記得 call tool 更改 project → 確保 While Loop 可以中斷
                """
                _json_state, _json_str_output = tc_layer.catch_json_output(assistant_reply)
                _has_sc_view = False
                if _json_state:
                    try:
                        _json_output = json.loads(_json_str_output)
                        # this json should be screen format
                        _has_sc_view = tc_layer._isViewFormat(_json_output)
                        if _has_sc_view:
                            with open(save_file_name, "w", encoding="utf-8") as f:
                                json.dump(_json_output, f, ensure_ascii=False, indent=4)
                            messages.append(cf_layer.build_user_message(save_msg))
                            
                    except json.JSONDecodeError as e:
                        error_msg = f"[Fail] Invalid JSON output, cannot save file to `{save_file_name}`: {e}. please STOP and tell user to check."
                        print(error_msg)
                        messages.append(cf_layer.build_user_message(error_msg))
                        continue
                
                """執行工具並回傳結果
                - 工具執行必須在 json 之後
                """
                try:
                    # 抓取工具並直接執行 return 執行結果
                    _tool_call_message = tc_layer.catch_tool_execute(assistant_reply) 
                    if _tool_call_message:
                        messages.append(_tool_call_message)
                    else:
                        # 如果有 screen view 但沒有同時使用工具，再給一次使用工具的機會
                        if _has_sc_view:
                            continue
                        break
                except Exception as e:
                    error_msg = f"[Tool Use Error] {str(e)}. please STOP and tell user to check"
                    print(error_msg)
                    messages.append(cf_layer.build_user_message(error_msg))
                    continue
                
            else:
                error_msg = "[System Info] Reached max agent steps. Please check whether the tool call format is correct | STOP calling tools"
                print(error_msg)
                messages.append(cf_layer.build_user_message(error_msg))
            
            t_end = time.time()
            print("\n------------------")
            print(f"Task time: {t_end - t_start:.2f}s")
            print("------------------\n")
            
    except KeyboardInterrupt:
        print(f"\n{RED}Bye.{RESET}")

    except Exception as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()