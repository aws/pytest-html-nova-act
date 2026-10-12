# Copyright 2025 Amazon Inc

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import html
from pathlib import Path

import pytest

from pytest_html_nova_act.plugin import PytestHtmlNovaActPlugin


class _FakeConfig:
    def getoption(self, name: str) -> bool:
        return True


@pytest.fixture()
def plugin() -> PytestHtmlNovaActPlugin:
    return PytestHtmlNovaActPlugin(_FakeConfig())


def test_accordion_escapes_untrusted_file_name(
    plugin: PytestHtmlNovaActPlugin, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = "<img src=x onerror=alert(1)>"
    # Some OSes reject "<" and ">" in file names, so fake the read instead of
    # creating the file.
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None: "<p>ok</p>")

    rendered = plugin._generate_action_viewer_accordion_html(f"/logs/{payload}.html")

    assert payload not in rendered
    assert "&lt;img src=x onerror=alert(1)&gt;.html</label>" in rendered
    # Autoescape escapes once; the filename must not be double-escaped.
    assert "&amp;lt;" not in rendered


def test_accordion_escapes_action_viewer_html_in_srcdoc(
    plugin: PytestHtmlNovaActPlugin, tmp_path: Path
) -> None:
    viewer = tmp_path / "act.html"
    viewer.write_text("<p class='x'>hi</p>", encoding="utf-8")

    rendered = plugin._generate_action_viewer_accordion_html(str(viewer))

    # The single quote must be escaped so it cannot break out of srcdoc='...'.
    assert "srcdoc='&lt;p class=&#39;x&#39;&gt;hi&lt;/p&gt;'" in rendered
    assert "&amp;lt;" not in rendered


def test_results_table_hook_escapes_file_name_once(
    plugin: PytestHtmlNovaActPlugin, tmp_path: Path
) -> None:
    viewer = tmp_path / "a&b.html"
    viewer.write_text("<p>ok</p>", encoding="utf-8")
    # pytest-html hands the hook log text that is already HTML-escaped.
    data = [f"View your act run here: {html.escape(str(viewer))}"]

    plugin.pytest_html_results_table_html(None, data)

    assert "a&amp;b.html</label>" in data[0]
    assert "&amp;amp;" not in data[0]
