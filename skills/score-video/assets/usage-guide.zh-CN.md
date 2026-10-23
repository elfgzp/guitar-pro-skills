# 谱面视频使用说明

本次使用 `{{source_file}}` 中的 **{{track_name}}** 轨道。

## 选择文件

| 文件 | 用途 | 声音 |
| --- | --- | --- |
| `{{master_file}}` | 带透明通道的主素材；在支持该格式的剪辑软件里叠加到演奏视频上 | {{master_audio}} |
| `{{preview_file}}` | 已合成 {{preview_background}} 背景的效果预览 | {{preview_audio}} |
| `{{chroma_file}}` | {{chroma_color}}幕兼容素材，需要在剪辑软件中移除背景色 | {{chroma_audio}} |

透明主素材规格：{{master_format}}，{{master_dimensions}}，{{fps}} fps。
色幕素材规格及谱面位置：{{chroma_dimensions}}，{{chroma_placement}}。
普通播放器显示黑色底板不一定表示透明通道丢失；本次透明验证结果为：{{alpha_validation}}。

## 对齐演奏

- 速度：{{tempo_summary}}。
- 时间零点：{{time_zero_description}}。
- 倒数、片头及额外偏移：{{lead_in_description}}。
- 乐谱时长：{{score_duration_seconds}} 秒；视频时长：{{video_duration_seconds}} 秒。

将下面某个明确的音乐事件对齐到实录中的对应位置，然后检查中段和结尾。
保留乐谱开头的休止；对齐第一个发声音符时，也要计入它距谱视频起点的时间。

| 对齐事件 | 在谱视频中的时间（秒） |
| --- | ---: |
| {{start_landmark}} | {{start_seconds}} |
| {{middle_landmark}} | {{middle_seconds}} |
| {{end_landmark}} | {{end_seconds}} |

如果全程相差固定时间，移动谱视频的起点；如果差距逐渐扩大或变化，检查实录速度及局部对齐。
谱视频与 GP 同速不代表已与真人演奏同步。合成参考音频如有提供，其用途和来源以上表为准；成片按需要保留自己的演奏音频。

## 使用透明主素材

1. 将演奏视频放到主时间线，将 `{{master_file}}` 放到上方的视频层。
2. 保持谱面宽高比，根据主素材尺寸调整大小与位置，避免裁掉品位数字或播放线。
3. 按上面的事件时间对齐，检查开始、中段和结尾，再导出一小段确认效果。

## Mac 版 iMovie：使用绿／蓝幕素材

1. 导入演奏视频和 `{{chroma_file}}`，先把演奏视频拖进主时间线。
2. 将色幕谱视频拖到演奏片段的**上方**，出现绿色「＋」后松手，形成上下两层。
3. 选中上层谱视频，点击预览窗上方的 **“视频叠层设置”**，在下拉菜单中选择 **“绿/蓝幕”**，再点击应用对勾。若边缘残留底色，可少量调整“柔和度”，同时检查细谱线是否仍清晰。[Apple 操作说明](https://support.apple.com/zh-cn/guide/imovie/mov82da1338a/mac)
4. 打开谱视频的裁剪设置，选择 **“适合”**，保留完整画面；谱面位置按本说明的素材规格确认。[Apple 裁剪说明](https://support.apple.com/zh-cn/guide/imovie/mova56757e7e/mac)
5. 按对齐事件移动谱视频起点。根据上表的声音说明处理音量，避免参考音频与演奏音频意外重叠。
6. 播放检查后，选择 **“文件 → 共享 → 文件”**，格式选“视频和音频”，选择需要的分辨率并保存。[Apple 导出说明](https://support.apple.com/zh-cn/guide/imovie/move6e0cb2ad/mac)

如果找不到“绿/蓝幕”，先确认谱视频位于另一个视频片段上方，并且当前选中的是上层谱视频。

## 本次验证与限制

- 谱面及视频时间：{{timing_validation}}。
- 滚动、滑音／连音及画面抽查：{{visual_validation}}。
- 剪辑软件实际导入／合成验证：{{editor_validation}}。
- 已知限制：{{limitations}}。

以上 iMovie 步骤是产物的可选使用方法。生成谱面视频本身不需要 iMovie 或其他剪辑软件。
