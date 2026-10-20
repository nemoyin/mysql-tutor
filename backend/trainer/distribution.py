from pathlib import Path
import shutil


def validate_distribution(root: Path):
    required={'runtime/mysql/bin/mysqld.exe':'MySQL 运行文件',
              'MySQL学习工具.exe':'启动程序','web/index.html':'学习页面',
              'content/chapters/01.json':'离线课程','runtime/manifest.json':'运行环境清单'}
    for relative,label in required.items():
        if not (root/relative).is_file(): raise RuntimeError(f'缺少{label}：{relative}')


def assemble_distribution(source: Path, frozen: Path, output: Path):
    if output.exists(): raise RuntimeError('输出目录已存在，请选择新的输出目录。')
    output.mkdir(parents=True)
    shutil.copy2(frozen/'SQLStudio.exe',output/'MySQL学习工具.exe')
    shutil.copytree(frozen/'_internal',output/'_internal')
    shutil.copytree(source/'runtime/mysql',output/'runtime/mysql')
    shutil.copy2(source/'runtime/manifest.json',output/'runtime/manifest.json')
    shutil.copytree(source/'content',output/'content')
    shutil.copytree(source/'frontend/dist',output/'web')
    validate_distribution(output)
