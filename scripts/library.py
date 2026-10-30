#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""browser-workflow-recorder 任务库管理脚本。

管理个人浏览器工作流任务库（library.json）：
  list                列出全部流程
  get <name>          查看单个流程完整记录
  add --spec-file F   新增流程（重名报错，不覆盖）
  update --name N --spec-file F  替换某流程记录
  remove --name N --confirm  删除某流程（须显式确认）

库根目录默认 <当前用户主目录>\Doubao\browser-workflows（自动推导），
可用 --root 覆盖。所有文件一律 UTF-8 读写（无 BOM）。
"""

import argparse
import json
import os
import sys
from datetime import date

DEFAULT_ROOT = os.path.join(os.path.expanduser("~"), "Doubao", "browser-workflows")
LIBRARY_FILE = "library.json"
REQUIRED_FIELDS = ("name", "display_name", "purpose", "skill_dir", "project_dir")


def _library_path(root):
    return os.path.join(root, LIBRARY_FILE)


def _ensure_root(root):
    os.makedirs(root, exist_ok=True)


def load_library(root):
    _ensure_root(root)
    path = _library_path(root)
    if not os.path.exists(path):
        data = {"version": 1, "workflows": []}
        save_library(root, data)
        return data
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "workflows" not in data:
        raise SystemExit(f"库文件格式异常，请检查: {path}")
    return data


def save_library(root, data):
    _ensure_root(root)
    path = _library_path(root)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _read_spec(spec_file):
    if not os.path.exists(spec_file):
        raise SystemExit(f"spec 文件不存在: {spec_file}")
    with open(spec_file, "r", encoding="utf-8") as f:
        spec = json.load(f)
    if not isinstance(spec, dict):
        raise SystemExit("spec 必须是 JSON 对象")
    missing = [k for k in REQUIRED_FIELDS if not spec.get(k)]
    if missing:
        raise SystemExit(f"spec 缺少必填字段: {', '.join(missing)}")
    if "params" in spec and not isinstance(spec["params"], list):
        raise SystemExit("params 必须是数组")
    if "cron_job_ids" in spec and not isinstance(spec["cron_job_ids"], list):
        raise SystemExit("cron_job_ids 必须是数组")
    return spec


def _find(data, name):
    for wf in data["workflows"]:
        if wf.get("name") == name:
            return wf
    return None


def cmd_list(args):
    data = load_library(args.root)
    wfs = data["workflows"]
    if not wfs:
        print("任务库为空。录制第一个流程后会自动登记。")
        return
    widths = {"name": max(len("流程名"), max(len(w.get("name", "")) for w in wfs)),
              "display": max(len("中文名"), max(len(w.get("display_name", "")) for w in wfs)),
              "purpose": max(len("用途"), max(len(w.get("purpose", "")) for w in wfs))}
    print(f"{'流程名':<{widths['name']}}  {'中文名':<{widths['display']}}  {'用途':<{widths['purpose']}}")
    print("-" * (widths["name"] + widths["display"] + widths["purpose"] + 6))
    for wf in wfs:
        print(f"{wf.get('name',''):<{widths['name']}}  {wf.get('display_name',''):<{widths['display']}}  {wf.get('purpose',''):<{widths['purpose']}}")


def cmd_get(args):
    data = load_library(args.root)
    wf = _find(data, args.name)
    if wf is None:
        raise SystemExit(f"未找到流程: {args.name}")
    print(json.dumps(wf, ensure_ascii=False, indent=2))


def cmd_add(args):
    spec = _read_spec(args.spec_file)
    data = load_library(args.root)
    if _find(data, spec["name"]) is not None:
        raise SystemExit(f"流程已存在，不要覆盖: {spec['name']}（修改请用 update）")
    record = dict(spec)
    record.setdefault("params", [])
    record.setdefault("trigger_examples", [])
    record.setdefault("cron_job_ids", [])
    record.setdefault("notes", "")
    record.setdefault("created_at", date.today().isoformat())
    data["workflows"].append(record)
    save_library(args.root, data)
    print(f"已入库: {record['name']}（共 {len(data['workflows'])} 个流程）")


def cmd_update(args):
    spec = _read_spec(args.spec_file)
    if spec.get("name") != args.name:
        raise SystemExit(f"--name 与 spec 中的 name 不一致: {args.name} != {spec.get('name')}")
    data = load_library(args.root)
    wf = _find(data, args.name)
    if wf is None:
        raise SystemExit(f"未找到流程: {args.name}")
    record = dict(spec)
    record.setdefault("params", [])
    record.setdefault("trigger_examples", [])
    record.setdefault("cron_job_ids", wf.get("cron_job_ids", []))
    record.setdefault("notes", wf.get("notes", ""))
    record["created_at"] = wf.get("created_at", record.get("created_at", date.today().isoformat()))
    data["workflows"] = [record if w.get("name") == args.name else w for w in data["workflows"]]
    save_library(args.root, data)
    print(f"已更新: {record['name']}")


def cmd_remove(args):
    if not args.confirm:
        raise SystemExit("删除须带 --confirm（且仅在用户明确要求删除时执行）")
    data = load_library(args.root)
    wf = _find(data, args.name)
    if wf is None:
        raise SystemExit(f"未找到流程: {args.name}")
    before = len(data["workflows"])
    data["workflows"] = [w for w in data["workflows"] if w.get("name") != args.name]
    save_library(args.root, data)
    print(f"已删除: {args.name}（{before} -> {len(data['workflows'])}）")


def main():
    parser = argparse.ArgumentParser(description="浏览器工作流任务库管理")
    parser.add_argument("--root", default=DEFAULT_ROOT, help=f"任务库根目录（默认 {DEFAULT_ROOT}）")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="列出全部流程")
    p_list.set_defaults(func=cmd_list)

    p_get = sub.add_parser("get", help="查看单个流程")
    p_get.add_argument("name")
    p_get.set_defaults(func=cmd_get)

    p_add = sub.add_parser("add", help="新增流程")
    p_add.add_argument("--spec-file", required=True)
    p_add.set_defaults(func=cmd_add)

    p_upd = sub.add_parser("update", help="替换流程记录")
    p_upd.add_argument("--name", required=True)
    p_upd.add_argument("--spec-file", required=True)
    p_upd.set_defaults(func=cmd_update)

    p_rm = sub.add_parser("remove", help="删除流程")
    p_rm.add_argument("--name", required=True)
    p_rm.add_argument("--confirm", action="store_true")
    p_rm.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    try:
        args.func(args)
    except SystemExit as e:
        sys.exit(e.code)


if __name__ == "__main__":
    main()
