# AI 协作记录与当前版本

本目录从原始 Codex 会话提取四条迭代的用户消息和 AI 可见回复，保留顺序及时间戳。图片、本机路径和隐私信息作脱敏处理。附图可由参赛者对照原始会话补交。

| 对话 | 可检查的代码与结果 |
| --- | --- |
| [免费官网检索](01-免费官网检索.md) | `backend/official_notices.py`、`backend/search_service.py`，验证模拟不可达时本地回退 |
| [报到问答与个人清单](02-报到问答与个人清单.md) | `backend/arrival_answer.py`、`frontend/app.js`，验证分段引用、选择保存和会话隔离 |
| [长卷滚动透视](03-长卷滚动透视.md) | `frontend/journey.js`、`tools/verify_journey.mjs`，验证静止透视、滚动和首尾衔接 |
| [问答措辞改为办理建议](04-问答措辞改为办理建议.md) | `backend/answer.py`、`backend/store.py`，验证往年资料年份提示与无资料时的办理建议 |

原始归档末次提交为 `1a8b75333b22e0ac469c2676b7fb1fc06ad4c50d`。已验证的当前工作区于恢复仓库时通过 `73e75f61be161df4c115e55a93046659247ec1d1` 整合。上述后期改动可从该提交核对当前代码。原开发过程的逐轮 Git 提交在可用归档中的覆盖范围以实际日志为准。

## 验收

在仓库根目录执行 `python -X utf8 -I -S tools/jury_check.py`。验收使用隔离数据和本机临时端口，输出复合问答、会话隔离、保存及重启复测结果。
