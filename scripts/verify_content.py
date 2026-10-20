from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import pytest
raise SystemExit(pytest.main(['backend/tests/integration/test_all_content.py','-q']))
