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
    assert '<div id="loading" class="loading" role="status" aria-live="polite" aria-atomic="true">' in html
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
  await check('?id=' + 'a'.repeat(161), () => {throw Error('fetch must not run');}, /идентификатор/);
  await check('?id=fixture-1', () => Promise.reject(Error('offline')), /Не удалось загрузить/);
  await check('?id=fixture-1', () => Promise.resolve({ok:false,status:503}), /HTTP 503/);
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


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js unavailable")
def test_match_detail_incomplete_success_payload_is_accessible_error():
    """Incomplete HTTP 200 must show a focusable error rather than a JS TypeError."""
    html = PAGE.read_text(encoding="utf-8")
    script = re.search(r"<script>(.*?)</script>", html, re.S)
    assert script is not None
    harness = r"""
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = require('node:fs').readFileSync(0, 'utf8');
async function check(payload, expected) {
  const elements = {
    loading: {hidden:false}, content: {hidden:false},
    error: {style:{display:'none'}, textContent:'', focus() {this.focused=true;}}
  };
  vm.runInNewContext(source, {
    document: {getElementById: id => elements[id]},
    location: {search:'?id=fixture-1'}, URLSearchParams,
    fetch: async () => ({ok:true,json:async () => payload})
  });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(elements.loading.hidden, true);
  assert.equal(elements.content.hidden, true);
  assert.equal(elements.error.style.display, 'block');
  assert.equal(elements.error.focused, true);
  assert.match(elements.error.textContent, expected);
  assert.doesNotMatch(elements.error.textContent, /TypeError|Cannot read properties/);
}
(async () => {
  await check({schema_version:'product-market-view.v1',match:null}, /Ответ сервера не содержит полных данных матча/);
  await check({schema_version:'product-market-view.v1',match:{
    match:{home_team:'Home',away_team:'Away'},
    markets:{'1x2':{selections:[]}}
  }}, /Ответ сервера не содержит полных данных матча/);
  await check(null, /Неожиданная схема/);
})().catch(err => {console.error(err);process.exitCode=1;});
"""
    result = subprocess.run(
        ["node", "-e", harness], input=script.group(1),
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
