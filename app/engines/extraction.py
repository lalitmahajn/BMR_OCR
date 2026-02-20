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

    def _normalize_columns(
        self, raw_rows: List[Dict[str, str]], column_mapping: Dict[str, List[str]]
    ) -> List[Dict[str, str]]:
        """Maps OCR column headers to normalized template keys using fuzzy matching."""
        from thefuzz import fuzz

        # Build mapping: OCR header → normalized key (cached for all rows)
        header_map = {}
        if raw_rows:
            sample_keys = list(raw_rows[0].keys())
            for raw_key in sample_keys:
                if raw_key.startswith("_"):
                    header_map[raw_key] = raw_key  # Preserve internal keys
                    continue
                best_score = 0
                best_norm = None
                for norm_key, aliases in column_mapping.items():
                    for alias in aliases:
                        score = fuzz.ratio(alias.lower(), raw_key.lower())
                        if score > best_score and score > 70:
                            best_score = score
                            best_norm = norm_key
                header_map[raw_key] = best_norm or raw_key

        normalized = []
        for row in raw_rows:
            new_row = {}
            for raw_key, val in row.items():
                norm_key = header_map.get(raw_key, raw_key)
                new_row[norm_key] = val
            normalized.append(new_row)
        return normalized

    def extract_field(
        self,
        markdown: str,
        field_def: Union[Dict, ConfigField],
        boundary_labels: Optional[List[str]] = None,
        fallback_name: Optional[str] = None,
        start_pos: int = 0,
    ) -> (Optional[str], int, float):
        """
        Extracts a single field value based on expected labels and regex.
        Uses lookahead to avoid consuming adjacent fields.
        Returns extracted value, end position, and confidence score.
        """
        if not markdown:
            return None, start_pos, 0.0

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
                    # Regex Passed + Label Found = High Confidence
                    if val is not None:
                        return val, start_pos + match.end(), 0.95

                # Label Found (No Regex or No Validation) = Medium Confidence
                if val is not None:
                    return val, start_pos + match.end(), 0.80

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
                # Regex Fallback (No Label) = Low Confidence
                return val, start_pos + direct_match.end(), 0.70
            else:
                logger.debug(f"Fallback regex failed for '{display_label}'")

        logger.warning(
            f"Could not extract value for label '{fallback_name or 'Unknown'}'"
        )
        return None, start_pos, 0.0

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

                        # NEW: Handle wrapped lines (previous row full, current row short)
                        if (
                            len(prev_cells) == expected_cols
                            and len(cells) < expected_cols
                        ):
                            # Heuristic: If line doesn't start with pipe, it's likely a wrap
                            if not line_strip.startswith("|"):
                                # Append all content to the last cell of previous row
                                joined_content = " ".join(cells)
                                temp_rows[-1][-1] = (
                                    f"{prev_cells[-1]} {joined_content}".strip()
                                )
                                continue

                        # Existing Merge: If previous row is incomplete and this line continues it
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
            val, current_pos, confidence = self.extract_field(
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
                    val, end_pos, confidence = self.extract_field(
                        markdown,
                        FieldDefinition(
                            name=key, type=FieldType.STRING, expected_label=[config]
                        ),
                        boundary_labels=boundary_labels,
                        start_pos=header_cursor,
                    )
                else:
                    val, end_pos, confidence = self.extract_field(
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
                    "confidence": confidence,
                    "config": config,
                }

        # 2. Extract Named Tables (new format)
        if ext.tables:
            all_raw_rows = self.extract_table_data(markdown, ext.table_config)
            results["tables"] = {}

            for table_name, table_cfg in ext.tables.items():
                # Filter rows by section_header if specified
                if table_cfg.section_header:
                    from thefuzz import fuzz

                    matched_rows = []
                    in_section = False
                    for row in all_raw_rows:
                        section = row.get("_table_name", "")
                        if (
                            section
                            and fuzz.partial_ratio(
                                table_cfg.section_header.lower(), section.lower()
                            )
                            > 75
                        ):
                            in_section = True
                        elif section and in_section:
                            # New section started, stop collecting
                            break
                        if in_section:
                            matched_rows.append(row)

                    if not matched_rows:
                        # Fallback: try matching column headers
                        if table_cfg.column_mapping:
                            target_cols = set()
                            for aliases in table_cfg.column_mapping.values():
                                target_cols.update(a.lower() for a in aliases)
                            for row in all_raw_rows:
                                row_cols = set(
                                    k.lower()
                                    for k in row.keys()
                                    if not k.startswith("_")
                                )
                                overlap = sum(
                                    1
                                    for tc in target_cols
                                    if any(fuzz.ratio(tc, rc) > 70 for rc in row_cols)
                                )
                                if overlap >= 2:
                                    matched_rows.append(row)
                    table_rows = matched_rows
                else:
                    # No section_header — try column-header matching
                    if table_cfg.column_mapping:
                        from thefuzz import fuzz

                        target_cols = set()
                        for aliases in table_cfg.column_mapping.values():
                            target_cols.update(a.lower() for a in aliases)

                        matched_rows = []
                        for row in all_raw_rows:
                            row_cols = set(
                                k.lower() for k in row.keys() if not k.startswith("_")
                            )
                            overlap = sum(
                                1
                                for tc in target_cols
                                if any(fuzz.ratio(tc, rc) > 70 for rc in row_cols)
                            )
                            if overlap >= 2:
                                matched_rows.append(row)
                        table_rows = matched_rows if matched_rows else all_raw_rows
                    else:
                        table_rows = all_raw_rows

                # Normalize columns using column_mapping
                if table_cfg.column_mapping and table_rows:
                    table_rows = self._normalize_columns(
                        table_rows, table_cfg.column_mapping
                    )

                # Store as dynamic rows with config
                results["tables"][table_name] = []
                for raw_row in table_rows:
                    keys = list(raw_row.keys())
                    param_col = (
                        keys[1] if len(keys) >= 2 else (keys[0] if keys else "Unknown")
                    )
                    tpl = TableRowTemplate(parameter=str(raw_row.get(param_col, "Row")))
                    results["tables"][table_name].append(
                        {"config": tpl, "extracted": raw_row}
                    )

                logger.info(
                    f"Table '{table_name}': extracted {len(results['tables'][table_name])} rows"
                )

        # 2b. Extract Single Table (legacy format — backward compatible)
        elif ext.test_parameters_table or (
            ext.table_config and ext.table_config.dynamic_rows
        ):
            all_raw_rows = self.extract_table_data(markdown, ext.table_config)

            # Normalize columns if column_mapping is present
            if ext.table_config and ext.table_config.column_mapping and all_raw_rows:
                all_raw_rows = self._normalize_columns(
                    all_raw_rows, ext.table_config.column_mapping
                )

            # Dynamic Rows Extraction
            if ext.table_config and ext.table_config.dynamic_rows:
                for raw_row in all_raw_rows:
                    keys = list(raw_row.keys())
                    param_col = (
                        keys[1] if len(keys) >= 2 else (keys[0] if keys else "Unknown")
                    )

                    tpl = TableRowTemplate(parameter=str(raw_row.get(param_col, "Row")))

                    results["rows"].append(
                        {
                            "config": tpl,
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
                    else:
                        # Ensure the parameter appears in the output even if not found
                        results["rows"].append({"config": row_tpl, "extracted": {}})

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
                        raw_val, footer_cursor, confidence = self.extract_field(
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
                            # Fallback to table search (Low Confidence)
                            confidence = 0.6
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
                            "confidence": confidence,
                            "config": {"label": label},
                        }
                    continue

                # Standard Field (Dict)
                label = (
                    config.label
                    if (hasattr(config, "label") and config.label)
                    else (config.get("label") if isinstance(config, dict) else key)
                )
                raw_val, footer_cursor, confidence = self.extract_field(
                    markdown,
                    FieldDefinition(
                        name=key, type=FieldType.STRING, expected_label=[label]
                    ),
                    boundary_labels=footer_labels,
                    start_pos=footer_cursor,
                )

                if not raw_val:
                    # Fallback to table search
                    confidence = 0.6
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

                results["footers"][key] = {
                    "value": raw_val,
                    "confidence": confidence,
                    "config": config,
                }

        return results

    def extract_packing_details(self, markdown: str, template: Any) -> Dict[str, Any]:
        """
        Specialized extraction for Packing Details (P27, P28).
        Handles headers embedded within table rows.
        """
        # 1. Standard Extraction first
        base_res = self.process_nested_template(markdown, template)

        # 2. Extract Embedded Headers from Rows
        header_data = base_res.get("headers", {})
        all_rows = [r["extracted"] for r in base_res["rows"]]
        packing_rows = []

        # Track processed rows to skip them in the final body table
        processed_row_indices = set()

        for i, row in enumerate(all_rows):
            row_vals = list(row.values())
            row_text = " ".join([str(v) for v in row_vals]).lower()

            # --- Embedded Header Detection Logic ---

            # Product Name & Batch No
            if "name of product" in row_text:
                processed_row_indices.add(i)
                for val in row_vals:
                    v_str = str(val)
                    if "Name of Product" in v_str:
                        prod_match = re.search(
                            r"Name\s*of\s*Product\s*[:\\-]*\s*(.*?)\s*(?:Batch|$)",
                            v_str,
                            re.IGNORECASE,
                        )
                        if prod_match:
                            val = prod_match.group(1).strip()
                            if val:
                                header_data["PRODUCT_NAME"] = {
                                    "value": val,
                                    "confidence": 0.90,
                                    "config": "PRODUCT_NAME",
                                }

                        batch_match = re.search(
                            r"Batch\s*No\\.?\s*[:\\-]*\s*(.*)", v_str, re.IGNORECASE
                        )
                        if batch_match:
                            val = batch_match.group(1).strip()
                            if val:
                                header_data["BATCH_NO"] = {
                                    "value": val,
                                    "confidence": 0.90,
                                    "config": "BATCH_NO",
                                }

            # Total Qty & Tare Wet
            if "total qty" in row_text:
                processed_row_indices.add(i)
                for val in row_vals:
                    v_str = str(val)
                    if "Total Qty" in v_str:
                        qty_match = re.search(
                            r"Total\s*Qty\s*[:\\-]*\s*(.*?)\s*(?:Tare|$)",
                            v_str,
                            re.IGNORECASE,
                        )
                        if qty_match:
                            header_data["TOTAL_QTY"] = {
                                "value": qty_match.group(1).strip(),
                                "confidence": 0.90,
                                "config": "TOTAL_QTY",
                            }

                        tare_match = re.search(
                            r"Tare\s*Wet\\.?\s*[:\\-]*\s*(.*)", v_str, re.IGNORECASE
                        )
                        if tare_match:
                            header_data["TARE_WT"] = {
                                "value": tare_match.group(1).strip(),
                                "confidence": 0.90,
                                "config": "TARE_WT",
                            }

            # Balance ID & Calibration
            if "balance id" in row_text:
                processed_row_indices.add(i)
                for val in row_vals:
                    v_str = str(val)
                    if "Balance ID" in v_str:
                        bal_match = re.search(
                            r"Balance\s*ID\\.?No\\.?\s*[:\\-]*\s*(.*?)\s*(?:Calibration|$)",
                            v_str,
                            re.IGNORECASE,
                        )
                        if bal_match:
                            header_data["BALANCE_ID"] = {
                                "value": bal_match.group(1).strip(),
                                "confidence": 0.90,
                                "config": "BALANCE_ID",
                            }

                        cal_match = re.search(
                            r"Calibration\s*status\s*[:\\-]*\s*(.*)",
                            v_str,
                            re.IGNORECASE,
                        )
                        if cal_match:
                            header_data["CALIBRATION_STATUS"] = {
                                "value": cal_match.group(1).strip(),
                                "confidence": 0.90,
                                "config": "CALIBRATION_STATUS",
                            }

            # Page Info / Ref BMR
            if "page no" in row_text and "PAGE_INFO" not in header_data:
                page_match = re.search(
                    r"Page\s*No\\.?[\s\\-]*(\d+\s*of\s*\\d+)", row_text, re.IGNORECASE
                )
                if page_match:
                    header_data["PAGE_INFO"] = {
                        "value": page_match.group(1),
                        "confidence": 0.90,
                        "config": "PAGE_INFO",
                    }

            if "ref. bmr no" in row_text and "REF_BMR_NO" not in header_data:
                bmr_match = re.search(
                    r"Ref\.\s*BMR\s*No\\.?\s*[:\\-]*\s*([\w\\-\\.]+)",
                    row_text,
                    re.IGNORECASE,
                )
                if bmr_match:
                    header_data["REF_BMR_NO"] = {
                        "value": bmr_match.group(1),
                        "confidence": 0.90,
                        "config": "REF_BMR_NO",
                    }

            # Identify valid body rows (Packing Table)
            # Heuristic: If it has "Drum No" or looks like data, and wasn't consumed as a header row
            if i not in processed_row_indices:
                # Filter out pure garbage/merged header fragments
                if "net wet =" in row_text or "gross wet =" in row_text:
                    continue  # Sub-header rows
                if any(k in row_text for k in ["drum no", "tare wt"]):
                    continue  # Table header row

                packing_rows.append(
                    {
                        "config": TableRowTemplate(parameter="Packing Entry"),
                        "extracted": row,
                    }
                )

        # Update results
        base_res["headers"] = header_data
        base_res["rows"] = packing_rows
        return base_res

    def extract_checklist(self, markdown: str, template: Any) -> Dict[str, Any]:
        """
        Specialized extraction for BMR Checklist (P29, P30).
        Interprets checkmarks (☑) as Status (Yes/No/NA).
        """
        base_res = self.process_nested_template(markdown, template)

        # Clean up Headers
        header_data = base_res.get("headers", {})
        if "DOCUMENT_NO" not in header_data or not header_data["DOCUMENT_NO"].get(
            "value"
        ):
            doc_match = re.search(
                r"DOCUMENT\s*NO\.?\s*\|\s*([\w\-/]+)", markdown, re.IGNORECASE
            )
            if doc_match:
                header_data["DOCUMENT_NO"] = {
                    "value": doc_match.group(1).strip(),
                    "confidence": 0.90,
                    "config": "DOCUMENT_NO",
                }

        base_res["headers"] = header_data

        # Process Rows for Checkmarks
        all_rows = [r["extracted"] for r in base_res["rows"]]
        checklist_rows = []

        for row in all_rows:
            row_vals = list(row.values())
            row_text = " ".join([str(v) for v in row_vals]).lower()

            # Skip header rows
            if "review points" in row_text or "attachments" in row_text:
                continue

            # Identify Status based on Checkmark position
            status = "PENDING"
            point = ""

            # Find the checkmark
            checkmark_col_idx = -1
            clean_values = [str(v).strip() for v in row_vals]

            # Find Point (longest text)
            longest_val = max(clean_values, key=len) if clean_values else ""
            if (
                len(longest_val) > 5
                and "☑" not in longest_val
                and "✓" not in longest_val
            ):
                point = longest_val

            # Find Status
            for idx, val in enumerate(clean_values):
                if "☑" in val or "✓" in val:
                    checkmark_col_idx = idx
                    break

            if checkmark_col_idx != -1:
                # Heuristic mapping for P29/P30
                # Usually: Sr(0) | Point(1) | Yes(2) | No(3) | NA(4)
                if checkmark_col_idx == 2:
                    status = "Yes"
                elif checkmark_col_idx == 3:
                    status = "No"
                elif checkmark_col_idx == 4:
                    status = "NA"
                else:
                    status = "Checked (Unknown Col)"

            if point:
                checklist_rows.append(
                    {
                        "config": TableRowTemplate(
                            parameter=point[:50].replace("\n", " ").strip() + "..."
                        ),  # Summary label
                        "extracted": {"Point": point, "Status": status},
                    }
                )

        base_res["rows"] = checklist_rows
        return base_res
