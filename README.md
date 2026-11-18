# CampusMate 2.0.1 · 多高校新生指南

评委可先按[可信问答与双校演示](docs/trusted-evidence-demo.md)复现本次升级，也可从[十分钟复现指南](docs/评委十分钟复现.md)开始。当前设计见[技术说明](docs/当前版技术说明.md)，开发证据与材料状态见[参赛证据索引](docs/参赛证据索引.md)。

本次地图更新：默认改用用户上传地图的美化版，保留原图对照、可开关的地点标记与已校准的图上坐标。详见[地图美化与接入](docs/地图美化与接入.md)。旧版泛化SVG只保留为历史/空白学校示意，不作为本校默认地图。

在收到的“初到”1.6项目上渐进改造，保留本地BM25问答、任务、演练、行李准备、成长推荐、宿舍参考等可用代码。河南科技职业大学为完整示范学校。河南科技大学已接入本校招生章程和官网公告，支持问答与个人任务。空白配置单独标注为待接入模板。

## 启动

需要Python 3.10+和现代浏览器，无需安装第三方包、下载模型或提供密钥：

```powershell
python -X utf8 -S run.py
```

打开 http://127.0.0.1:8765/ ，通过顶部选择学校。端口占用可加`--port 8766`。服务仍仅绑定本机，不具备账户登录、学校管理员认证或公网服务能力。

## 本版变化

- `config/schools/<school_id>.json`控制学校名称、官方域名、官网入口、状态和地图说明；可配置本校`places`列表，未接入地点保持为空。
- 每个学校有独立的检索实例和`.runtime/schools/<school_id>/guide.sqlite3`。同一浏览器会话的问答、任务、准备台等按学校隔离；未知学校或请求中不一致的学校标识会被拒绝。
- 前端每次API请求携带`X-CampusMate-School`，页面URL保留`school_id`。API也接受查询参数或JSON中的`school_id`；旧客户端未提供时默认`hnvust`。
- 问答可选择“本地知识库”或“联网增强”。增强模式同时执行本地检索与独立搜索服务，保留每条来源的URL、采集时间和可信度说明；搜索摘要不视作已核验正文。
- 本地资料和已读取的官网正文出现不同适用年份，或日期、金额集合存在明显差异时，会提示打开原文核对。差异提示采用规则匹配。
- 河职大使用上传地图的美化版并提供原图对照。河科大在核实本校地图和地点之前显示空白示意及资料状态。
- “日程与任务”可按住校、资助了解需求和跨城出行预览准备建议，再加入待办。日期自填，重复生成保留已完成状态与修改后的日期，不代替学校规定。
- 新版任务/准备台备份携带`school_id`，不同学校或缺少标识的旧备份不会被直接导入，避免混入错误学校数据。

## 两种外部服务分别配置

默认问答使用本地资料，外部模型关闭。选择「联网增强」时，默认检索所选学校的公开公告栏目，无需搜索密钥。程序按本校 HTTPS 域名及 robots.txt 读取匹配公告，缓存成功的索引和正文 30 分钟。正文不可读时仍可显示原文入口，回答使用本地资料。`.env.example`仅作参考，程序**不会自动读取.env**。如要完全关闭联网，启动前设置 `CAMPUSMATE_ALLOW_SEARCH=false`。

如另行选用 Brave 搜索，需自行申请 Brave Search API 密钥，并在启动前设置：

```powershell
$env:CAMPUSMATE_ALLOW_SEARCH = 'true'
$env:CAMPUSMATE_SEARCH_PROVIDER = 'brave'
$env:CAMPUSMATE_SEARCH_API_KEY = Read-Host '输入你自己的搜索服务密钥' -MaskInput
python -X utf8 -S run.py
```

`-MaskInput`需要PowerShell 7；旧版PowerShell请通过系统环境变量管理器安全配置。搜索可能产生费用。界面选择“联网增强”才请求搜索；无密钥、无官方域名、超时或失败会显示回退原因。只向固定的`https://api.search.brave.com/res/v1/web/search`发送学校名、官方域名及有限公开主题词，不发送完整问题、会话、出行偏好或历史记录。结果必须属于所选学校配置的HTTPS官方域名及其子域；禁止跟随搜索API重定向。对符合本校公告路径且允许读取的结果，继续核验正文。

可选AI生成仍使用原有DeepSeek适配器，和搜索服务互不代替：

```powershell
$env:GUIDE_ALLOW_REMOTE_LLM = 'true'
$env:GUIDE_LLM_API_KEY = Read-Host '输入自己获授权的新AI密钥' -MaskInput
python -X utf8 -S run.py
```

AI 开启后，联网增强模式会将问题及已核验的本地段落和官网正文节选发送给 DeepSeek。每段生成内容必须引用允许的编号，数字必须出现在引用段落中。资料有冲突、问题涉及敏感的具体办理安排或校验失败时，直接返回证据及核对提示。原有交接密钥指纹拒绝机制保留。`GUIDE_LLM_MODEL`默认`deepseek-chat`；`GUIDE_DATA_DIR`可指定数据根目录。关闭终端或移除环境变量可清除本次配置。

