import re


class ToolCallStreamFilter:
    def __init__(self):
        self.buffer = ""
        self.in_tool_call = False
        self.tool_call_buffer = ""

    def get_tool_hint(self, tool_call_text: str) -> str:
        
        # color
        BEGIN_COLOR = "\033[92m"
        RESET = "\033[0m"
        
        """
        根據 tool_call 內容回傳 terminal 要顯示的簡短提示。
        不顯示 tool_call 細節。
        """
        if "ReadImageFromFile" in tool_call_text or "ReadImageByteData" in tool_call_text:
            return BEGIN_COLOR + "\nLLM is reading an image...\n" + RESET

        if "GetScreenLayout" in tool_call_text:
            return BEGIN_COLOR + "\nLLM is reading screen layout from Project...\n" + RESET

        if "OverrideRes2Proj" in tool_call_text:
            return BEGIN_COLOR + "\nLLM is updating the project file with new design...\n" + RESET

        if "UpsertWidgets" in tool_call_text:
            return BEGIN_COLOR + "\nLLM is modifying screen objects...\n" + RESET

        if "ReadScreenShot" in tool_call_text:
            return BEGIN_COLOR + "\nLLM is verifying screen by snapshot...\n" + RESET
        
        return BEGIN_COLOR + "\nLLM is using a tool...\n" + RESET

    def feed(self, text: str) -> str:
        self.buffer += text
        output = ""

        while self.buffer:
            if self.in_tool_call:
                m = re.search(r"\r?\n```", self.buffer)

                if not m:
                    # 還沒遇到 tool_call 結尾，收集內容但不顯示
                    self.tool_call_buffer += self.buffer
                    self.buffer = ""
                    return output

                # 收集 tool_call 結尾前的內容
                self.tool_call_buffer += self.buffer[:m.start()]

                # 顯示簡短提示
                output += self.get_tool_hint(self.tool_call_buffer)

                # 清空 tool_call buffer
                self.tool_call_buffer = ""

                # 跳過結束 fence
                self.buffer = self.buffer[m.end():]
                self.in_tool_call = False
                continue

            idx = self.buffer.find("```")

            if idx == -1:
                # 保留最後 2 個字元，避免 ``` 被 chunk 切開
                if len(self.buffer) > 2:
                    output += self.buffer[:-2]
                    self.buffer = self.buffer[-2:]
                return output

            # 先輸出 ``` 前面的正常文字
            output += self.buffer[:idx]
            self.buffer = self.buffer[idx:]

            # 等待 code fence 第一行完整
            newline_match = re.search(r"\r?\n", self.buffer)
            if not newline_match:
                return output

            first_line = self.buffer[:newline_match.start()]
            rest = self.buffer[newline_match.end():]

            # 判斷是不是 tool_call code block
            if re.match(r"```\s*tool_call\s*$", first_line, re.IGNORECASE):
                self.buffer = rest
                self.in_tool_call = True
                self.tool_call_buffer = ""
                continue

            # 不是 tool_call，正常顯示 code fence 第一行
            output += self.buffer[:newline_match.end()]
            self.buffer = rest

        return output

    def flush(self) -> str:
        if self.in_tool_call:
            # 如果 stream 結束時還在 tool_call 裡，就只顯示簡短提示
            hint = self.get_tool_hint(self.tool_call_buffer) if self.tool_call_buffer else ""
            self.buffer = ""
            self.tool_call_buffer = ""
            self.in_tool_call = False
            return hint

        out = self.buffer
        self.buffer = ""
        return out