from pathlib import Path
import json


def load_catalog():
    path = Path(__file__).resolve().parents[1] / 'dataset/catalog.json'
    return json.loads(path.read_text(encoding='utf-8'))


def load_chapters(content_root: Path):
    return [json.loads(file.read_text(encoding='utf-8')) for file in sorted((content_root/'chapters').glob('*.json'))]


def load_problem(content_root: Path, problem_id: str):
    for chapter in load_chapters(content_root):
        for problem in chapter['problems']:
            if problem['id']==problem_id:
                return problem
    raise ValueError('练习不存在，请从课程目录重新选择。')


def public_problem(problem):
    hidden={'answer_sql','wrong_sql','equivalent_sql','hints'}
    return {k:v for k,v in problem.items() if k not in hidden}