**本轮未使用真实密钥调用付费搜索或AI，联网协议与失败路径通过模拟响应验证，不声称已验证真实线上搜索覆盖率或生成质量。**

## 学校与知识接入

1. 复制空白学校配置，修改文件名及`school_id`，使用小写字母开头、字母数字/下划线/短横线组成的2–40字符标识。
2. 填入已核实的名称、官方域名、官网、资料状态和地图说明。使用 `notice_pages` 配置本校公告栏目。`legacy_content`保持`false`；仅`hnvust`能引用原交接学校资料。
3. 创建`knowledge/<school_id>/sources.json`，参照`knowledge/SOURCE_TEMPLATE.json`。只下载经核实的学校官方公开文件，记录实际标题、URL、发布日期（未知为null）、实际下载时间、文件路径、SHA-256与适用年份。
4. 待核实条目标记`pending_verification`；已确认网址但没有文件的条目标记`verified_url_pending_download`。实际下载且校验匹配的条目标记 `verified_download`。人工核对官网正文后整理的文字使用 `verified_summary`，填入 `verified_at`，下载时间留空。
5. 新知识加载器只索引清单控制的UTF-8`.txt`正文；HTML/PDF保留原件，需另行人工复核转换为文本并记录派生关系。文件必须在本校知识目录内且来源为本校官方HTTPS域名。
6. 若有经过核实的地点，在学校配置添加`places`，每项包含`id/name/category/x/y/question/note`，坐标为图上0–100百分比，`note`说明具体资料来源与限制。重启服务加载配置。新学校的宿舍/演练/成长模块仍需独立资料适配，不会自动复制河职大内容。

河职大已入库两份官网资料摘要，分别依据[2026 年招生章程](https://www.hnvust.cn/info/1036/3851.htm)和[2026 年度信息公开工作报告](https://www.hnvust.cn/info/1036/4151.htm)。河科大已入库[2026 年普通本科招生章程](https://zjc.haust.edu.cn/info/1133/35053.htm)的校区和招生范围。两校的完整报到须知、校区办理点和接站安排待补充。

## 数据与升级

这是在原项目副本中的开发，桌面原件未修改。新版不自动迁移旧`.runtime/guide.sqlite3`，以免误把未标识的数据分给其他学校。若需迁移，先停止旧服务并备份数据库，再运行：

```powershell
python -X utf8 -S tools/migrate_legacy_data.py --source '旧项目/.runtime/guide.sqlite3' --destination '.runtime'
```

脚本仅将明确的旧单校数据库备份至`hnvust`子目录，目标存在时拒绝覆盖。浏览器沿用原会话标识才能访问原记录；清除浏览器存储会失去旧会话入口。新旧备份格式不要自行添加学校标识后盲目导入，应先核对内容。

按学校分库用于防止单机产品的数据串用，学校选择本身不是身份认证。共享电脑上仍应自行保护浏览器会话；需要公网部署时还须实现登录、权限、管理员知识审核及运维方案。

## 验证

```powershell
python -X utf8 -I -S tools/verify.py
python -X utf8 -I -S tools/verify_multi.py
python -X utf8 -I -S tools/evaluate_retrieval.py --output docs/evaluation-campusmate.json
node --test tools/verify_appearance_state.mjs
```

应用无需Node；Node只用于开发验证。新增测试覆盖真实HTTP的学校边界、备份隔离、任务幂等、SVG合法性，以及模拟搜索接口、并行检索、差异提示与错误回退。检索评估是22个固定问题的关键词覆盖，不等于答案事实正确率。详见`docs/campusmate-verification.json`及`docs/CampusMate诊断与改造说明.md`。

## 代码与历史

### 开源许可

CampusMate 项目原创程序代码及其原创开发文档采用 [MIT 许可证](LICENSE)。PixiJS 和 Three.js 随附各自的许可。学校资料、地图、照片、角色插画与其他素材的使用权遵循原权利人的条款。

核心运行文件仍为`run.py`、`backend/main.py`、`backend/answer.py`、`backend/store.py`与`frontend/`，新增学校注册、清单知识加载、搜索接口、插画地图和报到建议模块。旧Streamlit/FastAPI/Chroma依赖文件仅为继承遗留，不用于当前启动路径。

本次输入不含`.git`或可恢复bundle，因而新建仓库的首提交只记录**收到的解压目录基线**，之后才记录真实改造；不重建README中提及但本次未提供的旧提交。历史README、旧截图、原交付清单、既有Prompt素材记录保留作历史资料，不作为本轮操作或校验的证明。完整旧README见`docs/README-legacy-1.6.md`。交付包附`history.bundle`，可用`git clone history.bundle restored-campusmate`恢复本轮真实提交。
