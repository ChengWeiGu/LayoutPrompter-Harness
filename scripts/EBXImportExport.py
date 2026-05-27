"""
import_screen_between_projects.py
----------------------------------
跨 EBV7 專案匯入一個 Screen（連同其相依的 Composite Model）。

使用情境：
    來源專案 (SRC) 與 目標專案 (DST) 都已在 EasyBuilder X 中開啟，
    本機 AI socket registry 找得到兩個實例。

執行方式：
    python import_screen_between_projects.py \
        --src-project Alarm-test.ebxprj \
        --dst-project Project.ebxprj \
        --screen "TEST 1"

設計重點：
    1. 透過 %APPDATA%\\Weintek\\EasyBuilder X\\ai-sockets\\*.json 自動定位 host:port。
    2. 跨專案匯入 Screen 之前，必須先把它依賴的 Composite Model 一併匯入，否則
       importScreenView 會回 missing_references。
    3. Export / Import 一律走 detectImportConflicts → import 的順序，避免無聲覆蓋。
"""

from __future__ import annotations
import argparse
import glob
import json
import os
import socket
import sys
import uuid
from typing import Any, Iterable

SCHEMA = "1.3"
REGISTRY = (
    os.environ.get("EB_AI_REGISTRY_DIR")
    or os.path.join(os.environ["APPDATA"], "Weintek", "EasyBuilder X", "ai-sockets")
)


# ---------- 通訊層 ----------

def _send(host: str, port: int, method: str, params: dict | None, timeout: float) -> dict:
    req = {
        "id": str(uuid.uuid4()),
        "method": method,
        "schema_version": SCHEMA,
        "params": params or {},
    }
    payload = (json.dumps(req, ensure_ascii=False) + "\n").encode("utf-8")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
        s.sendall(payload)
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))


def call(host: str, port: int, method: str, params: dict | None = None, timeout: float = 60) -> dict:
    """送一筆 RPC，失敗丟例外。回傳 result 內容。"""
    resp = _send(host, port, method, params, timeout)
    if not resp.get("ok"):
        err = resp.get("error", {})
        code = err.get("code", "UNKNOWN_ERROR")
        msg = err.get("message", "")
        raise RuntimeError(f"{method} failed: {code}: {msg}")
    return resp.get("result", {})


# ---------- registry 探索 ----------

