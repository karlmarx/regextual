
import re
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Input, Label, Markdown, TextArea
from textual.reactive import reactive
from textual.on import on # Import the 'on' decorator

class RegexTesterApp(App[None]):
    """A Textual app for testing regular expressions."""

    TITLE = "Regex Tester - Python 3.13 + Textual 3.2.0 + UV" # Updated Title
    CSS = """
    Screen {
        /* Global screen styles can be added here if needed */
    }

    Vertical#main_container {
        width: 90%;
        max-width: 120; /* Max width of 120 columns */
        height: auto;
        margin: 1 auto; /* Center the container */
        padding: 1;
        border: round $primary;
        background: $surface;
    }

    Input, TextArea {
        margin-bottom: 1;
    }

    Input {
        border: round $primary;
    }

    TextArea {
        height: 10; /* Default height for test string input */
        border: round $primary;
    }

    Label {
        margin-bottom: 1; /* Space below labels */
    }

    #regex_status {
        height: auto; /* Allow status to wrap if error message is long */
        min-height: 1;
        margin-bottom: 1;
        /* Default color will be used for "Regex Status:", Rich tags will colorize specific parts */
    }

    Vertical#results_area {
        height: auto;
        margin-top: 1; /* Space above results */
    }

    Markdown#match_results {
        height: auto;
        min-height: 8; /* Minimum height for the results display */
        border: round $secondary;
        padding: 0 1;
        background: $panel;
    }
    """

    # Reactive properties to store the current regex pattern and test string.
    regex_pattern: reactive[str] = reactive("")
    test_string: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Vertical(id="main_container"):
            yield Label("Regular Expression Pattern:")
            yield Input(
                placeholder="Enter your regex here (e.g., [a-z]+)",
                id="regex_pattern_input"
            )
            yield Label("Regex Status: (Enter a pattern)", id="regex_status")

            yield Label("Test String:")
            yield TextArea(
                id="test_string_area",
                language="text", # Using "text" as a generic language for the TextArea
                theme="vscode_dark", # A common theme, Textual usually includes it or similar
                show_line_numbers=True
            )

            with Vertical(id="results_area"):
                yield Label("Match Results:")
                yield Markdown("", id="match_results")
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is first mounted. Focus the regex input."""
        self.query_one("#regex_pattern_input", Input).focus()

    # Event handlers using the 'on' decorator for more targeted handling
    @on(Input.Changed, "#regex_pattern_input")
    async def handle_regex_input_change(self, event: Input.Changed) -> None:
        """Handle changes in the regex Input widget."""
        self.regex_pattern = event.value

    @on(TextArea.Changed, "#test_string_area")
    async def handle_test_string_area_change(self, event: TextArea.Changed) -> None:
        """Handle changes in the test string TextArea widget."""
        # For TextArea.Changed, event.text_area gives the instance, then .text for content
        self.test_string = event.text_area.text

    # Watch methods are called when reactive attributes change
    async def watch_regex_pattern(self, old_pattern: str, new_pattern: str) -> None:
        """Called when self.regex_pattern changes."""
        if old_pattern != new_pattern:
            await self._update_matches()

    async def watch_test_string(self, old_string: str, new_string: str) -> None:
        """Called when self.test_string changes."""
        if old_string != new_string:
            await self._update_matches()

    async def _update_matches(self) -> None:
        """
        Compiles the current regex pattern and finds matches in the current test string.
        Updates the status label and the match results Markdown display.
        """
        status_label = self.query_one("#regex_status", Label)
        results_markdown = self.query_one("#match_results", Markdown)

        pattern = self.regex_pattern
        current_test_str = self.test_string

        if not pattern:
            status_label.update("Regex Status: (Enter a pattern)")
            await results_markdown.update("Enter a regex pattern to see matches.")
            return

        try:
            compiled_regex = re.compile(pattern)
            # Using Rich tags for status, e.g., "[b green]Valid[/b]"
            status_label.update("Regex Status: [b green]Valid[/b]")
        except re.error as e:
            status_label.update(f"Regex Status: [b red]Invalid[/b] - {e}")
            await results_markdown.update(f"### Regex Error\n\n```\n{e}\n```")
            return
        except Exception as e: # Catch other potential errors during compile
            status_label.update(f"Regex Status: [b red]Error[/b] - Unexpected: {e}")
            await results_markdown.update(f"### Unexpected Compilation Error\n\n```\n{e}\n```")
            return

        if not current_test_str:
            await results_markdown.update("Enter a test string to find matches.")
            return

        matches_details_md = []
        highlighted_text_parts_for_md = []
        last_char_index = 0

        try:
            for match_obj in compiled_regex.finditer(current_test_str):
                start, end = match_obj.span()
                matched_text_segment = match_obj.group(0)

                # Prepare for highlighted output: escape Markdown in non-matched parts
                non_match_part = current_test_str[last_char_index:start]
                # Basic escaping for Markdown special characters
                escaped_non_match = re.sub(r"([*_`\[\]\(\)!#\-\+\.])", r"\\\1", non_match_part)
                highlighted_text_parts_for_md.append(escaped_non_match)

                # Bold the matched part (escape special chars inside match if needed, then bold)
                escaped_match_segment = re.sub(r"([*_`\[\]\(\)!#\-\+\.])", r"\\\1", matched_text_segment)
                highlighted_text_parts_for_md.append(f"**{escaped_match_segment}**")
                last_char_index = end

                # Prepare details for each match
                match_info = f"- **Match**: `{escaped_match_segment}` (span=({start}, {end}))" # Use escaped version

                groups = match_obj.groups() # Returns a tuple of all groups
                if groups:
                    group_str_parts = []
                    for i, g in enumerate(groups):
                        escaped_g = re.sub(r"([*_`\[\]\(\)!#\-\+\.])", r"\\\1", g) if g is not None else "None"
                        group_str_parts.append(f"`{escaped_g}`")
                    match_info += f"\n  - Groups ({len(groups)}): ({', '.join(group_str_parts)})"

                groupdict = match_obj.groupdict() # Returns a dict of named groups
                if groupdict:
                    named_group_parts = []
                    for name, val in groupdict.items():
                        escaped_val = re.sub(r"([*_`\[\]\(\)!#\-\+\.])", r"\\\1", val) if val is not None else "None"
                        named_group_parts.append(f"{name}=`{escaped_val}`")
                    match_info += f"\n  - Named Groups: {{{', '.join(named_group_parts)}}}"
                matches_details_md.append(match_info)

            # Append the rest of the string after the last match
            final_non_match_part = current_test_str[last_char_index:]
            escaped_final_non_match = re.sub(r"([*_`\[\]\(\)!#\-\+\.])", r"\\\1", final_non_match_part)
            highlighted_text_parts_for_md.append(escaped_final_non_match)

            highlighted_output_for_markdown = "".join(highlighted_text_parts_for_md)

        except Exception as e: # Catch errors during finditer or processing
            status_label.update(f"Regex Status: [b red]Error during matching[/b] - {e}")
            await results_markdown.update(f"### Matching Error\n\n```\n{e}\n```")
            return

        if matches_details_md:
            results_content = "### Highlighted Text:\n\n"
            results_content += highlighted_output_for_markdown if highlighted_output_for_markdown else "(No visual text to highlight if all is matched or empty)"
            results_content += "\n\n### Match Details:\n\n" + "\n\n".join(matches_details_md)
            await results_markdown.update(results_content)
        else:
            # If the string is not empty but no matches, show the original string (escaped)
            if current_test_str:
                escaped_current_test_str = re.sub(r"([*_`\[\]\(\)!#\-\+\.])", r"\\\1", current_test_str)
                await results_markdown.update(f"No matches found in:\n\n{escaped_current_test_str}")
            else:
                await results_markdown.update("No matches found.")

def main_cli():
    """Entry point function for the CLI."""
    app = RegexTesterApp()
    app.run()

if __name__ == "__main__":
    main_cli()

