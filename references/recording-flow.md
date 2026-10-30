# 录制新流程（完整步骤）

本文件描述"录制一个新浏览器工作流"的完整编排。**录制机制本身必须遵循 browser-record-replay 技能的既定流程**，动手前先完整读取该技能的 `SKILL.md`、`references/recording-to-production.md`、`references/windows-powershell.md`。以下步骤只补充本任务库的编排层。

## 0. 前置检查

按主文档"环境前置"检查引擎健康；不健康先 bootstrap 或请用户重启豆包，就绪后再开始。

## 1. 与用户对齐（开始录制前必须完成）

用业务语言向用户确认，一次问清：

1. **流程英文短名**（如 `daily-sales-export`，用作目录名与触发名）与**中文名**（如 `每日销售数据导出`）。
2. **一句话用途**：这个流程做什么、做完要得到什么结果。
3. **目标网站/页面**：在哪个系统里操作（运营后台、电商平台、飞书网页版等）。
4. **参数清单**：这次演示中哪些地方每次会变（日期、商品、订单号、关键词、渠道…）。对每个参数确认：
   - 中文含义（用户视角的标签，如"开始日期"）
   - 默认值（若用户常用某个值，记为默认值并说明"这次录制会以该值演示，回放时可改"）
   - 是否必填
5. **结果确认方式**：演示结束后，用户拿什么判断成功（如"页面出现导出完成的提示"、"表格列出 N 行数据"）。

对齐完成、用户确认后，才进入录制。用户未确认参数设计前不得开始录制。

## 2. 创建项目并开始录制

按 browser-record-replay 流程执行，命令形如（以 PowerShell 直接调用 `rpa-dev-local.exe`，不要经 python 中转）：

```powershell
$rpaDev = (Get-Command "rpa-dev-local.exe").Source
$root   = "C:\Users\<用户名>\Doubao\browser-workflows"
$proj   = Join-Path $root "<流程英文短名>"
& $rpaDev local app create --dir $proj --name <流程英文短名>
& $rpaDev local session start --project $proj
& $rpaDev local record start --project $proj --title "<中文名>演示"
```

录制是**可见**的。开始后对用户说（只准用这句话）：

> "录制已开始。请按平时的方式完成操作演示。演示结束后先不要关闭浏览器，只回复“完成”。"

## 3. 停止录制与整理任务说明

用户回复"完成"后**立即**运行 `local record stop`，等产物保存成功。然后只对用户说：

> "演示已记录。我正在整理任务说明，现在不需要你操作。"

整理任务说明时：

- 核对录制的每一步与每张截图，确认业务步骤完整、输入位置清晰。
- **参数化**：把录制中出现的每个输入值整理成语义字段。字段名用 snake_case（如 `start_date`、`sku_code`），字段要有：中文标签、必填/默认规则、绑定到录制的哪一步。默认值用录制证据中的值，但必须请用户确认是否合理。
- 整理成"任务说明"（目标、任务入参、自动完成步骤、结果），展示给用户，只请用户回复"确认"：

> "任务说明已整理好。请查看目标、任务入参、自动完成步骤和结果；没有问题请回复“确认”。"

用户回复"确认"后，只对用户说：

> "任务说明已确认。我正在根据你的演示准备自动化，现在不需要你操作。"

随后静默执行确认与实现准备（intake confirm、contract 等），不对用户复述内部文档、选择器、预检等细节。

## 4. 实现与交付

按 browser-record-replay 流程：

1. 读取其返回的实现契约与 starter，只复制经过核对的业务逻辑。
2. 参数通过 `--param-file` 传入；每个语义字段都要在实现中生效。
3. 业务断言、等待、失败分类、多标签页处理、finally 清理都要齐备。
4. 运行 `local deliver run`（带代表性真实参数与明确的语义结果契约），通过后再安装为代理技能。

## 5. 登记入库

交付/安装成功、且验证回放通过后，把任务登记进任务库：

```powershell
python "<本技能目录>\scripts\library.py" add --spec-file <spec.json>
```

spec.json 形如（UTF-8 无 BOM）：

```json
{
  "name": "daily-sales-export",
  "display_name": "每日销售数据导出",
  "purpose": "打开运营后台，按日期与渠道导出销售报表并下载",
  "site": "https://ops.example.com",
  "skill_dir": "C:\\Users\\<用户名>\\AppData\\Local\\Doubao\\rpa-dev\\exports\\skills\\daily-sales-export",
  "project_dir": "C:\\Users\\<用户名>\\Doubao\\browser-workflows\\daily-sales-export",
  "params": [
    {"field": "start_date", "label": "开始日期", "required": true, "default": null, "hint": "格式 YYYY-MM-DD"},
    {"field": "channel", "label": "渠道", "required": false, "default": "全部", "hint": "如 天猫 / 抖音 / 全部"}
  ],
  "trigger_examples": ["跑一下每日销售数据", "执行每日销售数据导出"],
  "cron_job_ids": [],
  "notes": ""
}
```

- `skill_dir` 必须是浏览器自动化交付返回的实际安装/导出目录；不确定时用 `get` 前先确认真实路径。
- `add` 后立即用 `list` 或 `get` 回读验证已入库。

## 6. 告知用户

用一句话说明任务已入库，并给出触发例句，例如：

> "「每日销售数据导出」已录制入库。以后你说『跑一下每日销售数据』，告诉我日期和渠道即可自动执行；也可以让我设成每天定时跑。"

## 重录与修改

- 流程操作方式变了：走 `local app create` 新建同名项目前先确认旧任务；改完按第 3~5 步重新入库（`update`）。
- 只改参数默认值/说明：直接 `update` 任务的 `params`，无需重录。
