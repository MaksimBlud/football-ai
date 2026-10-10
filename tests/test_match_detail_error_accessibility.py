"""Accessible error state for the standalone match-detail page."""

from pathlib import Path
import re
import shutil
import subprocess

import pytest


PAGE = Path("static/match.html")


def test_match_detail_error_is_announceable_and_focusable():
    html = PAGE.read_text(encoding="utf-8")
    assert '<div id="error" class="error" role="alert" tabindex="-1"></div>' in html
    assert ".error:focus{" in html


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js unavailable")
def test_match_detail_error_focuses_without_exposing_stale_content():
    html = PAGE.read_text(encoding="utf-8")
    script = re.search(r"<script>(.*?)</script>", html, re.S)
    assert script is not None
    harness = r"""
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = require('node:fs').readFileSync(0, 'utf8');

async function check(search, fetchImpl, expected) {
  const elements = {
    loading: {hidden: false},
    content: {hidden: false},
    error: {style: {display: 'none'}, textContent: '',
      focus() {this.focused = true;}}
  };
  const document = {getElementById: id => elements[id]};
  vm.runInNewContext(source, {
    document, location: {search}, URLSearchParams, fetch: fetchImpl
  });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(elements.loading.hidden, true);
  assert.equal(elements.content.hidden, true);
  assert.equal(elements.error.style.display, 'block');
  assert.equal(elements.error.focused, true);
  assert.match(elements.error.textContent, expected);
}

(async () => {
  await check('', () => {throw Error('fetch must not run');}, /идентификатор/);
  await check('?id=fixture-1', () => Promise.reject(Error('offline')), /Не удалось загрузить/);
})().catch(err => {console.error(err); process.exitCode = 1;});
"""
    result = subprocess.run(
        ["node", "-e", harness],
        input=script.group(1),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
