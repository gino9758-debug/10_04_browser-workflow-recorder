# 回放已录流程（完整步骤）

本文件描述"执行/回放一个已录制浏览器工作流"的完整编排。运行机制遵循 browser-record-replay 技能（先读取其 `SKILL.md` 与 `references/windows-powershell.md`）。

## 0. 前置检查

按主文档"环境前置"检查引擎健康。`healthy=true 且 ready=true` 才继续。

## 1. 定位任务

用库脚本查任务：

```powershell
python "<本技能目录>\scripts\library.py" get <流程名>
```

- 用户可能用中文名/触发例句指代流程：先 `list` 看全库，再按 `display_name`、`trigger_examples`、`purpose` 匹配。
- 查不到或名字含糊：展示库中现有任务清单，请用户确认是哪一个；不要猜。
- 取到任务的 `skill_dir`（已安装技能的绝对目录）。

## 2. 收集参数

按任务的 `params` schema 收集本次执行参数：

1. 上下文里已有明确值（用户刚才说过、或定时任务 query 里带了）→ 直接采用。
2. `required=true` 且无值 → 必须向用户问清，一次问全，不猜测。
3. 有 `default` 且用户未指定 → 用默认值，并在执行前向用户说明将使用的值。
4. `hint` 用于说明格式/取值范围。

把参数写成 UTF-8 无 BOM 的 JSON 文件（禁止把 JSON 拼进命令行）：

```powershell
$paramPath = Join-Path $env:TEMP ("rpa-params-" + [guid]::NewGuid().ToString('N') + ".json")
$params = @{ "start_date" = "2026-10-13"; "channel" = "抖音" } | ConvertTo-Json -Depth 20
[IO.File]::WriteAllText($paramPath, $params, (New-Object System.Text.UTF8Encoding $false))
```

## 3. 执行回放

已安装技能的 runner 是 `scripts/run.js`。Windows 上用 browser-record-replay 的 `references/windows-run.ps1` 辅助以隐藏进程方式运行长任务：

```powershell
$rpaSkillRoot = "<browser-record-replay 技能目录>"   # 从已安装技能列表解析
$jobFile = Join-Path $env:TEMP ("rpa-job-" + [guid]::NewGuid().ToString('N') + ".json")
$job = @{
    executable = (Get-Command "node.exe").Source
    cwd = "<任务 skill_dir>"
    args = @("<任务 skill_dir>\scripts\run.js", "--param-file", $paramPath)
    output_dir = Join-Path "<任务 project_dir>" (".rpa-dev/jobs/" + [guid]::NewGuid().ToString('N'))
}
[IO.File]::WriteAllText($jobFile, ($job | ConvertTo-Json -Depth 20), (New-Object System.Text.UTF8Encoding $false))
$receipt = & "$rpaSkillRoot\references\windows-run.ps1" -SpecFile $jobFile | ConvertFrom-Json
```

轮询等待完成记录（`terminal=true`），检查退出码与业务结果。`unknown`/`interrupted` 不算成功，不得盲目自动重试；重试前先判断失败类别（登录态过期、页面结构变化、参数格式错等），需要用户处理（如重新登录）就明确请用户操作。

单次回放同一项目是单飞的：若返回"运行中"，等待该次运行结束，不要并发再跑。

## 4. 呈现结果

- 业务结果是**记录集合** → 必须渲染为 Markdown 表格：每行一条记录，列为确认的业务输出字段，禁止用列表/JSON/字段清单代替。
- 是**单个结构化记录**（≥2 个业务字段）→ 用两列表格（字段 | 结果），URL 保持完整。
- 真无结果 → 说明"未找到匹配结果"及用户能理解的原因，不编造行。
- 不暴露 `success`、`validated`、trace、内部 ID 等内部字段为业务列。

## 5. 收尾

- 执行结束后清理本次临时参数文件（$paramPath）。
- 如需继续对话（例如用户要求改参数重跑），保留浏览器环境；确认用户不再用时再清理。
