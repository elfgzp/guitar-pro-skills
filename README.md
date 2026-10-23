# Guitar Pro Skills

中文 | [English](README.en.md)

把 PDF／图片中的五线谱、六线谱与鼓谱，整理成可编辑、可播放、可核对的 **Guitar Pro** 谱文件的模块化 Agent Skills。

覆盖源谱检查、识谱录入、节奏校订、鼓轨处理、吉他编配、格式导出、最终验谱和透明滚动谱视频。每个 skill 独立描述输入、操作和交付证据；按需加载，不需要一次读完全部内容。默认用 **alphaTab** 验谱，按交付需要增加 TuxGuitar 兼容检查。

这是一套可复用的工作方法和小工具。复杂扫描件、特殊字体和演奏技法仍需要模型或人工识别；本仓库没有声称可以把任意 PDF 一键准确转换为 Guitar Pro。

## Skills

| Skill | 负责什么 | 主要产物 |
| --- | --- | --- |
| [score-source-inspect](skills/score-source-inspect/SKILL.md) | 判断矢量／扫描／混合 PDF，识别谱表、字体和图例 | 页清单、源谱定位、提取策略 |
| [score-transcribe](skills/score-transcribe/SKILL.md) | 录入音高、弦品、声部、反复、延音和技法 | 带原谱依据的中间记录 |
| [score-rhythm-audit](skills/score-rhythm-audit/SKILL.md) | 检查拍号、三连音、跨声部对齐与相似错误 | 节奏报告、经原谱核对的修正 |
| [score-percussion](skills/score-percussion/SKILL.md) | 识别鼓件、处理鼓延音、诊断空轨或无声 | 鼓件映射、GPIF 审计与可选补丁 |
| [score-arrange](skills/score-arrange/SKILL.md) | 按整小节主音优先或约定的补空模式合并吉他，保留原轨并验收 | 新编配轨、逐小节来源、差异记录 |
| [score-export](skills/score-export/SKILL.md) | 选择 `.gp`／`.gp5` 等格式，保留信息并回读 | 导出文件、格式损失记录 |
| [score-verify](skills/score-verify/SKILL.md) | 用 alphaTab 检查结构、渲染和播放，再比对原谱 | 分层验证报告、预览与交付清单 |
| [score-video](skills/score-video/SKILL.md) | 将选定 GP 轨道按等拍距排版、随 BPM 生成透明横向滚动视频 | 带 alpha 的 MOV、时间轴与编码报告 |

Guitar Pro 是产品正式名称；`.gp` 与 `.gp5` 是不同代际的文件格式，不是修改扩展名就能互换。MusicXML 与 MIDI 可作为辅助交付，MIDI 不保存完整谱面和指法。格式选择见 [score-export](skills/score-export/SKILL.md)。

## 使用方式

```sh
git clone https://github.com/elfgzp/guitar-pro-skills.git
cd guitar-pro-skills
```

**支持 Agent Skills 的工具：** 将需要的 `skills/<名称>/` 整个目录安装到该工具支持的 skills 目录。保留其 `references/`、`scripts/` 和依赖清单；不同产品的安装位置由该产品决定。每个 skill 可以单独复制，跨 skill 的交接是可选的。

**其他模型／聊天工具：** 提供相关 `SKILL.md` 作为任务说明，按需附上它链接的参考文件。能执行 Python 或 Node.js 时调用小工具；只有视觉能力时按相同步骤检查并记录未完成项。无需特定厂商 API、MCP、系统提示词或操作系统。

例如：

> 请读取 `score-source-inspect`，检查这份乐队总谱。保留所有轨道，列出不确定项。随后按需要使用其余 skills，输出 Guitar Pro 文件。用 alphaTab 验谱；如需 TuxGuitar 兼容，请另列兼容检查结果。

已有谱文件的问题可以直接进入相应 skill：节奏不齐用 `score-rhythm-audit`，鼓没声音用 `score-percussion`，将已有主音／节奏吉他编成单吉他用 `score-arrange`，最终交付用 `score-verify`。

