from trainer.query.executor import QueryExecutor


def test_all_content_is_complete_and_answers_work(runtime):
    from trainer.content.loader import load_chapters
    from trainer.grading.service import grade_submission
    chapters = load_chapters(runtime.paths.content)
    assert len(chapters)==8
    problems=[p for c in chapters for p in c['problems']]
    assert len(problems)==40
    assert len({p['id'] for p in problems})==40
    executor=QueryExecutor(runtime)
    equivalents=0
    for p in problems:
        assert p['lesson'] and p['example_sql'] and len(p['hints'])>=2 and p['prompt']
        assert grade_submission(executor,p,p['answer_sql']).status=='passed',p['id']
        assert grade_submission(executor,p,p['wrong_sql']).status!='passed',p['id']
        for sql in p.get('equivalent_sql',[]):
            assert grade_submission(executor,p,sql).status=='passed',p['id']
            equivalents+=1
    assert equivalents>=10
