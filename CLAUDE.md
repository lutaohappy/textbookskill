# Vocational Course Generator

This repository contains a skill for automated vocational course curriculum development.

## Usage

Load the skill in Claude Code:

```
/c Skill vocational-course-generator
```

Or reference the skill file directly:

```
Load the skill at skill/SKILL.md and follow its instructions.
```

## Requirements

```bash
pip install -r requirements.txt
```

## Workflow

1. **Generate TOC**: `python3 skill/scripts/generate_toc.py`
2. **Generate YAML** from draft: `python3 skill/scripts/generate_yaml.py <目录摘要>.md`
3. **Build course**: `python3 skill/scripts/build_course.py <course>.yaml`

See `skill/SKILL.md` for full instructions.