def discover() -> list[dict]:
    """回傳本機存活的 EBV7 實例（自動過濾 stale registry）。"""
    out = []
    for f in glob.glob(os.path.join(REGISTRY, "*.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                inst = json.load(fp)
        except Exception:
            continue
        try:
            r = _send(inst["host"], inst["port"], "ping", {}, 2)
            if r.get("ok"):
                out.append(inst)
        except Exception:
            continue
    return out


def pick(instances: list[dict], project_name: str) -> tuple[str, int]:
    """從 registry 找出指定 project_name 的 host:port。"""
    matches = [i for i in instances if i.get("project_name") == project_name]
    if not matches:
        names = sorted({i.get("project_name", "?") for i in instances})
        raise RuntimeError(f"找不到 project_name={project_name!r}；目前存活的：{names}")
    if len(matches) > 1:
        raise RuntimeError(f"project_name={project_name!r} 有多個實例 ({len(matches)})；請改用 pid 區分")
    inst = matches[0]
    return inst["host"], inst["port"]


# ---------- 業務邏輯 ----------

def composite_models_used_by_screen(screen_archive: dict) -> list[str]:
    """掃 screen archive，回傳被引用的 compositeModel 名稱（去重，保序）。"""
    seen: list[str] = []
    body = screen_archive.get("body", {})
    for screen in body.get("screens", []) + body.get("windows", []):
        for obj in screen.get("objects", []):
            name = obj.get("compositeModel")
            if name and name not in seen:
                seen.append(name)
    return seen


def import_one_composite(dst: tuple[str, int], src: tuple[str, int], model_name: str) -> dict:
    """從 src 匯出單一 composite model，detect 衝突後寫入 dst。"""
    archive = call(*src, "exportCompositeModel", {"model_name": model_name})["archive"]
    try:
        conflicts = call(*dst, "detectImportConflicts", {"archive": archive})
        if conflicts.get("has_conflicts"):
            print(f"  ⚠ composite {model_name!r} 在目標已有同名項：{conflicts['conflicts']}")
    except RuntimeError as e:
        # 大型 composite archive 可能超過 server 端 64KB read buffer，detect 略過不致命
        if "REQUEST_TOO_LARGE" in str(e):
            print(f"  ⚠ archive 過大，跳過 conflict detect，直接 import（import 端會回 renamed/overridden 資訊）")
        else:
            raise
    try:
        result = call(*dst, "importCompositeModel", {"archive": archive})
    except RuntimeError as e:
        if "REQUEST_TOO_LARGE" in str(e):
            size_kb = len(json.dumps(archive, ensure_ascii=False)) / 1024
            raise RuntimeError(
                f"composite {model_name!r} 序列化後 ~{size_kb:.1f} KB，超過 EBV7 server 端 "
                f"READ_BUFFER_LIMIT (預設 64 KB)。請改用 getProjectFile/setProjectFile 整包搬遷，"
                f"或調整 server 端 READ_BUFFER_LIMIT。"
            ) from e
        raise
    return result


def import_screen(dst: tuple[str, int], src: tuple[str, int], screen_name: str) -> None:
    print(f"[1/4] 從來源匯出 screen：{screen_name!r}")
    screen_archive = call(*src, "exportScreenView", {"screen_name": screen_name})["archive"]

    deps = composite_models_used_by_screen(screen_archive)
    print(f"[2/4] screen 引用的 composite model：{deps or '(無)'}")

    for model_name in deps:
        print(f"      → 匯入 composite model：{model_name!r}")
        res = import_one_composite(dst, src, model_name)
        added = res.get("added_model_names", [])
        unresolved = res.get("unresolved_references", [])
        print(f"        added={added}, unresolved={len(unresolved)}")
        for u in unresolved:
            print(f"          ⚠ {u.get('kind')} {u.get('entity_path')} → {u.get('path')}")

    print(f"[3/4] 在目標偵測 screen 衝突")
    conflicts = call(*dst, "detectImportConflicts", {"archive": screen_archive})
    if conflicts.get("has_conflicts"):
        raise RuntimeError(f"目標已有同名 screen，請先處理：{conflicts['conflicts']}")
    print(f"      conflict_count = 0")

    print(f"[4/4] 匯入 screen 到目標")
    res = call(*dst, "importScreenView", {"archive": screen_archive})
    if not res.get("success"):
        raise RuntimeError(f"importScreenView 失敗：{res}")
    print(f"      imported = {res.get('imported_window_names')}")


# ---------- 入口 ----------

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="跨 EBV7 專案匯入單一 Screen（含相依的 Composite Model）")
    p.add_argument("--src-project", required=True, help="來源專案的 project_name（例如 Alarm-test.ebxprj）")
    p.add_argument("--dst-project", required=True, help="目標專案的 project_name（例如 Project.ebxprj）")
    p.add_argument("--screen", required=True, help="要匯入的 Screen 名稱（例如 'TEST 1'）")
    p.add_argument("--snapshot", action="store_true", help="匯入後對目標 screen 拍 PNG snapshot")
    args = p.parse_args(argv)

    instances = discover()
    if not instances:
        print("沒有偵測到任何存活的 EBV7 實例", file=sys.stderr)
        return 1

    print("[discover] 存活實例：")
    for i in instances:
        print(f"  - pid={i.get('pid')} {i.get('project_name')} @ {i.get('host')}:{i.get('port')}")

    src = pick(instances, args.src_project)
    dst = pick(instances, args.dst_project)
    print(f"[target] SRC = {args.src_project} @ {src[0]}:{src[1]}")
    print(f"[target] DST = {args.dst_project} @ {dst[0]}:{dst[1]}")

    import_screen(dst, src, args.screen)

    pv = call(*dst, "getProjectView")
    screens = [s.get("name") for s in pv.get("screens", [])]
    print(f"[verify] DST screens = {screens}")
    if args.screen not in screens:
        print(f"⚠ 目標專案找不到 {args.screen!r}", file=sys.stderr)
        return 2

    if args.snapshot:
        snap = call(*dst, "getSnapshot", {"screen_name": args.screen})
        print(f"[snapshot] {snap.get('absolute_path')}")

    print("✅ 完成")
    return 0


# ---------- 自建 ----------
def export_project(project_path:str, screen_name:str) -> dict:
    """
    Args:
        project_path (str): EBXPRJ File
        screen_name (str): screen name
    """
    try:
        instances = discover()
        if not instances:
            raise Exception(f"[EBV7 Socket Error] 沒有偵測到任何存活的 EBV7 實例")
        
        src = pick(instances, project_path)
        result = call(*src, "exportScreenView", {"screen_name": screen_name})
        ebx_proj = result["archive"]
        return ebx_proj
    
    except Exception as e:
        raise
    
def import_project(archive:dict, target_project:str):
    """
    Args:
        archive (dict): Src Project in json format
        target_project (str): EBXPRJ File
    """
    try:
        instances = discover()
        if not instances:
            raise Exception(f"[EBV7 Socket Error] 沒有偵測到任何存活的 EBV7 實例")
        
        dst = pick(instances, target_project)
        conflicts = call(
                        *dst,
                        "detectImportConflicts",
                        {"archive": archive},
                    )
        
        # if conflicts.get("has_conflicts"):
        #     raise RuntimeError(f"Import conflicts: {conflicts['conflicts']}")

        result = call(
            *dst,
            "importScreenView",
            {"archive": archive},
        )

        status = result['success']
        if not status:
            raise Exception(f"[EBV7 Socket Error] cannot import project to {target_project}")
        
    except Exception as e:
        raise
    




if __name__ == "__main__":
    # sys.exit(main())

    # project_path = "Project_DrawWidgets.ebxprj"
    # screen_name = "demo1"
    # ebx_proj = export_project(project_path, screen_name)
    # print(json.dumps(ebx_proj, ensure_ascii=False, indent=4))
    
    json_file = "Project_DrawWidgets.json"
    target_project = "Project_DrawWidgets.ebxprj"
    with open(json_file, "r", encoding="utf-8") as f:
        ebx_proj = json.load(f)
    import_project(ebx_proj, target_project)
    
    
    
