from pathlib import Path
import pytest


def test_missing_runtime_is_not_silently_replaced(tmp_path):
    from trainer.distribution import validate_distribution
    with pytest.raises(RuntimeError,match='MySQL'):
        validate_distribution(tmp_path)


def test_distribution_assembly_excludes_learner_data(tmp_path):
    from trainer.distribution import assemble_distribution
    source=tmp_path/'source'; frozen=tmp_path/'frozen'; output=tmp_path/'out'
    for directory in [source/'runtime/mysql/bin',source/'content/chapters',source/'frontend/dist/assets',source/'data',frozen/'_internal']:
        directory.mkdir(parents=True)
    (source/'runtime/mysql/bin/mysqld.exe').write_text('mysql')
    (source/'content/chapters/01.json').write_text('{}')
    (source/'frontend/dist/index.html').write_text('<html/>')
    (source/'data/secret').write_text('not for distribution')
    (source/'runtime/manifest.json').write_text('{}')
    (frozen/'SQLStudio.exe').write_text('app')
    assemble_distribution(source,frozen,output)
    assert (output/'MySQL学习工具.exe').read_text()=='app'
    assert not (output/'data').exists()
    assert (output/'runtime/mysql/bin/mysqld.exe').exists()
