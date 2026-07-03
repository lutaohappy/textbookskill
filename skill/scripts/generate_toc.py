#!/usr/bin/env python3
"""
Step 1：生成目录摘要
   交互模式：python3 generate_toc.py
   AI 模式：python3 generate_toc.py --auto --course "深度学习" --hours 56 --template 混合型
-> 输出 {课程名}_目录摘要_{ts}.md（含写作任务描述，可修改确认后进入 Step 2）
"""
import sys, os, argparse, yaml
sys.path.insert(0, os.path.dirname(__file__))
from shared.textbook_generator import TEMPLATE_DIR, load_template, _words, timestamp
from shared.llm import call_llm
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEMPLATES = sorted(f.replace('.yaml', '') for f in os.listdir(TEMPLATE_DIR) if f.endswith('.yaml'))

def ask(question, default=''):
    prompt = f'{question} [{default}]: ' if default else f'{question}: '
    val = input(prompt).strip()
    return val if val else default

def select(question, options):
    print(f'\n{question}')
    for i, opt in enumerate(options, 1):
        print(f'  {i}. {opt}')
    while True:
        try:
            idx = int(input(f'  选择 (1-{len(options)}): ').strip())
            if 1 <= idx <= len(options):
                return options[idx - 1]
        except ValueError:
            pass

def _llm_generate_chapters(course, total_hours, tmpl):
    tmpl_sections = '\n'.join(f'  - {s["heading"]}（类型：{s["type"]}）' for s in tmpl['sections'])
    prompt = f'''为《{course}》课程设计一个完整的章节目录。

课程参数：
- 名称：{course}
- 总学时：{total_hours}
- 模板：{tmpl['name']}

每章结构需包含以下板块：
{tmpl_sections}

要求：
1. 根据总学时合理划分章节数量（通常是总学时/2~总学时/6，每章4-12学时）
2. 每章标题要具体、有领域特色，避免泛泛的"基础知识""概述"
3. 输出格式：每行一个章节，用 | 分隔：章节号|标题|学时|章概述（20字内）

示例输出：
1|深度学习初探——手写数字识别|12|从零搭建第一个神经网络
2|图像识别——卷积神经网络实战|10|理解卷积与池化在视觉任务中的应用

注意：只输出上述格式，不要有任何额外说明。总学时加起来要刚好等于{total_hours}。'''

    system = '你是职业教育课程设计专家。请严格按照格式输出章节规划，不要输出任何额外文字。'
    result = call_llm(prompt, system=system).strip()

    chapters = []
    for line in result.split('\n'):
        line = line.strip()
        if not line or '|' not in line:
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 3:
            try:
                ch_num = int(parts[0])
                ch_title = parts[1]
                ch_hours = int(parts[2])
                chapters.append({'num': ch_num, 'title': ch_title, 'hours': ch_hours})
            except ValueError:
                continue

    if not chapters:
        print('LLM 返回格式异常，请重试。原始输出：')
        print(result[:500])
        sys.exit(1)

    total = sum(ch['hours'] for ch in chapters)
    if total != total_hours:
        diff = total_hours - total
        if len(chapters) > 0:
            chapters[-1]['hours'] += diff

    return chapters

def generate_toc_auto(course, total_hours, tmpl_name):
    print(f'🤖 AI 模式：正在为《{course}》生成目录...')
    tmpl = load_template(tmpl_name)
    chapters = _llm_generate_chapters(course, total_hours, tmpl)
    for ch in chapters:
        print(f'  第{ch["num"]}章 {ch["title"]}（{ch["hours"]}学时）')
    print(f'\n共 {len(chapters)} 章，{sum(ch["hours"])} 学时')

    ts = timestamp()
    md = _render_toc_md(course, total_hours, tmpl, chapters, BASE_DIR)
    out_name = f'{course}_目录摘要_{ts}.md'
    out_path = os.path.join(out_name)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f'\n✅ {out_path}')
    print(f'\nStep 2: 确认后运行 python3 generate_yaml.py "{out_path}"')

def generate_toc_interactive():
    print('═══ 目录摘要生成 ═══\n')

    course = ask('课程名称', '新课程')
    total_hours = int(ask('总学时', '56'))
    tmpl_name = select('选择课程模板', TEMPLATES)
    tmpl = load_template(tmpl_name)

    chapters = []
    ch_num = 1
    remaining = total_hours
    print(f'\n逐章录入（剩余 {remaining} 学时，输入 0 结束）：')
    while remaining > 0:
        title = ask(f'第{ch_num}章标题', f'第{ch_num}章')
        hours = int(ask(f'  学时（剩余 {remaining}）', str(min(6, remaining))))
        if hours == 0:
            break
        chapters.append({'num': ch_num, 'title': title, 'hours': hours})
        ch_num += 1
        remaining -= hours
        if remaining <= 0:
            break

    if not chapters:
        print('未输入任何章节。')
        return

    ts = timestamp()
    md = _render_toc_md(course, total_hours, tmpl, chapters, BASE_DIR)
    out_name = f'{course}_目录摘要_{ts}.md'
    out_path = os.path.join(out_name)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(md)
    print(f'\n✅ {out_path}')
    print(f'\nStep 2: 确认后运行 python3 generate_yaml.py "{out_path}"')

