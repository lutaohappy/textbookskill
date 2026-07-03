#!/usr/bin/env python3
"""
统一教材生成入口 v4.3：
  python3 build_course.py                        # 生成所有 course YAML
  python3 build_course.py "机器学习经典10大算法"  # 按课程名
  python3 build_course.py courses/xxx.yaml        # 或直接指定 YAML 路径
  python3 build_course.py --generate "深度学习"   # AI 填充内容后生成
"""
import sys, os, glob, argparse, yaml
sys.path.insert(0, os.path.dirname(__file__))
from shared.textbook_generator import generate_all, load_template
from shared.llm import call_llm

YAML_DIR = os.path.join(os.path.dirname(__file__), 'courses')

PLACEHOLDER_TOPICS = {'技术点一', '技术点二', '概念名称'}
PLACEHOLDER_PHRASES = {'任务描述', '知识支撑', '行动指南', '概念定义', '原理说明'}

def find_yaml(keyword):
    for f in os.listdir(YAML_DIR):
        if f.endswith('.yaml') and keyword in f:
            return os.path.join(YAML_DIR, f)
    return None

def _is_placeholder(s):
    if not s:
        return True
    return any(phrase in s for phrase in PLACEHOLDER_PHRASES)

def _needs_generation(sec_data, stype):
    if stype == 'knowledge':
        topics = sec_data.get('topics', {})
        if not topics:
            return True
        for name, tdata in topics.items():
            if name in PLACEHOLDER_TOPICS or _is_placeholder(tdata.get('desc', '')):
                return True
        return False
    elif stype == 'knowledge_theory':
        topics = sec_data.get('topics', {})
        if not topics:
            return True
        for name, tdata in topics.items():
            if name in PLACEHOLDER_TOPICS or _is_placeholder(tdata.get('concept', '')):
                return True
        return False
    return False

def _generate_section_content(chapter, sec_heading, sec_def, tmpl_name, sec_data):
    stype = sec_def.get('type', '')
    budget_ratio = sec_def.get('budget_ratio', 0)
    word_budget = int(chapter['hours'] * 45 * 210 * 0.6 * budget_ratio)

    if stype == 'knowledge':
        system = '''你是职业教育课程内容专家。根据章节信息生成"核心技术讲解"的内容。

输出必须是纯 YAML 格式（不要有 ```yaml 标记），包含 2-3 个技术点：
topics:
  技术点名称A:
    desc: 任务描述（工作中遇到的真实场景和问题，50-80字）
    know: 知识支撑（核心概念、原理、技术参数，150-200字）
    guide: 行动指南（实操建议、注意事项、排错经验，80-120字）
  技术点名称B:
    desc: ...
    know: ...
    guide: ...

技术点名称要具体、有领域特色。内容面向职校学生，语言通俗易懂，多举实际工程例子。'''
        prompt = f'''为以下章节生成"核心技术讲解"内容：

课程模板：{tmpl_name}
章标题：第{chapter['num']}章 {chapter['title']}
学时：{chapter['hours']}
字数预算：{word_budget}字

要求：
1. 技术点名称要具体，直接使用该章涉及的核心技术名
2. desc 写工作中遇到什么实际问题驱动了该技术的学习
3. know 写核心概念和技术原理
4. guide 写实操建议和注意事项
5. 内容面向职校学生，用真实工程案例辅助说明
6. 仅输出 YAML 内容，不含任何额外说明'''

    elif stype == 'knowledge_theory':
        system = '''你是职业教育课程内容专家。根据章节信息生成"知识讲解"内容。

输出必须是纯 YAML 格式（不要有 ```yaml 标记），包含 2-3 个概念：
topics:
  概念名称A:
    concept: 概念定义（50-80字）
    principle: 原理说明（80-120字）
    application: 应用场景（60-100字）
    caution: 注意事项（40-60字）
  概念名称B:
    concept: ...
    principle: ...
    application: ...
    caution: ...'''
        prompt = f'''为以下章节生成"知识讲解"内容：

课程模板：{tmpl_name}
章标题：第{chapter['num']}章 {chapter['title']}
学时：{chapter['hours']}
字数预算：{word_budget}字

要求：
1. 概念名称要具体、有领域特色
2. 内容面向职校学生，条理清晰
3. 仅输出 YAML 内容，不含任何额外说明'''

    elif stype == 'requirement':
        system = '''你是职业教育课程内容专家。根据章节信息生成"需求分析与方案设计"的完整内容。

输出必须是纯 YAML 格式（不要有 ```yaml 标记）：
background: 项目背景描述（文字）
pain_points: 用户痛点（文字）
comparison:
  headers: [对比维度, 方案A, 方案B]
  rows:
    - [维度值, A值, B值]
    - ...
  conclusion: 选型结论（文字）'''
        bg = sec_data.get('background', '')
        bg_prefix = f'已有背景：\n{bg}\n\n' if bg else ''
        prompt = f'''为以下章节生成"需求分析与方案设计"内容：

课程模板：{tmpl_name}
章标题：第{chapter['num']}章 {chapter['title']}
学时：{chapter['hours']}

{bg_prefix}要求：
1. 项目背景需贴合章节主题
2. 对比维度至少4个
3. 结论需明确
4. 仅输出 YAML 内容'''

    else:
        return None

    result = call_llm(prompt, system=system, max_tokens=4096, temperature=0.7)
    result = result.strip()
    if result.startswith('```'):
        lines = result.split('\n', 1)
        if len(lines) > 1:
            result = lines[1]
    if result.endswith('```'):
        result = result.rsplit('\n', 1)[0]

    try:
        data = yaml.safe_load(result)
        if data:
            return data
    except Exception as e:
        print(f'    YAML 解析失败: {e}')
        print(f'    LLM 原始输出:\n{result[:300]}')
    return None