编配规则由演奏需求决定：若选择“整小节主音优先”，主音轨在该小节只要有任何音符（含闷音、延音和倚音），就保留整小节及其中休止；只有主音全小节无音符时才用节奏轨。它与在主音空隙中补节奏是两种不同模式。新增轨应逐小节核对来源，并检查原有乐队轨道、跨小节滑音／延音和目标软件的静音状态。

## 可执行工具

以下命令在仓库根目录运行。Python 3.11+、Node.js 20+ 是本仓库验证的运行环境；只安装当前需要的依赖。路径均由调用者指定。

### 检查 PDF

```sh
python -m venv .venv
# 激活方式依操作系统选择：POSIX 为 . .venv/bin/activate
python -m pip install -r skills/score-source-inspect/requirements.txt
python skills/score-source-inspect/scripts/inspect_pdf.py input/score.pdf --output output/pdf-report.json
```

报告是版面与对象清单，不能单凭字符数量认定音乐符号可直接提取。

### 检查准确分数表示的节奏

```sh
python skills/score-rhythm-audit/scripts/audit_rhythm.py examples/rhythm-triplet.json --output output/rhythm-report.json
```

输入格式见 [rhythm-json.md](skills/score-rhythm-audit/references/rhythm-json.md)。工具逐声部检查间隙、重叠和小节长度，可通过 `--reference` 比较独立校订的节奏。不会把不齐的小节自动拉伸到满拍。

### alphaTab 验谱与原创新谱例

```sh
npm --prefix skills/score-verify ci
node skills/score-verify/scripts/make_demo.cjs output/demo.gp
node skills/score-verify/scripts/audit_alphatab.cjs output/demo.gp --json output/alphatab-report.json
node --test tests/test_alphatab.cjs
```

演示文件由代码生成，只含人工构造的短谱例。CLI 的结构检查与 MIDI 事件检查不能代替听音或对照原谱。

检查滑音遗漏时，先从原谱独立记录滑音类型和逐音起止位置，再比较导出文件：

```sh
node skills/score-verify/scripts/audit_alphatab.cjs output/score.gp --expected-slides input/source-slides.json --json output/slide-report.json
```

清单格式见 [滑音验证](skills/score-verify/references/slides.md)。工具检查已声明范围内的遗漏、多余滑音和错误终点，支持跨小节、闷音起点、倚音和显式弦号；默认报告也会列出文件里已有的滑音。期望清单必须来自独立原谱核对，不能从待检查的 GP 自动生成，否则无法发现录入时已经漏掉的技法。识谱注意事项见 [滑音录入](skills/score-transcribe/references/slides.md)。

本地浏览器预览：

```sh
python -m http.server 8765 --bind 127.0.0.1
```

打开 `http://127.0.0.1:8765/skills/score-verify/scripts/viewer.html`，选择本地谱文件。服务应只在可信本地目录运行；预览依赖安装在该 skill 内的 alphaTab。具体显示与播放步骤见 [score-verify](skills/score-verify/SKILL.md)。

鼓轨 GPIF 审计、可选补丁和支持范围见 [score-percussion](skills/score-percussion/SKILL.md)。补丁只处理经过确认的格式兼容问题；不能补出原谱中尚未识别的音符。

### 透明滚动谱视频

`score-video` 从已有 GP 选择轨道，通过 alphaTab 等拍距横向排版、完整速度时间轴、Pillow 逐帧合成和 FFmpeg 编码，生成静音的 ProRes 4444 透明 MOV。谱面连续经过固定播放线，起点为首拍，默认没有片头或倒数；无需 iMovie、其他剪辑软件或播放器录屏。

每个四分音符占用固定像素距离，镜头按 BPM 推进：速度为“每拍像素数 × BPM ÷ 60”。相同 BPM 下，密集音符、长音或换拍号都不会让滚动忽快忽慢；实际变速事件仍按原谱生效，包括长音中途的变速。普通谱面按内容疏密分配宽度，不能直接拿来做匀速滚动；旧素材需要重新渲染。

