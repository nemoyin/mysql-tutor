import pytest


def test_profiles_normalize_and_reject_duplicates(tmp_path):
    from trainer.learning.store import LearningStore
    store = LearningStore(tmp_path/'learning.db')
    a=store.create_profile(' 小林 ')
    assert a['nickname']=='小林'
    with pytest.raises(ValueError): store.create_profile('小林')
    with pytest.raises(ValueError): store.create_profile('  ')


def test_drafts_revision_and_profile_isolation(tmp_path):
    from trainer.learning.store import LearningStore
    path=tmp_path/'learning.db'
    store=LearningStore(path)
    a=store.create_profile('甲')['id']; b=store.create_profile('乙')['id']
    store.save_draft(a,'01-01','SELECT 1',2)
    with pytest.raises(ValueError): store.save_draft(a,'01-01','older',1)
    assert store.get_draft(b,'01-01')['sql']==''
    assert store.get_draft(a,'01-02')['sql']==''
    assert LearningStore(path).get_draft(a,'01-01')['sql']=='SELECT 1'


def test_answer_reveal_survives_restart_and_preserves_first_completion(tmp_path):
    from trainer.learning.store import LearningStore
    path=tmp_path/'learning.db'; store=LearningStore(path)
    a=store.create_profile('甲')['id']
    store.reveal_answer(a,'01-01')
    store.record_grade(a,'01-01','passed')
    store=LearningStore(path)
    store.record_grade(a,'01-01','passed')
    assert store.progress(a)['01-01']['mode']=='assisted'
    assert store.progress(a)['01-01']['answer_seen']


def test_reset_preserves_drafts_history_and_other_profiles(tmp_path):
    from trainer.learning.store import LearningStore
    store=LearningStore(tmp_path/'learning.db')
    a=store.create_profile('甲')['id']; b=store.create_profile('乙')['id']
    for pid in [a,b]:
        store.save_draft(pid,'01-01','SELECT 1',1)
        store.record_grade(pid,'01-01','passed')
        store.add_history(pid,'01-01','SELECT 1','ok')
    store.reset_progress(a)
    assert store.progress(a)=={}
    assert store.progress(b)['01-01']['mode']=='independent'
    assert store.get_draft(a,'01-01')['sql']=='SELECT 1'
    assert len(store.history(a))==1