def generate_and_build(yaml_path):
    with open(yaml_path, encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    tmpl = load_template(cfg['template'])
    sec_type_map = {s['heading']: s for s in tmpl.get('sections', [])}

    modified = False
    for ch in cfg['chapters']:
        for sec in ch.get('sections', []):
            heading = sec['heading']
            sec_def = sec_type_map.get(heading, {})
            stype = sec_def.get('type', '')
            if stype not in ('knowledge', 'knowledge_theory', 'requirement'):
                continue
            if not _needs_generation(sec['data'], stype):
                continue

            print(f'  🤖 第{ch["num"]}章 {heading}...')
            new_data = _generate_section_content(ch, heading, sec_def, cfg['template'], sec.get('data', {}))
            if new_data:
                if stype == 'requirement':
                    sec['data'] = new_data
                else:
                    for k, v in new_data.items():
                        sec['data'][k] = v
                modified = True
                topic_count = len(new_data.get('topics', {})) if 'topics' in new_data else 0
                print(f'    ✅ 已生成 {topic_count} 个技术点')
            else:
                print(f'    ⚠️ 生成失败，跳过')

    if modified:
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False, width=120)
        print(f'\n✅ YAML 已更新: {yaml_path}')

    generate_all(yaml_path)

def main():
    parser = argparse.ArgumentParser(description='教材生成工具')
    parser.add_argument('targets', nargs='*', help='课程名或 YAML 路径')
    parser.add_argument('--generate', action='store_true', help='AI 自动填充章节内容后生成')
    args = parser.parse_args()

    if args.generate:
        targets = []
        if args.targets:
            for a in args.targets:
                if a.endswith('.yaml'):
                    if os.path.exists(a):
                        targets.append(a)
                else:
                    found = find_yaml(a)
                    if found:
                        targets.append(found)
                    else:
                        print(f'未找到匹配课程: {a}')
        else:
            targets = sorted(glob.glob(os.path.join(YAML_DIR, '*.yaml')))
        for t in targets:
            generate_and_build(t)
        return

    targets = args.targets
    if targets:
        yamls = []
        for a in targets:
            if a.endswith('.yaml'):
                if os.path.exists(a):
                    yamls.append(a)
            else:
                found = find_yaml(a)
                if found:
                    yamls.append(found)
                else:
                    print(f'未找到匹配课程: {a}')
        for y in yamls:
            generate_all(y)
    else:
        yamls = sorted(glob.glob(os.path.join(YAML_DIR, '*.yaml')))
        for y in yamls:
            print(f'\n--- {os.path.basename(y)} ---')
            generate_all(y)

if __name__ == '__main__':
    main()
