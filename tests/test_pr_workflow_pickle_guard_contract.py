from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ROOT / ".github/workflows/research-pr-validation.yml",
    ROOT / ".github/workflows/serie-a-pr-validation.yml",
)


def test_research_and_serie_a_pickle_guards_require_a_real_merge_base():
    for path in WORKFLOWS:
        source = path.read_text(encoding="utf-8")
        assert "fetch-depth: 0" in source
        assert "BASE_REF: ${{ github.base_ref || 'main' }}" in source
        assert 'git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"' in source
        assert 'git merge-base "refs/remotes/origin/${BASE_REF}" HEAD' in source
        assert "FAIL_CLOSED: unable to determine merge base for production artifact diff" in source
        assert 'git diff --name-only "$BASE_COMMIT" HEAD' in source
        assert "FAIL_CLOSED: unable to inspect changed files for production artifact diff" in source
        assert "origin/main...HEAD" not in source
        assert 'git diff --name-only "origin/' not in source
        assert "grep -F '.pkl'" in source
