---
name: vocational-course-generator
description: >
  Template-driven vocational course curriculum development skill. Three-step workflow:
  (1) Generate TOC with diagram planning, (2) Generate YAML skeleton, (3) Build course
  textbooks (docx) with embedded SVG diagrams. Supports mixed-type, project-based, and
  theory-based templates. Each chapter gets auto-planned diagrams (MLP/CNN/YOLO/LSTM/GAN
  architecture, deployment topology, etc.). Output: docx textbooks, hour allocation tables,
  and implementation plans — all with SVG→PNG diagram embedding.
version: 4.3
---

# 职业教育课程开发 Skill v4.3 —— 模板驱动 + YAML 数据分离

> 核心理念：**三步流程（设计目录 → 生成 YAML → 构建教材），课程内容以 YAML 文件定义，通过模板驱动渲染 docx 和配套文档**，面向职校学生的案例教学、方案设计、核心技术讲解和技术选型。

---

---

## Step 1：设计目录

## 架构概览：模板驱动 + YAML 数据分离

```
                    ┌─────────────┐
                    │  课程模板    │  ← shared/templates/（3 种类型）
                    └──────┬──────┘
                           │ 定义章节结构、板块分配
                    ┌──────▼──────┐
                    │  YAML 数据   │  ← courses/（课程独立内容）
                    │ ┌─────────┐ │
                    │ │ 章节1    │ │
                    │ │ 章节2    │ │
                    │ │ 章节3    │ │
                    │ └─────────┘ │
                    └──────┬──────┘
                           │ 模板驱动渲染
                    ┌──────▼──────┐
                    │ 教材 docx   │ → docx 输出（含 SVG→PNG 配图）
                    │ TOC md      │ → 字数分配参考
                    │ 课时分配表  │ → 教学进度规划
                    │ 实施方案    │ → 教学实施参考
                    └─────────────┘
```

## 三步流程详解

### Step 1：设计目录（generate_toc.py）
- 方式 A（交互）：python3 generate_toc.py — 输入课程名、总学时、选模板、逐章录入
- 方式 B（AI）：python3 generate_toc.py --auto --course "课程名" --hours 56 --template 混合型
- 每章自动推荐 1 张 SVG 配图（类型+内容+路径）
- 输出 `{课程名}_目录摘要_{ts}.md`

### Step 2：生成 YAML 骨架（generate_yaml.py）
- python3 generate_yaml.py "{课程名}_目录摘要_{ts}.md"
- 读取目录摘要，按模板生成 YAML 骨架（含空内容结构）
- 手动填充各章节内容后进入 Step 3
- 输出到 `courses/{课程名}.yaml`

### Step 3：构建教材（build_course.py）
- python3 build_course.py — 生成 courses/ 下所有课程
- python3 build_course.py "课程名" — 按课程名匹配
- python3 build_course.py --generate "课程名" — AI 自动填充章节内容后生成
- 输出：教材 docx、目录字数分配 md、课时分配表 docx、实施方案 docx

## 配图说明
每章至少配 1 张 SVG 图。用 baoyu-diagram skill 生成 SVG，路径在 TOC 中已自动规划。cairosvg 在运行时自动将 SVG 转为 PNG 嵌入 docx。

## 环境变量
- LLM_API_KEY — API Key（也支持 ANTHROPIC_API_KEY / OPENAI_API_KEY）
- LLM_MODEL — 模型名（默认 claude-sonnet-4-20250514）
- LLM_BASE_URL — API 地址（默认 https://api.anthropic.com/v1）
