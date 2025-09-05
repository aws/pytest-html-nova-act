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


def pytest_addoption(parser):
    """Command-line options for pytest-html-nova-act."""
    group = parser.getgroup("terminal reporting")
    group.addoption(
        "--add-nova-act-report",
        action="store_true",
        default=False,
        help="Enable adding expandable links to the pytest-html report.",
    )


def pytest_configure(config):
    """
    Configure pytest with the Nova Act Report plugin.

    This function initializes and registers the PytestHtmlNovaActPlugin if the
    'add_nova_act_report' option is enabled in the pytest configuration.
    """
    if config.getoption("add_nova_act_report"):
        config._plugin_add_nova_act_report = PytestHtmlNovaActPlugin(config)
        config.pluginmanager.register(
            config._plugin_add_nova_act_report, "pytest_html_nova_act_plugin"
        )


def pytest_unconfigure(config):
    """
    Unconfigure pytest by cleaning up the Nova Act Report plugin.

    This function removes the PytestHtmlNovaActPlugin instance from the config
    and unregisters it from the plugin manager when pytest is shutting down.
    """
    plugin_add_nova_act_report = getattr(config, "_plugin_add_nova_act_report", None)
    if plugin_add_nova_act_report:
        del config._plugin_add_nova_act_report
        config.pluginmanager.unregister(plugin_add_nova_act_report)


class PytestHtmlNovaActPlugin:
    """
    A pytest plugin that adds expandable HTML report links to the pytest-html report.

    This plugin looks for Act workflow report links in test output and embeds them
    as expandable sections in the pytest-html report.
    """

    def __init__(self, config):
        """
        Initialize the plugin.

        Args:
            config: The pytest config object containing plugin configuration.
        """
        self.add_nova_act_links_enabled = config.getoption("--add-nova-act-report")

    def pytest_html_results_table_html(self, report, data):
        """
        Hook implementation that modifies the HTML results table.

        Args:
            report: The pytest report object
            data: List containing the HTML data to be modified
        """
        if self.add_nova_act_links_enabled:
            files = self._extract_report_links(data)
            html_blob = self._create_expandable_html_div(files)
            data.insert(
                0, html_blob
            )  # Use pytest_html.extras.html for proper integration

    def _extract_report_links(self, data):
        """
        Parses a list of strings to find and extract all report links (multiple per line supported).

        Args:
            data: A list of strings, where multiple report links might exist on a single line.

        Returns:
            A list of strings, where each string is a report link found.
            Returns an empty list if no report links are found.
        """

        report_links = []
        for line in data:
            matches = re.findall(r"View your act run here: (.*?\.html)", line)
            if matches:
                # Decode HTML entities in file paths (e.g., &#x27; -> ')
                decoded_matches = [html.unescape(match) for match in matches]
                report_links.extend(decoded_matches)
        return report_links

    def _create_expandable_html_div(self, files):
        """
        Creates an HTML div with an expandable section for each HTML file
        using pure CSS and HTML.

        Args:
            files: A list of full paths to .html files.

        Returns:
            A string containing the HTML div structure with CSS.
        """
        html_div = """
        <div class='combined-reports'>
            <style>
    
                .combined-reports {
                    white-space: normal;
                }
    
                .accordion-item {
                    margin-bottom: 2px;
                    white-space: normal;
                }
    
                .accordion-item label {
                    color: #444;
                    cursor: pointer;
                    padding: 3px;
                    width: 100%;
                    display: block;
                    text-align: left;
                }
    
                .accordion-item label:hover {
                    background-color: #ccc;
                }
    
                .accordion-content {
                    padding: 0 3px;
                    background-color: #f1f1f1;
                    overflow: hidden;
                    max-height: 0;
                    transition: max-height 0.3s ease-out;
                }
    
                /* Show content when the checkbox is checked */
                .accordion-item input[type="checkbox"]:checked + label + .accordion-content {
                    max-height: fit-content; /* Let content determine the height */
                    transition: max-height 0.2s ease-in;
                }
    
                /* Hide the checkbox */
                .accordion-item input[type="checkbox"] {
                    display: none;
                }
    
                .embedded-html {
                    white-space: normal;
                    width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    margin-bottom: 2px;
                    padding: 3px; /* Add some padding inside the embedded HTML */
                }
    
                /* Counter the white-space: pre-wrap for list items within embedded HTML */
                .embedded-html ul,
                .embedded-html ol,
                .embedded-html li {
                    white-space: normal;
                }
    
            </style>
        """
        for i, html_file_path in enumerate(files):
            try:
                file_path = Path(html_file_path)
                html_content = file_path.read_text(encoding="utf-8")
                file_name = file_path.name
                checkbox_id = f"accordion-toggle-{uuid.uuid4()}"
                html_div += f"""
                <div class="accordion-item">
                    <input type="checkbox" id="{checkbox_id}">
                    <label for="{checkbox_id}"> {">>> "}Click to Expand Act Workflow Viewer for file {file_name}</label>
                    <div class="accordion-content">
                        <div class="embedded-html">
                            {html_content}
                        </div>
                    </div>
                </div>
                """
            except FileNotFoundError:
                html_div += f"<p style='color: red;'>Error: File not found - {html_file_path}</p>"
            except Exception as e:
                html_div += f"<p style='color: red;'>Error reading file {html_file_path}: {e}</p>"
        html_div += """
        </div>
        """

        return html_div
