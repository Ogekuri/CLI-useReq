"""!
@file table_style.py
@brief Canonical glyph set and border composers for every CLI-generated table.
@details Single authoritative definition of the CLI table rendering style (SRS-636,
SRS-637, SRS-638): rounded corner borders, single-line content and inter-row
separators, and the double-line header-to-content separator. Pure formatting module
with no I/O and no intra-package dependencies so `usereq.config_cli` and `usereq.cli`
can both consume it.
@author useReq
@version 0.75.3
"""

from __future__ import annotations

from typing import Sequence

TABLE_TOP_LEFT = "╭"
"""! @brief Rounded top-left corner glyph of the top border (SRS-636)."""

TABLE_TOP_RIGHT = "╮"
"""! @brief Rounded top-right corner glyph of the top border (SRS-636)."""

TABLE_BOTTOM_LEFT = "╰"
"""! @brief Rounded bottom-left corner glyph of the bottom border (SRS-636)."""

TABLE_BOTTOM_RIGHT = "╯"
"""! @brief Rounded bottom-right corner glyph of the bottom border (SRS-636)."""

TABLE_HORIZONTAL = "─"
"""! @brief Single-line horizontal filler glyph of content borders (SRS-636)."""

TABLE_VERTICAL = "│"
"""! @brief Single-line vertical separator glyph of content rows (SRS-636)."""

TABLE_TOP_JUNCTION = "┬"
"""! @brief Single-line column junction glyph of the top border (SRS-636)."""

TABLE_BOTTOM_JUNCTION = "┴"
"""! @brief Single-line column junction glyph of the bottom border (SRS-636)."""

TABLE_ROW_LEFT = "├"
"""! @brief Single-line left junction glyph of an inter-row separator (SRS-638)."""

TABLE_ROW_JUNCTION = "┼"
"""! @brief Single-line column junction glyph of an inter-row separator (SRS-638)."""

TABLE_ROW_RIGHT = "┤"
"""! @brief Single-line right junction glyph of an inter-row separator (SRS-638)."""

TABLE_HEADER_FILL = "═"
"""! @brief Double-line horizontal filler glyph of the header separator (SRS-637)."""

TABLE_HEADER_LEFT = "╞"
"""! @brief Double-line left junction glyph of the header separator (SRS-637)."""

TABLE_HEADER_JUNCTION = "╪"
"""! @brief Double-line column junction glyph of the header separator (SRS-637)."""

TABLE_HEADER_RIGHT = "╡"
"""! @brief Double-line right junction glyph of the header separator (SRS-637)."""

TABLE_BORDER_GLYPHS = frozenset(
    TABLE_TOP_LEFT
    + TABLE_TOP_RIGHT
    + TABLE_BOTTOM_LEFT
    + TABLE_BOTTOM_RIGHT
    + TABLE_HORIZONTAL
    + TABLE_VERTICAL
    + TABLE_TOP_JUNCTION
    + TABLE_BOTTOM_JUNCTION
    + TABLE_ROW_LEFT
    + TABLE_ROW_JUNCTION
    + TABLE_ROW_RIGHT
    + TABLE_HEADER_FILL
    + TABLE_HEADER_LEFT
    + TABLE_HEADER_JUNCTION
    + TABLE_HEADER_RIGHT
)
"""!
@brief Every structural table glyph subject to ANSI border colorization (SRS-049).
@details Cell payload characters never appear in this set, so colorization preserves payload text.
"""


def top_border(widths: Sequence[int]) -> str:
    """!
    @brief Render the rounded top border line of one table.
    @details Composes TABLE_TOP_LEFT, one TABLE_HORIZONTAL filler segment of
    `width + 2` cells per column (one padding space per cell side),
    TABLE_TOP_JUNCTION between adjacent columns, and TABLE_TOP_RIGHT (SRS-636).
    @param widths {Sequence[int]} Column widths, one entry per table column.
    @return {str} Top border line such as `╭─────┬───────╮`.
    @satisfies SRS-636
    """
    return (
        TABLE_TOP_LEFT
        + TABLE_TOP_JUNCTION.join(TABLE_HORIZONTAL * (width + 2) for width in widths)
        + TABLE_TOP_RIGHT
    )


def header_separator(widths: Sequence[int]) -> str:
    """!
    @brief Render the double-line separator between the header row and the content rows.
    @details Composes TABLE_HEADER_LEFT, one TABLE_HEADER_FILL segment of
    `width + 2` cells per column, TABLE_HEADER_JUNCTION between adjacent columns, and
    TABLE_HEADER_RIGHT (SRS-637). Rendered exactly once per table, directly below the
    header row, so it stays the only double line of the table.
    @param widths {Sequence[int]} Column widths, one entry per table column.
    @return {str} Header separator line such as `╞═════╪═══════╡`.
    @satisfies SRS-637
    """
    return (
        TABLE_HEADER_LEFT
        + TABLE_HEADER_JUNCTION.join(
            TABLE_HEADER_FILL * (width + 2) for width in widths
        )
        + TABLE_HEADER_RIGHT
    )


def row_separator(widths: Sequence[int]) -> str:
    """!
    @brief Render the single-line separator between two content rows.
    @details Composes TABLE_ROW_LEFT, one TABLE_HORIZONTAL filler segment of
    `width + 2` cells per column, TABLE_ROW_JUNCTION between adjacent columns, and
    TABLE_ROW_RIGHT (SRS-638). Emitted only by tables that separate content rows.
    @param widths {Sequence[int]} Column widths, one entry per table column.
    @return {str} Inter-row separator line such as `├─────┼───────┤`.
    @satisfies SRS-638
    """
    return (
        TABLE_ROW_LEFT
        + TABLE_ROW_JUNCTION.join(TABLE_HORIZONTAL * (width + 2) for width in widths)
        + TABLE_ROW_RIGHT
    )


def bottom_border(widths: Sequence[int]) -> str:
    """!
    @brief Render the rounded bottom border line of one table.
    @details Composes TABLE_BOTTOM_LEFT, one TABLE_HORIZONTAL filler segment of
    `width + 2` cells per column, TABLE_BOTTOM_JUNCTION between adjacent columns, and
    TABLE_BOTTOM_RIGHT (SRS-636).
    @param widths {Sequence[int]} Column widths, one entry per table column.
    @return {str} Bottom border line such as `╰─────┴───────╯`.
    @satisfies SRS-636
    """
    return (
        TABLE_BOTTOM_LEFT
        + TABLE_BOTTOM_JUNCTION.join(TABLE_HORIZONTAL * (width + 2) for width in widths)
        + TABLE_BOTTOM_RIGHT
    )
