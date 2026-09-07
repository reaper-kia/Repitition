import re
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import String

from src.modules.users.infra.models import UserModel


PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.unit
def test_user_model_has_role_column_with_required_shape() -> None:
    columns = UserModel.__table__.columns

    assert "role" in columns
    assert "is_admin" not in columns

    role = columns["role"]
    assert isinstance(role.type, String)
    assert role.type.length == 32
    assert role.nullable is False
    assert role.index is True


@pytest.mark.e2e
def test_clean_migration_creates_role_and_role_index() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head", "--sql"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output

    normalized_sql = " ".join(output.lower().split())
    assert re.search(
        r"\brole varchar\(32\)(?: default '[^']+')? not null\b",
        normalized_sql,
    )
    assert "create index ix_users_role on users (role)" in normalized_sql
    assert "is_admin" not in normalized_sql
