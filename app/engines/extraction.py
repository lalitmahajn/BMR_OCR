import re
from typing import Dict, List, Optional, Any, Union
from loguru import logger
from app.schemas.template import (
    FieldDefinition,
    TableConfig,
    ExtractionTemplate,
    ConfigField,
    TableRowTemplate,
    PageTemplate,
    FieldType,
)


class MarkdownExtractionEngine:
    """Engine for extracting structured data from markdown text.
    Optimized for Mistral OCR output.
    """

    def __init__(self):
        pass

    def extract_field(
        self,
        markdown: str,
        field_def: Union[Dict, ConfigField],
        boundary_labels: Optional[List[str]] = None,
        fallback_name: Optional[str] = None,
        start_pos: int = 0,
    ) -> (Optional[str], int):
        """
        Extracts a single field value based on expected labels and regex.
        Uses lookahead to avoid consuming adjacent fields.
        Returns extracted value and the end position of the match.
        """
        if not markdown:
            return None, start_pos

        # 1. Gather potential labels
        labels = []
        regex_pattern = None

        if isinstance(field_def, dict):
            labels = [field_def.get("label")] + field_def.get("expected_label", [])
            regex_pattern = field_def.get("regex")
            if not regex_pattern:
                vr = field_def.get("validation_rules")
                if isinstance(vr, dict):
                    regex_pattern = vr.get("regex")
        else:
            labels = [
                getattr(field_def, "label", None),
                getattr(field_def, "name", None),
            ]
            if hasattr(field_def, "expected_label") and field_def.expected_label:
                labels += field_def.expected_label

            # Extract regex from object
            regex_pattern = getattr(field_def, "regex", None)

            # Helper for Pydantic "extra" fields if getattr fails
            if (
                not regex_pattern
                and hasattr(field_def, "model_extra")
                and field_def.model_extra
            ):
                regex_pattern = field_def.model_extra.get("regex")

            # Legacy/Alternative Validation Paths
            if not regex_pattern and hasattr(field_def, "validation_rules"):
                vr = field_def.validation_rules
                if vr:
                    regex_pattern = getattr(vr, "regex", None)
            if not regex_pattern and hasattr(field_def, "validation"):
                vr = field_def.validation
                if vr:
                    regex_pattern = getattr(vr, "regex", None)

            # Verify we got it
            if regex_pattern:
                logger.debug(f"Found regex for field '{labels[0]}': {regex_pattern}")
            else:
                logger.debug(f"No regex found for field object: {field_def}")

        unique_labels = sorted(
            list(set([l for l in labels if l])), key=len, reverse=True
        )

        # Use only text from start_pos
        search_text = markdown[start_pos:]

        best_match = None
        best_match_end = -1

        # 2. Try each label
        for label in unique_labels:
            # CLEANUP: Standardize label by stripping common trailing symbols
            label_clean = re.sub(r"[:\-=.]+$", "", label).strip()
            # Support flexible spacing and newlines
            label_pattern = (
                re.escape(label_clean)
                .replace(r"\ ", r"\s+")
                .replace(r"\\n", r"[\s\n]+")
            )

            # Lookahead: Stop at another field label, a pipe, or end of string
            # PRIORITIZE specific labels from template
            lookahead_parts = []
            if boundary_labels:
                for bl in boundary_labels:
                    bl_clean = re.sub(r"[:\-=.]+$", "", bl).strip()
                    # Skip if it's the current label or too similar
                    if (
                        bl_clean.lower() != label_clean.lower()
                        and bl_clean.lower() not in label_clean.lower()
                    ):
                        bl_pattern = (
                            re.escape(bl_clean)
                            .replace(r"\ ", r"\s+")
                            .replace(r"\\n", r"[\s\n]+")
                        )
                        lookahead_parts.append(rf"(?:^|\||\s){bl_pattern}")

            # Generic lookahead
            lookahead_parts.append(r"\s+[A-Z][a-zA-Z0-9./()&._]{3,}\s*[:\-=]")
            lookahead_parts.append(r"\|")
            lookahead_parts.append(r"$")

            lookahead = "|".join(lookahead_parts)
            boundary = r"\b" if label_clean[-1].isalnum() else ""
            pattern = rf"(?:^|\||\s){label_pattern}{boundary}[.\s]*?[:\-=]*\s*?(.*?)(?={lookahead})"

            match = re.search(pattern, search_text, re.IGNORECASE | re.DOTALL)

            if match:
                val = match.group(1).strip()
                # Value cleaning
                val = re.sub(r"^[.\s:\-=|]+", "", val).strip()
                val = re.sub(r"Signature[:\s]*", "", val, flags=re.IGNORECASE).strip()
                val = re.sub(r"[.\s:\-=|]+$", "", val).strip()

                # If it's a short field, don't let it be multiline by default
                if "\n" in val and len(val) < 100:
                    val = val.split("\n")[0].strip()

                # VALIDATION
                if regex_pattern:
                    if not re.search(regex_pattern, val):
                        logger.debug(
                            f"Value '{val}' failed regex '{regex_pattern}' for label '{label}'"
                        )
                        continue

                # Return valid match even if value is empty (e.g. anchor fields)
                if val is not None:
                    return val, start_pos + match.end()

        # FALLBACK: Direct Regex Extraction
        # If label search failed but a custom regex is provided, try extracting with it directly
        display_label = fallback_name or (labels[0] if labels else "Unknown")

        if regex_pattern:
            logger.debug(
                f"Attempting fallback regex for '{display_label}' with pattern '{regex_pattern}'"
            )
            # Use the original search_text (or markdown subset)
            direct_match = re.search(
                regex_pattern, search_text, re.IGNORECASE | re.DOTALL
            )
            if direct_match:
                if direct_match.groups():
                    val = direct_match.group(1).strip()
                else:
                    val = direct_match.group(0).strip()
                logger.debug(
                    f"Direct Regex extraction success for '{display_label}': '{val[:50]}...'"
                )
                return val, start_pos + direct_match.end()
            else:
                logger.debug(f"Fallback regex failed for '{display_label}'")

        logger.warning(
            f"Could not extract value for label '{fallback_name or 'Unknown'}'"
        )
        return None, start_pos

    def extract_table_data(
        self, markdown: str, table_config: Optional[TableConfig] = None
    ) -> List[Dict[str, str]]:
        """
        Parses all markdown tables and returns a flattened list of rows.
        Supports dynamic header promotion if a row looks like a more relevant header.
        """
        all_rows = []
        if not markdown:
            return all_rows

        lines = markdown.splitlines()
        header_cols = []
        in_table = False
        temp_rows = []

        current_section = None
        active_table_section = None

        for i, line in enumerate(lines):
            line_strip = line.strip()

            # Track Section Headers
            header_match = re.match(r"^#+\s*(.*)", line_strip)
            if header_match:
                current_section = header_match.group(1).strip()

            is_pipe = "|" in line_strip

            # Detect table separator |---|
            if re.match(r"^\s*\|[-\s|]+\|\s*$", line_strip):
                if i > 0 and "|" in lines[i - 1]:
                    # FLUSH PREVIOUS TABLE DATA IF EXISTS
                    if temp_rows and header_cols:
                        for cells in temp_rows:
                            row_dict = {}
                            for k, col_name in enumerate(header_cols):
                                if k < len(cells):
                                    row_dict[col_name] = re.sub(
                                        r"\*\*|\*", "", cells[k]
                                    ).strip()
                                else:
                                    row_dict[col_name] = ""
                            if active_table_section:
                                row_dict["_table_name"] = active_table_section
                            all_rows.append(row_dict)
                        temp_rows = []
                        # RESET headers too? usually yes for a new table structure
                        header_cols = []

                    header_line = lines[i - 1]
                    header_parts = header_line.split("|")
                    if len(header_parts) > 0 and not header_parts[0].strip():
                        header_parts = header_parts[1:]
                    if len(header_parts) > 0 and not header_parts[-1].strip():
                        header_parts = header_parts[:-1]

                    header_cols = [
                        re.sub(r"\*\*|\*", "", c).strip() for c in header_parts
                    ]
                    header_cols = [
                        c if c else f"Col_{j}" for j, c in enumerate(header_cols)
                    ]

                    logger.debug(f"Detected table headers: {header_cols}")
                    in_table = True
                    active_table_section = current_section
                    continue

            # HEURISTIC: Loose tables (consecutive piped lines)
            if not in_table and is_pipe and line_strip.count("|") >= 2:
                if i < len(lines) - 1 and lines[i + 1].strip().count("|") >= 2:
                    current_headers = [c.strip() for c in line.split("|") if c.strip()]
                    if any(h for h in current_headers):
                        header_parts = line.split("|")
                        if len(header_parts) > 0 and not header_parts[0].strip():
                            header_parts = header_parts[1:]
                        if len(header_parts) > 0 and not header_parts[-1].strip():
                            header_parts = header_parts[:-1]

                        header_cols = [
                            re.sub(r"\*\*|\*", "", c).strip() for c in header_parts
                        ]
                        header_cols = [
                            c if c else f"Col_{j}" for j, c in enumerate(header_cols)
                        ]
                        logger.debug(f"Detected heuristic table headers: {header_cols}")
                        in_table = True
                        active_table_section = current_section
                        continue

            if in_table:
                # Table row processing
                if is_pipe:
                    cells = [c.strip() for c in line.split("|")]
                    # Remove first/last empty cells from pipe split
                    if len(cells) > 0 and not cells[0]:
                        cells = cells[1:]
                    if len(cells) > 0 and not cells[-1]:
                        cells = cells[:-1]

                    # Merge Logic for Multi-line rows
                    if temp_rows and header_cols:
                        prev_cells = temp_rows[-1]
                        expected_cols = len(header_cols)
                        # If previous row is incomplete and this line continues it
                        if len(prev_cells) < expected_cols and cells:
                            # Merge: append current cells to previous row
                            # Handle case where first cell of continuation may be part of last cell
                            if prev_cells and cells[0]:
                                # Check if first cell looks like a continuation (no sr.no pattern)
                                first_cell = cells[0].strip()
                                if first_cell and not re.match(
                                    r"^\d+\)?\s*$", first_cell
                                ):
                                    # Merge first cell with last cell of previous row
                                    temp_rows[-1][-1] = (
                                        f"{prev_cells[-1]} {first_cell}".strip()
                                    )
                                    cells = cells[1:]  # Remove merged cell
                            temp_rows[-1].extend(cells)
                            continue

                    # --- Template-Driven Header Promotion ---
                    row_text = " ".join(cells).lower()
                    idx_keys = (
                        table_config.index_column_keywords
                        if table_config
                        else ["sr. no", "index"]
                    )
                    hdr_keys = (
                        table_config.header_identifier_keywords
                        if table_config
                        else ["parameter", "test", "field"]
                    )

                    is_index_row = any(k in row_text for k in idx_keys)
                    is_header_row = any(k in row_text for k in hdr_keys)

                    if is_index_row and is_header_row:
                        header_cols = [re.sub(r"\*\*|\*", "", c).strip() for c in cells]
                        header_cols = [
                            c if c else f"Col_{j}" for j, c in enumerate(header_cols)
                        ]
                        logger.debug(f"Promoted row to headers: {header_cols}")
                        continue

                    # --- Row Collection ---
                    temp_rows.append(cells)
                elif temp_rows and not line_strip:
                    # Allow one blank line inside table
                    if i < len(lines) - 1 and "|" not in lines[i + 1]:
                        in_table = False
                        if temp_rows and header_cols:
                            for cells in temp_rows:
                                row_dict = {}
                                for k, col_name in enumerate(header_cols):
                                    if k < len(cells):
                                        val = re.sub(r"\*\*|\*", "", cells[k]).strip()
                                        row_dict[col_name] = val
                                    else:
                                        row_dict[col_name] = ""
                                if active_table_section:
                                    row_dict["_table_name"] = active_table_section
                                all_rows.append(row_dict)
                        temp_rows = []
                        header_cols = []
                else:
                    in_table = False
                    if temp_rows and header_cols:
                        for cells in temp_rows:
                            row_dict = {}
                            for k, col_name in enumerate(header_cols):
                                if k < len(cells):
                                    val = re.sub(r"\*\*|\*", "", cells[k]).strip()
                                    row_dict[col_name] = val
                                else:
                                    row_dict[col_name] = ""
                            if active_table_section:
                                row_dict["_table_name"] = active_table_section
                            all_rows.append(row_dict)
                    temp_rows = []
                    header_cols = []

        # Build final row dictionaries
        for cells in temp_rows:
            row_dict = {}
            for k, col_name in enumerate(header_cols):
                if k < len(cells):
                    val = re.sub(r"\*\*|\*", "", cells[k]).strip()
                    row_dict[col_name] = val
                else:
                    row_dict[col_name] = ""
            if active_table_section:
                row_dict["_table_name"] = active_table_section
            all_rows.append(row_dict)

        logger.debug(f"Extracted {len(all_rows)} table rows total")
        return all_rows

    def map_extracted_data(
        self, markdown: str, fields_def: List[FieldDefinition]
    ) -> Dict[str, str]:
        results = {}
        current_pos = 0
        for f_def in fields_def:
            val, current_pos = self.extract_field(
                markdown, f_def, start_pos=current_pos
            )
            results[f_def.name] = val
        return results

    def process_nested_template(self, markdown: str, template: Any) -> Dict[str, Any]:
        """Processes a nested template structure (Header, Table, Footer)."""
        results = {"headers": {}, "rows": [], "footers": {}}
        ext = template

        # 1. Extract Header Fields
        header_cursor = 0
        if ext.header_fields:
            # Collect all labels as boundaries to prevent greedy consumption
            boundary_labels = []
            for key, config in ext.header_fields.items():
                if isinstance(config, str):
                    boundary_labels.append(config)
                else:
                    lbl = getattr(config, "label", None)
                    if lbl:
                        boundary_labels.append(lbl)
                    if hasattr(config, "expected_label") and config.expected_label:
                        boundary_labels.extend(config.expected_label)

            for key, config in ext.header_fields.items():
                # Handle simplified string config (backwards compatibility)
                if isinstance(config, str):
                    val, end_pos = self.extract_field(
                        markdown,
                        FieldDefinition(
                            name=key, type=FieldType.STRING, expected_label=[config]
                        ),
                        boundary_labels=boundary_labels,
                        start_pos=header_cursor,
                    )
                else:
                    val, end_pos = self.extract_field(
                        markdown,
                        config,
                        fallback_name=key,
                        boundary_labels=boundary_labels,
                        start_pos=header_cursor,
                    )

                # Update cursor if something was found (even if empty string)
                if val is not None:
                    header_cursor = end_pos

                results["headers"][key] = {
                    "value": val,
                    "config": config,
                }

        # 2. Extract Table Rows
        if ext.test_parameters_table or (
            ext.table_config and ext.table_config.dynamic_rows
        ):
            all_raw_rows = self.extract_table_data(markdown, ext.table_config)

            # Dynamic Rows Extraction
            if ext.table_config and ext.table_config.dynamic_rows:
                for raw_row in all_raw_rows:
                    # Construct a generic result object for each row
                    # We use the first column as the "parameter" for identification if possible
                    keys = list(raw_row.keys())
                    param_col = (
                        keys[1] if len(keys) >= 2 else (keys[0] if keys else "Unknown")
                    )

                    results["rows"].append(
                        {
                            "config": {"parameter": raw_row.get(param_col, "Row")},
                            "extracted": raw_row,
                        }
                    )

            # Template-based Extraction (Legacy/Fixed)
            elif ext.test_parameters_table:
                from thefuzz import fuzz

                for row_tpl in ext.test_parameters_table:
                    highest_score = 0
                    best_match = None

                    kw_param = (
                        ext.table_config.parameter_column_keywords
                        if ext.table_config
                        else ["parameter", "test"]
                    )

                    for raw_row in all_raw_rows:
                        is_explicit_param_col = False
                        param_key = next(
                            (
                                k
                                for k in raw_row.keys()
                                if any(kw.lower() in k.lower() for kw in kw_param)
                            ),
                            None,
                        )

                        if param_key:
                            is_explicit_param_col = True
                        else:
                            keys = list(raw_row.keys())
                            if len(keys) >= 2:
                                param_key = keys[1]
                            else:
                                continue

                        val = raw_row[param_key]
                        if len(row_tpl.parameter) <= 3:
                            score = fuzz.ratio(row_tpl.parameter.lower(), val.lower())
                        else:
                            score = fuzz.partial_ratio(
                                row_tpl.parameter.lower(), val.lower()
                            )

                        if is_explicit_param_col:
                            score += 5

                        if score > 85 and score > highest_score:
                            highest_score = score
                            best_match = raw_row

                    if best_match:
                        results["rows"].append(
                            {"config": row_tpl, "extracted": best_match}
                        )

        # 3. Extract Footers
        if ext.footer_fields:
            footer_labels = []
            for cfg in ext.footer_fields.values():
                if isinstance(cfg, list):
                    footer_labels.extend(cfg)
                elif hasattr(cfg, "label"):
                    footer_labels.append(cfg.label)
                elif isinstance(cfg, dict) and "label" in cfg:
                    footer_labels.append(cfg["label"])

            noise_list = ext.noise_markers or []
            # Reuse all_raw_rows if available, otherwise extract once
            if "all_raw_rows" not in locals():
                all_raw_rows = self.extract_table_data(markdown, ext.table_config)

            # Use a separate cursor for footer extraction
            footer_cursor = 0

            for key, config in ext.footer_fields.items():
                # Handle list (legacy)
                if isinstance(config, list):
                    for i, label in enumerate(config):
                        raw_val, footer_cursor = self.extract_field(
                            markdown,
                            FieldDefinition(
                                name=f"{key}_{i}",
                                type=FieldType.STRING,
                                expected_label=[label],
                            ),
                            boundary_labels=footer_labels,
                            start_pos=footer_cursor,
                        )
                        if not raw_val:
                            for row in all_raw_rows:
                                if any(
                                    label.lower() in str(v).lower()
                                    for v in row.values()
                                ) or any(
                                    label.lower() in str(k).lower() for k in row.keys()
                                ):
                                    best_col = next(
                                        (
                                            k
                                            for k in row.keys()
                                            if label.lower() in k.lower()
                                        ),
                                        None,
                                    )
                                    if best_col:
                                        raw_val = row[best_col]
                                    else:
                                        for v in row.values():
                                            if label.lower() in str(v).lower():
                                                raw_val = str(v)
                                                break
                                    if raw_val:
                                        break
                        results["footers"][f"{key}_{i}"] = {
                            "value": raw_val,
                            "config": {"label": label},
                        }
                    continue

                # Standard Field (Dict)
                label = (
                    config.label
                    if (hasattr(config, "label") and config.label)
                    else (config.get("label") if isinstance(config, dict) else key)
                )
                raw_val, footer_cursor = self.extract_field(
                    markdown,
                    FieldDefinition(
                        name=key, type=FieldType.STRING, expected_label=[label]
                    ),
                    boundary_labels=footer_labels,
                    start_pos=footer_cursor,
                )

                if not raw_val:
                    for row in all_raw_rows:
                        # Check keys
                        best_col = next(
                            (k for k in row.keys() if label.lower() in k.lower()), None
                        )
                        if best_col and row[best_col]:
                            raw_val = row[best_col]
                            break
                        # Check values
                        for v in row.values():
                            if label.lower() in str(v).lower():
                                raw_val = str(v)
                                idx = raw_val.lower().find(label.lower())
                                raw_val = raw_val[idx + len(label) :].strip()
                                break
                        if raw_val:
                            break

                if raw_val:
                    raw_val = re.sub(r"^[ :\-=]+", "", raw_val).strip()
                    for marker in noise_list:
                        idx = raw_val.upper().find(marker.upper())
                        if idx != -1:
                            raw_val = raw_val[:idx].strip()

                results["footers"][key] = {"value": raw_val, "config": config}

        return results
