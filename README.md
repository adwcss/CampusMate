# 初到 CampusMate

河南科技职业大学新生报到助手。新生可以提出报到问题、展开资料出处，再把证件和交通等准备事项加入自己的清单。校园探索长卷、地图、宿舍参考、竞赛与社团指南提供到校前的辅助信息。

## 运行与评审

需要 Python 3.10 或更高版本和现代浏览器。本地问答、报到清单及校园导览可直接运行。

```powershell
python -X utf8 -S run.py
```

打开 [本机 CampusMate](http://127.0.0.1:8765/)，可用 `--port 8766` 修改端口。顶部显示河南科技职业大学。个人记录使用本机 SQLite，按浏览器会话保存。

- [演示和技术文档](submission/README.md)
- [评委复现步骤](docs/single-school-review.md)
- [迎新资料覆盖表](docs/迎新资料覆盖表.md)

## 启用 DeepSeek 联网补查

默认优先查本地。启用 DeepSeek 后，遇到本地无匹配、赛事简介无法支持具体考点，或模型判断资料不足时，会查找公开来源，再按引文组织答案。学生可展开编号打开出处。本校报到、缴费等待办事项优先查本校官网，往届资料按适用年份引用。联网超时则使用可用资料或给出核对建议。

如需试用，在仅供本机后端读取的 `config/deepseek.local.env` 中加入以下三项。该文件已被 Git 忽略，请使用本人有权使用的密钥。搜索和模型调用可能产生费用。

```dotenv
GUIDE_ALLOW_REMOTE_LLM=true
GUIDE_LLM_MODEL=deepseek-flash
GUIDE_LLM_API_KEY=填入自己的密钥
```

也可通过同名环境变量设置，环境变量优先。设置 `CAMPUSMATE_ALLOW_SEARCH=false` 关闭联网查询。问答中请勿输入个人敏感信息。手动切换「联网增强」可并行读取学校公开公告。

## 验证

```powershell
python -X utf8 -S -m unittest tools.verify
python -X utf8 -S tools/jury_check.py
node --test tools/verify_appearance_state.mjs
```

Node.js 仅用于前端测试。单校版回归覆盖报到问答、引用、清单保存、会话隔离和联网回退。外部服务的模拟测试与真实案例分别记录。原有多校测试和说明用于查阅历史。

## 开源许可

项目原创代码与原创开发文档采用 [MIT 许可证](LICENSE)。PixiJS 和 Three.js 随附各自许可。学校资料、地图、照片、角色插画及其他素材遵循各自权利人的条款。