def _suggest_diagram(title):
    dg_type_map = [
        (['生成', '风格', 'GAN', '对抗'], '架构图', '生成器/判别器结构及对抗训练流程'),
        (['分析', '情感', '文本', 'NLP', '语言'], '架构图', '序列模型结构，Embedding→编码→分类'),
        (['识别', '分类', '检测', '目标'], '架构图', '网络/模型结构示意，标注各层输入输出'),
        (['初探', '基础', '入门', '原理'], '架构图', '网络结构示意，含层次和连接关系'),
        (['部署', '服务', '上线', '运维'], '部署架构图', '系统组件关系、调用链路、数据流向'),
        (['综合', '实战', '项目'], '流程图/架构图', '完整业务流程或系统架构'),
    ]
    for keywords, dg_type, content in dg_type_map:
        if any(kw in title for kw in keywords):
            return dg_type, content
    return '流程图', '核心流程步骤示意，含输入输出'

def _render_toc_md(course, total_hours, tmpl, chapters, base_path=''):
    lines = [f'# 《{course}》目录摘要\n---\n']
    lines.append(f'总学时：{total_hours} | 模板：{tmpl["name"]}\n\n')
    lines.append('> 此为经人机交互确定的目录边界。确认后进入 Step 2 生成 YAML。\n')
    lines.append('> ⚠️ 每章至少需1张SVG配图（路径已自动生成），用 baoyu-diagram skill 按路径生成。\n\n')

    for ch in chapters:
        tb = _words(ch['hours'], 0.6)
        lines.append(f'## 第{ch["num"]}章 {ch["title"]}（{ch["hours"]}学时，{tb}字）\n')
        h2 = 0
        for sec in tmpl['sections']:
            h2 += 1
            budget = int(tb * sec.get('budget_ratio', 0))
            lines.append(f'- {h2} {sec["heading"]}（{budget}字）\n')
            lines.append(f'  - **写作任务**：{sec["write_task"]}\n')

            if sec['type'] == 'objectives':
                sub = int(budget / 3)
                for i, h3 in enumerate(['知识目标', '技能目标', '素养目标']):
                    lines.append(f'  - {h2}.{i+1} {h3}（{sub}字）\n')
            elif sec['type'] == 'knowledge':
                lines.append(f'  - {h2}.1 技术点一（{budget}字）\n')
            elif sec['type'] == 'self_test':
                lines.append(f'  - {h2}.1 一、选择题（{int(budget*0.4)}字）\n')
                lines.append(f'  - {h2}.2 二、思考题（{int(budget*0.3)}字）\n')
                lines.append(f'  - {h2}.3 三、实操题（{int(budget*0.3)}字）\n')
            elif sec['type'] in ('case', 'design'):
                lines.append(f'  - {h2}.1 {sec["heading"]}（{budget}字）\n')
            else:
                lines.append(f'  - {h2}.1 {sec["heading"]}（{budget}字）\n')

        h2 += 1
        dg_type, dg_content = _suggest_diagram(ch['title'])
        lines.append(f'- {h2} 🎨 配图规划\n')
        lines.append(f'  - **建议配图类型**：{dg_type}\n')
        lines.append(f'  - **建议配图内容**：{dg_content}\n')
        fig_name = dg_type.replace('/', '_')
        fig_dir = os.path.join(base_path, course, '图')
        fig_path = os.path.join(fig_dir, f'ch{ch["num"]}_01_{fig_name}.svg')
        lines.append(f'  - **输出路径**：{fig_path}\n')
        lines.append(f'  - **生成工具**：使用 baoyu-diagram skill 创建SVG\n')
        lines.append('\n')
    return ''.join(lines)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='生成课程目录摘要')
    parser.add_argument('--auto', action='store_true', help='AI 自动生成模式')
    parser.add_argument('--course', default='', help='课程名称')
    parser.add_argument('--hours', type=int, default=56, help='总学时')
    parser.add_argument('--template', default='混合型', help=f'课程模板（可选：{", ".join(TEMPLATES)}）')
    args = parser.parse_args()

    if args.auto:
        if not args.course:
            print('--auto 模式需要 --course 参数')
            sys.exit(1)
        generate_toc_auto(args.course, args.hours, args.template)
    else:
        generate_toc_interactive()
