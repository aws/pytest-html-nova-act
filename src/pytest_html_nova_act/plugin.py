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

import uuid
import re
import html
from pathlib import Path
import pytest
import warnings
import jinja2

PLUGIN_ATTR_NAME = "_plugin_add_nova_act_report"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Command-line options for pytest-html-nova-act."""
    group = parser.getgroup("terminal reporting")
    group.addoption(
        "--add-nova-act-report",
        action="store_true",
        default=False,
        help="Enable adding expandable links to the pytest-html report.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """
    Configure pytest with the Nova Act plugin.

    This function initializes and registers the PytestHtmlNovaActPlugin if the
    'add_nova_act_report' option is enabled in the pytest configuration.
    """
    if config.getoption("add_nova_act_report"):
        # Suppress Nova Act keyboard event watcher warnings - Nova Act tries to monitor
        # keyboard input via a background thread, but pytest redirects stdin to a pseudofile
        # that doesn't support fileno(). This causes harmless threading exceptions that don't
        # affect Nova Act functionality or test execution.
        warnings.filterwarnings(
            "ignore", category=pytest.PytestUnhandledThreadExceptionWarning
        )
        
        # Configure with CSS for embedded Nova Act Action Viewer HTML
        css_file = Path(__file__).parent / "static" / "nova_act_styles.css"
        if not hasattr(config.option, 'css'):
            config.option.css = []
        config.option.css.append(str(css_file))

        plugin = PytestHtmlNovaActPlugin(config)
        setattr(config, PLUGIN_ATTR_NAME, plugin)
        config.pluginmanager.register(plugin, "pytest_html_nova_act_plugin")


def pytest_unconfigure(config: pytest.Config) -> None:
    """
    Unconfigure pytest by cleaning up the Nova Act plugin.

    This function removes the PytestHtmlNovaActPlugin instance from the config
    and unregisters it from the plugin manager when pytest is shutting down.
    """
    plugin = getattr(config, PLUGIN_ATTR_NAME, None)
    if plugin:
        delattr(config, PLUGIN_ATTR_NAME)
        config.pluginmanager.unregister(plugin)


class PytestHtmlNovaActPlugin:
    """
    A pytest plugin that adds expandable Nova Act Action Viewer HTML to the pytest-html report.

    This plugin looks for Action Viewer HTML file paths in test output and embeds them
    as expandable sections in the pytest-html report.
    """

    def __init__(self, config: pytest.Config) -> None:
        """
        Initialize the plugin.

        Args:
            config: The pytest config object containing plugin configuration.
        """
        self.add_nova_act_links_enabled = config.getoption("--add-nova-act-report")

        if self.add_nova_act_links_enabled:
            # Load Jinja templates
            html_template_dir = Path(__file__).parent / "templates"
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(html_template_dir))
            self.action_viewer_item_template = env.get_template("action_viewer_accordion.html")

    def pytest_html_results_table_html(
        self, report: pytest.TestReport, data: list[str]
    ) -> None:
        """
        Pytest HTML hook called for each test.
        Modifies the report result HTML by embedding the Nova Act Action Viewer HTML files.

        Args:
            report: The pytest report object (unused)
            data: List containing the HTML data to be modified
        """
        if self.add_nova_act_links_enabled:
            self._insert_action_viewer_html(data)

    def _insert_action_viewer_html(self, data: list[str]) -> None:
        """
        Finds Nova Act Action Viewer file paths and adds accordions after them.

        Args:
            data: List of HTML strings
        """
        for i, logs in enumerate(data):
            initial_log_lines = logs.split("\n")
            modified_log_lines = []
            found_action_viewer_html_paths = False

            for log in initial_log_lines:
                modified_log_lines.append(log)
                action_viewer_html_paths = re.findall(
                    r"View your act run here: (.*?\.html)", log
                )
                if action_viewer_html_paths:
                    found_action_viewer_html_paths = True
                    for file_path in action_viewer_html_paths:
                        decoded_file_path = html.unescape(file_path)
                        action_viewer_html = self._generate_action_viewer_accordion_html(
                            decoded_file_path
                        )
                        modified_log_lines.append("")
                        modified_log_lines.append(action_viewer_html)

            if found_action_viewer_html_paths:
                data[i] = "\n".join(modified_log_lines)

    def _generate_action_viewer_accordion_html(self, html_file_path: str) -> str:
        """
        Reads the Action Viewer HTML file and populates the HTML template with it

        Args:
            html_file_path: Full path to the .html file.

        Returns:
            An HTML string for the Action Viewer accordion.
        """
        try:
            file_path = Path(html_file_path)
            action_viewer_html = file_path.read_text(encoding="utf-8")
            file_name = html.escape(file_path.name)
            checkbox_id = f"accordion-toggle-{uuid.uuid4()}"

            return self.action_viewer_item_template.render(
                checkbox_id=checkbox_id,
                file_name=file_name,
                action_viewer_html=action_viewer_html,
            )

        except FileNotFoundError:
            return f"<p style='color: red;'>Error: Action Viewer HTML file not found at {html.escape(html_file_path)}</p>"
        except Exception as e:
            return f"<p style='color: red;'>Error reading file {html.escape(html_file_path)}: {html.escape(str(e))}</p>"

    def pytest_html_results_summary(self, prefix: list[str], summary: list[str], postfix: list[str]) -> None:
        """
        Pytest HTML hook called once before report generation.
        Appends JavaScript into the report HTML for layout adjustments to the embedded Nova Act Action Viewer HTML.

        Args:
            prefix: List of HTML strings to prepend to summary
            summary: List of HTML strings for summary content
            postfix: List of HTML strings to append to summary
        """
        if not self.add_nova_act_links_enabled:
            return
        
        js_file = Path(__file__).parent / "static" / "nova_act_accordion.js"
        js_content = js_file.read_text(encoding="utf-8")
        postfix.append(f"<script>{js_content}</script>")