先按 [score-video](skills/score-video/SKILL.md) 安装该 skill 的 Node／Python 依赖、Playwright 浏览器和 FFmpeg，再在仓库根目录执行：

```sh
node skills/score-video/scripts/render_score.cjs --input input/score.gp --track 0 --output output/tiles --pixels-per-quarter 120
python skills/score-video/scripts/encode_overlay.py output/tiles/manifest.json output/overlay.mov
python skills/score-video/scripts/verify_overlay.py output/overlay.mov output/tiles/manifest.json
```

轨道索引从 0 开始；默认每四分音符 120 像素、`--scale 1.6`、1920 宽、60 FPS，画面高度来自渲染结果。拍距与符号大小分开控制，逐帧合成保留亚像素位移与透明边缘。支持范围和透明通道验证见 [视频说明](skills/score-video/references/video-formats.md)。未支持的反复／跳转、摇摆、倚音或多声部时间轴必须明确报错，不能套用固定小节时长。透明文件应解码检查 alpha；绿幕 MP4 只是可选的剪辑兼容衍生物。与真人演奏视频合成时，还需要对齐起点并检查速度漂移。

按 skill 完成交付时，还应在产物旁生成 `使用说明.md`：填写实际文件名、规格、音频状态、BPM／变速、对齐时间点及已验证范围。提供 iMovie 绿／蓝幕素材时，说明包含叠层、去背景、裁剪、对齐和导出步骤；生成视频仍不依赖剪辑软件。可复用的[中文使用说明模板](skills/score-video/assets/usage-guide.zh-CN.md)随 skill 一起分发，由执行 skill 的模型按实际产物填写。

## 完整流程与验收

```mermaid
flowchart LR
    A[源谱检查] --> B[音符与声部录入]
    B --> C[节奏校订]
    B --> D[鼓轨映射]
    C --> E[格式导出]
    D --> E
    E --> F[alphaTab 验谱]
    F --> G[原谱对照与交付]
    G -->|按需| H[透明滚动谱视频]
    F -->|发现差异| B
```

处理完整乐队总谱时，先建立全部轨道与小节清单，再分段录入；始终保留原谱页码、区域和修订依据。流程细节与交接产物见 [工作流](docs/workflow.md)。

验收分开记录：**格式可读取、结构正确、渲染正常、播放合理、原谱核对、目标软件兼容**。全部小节时值相加正确，不代表三连音正确；鼓轨有音符，不代表输出了正确鼓件或能听见声音；局部抽查通过，不代表全曲逐音校订完成。

## 开发与测试

```sh
python -m pip install -r requirements-dev.txt
npm --prefix skills/score-verify ci
python -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_alphatab.cjs
npm --prefix skills/score-video ci
npm --prefix skills/score-video test
python -m unittest discover -s skills/score-video/tests -p 'test_*.py'
python tools/check_repository.py
```

测试覆盖原始问题对应的通用失败模式：同列休止与音符、分数节奏、变拍与弱起、鼓件索引与 MIDI 音高混淆、滑音遗漏／错误终点／倚音、格式回读和验证结论的范围。实际覆盖边界见 [测试说明](docs/testing.md)。CI 运行相同的检查。

## 可移植性与许可

- skill 使用标准 `SKILL.md` + YAML 元信息，正文用英文提高跨模型复用性；README 提供中英两版。
- 脚本使用参数、相对资源路径和 JSON 报告，不绑定个人目录、账户或某一首曲目。
- 未包含原始商业谱面、用户 PDF、完整曲谱、字体、音色库或第三方源码。依赖通过包管理器安装；演示谱例为本仓库原创测试数据。
- 本仓库原创代码与文档采用 [MIT](LICENSE)。第三方依赖、Guitar Pro 商标及输入乐谱的权利分别归其权利人；本项目与 Arobas Music 无隶属关系。

参考：[Agent Skills 规范](https://agentskills.io/specification)、[Guitar Pro](https://www.guitar-pro.com/)、[alphaTab](https://www.alphatab.net/docs/introduction)、[PyGuitarPro](https://pyguitarpro.readthedocs.io/en/stable/)。
