#!/usr/bin/env python3
"""
Step 2：目录摘要 → YAML 骨架
   python3 generate_yaml.py {课程}_目录摘要_{ts}.md
→ 读取目录摘要，按模板生成 YAML 骨架（含空内容结构）
→ 手动填充各章节内容后进入 Step 3
"""
import sys, os, re, yaml
sys.path.insert(0, os.path.dirname(__file__))
from shared.textbook_generator import TEMPLATE_DIR, load_template, _words, timestamp

YAML_DIR = os.path.join(os.path.dirname(__file__), 'courses')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def parse_toc_md(toc_path):
    """解析目录摘要.md，提取课程名、模板、章节"""
    with open(toc_path, encoding='utf-8') as f:
        text = f.read()

    course_m = re.search(r'# 《(.+?)》', text)
    course = course_m.group(1) if course_m else ''

    tmpl_m = re.search(r'模板[：:]\s*(\S+)', text)
    template_name = tmpl_m.group(1) if tmpl_m else ''

    chapters = []
    pattern = re.compile(r'^## 第(\d+)章\s+(.+?)[（(](\d+)学时[）)]', re.MULTILINE)
    for m in pattern.finditer(text):
        chapters.append({
            'num': int(m.group(1)),
            'title': m.group(2).strip(),
            'hours': int(m.group(3)),
        })
    return course, template_name, chapters

def create_empty_data(stype):
    if stype == 'case':
        return {'title': '案例标题', 'body': '案例正文（描述业务背景、数据特征、方案实施和效果）'}
    elif stype == 'knowledge':
        return {
            'topics': {
                '技术点一': {'desc': '任务描述：在工作中遇到的场景和问题', 'know': '知识支撑：核心概念、原理和参数含义', 'guide': '行动指南：实操建议和注意事项'},
                '技术点二': {'desc': '任务描述', 'know': '知识支撑', 'guide': '行动指南'},
            },
            'code_examples': [],
            'diagrams': [{'title': '请替换为示意图标题（每章至少1张SVG配图）', 'path': '请替换为SVG文件绝对路径，如: /课程目录/图/chX_XX_描述.svg'}],
        }
    elif stype == 'design':
        return {'title': '方案标题', 'body': '设计任务：项目背景、数据说明、任务要求和交付物'}
    elif stype == 'comparison':
        return {'title': '对比标题', 'headers': ['维度', '方案A', '方案B'], 'rows': [['维度值', 'A值', 'B值']], 'recommendation': '选型建议'}
    elif stype == 'experiment':
        return {'background': '实验背景', 'steps': ['步骤1', '步骤2', '步骤3'], 'verification': '验证方法'}
    elif stype == 'requirement':
        return {'background': '项目背景', 'pain_points': '用户痛点', 'comparison': {'headers': ['维度', '方案A', '方案B'], 'rows': [], 'conclusion': '选型结论'}}
    elif stype == 'self_test':
        return {'test': [], 'think': [], 'practice': ''}
    elif stype == 'knowledge_theory':
        return {'topics': {'概念名称': {'concept': '概念定义', 'principle': '原理说明', 'application': '应用场景', 'caution': '注意事项'}}}
    return {}

def create_yaml_skeleton(course, template_name, chapters):
    tmpl = load_template(template_name)

    yaml_data = {
        'template': template_name,
        'course': course,
        'chapters': [],
    }

    for ch in chapters:
        ch_data = {
            'num': ch['num'],
            'title': ch['title'],
            'hours': ch['hours'],
            'theory_ratio': 0.6,
            'sections': [],
        }
        for sec_def in tmpl['sections']:
            stype = sec_def['type']
            sec_data = create_empty_data(stype)
            ch_data['sections'].append({
                'heading': sec_def['heading'],
                'data': sec_data,
            })
        yaml_data['chapters'].append(ch_data)

    return yaml_data

def main():
    args = sys.argv[1:]
    if not args:
        print('用法:')
        print('  python3 generate_yaml.py {课程}_目录摘要_{ts}.md    # 从目录摘要生成 YAML 骨架')
        return

    toc_path = args[0]
    if not os.path.exists(toc_path):
        print(f'文件不存在: {toc_path}')
        return
    course, template_name, chapters = parse_toc_md(toc_path)
    if not course or not chapters:
        print('未能解析目录摘要，请检查格式。')
        return
    print(f'课程: {course}, 模板: {template_name}, {len(chapters)} 章')
    existing_path = os.path.join(YAML_DIR, f'{course}.yaml')
    if os.path.exists(existing_path):
        yn = input(f'YAML 已存在: {existing_path}。覆盖? (y/N): ').strip().lower()
        if yn != 'y':
            print('跳过。')
            return
    yaml_data = create_yaml_skeleton(course, template_name, chapters)
    out_name = f'{course}.yaml'

    os.makedirs(YAML_DIR, exist_ok=True)
    out_path = os.path.join(YAML_DIR, out_name)
    with open(out_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)
    print(f'\n✅ {out_path}')
    print(f'⚠️  注意：每个章节 Knowledge 的 diagrams 字段含占位条目，请替换为实际SVG路径（每章至少1张配图）')
    print(f'   使用 baoyu-diagram skill 生成配图SVG，保存到 {course}/图/ 目录')
    print(f'Step 3: python3 build_course.py')

if __name__ == '__main__':
    main()
