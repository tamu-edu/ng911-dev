from __future__ import annotations

import copy
import html
import re
import textwrap
from pathlib import Path
from typing import Optional

from services.config.schemas.requirements_schema import REQUIREMENTS_SCHEMA


class DiagramService:
    """
    Reporting helper service for expected / observed sequence diagrams.

    Responsibilities:
    - resolve test_id from a requirement name via REQUIREMENTS_SCHEMA;
    - resolve TD_<test_id>.md from the test_descriptions directory;
    - parse expected sequence diagram from the TD markdown;
    - resolve observed sequence diagram HTML generated per variation;
    - convert observed diagram HTML -> Mermaid -> SVG;
    - return report artifact dictionaries for report_data enrichment.

    Notes:
    - This service is intentionally fail-safe: missing or malformed diagram
      inputs should not break report generation.
    - Expected diagram paths are returned relative to repository root when
      possible, e.g.:
          test_descriptions/_assets/INTEROP/TD_INTEROP_001_Sequence_Diagram.png
    - Observed diagram paths are returned relative to the output folder, e.g.:
          sequence_diagrams/imgs/INTEROP_..._sequence_diagram.svg
    """

    _SEQUENCE_SECTION_TITLE = "Sequence Diagram"

    def __init__(
        self,
        output_directory: str,
        test_descriptions_directory: str = "test_descriptions",
    ) -> None:
        self.output_directory = Path(output_directory).resolve()
        self.repo_root = Path(__file__).resolve().parents[3]

        td_dir = Path(test_descriptions_directory)
        if td_dir.is_absolute():
            self.test_descriptions_directory = td_dir
        else:
            self.test_descriptions_directory = (self.repo_root / td_dir).resolve()

        self._td_path_cache: dict[str, Optional[Path]] = {}
        self._expected_artifact_cache: dict[str, Optional[dict]] = {}
        self._observed_artifact_cache: dict[str, Optional[dict]] = {}
        self._variation_artifacts_cache: dict[tuple[str, str], list[dict]] = {}
        self._sequence_data: dict[str, str] = {}

    def get_sequence_data(self) -> dict[str, str]:
        return copy.deepcopy(self._sequence_data)

    def render_sequence_svg(
        self,
        mermaid_str: str,
    ) -> str:
        return self._render_sequence_mermaid_to_svg(mermaid_str)

    def get_variation_artifacts(
        self,
        requirement_name: str,
        variation_name: str,
    ) -> list[dict]:
        """
        Returns reporting artifacts for the given requirement / variation pair.

        Typical result:
        [
            {
                "type": "sequence_diagram",
                "role": "expected",
                "source": "test_description",
                "title": "Expected Sequence",
                "description": "Sequence diagram defined by the test description.",
                "path": "test_descriptions/_assets/INTEROP/TD_INTEROP_001_Sequence_Diagram.png"
            },
            {
                "type": "sequence_diagram",
                "role": "observed",
                "source": "pcap",
                "title": "Observed Sequence",
                "description": "Sequence diagram generated from the captured traffic.",
                "path": "sequence_diagrams/imgs/INTEROP_..._sequence_diagram.png"
            }
        ]

        If anything is missing, returns only what can be resolved.
        If nothing can be resolved, returns [].
        """
        test_id = self._get_test_id_from_requirement(requirement_name)
        if not test_id:
            return []

        cache_key = (test_id, variation_name)
        cached = self._variation_artifacts_cache.get(cache_key)
        if cached is not None:
            return copy.deepcopy(cached)

        artifacts: list[dict] = []

        expected = self._get_expected_artifact(test_id)
        if expected:
            artifacts.append(expected)

        observed = self._get_observed_artifact(variation_name)
        if observed:
            artifacts.append(observed)

        self._variation_artifacts_cache[cache_key] = copy.deepcopy(artifacts)
        return artifacts

    def _get_test_id_from_requirement(
        self,
        requirement_name: str,
    ) -> Optional[str]:
        req_schema = REQUIREMENTS_SCHEMA.get(requirement_name, {})
        test_id = req_schema.get("test_id")

        if not test_id:
            return None

        # Support both:
        # - "INTEROP_001"
        # - "tests.interop.INTEROP_001"
        return str(test_id).rsplit(".", 1)[-1]

    def _get_expected_artifact(self, test_id: str) -> Optional[dict]:
        if test_id in self._expected_artifact_cache:
            return copy.deepcopy(self._expected_artifact_cache[test_id])

        artifact: Optional[dict] = None

        try:
            td_path = self._find_td_path(test_id)
            if not td_path:
                self._expected_artifact_cache[test_id] = None
                return None

            expected_path = self._extract_expected_sequence_diagram_path(td_path)
            if not expected_path or not expected_path.exists():
                self._expected_artifact_cache[test_id] = None
                return None

            artifact = {
                "type": "sequence_diagram",
                "role": "expected",
                "source": "test_description",
                "title": "Expected Sequence",
                "description": ("Sequence diagram defined by the test description."),
                "path": self._to_repo_relative(expected_path),
            }
        except Exception:
            artifact = None

        self._expected_artifact_cache[test_id] = copy.deepcopy(artifact)
        return artifact

    def _find_td_path(self, test_id: str) -> Optional[Path]:
        if test_id in self._td_path_cache:
            return self._td_path_cache[test_id]

        td_filename = f"TD_{test_id}.md"

        if not self.test_descriptions_directory.exists():
            self._td_path_cache[test_id] = None
            return None

        matches = sorted(self.test_descriptions_directory.rglob(td_filename))

        if len(matches) == 1:
            self._td_path_cache[test_id] = matches[0].resolve()
            return self._td_path_cache[test_id]

        # More than one TD_<test_id>.md would be ambiguous.
        # Fail safely and do not attach an expected artifact.
        self._td_path_cache[test_id] = None
        return None

    def _extract_expected_sequence_diagram_path(
        self,
        td_path: Path,
    ) -> Optional[Path]:
        content = td_path.read_text(encoding="utf-8")

        section_match = re.search(
            r"(?ms)^\s*##\s+Sequence Diagram\s*$([\s\S]*?)(?=^\s*##\s+|\Z)",
            content,
        )
        if not section_match:
            return None

        section_body = section_match.group(1)

        image_match = re.search(
            r"!\[[^\]]*]\(([^)]+)\)",
            section_body,
        )
        if not image_match:
            return None

        relative_image_path = image_match.group(1).strip().strip("<>")

        # Paths in TDs are relative to the TD markdown location.
        resolved_path = (td_path.parent / relative_image_path).resolve()

        return resolved_path

    def _get_observed_artifact(self, variation_name: str) -> Optional[dict]:
        if variation_name in self._observed_artifact_cache:
            return copy.deepcopy(self._observed_artifact_cache[variation_name])

        artifact: Optional[dict] = None

        try:
            observed_path = self._ensure_observed_diagram_asset(variation_name)
            if not observed_path:
                self._observed_artifact_cache[variation_name] = None
                return None

            artifact = {
                "type": "sequence_diagram",
                "role": "observed",
                "source": "pcap",
                "title": "Observed Sequence",
                "description": (
                    "Sequence diagram generated from the captured traffic."
                ),
                "path": observed_path,
            }
        except Exception:
            artifact = None

        self._observed_artifact_cache[variation_name] = copy.deepcopy(artifact)
        return artifact

    def _ensure_observed_diagram_asset(
        self,
        variation_name: str,
    ) -> Optional[str]:
        """
        Ensures a renderable SVG asset exists for the observed sequence diagram.

        Input:
            <output_folder>/sequence_diagrams/
                <variation_name>_sequence_diagram.html

        Output:
            <output_folder>/sequence_diagrams/imgs/
                <variation_name>_sequence_diagram.svg

        Returns:
            Path relative to output_directory,
            or None if the observed HTML does not exist.
        """
        sequence_diagrams_dir = self.output_directory / "sequence_diagrams"

        html_path = sequence_diagrams_dir / f"{variation_name}_sequence_diagram.html"

        if not html_path.exists():
            return None

        imgs_dir = sequence_diagrams_dir / "imgs"

        imgs_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        svg_path = imgs_dir / f"{variation_name}_sequence_diagram.svg"

        mermaid_str = self._extract_mermaid_str_from_html(html_path)

        if not mermaid_str:
            return None

        self._sequence_data[variation_name] = mermaid_str

        # SVG already generated, but Mermaid source is still preserved.
        if svg_path.exists():
            return self._to_output_relative(svg_path)

        svg_content = self._render_sequence_mermaid_to_svg(mermaid_str)

        svg_path.write_text(
            svg_content,
            encoding="utf-8",
        )

        return self._to_output_relative(svg_path)

    def _extract_mermaid_str_from_html(self, html_path: Path) -> Optional[str]:
        content = html_path.read_text(encoding="utf-8")

        match = re.search(
            r'<div\s+class="mermaid">\s*(.*?)\s*</div>',
            content,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if not match:
            return None

        mermaid_str = html.unescape(match.group(1)).strip()
        return mermaid_str or None

    def _render_sequence_mermaid_to_svg(self, mermaid_str: str) -> str:
        participants, messages = self._parse_mermaid_sequence(mermaid_str)

        if not participants:
            return self._render_empty_svg("Sequence diagram is empty.")

        max_participant_len = max((len(p) for p in participants), default=12)
        participant_box_width = max(110, max_participant_len * 8 + 30)
        participant_box_height = 32

        left_margin = 60
        right_margin = 60
        top_margin = 24
        participant_box_y = top_margin
        # label_band_gap = 24
        message_gap = 64
        bottom_margin = 40

        participant_spacing = max(participant_box_width + 70, 190)

        x_positions: dict[str, int] = {}
        for index, participant in enumerate(participants):
            x_positions[participant] = (
                left_margin + participant_box_width // 2 + index * participant_spacing
            )

        width = (
            left_margin
            + right_margin
            + participant_box_width
            + max(0, len(participants) - 1) * participant_spacing
        )
        width = max(width, 900)

        first_message_y = participant_box_y + participant_box_height + 34

        height = first_message_y + max(len(messages), 1) * message_gap + bottom_margin
        height = max(height, 220)

        lifeline_start_y = participant_box_y + participant_box_height
        lifeline_end_y = height - 24

        svg_parts: list[str] = []

        svg_parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="Observed sequence diagram">'
        )

        svg_parts.append("""
<style>
    .bg { fill: #ffffff; }
    .participant-box {
        fill: #f3f4f6;
        stroke: #374151;
        stroke-width: 1.2;
        rx: 8;
        ry: 8;
    }
    .participant-text {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 14px;
        font-weight: 700;
        fill: #111827;
        text-anchor: middle;
        dominant-baseline: middle;
    }
    .lifeline {
        stroke: #9ca3af;
        stroke-width: 1.2;
        stroke-dasharray: 6 6;
    }
    .message-line {
        stroke: #2563eb;
        stroke-width: 2.0;
    }
    .message-label {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 13px;
        fill: #111827;
        text-anchor: middle;
    }
    .self-message-line {
        fill: none;
        stroke: #2563eb;
        stroke-width: 2.0;
    }
</style>
""")

        svg_parts.append(
            f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" />'
        )

        # Participant boxes and lifelines
        for participant in participants:
            center_x = x_positions[participant]
            box_x = center_x - participant_box_width / 2

            svg_parts.append(
                f'<rect class="participant-box" '
                f'x="{box_x}" y="{participant_box_y}" '
                f'width="{participant_box_width}" '
                f'height="{participant_box_height}" />'
            )

            svg_parts.append(
                f'<text class="participant-text" '
                f'x="{center_x}" '
                f'y="{participant_box_y + participant_box_height / 2}">'
                f"{html.escape(participant)}"
                f"</text>"
            )

            svg_parts.append(
                f'<line class="lifeline" '
                f'x1="{center_x}" y1="{lifeline_start_y}" '
                f'x2="{center_x}" y2="{lifeline_end_y}" />'
            )

        # Messages
        for index, message in enumerate(messages, start=1):
            src = message["src"]
            dst = message["dst"]
            label = message["label"]

            if src not in x_positions or dst not in x_positions:
                continue

            y = first_message_y + (index - 1) * message_gap

            if src == dst:
                self._append_self_message_svg(
                    svg_parts=svg_parts,
                    x=x_positions[src],
                    y=y,
                    label=label,
                )
                continue

            src_x_center = x_positions[src]
            dst_x_center = x_positions[dst]

            if dst_x_center > src_x_center:
                line_start_x = src_x_center + participant_box_width / 2 - 6
                line_end_x = dst_x_center - participant_box_width / 2 + 6
                arrow_direction = "right"
            else:
                line_start_x = src_x_center - participant_box_width / 2 + 6
                line_end_x = dst_x_center + participant_box_width / 2 - 6
                arrow_direction = "left"

            label_x = (line_start_x + line_end_x) / 2
            label_y = y - 10

            svg_parts.append(
                f'<line class="message-line" '
                f'x1="{line_start_x}" y1="{y}" '
                f'x2="{line_end_x}" y2="{y}" />'
            )

            svg_parts.append(
                self._build_arrowhead_svg(
                    x=line_end_x,
                    y=y,
                    direction=arrow_direction,
                )
            )

            svg_parts.append(
                self._build_wrapped_text_svg(
                    x=label_x,
                    y=label_y,
                    lines=self._wrap_text_for_svg(label, 36),
                    css_class="message-label",
                )
            )

        svg_parts.append("</svg>")

        return "\n".join(svg_parts)

    def _append_self_message_svg(
        self,
        svg_parts: list[str],
        x: float,
        y: float,
        label: str,
    ) -> None:
        loop_width = 56
        loop_height = 20

        path = f"M {x} {y} " f"h {loop_width} " f"v {loop_height} " f"h {-loop_width}"

        svg_parts.append(f'<path class="self-message-line" d="{path}" />')

        svg_parts.append(
            self._build_arrowhead_svg(
                x=x,
                y=y + loop_height,
                direction="left",
            )
        )

        svg_parts.append(
            self._build_wrapped_text_svg(
                x=x + loop_width / 2,
                y=y - 10,
                lines=self._wrap_text_for_svg(label, 24),
                css_class="message-label",
            )
        )

    def _parse_mermaid_sequence(
        self,
        mermaid_str: str,
    ) -> tuple[list[str], list[dict[str, str]]]:
        participants: list[str] = []
        messages: list[dict[str, str]] = []

        participant_set: set[str] = set()

        for raw_line in mermaid_str.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            if line == "sequenceDiagram":
                continue

            if line == "autonumber":
                continue

            if line.startswith("participant "):
                participant = line[len("participant ") :].strip()
                if participant and participant not in participant_set:
                    participants.append(participant)
                    participant_set.add(participant)
                continue

            msg_match = re.match(
                r"^(?P<src>.+?)->>(?P<dst>.+?):\s*(?P<label>.+)$",
                line,
            )
            if not msg_match:
                continue

            src = msg_match.group("src").strip()
            dst = msg_match.group("dst").strip()
            label = msg_match.group("label").strip()

            if src and src not in participant_set:
                participants.append(src)
                participant_set.add(src)

            if dst and dst not in participant_set:
                participants.append(dst)
                participant_set.add(dst)

            messages.append(
                {
                    "src": src,
                    "dst": dst,
                    "label": label,
                }
            )

        return participants, messages

    def _build_arrowhead_svg(
        self,
        x: float,
        y: float,
        direction: str,
    ) -> str:
        size = 7

        if direction == "right":
            p1 = (x, y)
            p2 = (x - size, y - size / 2)
            p3 = (x - size, y + size / 2)
        else:
            p1 = (x, y)
            p2 = (x + size, y - size / 2)
            p3 = (x + size, y + size / 2)

        points = f"{p1[0]},{p1[1]} {p2[0]},{p2[1]} {p3[0]},{p3[1]}"
        return f'<polygon points="{points}" fill="#2563eb" />'

    def _build_wrapped_text_svg(
        self,
        x: float,
        y: float,
        lines: list[str],
        css_class: str,
    ) -> str:
        if not lines:
            lines = [""]

        tspans: list[str] = []

        for index, line in enumerate(lines):
            dy = 0 if index == 0 else 15
            tspans.append(f'<tspan x="{x}" dy="{dy}">{html.escape(line)}</tspan>')

        return (
            f'<text class="{css_class}" x="{x}" y="{y}">' + "".join(tspans) + "</text>"
        )

    def _wrap_text_for_svg(
        self,
        text_value: str,
        max_chars_per_line: int,
    ) -> list[str]:
        return textwrap.wrap(
            text_value,
            width=max_chars_per_line,
            break_long_words=False,
            break_on_hyphens=False,
        )

    def _render_empty_svg(self, message: str) -> str:
        safe_message = html.escape(message)
        return f"""
<svg xmlns="http://www.w3.org/2000/svg"
     width="900" height="220" viewBox="0 0 900 220">
    <rect x="0" y="0" width="900" height="220" fill="#ffffff" />
    <text x="450" y="110"
          text-anchor="middle"
          font-family="Arial, Helvetica, sans-serif"
          font-size="18"
          fill="#374151">{safe_message}</text>
</svg>
""".strip()

    def _to_repo_relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.repo_root).as_posix()
        except ValueError:
            return path.as_posix()

    def _to_output_relative(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.output_directory).as_posix()
        except ValueError:
            return path.as_posix()
