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


def test_normal_hints_do_not_disclose_complete_passing_answers(runtime):
    from trainer.content.loader import load_chapters
    from trainer.grading.service import grade_submission
    from trainer.contracts import QueryFailure
    executor=QueryExecutor(runtime)
    leaked=[]
    for chapter in load_chapters(runtime.paths.content):
        for problem in chapter['problems']:
            for hint in problem['hints']:
                try:
                    if grade_submission(executor,problem,hint).status=='passed': leaked.append(problem['id'])
                except QueryFailure: pass
    assert leaked==[],f'Normal hints reveal answers: {leaked}'
