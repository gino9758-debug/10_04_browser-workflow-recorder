---
name: browser-workflow-recorder
description: 个人浏览器工作流录制与回放技能。把用户在豆包内置浏览器中的网页操作（业务后台、电商平台、飞书网页版、数据系统、资讯网站等）录制成可回放的自动化任务，支持带参数执行与定时执行，并维护个人任务库。触发场景：用户说"录制操作/录制流程/把这个流程录下来/记录我接下来的操作"，或"执行XX流程/跑一下XX/回放XX/定时执行XX/每天跑XX"等需要录制或回放浏览器操作时使用。
---

# 浏览器工作流录制与回放（个人任务库）

把用户亲自演示过的浏览器操作变成可反复执行的自动化任务，录一次、以后随时回放，支持每次输入不同参数，也可挂定时任务。

## 角色分工

本技能是**个人任务库管理器**：负责录制编排、任务入库、参数收集、回放执行、定时联动、库管理。录制引擎使用已安装的 **browser-record-replay** 技能（豆包内置浏览器自动化）。执行录制/回放命令前，必须先完整读取 browser-record-replay 的 `SKILL.md` 及其 `references/recording-to-production.md`、`references/windows-powershell.md`，录制机制以其为准；本技能只补充任务库与参数化编排。

## 关键路径

- 任务库根目录：`C:\Users\<用户名>\Doubao\browser-workflows\`（不存在则自动创建；发布版为占位符，安装时替换为你的 Windows 用户名）
- 库索引文件：`<库根目录>\library.json`
- 库管理脚本：`scripts/library.py`（本技能目录下）

## 意图分流

1. **录制新流程** → 见 `references/recording-flow.md`
2. **回放已录流程** → 见 `references/replay-flow.md`
3. **定时回放** → 见下文"定时回放"
4. **库管理**（查看/修改/删除任务）→ 用库脚本，见下文"库管理"

## 环境前置（录制与回放前必做）

用 PowerShell 直接调用 `rpa-dev-local.exe`（从 PATH 解析），检查引擎健康：

```powershell
$rpaDev = (Get-Command "rpa-dev-local.exe").Source
& $rpaDev local setup status
```

- `healthy=true 且 ready=true` → 继续。
- 版本门槛已通过但 `healthy=false` → 运行 `& $rpaDev local bootstrap` 一次，等待完成后复检状态。
- 复检仍不健康 → 请用户完全退出并重启豆包客户端，再复检；不要自行修复扩展或改注册表。

## 录制新流程（概要）

完整步骤见 `references/recording-flow.md`。要点：

1. **对齐需求**：与用户确认流程名称（英文短名）、中文名、一句话用途、目标网站、参数清单（每个参数的字段名/中文含义/默认值/是否必填）。
2. **读取 browser-record-replay 技能**，按其完整流程执行：创建项目 → 开始录制（可见录制，请用户演示）→ 停止录制 → 整理任务说明 → 用户回复"确认" → 生成实现 → 交付并安装为技能。
3. **参数化**：录制中的每个输入框都要整理成语义字段（snake_case 字段名 + 中文标签 + 必填/默认规则），默认值须请用户确认。
4. **入库**：交付成功后用库脚本登记任务（含已装技能目录、参数 schema、触发例句）。
5. **告知用户**：任务已入库，给出可用的触发例句。

## 定时回放

用户要求"每天/每周固定时间跑 XX 流程"时：

1. 先按技能发现流程读取 `doubao-cron-scheduler` 的 SKILL.md，按其指引创建定时任务。
2. 定时任务的 query 必须写明：`本次请求是由「<定时任务标题>」定时任务到时触发的，请执行任务库中已录制的「<流程中文名>」流程，参数：<本次要用的参数值>`。
3. 创建成功后，把返回的 `cron_job_id` 用库脚本 `update` 登记到该任务的 `cron_job_ids` 列表。
4. 定时任务到时后按 `references/replay-flow.md` 的回放步骤执行。

## 库管理

统一用 `scripts/library.py`（python，UTF-8）：

```powershell
python "<本技能目录>\scripts\library.py" list
python "<本技能目录>\scripts\library.py" get <流程名>
python "<本技能目录>\scripts\library.py" add --spec-file <spec.json>
python "<本技能目录>\scripts\library.py" update --name <流程名> --spec-file <spec.json>
python "<本技能目录>\scripts\library.py" remove --name <流程名> --confirm
```

- `add` 在流程名已存在时报错，不覆盖；改任务用 `update`。
- `remove` 必须带 `--confirm`，且只允许在用户明确要求删除某流程时执行。
- `list` 缺省展示：流程名、中文名、用途。

## 硬约束

- 不向任务库根目录以外写入；不删除、移动用户原有文件。
- 参数文件一律 UTF-8 无 BOM 写入，禁止把 JSON 直接拼进 PowerShell 命令行。
- 长时运行（回放）在 Windows 上用 browser-record-replay 自带的 `references/windows-run.ps1` 辅助执行，不依赖临时任务 ID。
- 回放结果按结果呈现契约输出（见 `references/replay-flow.md`）：集合结果必须渲染为 Markdown 表格。
- 不向用户暴露端口、进程号、Native Messaging、token、内部路径等诊断细节；用产品语言汇报进度。
