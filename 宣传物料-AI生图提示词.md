# 宣传物料 AI 生图提示词

> 用于 PPT 封面/宣传物料，需要拿去即梦、豆包、通义万相或 Midjourney 这类外部工具里跑——我这边没有接入图像生成模型，不能直接产出图片。
> 基调控制：题材是"应急"，要避免生成看起来像真实事故/伤亡现场的画面（不严肃、可能引起不适），全部往"科技感、专业、平静"的概念插画方向走，不要写实灾难场景。风格上也刻意不模仿参考材料里那种高饱和水晶质感科幻UI——我们希望画面显得可信、专业，而不是游戏宣传片。

## 一、封面主图：复兴岛大型活动 × 应急科技

**中文提示词（即梦 / 豆包 / 通义万相）**：
```
复兴岛大型户外演出活动航拍全景，黄昏蓝调天空，舞台灯光与观众区灯光星星点点，
现场上空叠加半透明的数字化监测光网——细线连接的光点标出通道、出入口、人员密度区域，
科技感克制不浮夸，写实摄影质感为主，局部叠加淡蓝色数据可视化效果，
整体氛围专业、沉稳、可信，适合政府/高校产学研项目宣传封面，
16:9 宽幅构图，电影级摄影感，无文字，无人脸特写
```

**English prompt（Midjourney）**：
```
Aerial panoramic view of a large outdoor concert venue at dusk on an island in Shanghai,
warm stage lights and audience area glowing against a deep blue twilight sky,
a subtle translucent digital overlay of thin connected light nodes above the venue
marking passages, entrances and crowd-density zones,
restrained sci-fi tech overlay, mostly photorealistic cinematic photography,
faint cyan data-visualization accents, professional and trustworthy mood,
suitable for a government / university research project cover slide,
16:9 wide composition, cinematic lighting, no text, no close-up faces --ar 16:9 --style raw
```

## 二、人机协同处置：人是主角，AI 是助手

**中文提示词**：
```
夜间大型活动现场，一名应急指挥人员站在临时指挥点前，手持对讲机，
面前有一块半透明悬浮数据面板，显示通道状态和任务清单的简洁图标（不要具体文字），
面板光效柔和、克制，不遮挡人物，构图上人物是画面主体、数据面板是辅助元素，
写实摄影风格，专业制服，冷静专注的神情，背景可见活动现场灯光虚化，
整体传达"人在决策、科技辅助"而不是"机器自主行动"，
16:9 构图，电影感打光，无文字
```

**English prompt**：
```
A calm on-site emergency commander at night during a large outdoor event,
holding a radio, standing in front of a soft translucent floating data panel
showing simple abstract icons for passage status and task lists (no readable text),
the panel light is subtle and does not overpower the human figure,
the person is clearly the主体 of the composition, the data panel is a supporting element,
photorealistic, professional uniform, calm and focused expression,
blurred event lighting in the background,
conveys "human decides, technology assists" rather than autonomous machines,
16:9 composition, cinematic lighting, no text --ar 16:9 --style raw
```

## 三、Ontology 本体基座：抽象概念图（技术方案类 PPT 插图）

**中文提示词**：
```
抽象科技概念插画，深蓝色背景，中央是一个由发光节点和连接线组成的知识网络结构，
节点大小不一，部分节点标注为简单几何图形（圆形、方形、六边形）代表不同类型的对象，
节点之间的连线粗细不一代表关系强弱，避免使用文字，
整体色调克制在深蓝、青色、少量暖色点缀，不使用高饱和紫色或粉色霓虹效果，
风格偏"数据可视化"而非"游戏UI"，干净、简洁、专业，
适合技术方案文档封面或分隔页，16:9 或 1:1 构图均可，无文字
```

**English prompt**：
```
Abstract technology concept illustration, deep navy background,
a central knowledge-graph structure made of glowing nodes and connecting lines,
nodes vary in size, some rendered as simple geometric shapes (circle, square, hexagon)
representing different object types, line thickness varies to represent relationship strength,
restrained color palette of deep blue and teal with sparse warm accent points,
avoid high-saturation purple or pink neon effects,
data-visualization aesthetic rather than video-game UI, clean and minimal, professional,
suitable as a technical document cover or section-divider image,
16:9 or 1:1 composition, no text --style raw
```

## 使用建议

- 先跑第一张（封面主图）看效果，三个工具（即梦/豆包/通义万相/Midjourney）出来的风格差异较大，建议同一个提示词跑2-4张选一张最合适的，不要指望一次就中。
- 如果生成结果偏"游戏感"太重、光效太夸张，在提示词里加一句"减少光效强度，更偏向真实摄影"（reduce glow intensity, more photorealistic）通常能收敛回来。
- 生成后如果要裁成 PPT 封面，注意关键内容不要贴边，视觉热点区域（人物、发光节点）尽量安排在画面中间偏上，方便后续叠加标题文字。
