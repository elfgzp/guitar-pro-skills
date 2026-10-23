# 从源谱到可交付 Guitar Pro / Source-to-score workflow

本页负责连接六个 skill。每个 skill 内的说明和工具仍可独立使用。
This page connects the six skills; each skill remains independently usable.

## 1. 建立边界 / Establish scope

记录输入文件的哈希、请求的轨道、目标格式和目标播放软件。全轨总谱必须先
建立轨道清单；不要因为某轨难识别或没有 TAB 就静默略过。识别印刷小节号、
文件内部序号、反复展开后的播放序号，避免后续把“第 89 小节”对错位置。

Record source hashes, requested tracks, output formats, and playback targets.
For an all-track score, inventory every part before transcription. Distinguish
printed measure numbers, file indices, and playback occurrences after repeats.

## 2. 查看源谱 / Inspect the source

用 `score-source-inspect` 检查页面对象，并实际渲染代表页。矢量谱可建立当前
字体的符号图集；扫描谱可使用可用的 OMR、图像处理或人工录入。两条路线都要
保留可定位的原谱依据。文字水印并不能证明音乐符号是矢量文字。

Use `score-source-inspect` to inventory page objects and render representative
pages. Build a font-specific symbol atlas for vector notation when appropriate.
For raster notation, choose available OMR, image processing, or manual entry.
Preserve source locations for either route. A text watermark does not make the
underlying score vector text.

**交接 / Handoff:** 页清单、轨道／谱表关系、拍号／调号／定弦、鼓谱图例、
提取路线、坐标约定、已知模糊区域。

## 3. 录入并保留依据 / Transcribe with provenance

用 `score-transcribe` 按谱系、声部和小节录入。中间数据可采用现有 MusicXML、
乐谱库模型或自定义结构，不要求重写一套通用识谱引擎。至少应能还原：

- 小节、声部、起音与时值；音符、和弦和休止的区别。
- 音高、弦品、实际定弦和移调；延音对象而非仅一个布尔标记。
- 反复来源、技法、歌词或尚未支持的标记。
- 原谱页／区域、识别依据、置信度和人工修订记录。

Use an existing notation model, MusicXML, or a task-specific representation.
Retain voice timing, pitch/fingering, note-level ties, repeat provenance,
techniques and lyrics, source locations, uncertainty, and corrections. A
confidence score should reflect actual evidence, not an arbitrary certainty.

**交接 / Handoff:** 可重复生成的录入数据、未解决项、明确的损失记录。

## 4. 校节奏与鼓轨 / Audit timing and percussion

用 `score-rhythm-audit` 检查每个声部，再用跨轨同步关系发现可疑位置。
几何间距只能辅助判断，不能代替符干、符尾、连桁、附点和连音组。
每个自动修正都应留下可供复核的记录。发现一处系统性错误后，搜索同样的
字体、连音括号、跨谱系或重复段结构，并逐项核对。

Check voices individually before cross-track alignment. Engraving distance is
supporting evidence, not musical time. Audit every automated correction and
search for matching failure patterns elsewhere in the score.

用 `score-percussion` 根据当前谱子的图例建立鼓件映射，分别核对谱面位置、
音头、实际 MIDI 输出和延音关系。先确定源谱有无音符，再排查编码、通道、
静音和音色；不要把“鼓轨无声”直接等同于声音设备故障。

Map the current score's drum legend, noteheads, staff positions, sounding MIDI
values, and ties. Trace source notes → encoded notes → generated attacks →
audio. Avoid skipping directly to audio-device troubleshooting.

**交接 / Handoff:** 分数节奏校验、源谱确认的修正、每鼓件的独立音符与敲击数。

## 5. 导出并回读 / Export and reimport

用 `score-export` 选择实际支持的编码器，写入新文件后回读。保留原始输入。
对每个目标格式检查轨道、弦品、音高、时值、延音、鼓件和技法；格式能力不同
时写清损失。不能把两个文件的音符总数相同当成逐事件一致。

Choose an encoder that supports the requested format, write a new output, and
reimport it. Compare semantic events, not only totals. Record format losses.
Use independent readers when practical because one library can repeat its own
mistake through a round trip.

**交接 / Handoff:** 输出文件、哈希、工具版本、语义比较结果、格式限制。

## 6. 分层验谱和交付 / Verify and deliver

用 `score-verify` 先跑 alphaTab 结构与播放事件检查，再查看全曲渲染和关键段
试听；最后对照原谱。局部发现问题后回到相应环节。目标要求 TuxGuitar 时，
另做其真实解析／播放检查并记录版本，不把它替代为主验谱器。

Run alphaTab structure/playback-event checks, inspect the complete render,
audition selected passages, and compare with the source. Perform a separate
target-version compatibility check when TuxGuitar is required.

最终清单应包含 / A delivery manifest should include:

| 层 / Layer | 应记录的证据 / Evidence |
| --- | --- |
| Parse / 解析 | 实际输出哈希、解析器与版本、错误 |
| Structure / 结构 | 轨道／小节／声部、时值、音高／鼓件、延音检查 |
| Visual / 视觉 | 已渲染范围、末小节是否存在、异常区域 |
| Playback / 播放 | MIDI 起音、实际音色试听、静音或爆音问题 |
| Source / 原谱 | 逐音或抽样范围、修正记录、未核对项 |
| Compatibility / 兼容 | 目标软件与版本、实际执行结果或未执行 |

状态使用 `pass / fail / not-run / partial`，不要把未执行写成通过。交付清楚命名
的最终版本、可选备份格式和限制说明，避免用户误开旧文件。

Use `pass / fail / not-run / partial`; unperformed work is not a pass. Deliver
clearly named final files, optional interchange formats, and limitations so users
can identify the verified version.
