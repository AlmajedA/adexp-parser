"""
adexp_subfield_validator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Build one regex per <SubField> that consists only of <AuxTermRef>s
(no nested <SubFieldRef> yet) and validate text strings against them.

Dash token  : zero‑or‑more blanks     (-BRNG 123, - BRNG 123)
Other tokens: one‑or‑more blanks      (BRNG 123 456)
"""

from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict

# ----------------------------------------------------------------------
# Regular‑expression snippets
# ----------------------------------------------------------------------
DASH_SEP_PATTERN = r"[ \r\n]*"   # between dash and next token: 0+ blanks
SEP_PATTERN      = r"[ \r\n]+"   # between all other tokens   : 1+ blanks

# ----------------------------------------------------------------------
class SubfieldValidator:
    """Compile regexes for every <SubField> that only references AuxTermRef."""

    def __init__(
        self,
        aux_xml: str | Path,
        sub_xml: str | Path,
        *,
        debug: bool = False,
    ) -> None:
        self.debug      = debug
        self.aux_regex  = self._load_aux_terms(aux_xml)
        self.sub_regex  = self._build_subfield_regexes(sub_xml)

    # ------------------------------------------------------------------
    # 1. Load auxiliary terms
    # ------------------------------------------------------------------
    def _load_aux_terms(self, fname: str | Path) -> Dict[str, str]:
        tree = ET.parse(fname)
        tag  = self._tag_in(tree.getroot(),
                            "AuxiliaryTerm", "AuxilliaryTerm")
        aux  = {el.get("id"): el.get("regexp") for el in tree.iter(tag)}

        # Fast sanity‑check: make sure all regexes compile
        for k, pat in aux.items():
            try:
                re.compile(pat)
            except re.error as e:  # pragma: no cover
                raise ValueError(
                    f"Regex for AuxTerm '{k}' does not compile: {e}"
                ) from None
        return aux

    # ------------------------------------------------------------------
    # 2. Build sub‑field regexes (aux‑only)
    # ------------------------------------------------------------------
    def _build_subfield_regexes(self, fname: str | Path) -> Dict[str, re.Pattern]:
        tree   = ET.parse(fname)
        result: Dict[str, re.Pattern] = {}

        for sf in tree.iter("SubField"):
            sf_id = sf.get("id")

            # skip composite sub‑fields containing other sub‑field refs
            if sf.findall("./SubFieldRef"):
                if self.debug:
                    print(f"[skip] {sf_id} – contains nested SubFieldRef")
                continue

            aux_refs = [ref.get("ref") for ref in sf.findall("./AuxTermRef")]

            if not aux_refs:  # pragma: no cover
                if self.debug:
                    print(f"[skip] {sf_id} – no AuxTermRef children")
                continue

            pieces: list[str] = []
            for idx, aux_id in enumerate(aux_refs):
                pat = self.aux_regex.get(aux_id)
                if pat is None:
                    raise KeyError(
                        f"AuxTerm '{aux_id}' used by SubField '{sf_id}' not found"
                    )

                # prepend a separator before every token but the first
                if idx > 0:
                    prev_aux = aux_refs[idx - 1]
                    sep      = (DASH_SEP_PATTERN if prev_aux == "literal_dash"
                                else SEP_PATTERN)
                    pieces.append(sep)

                pieces.append(pat)

            full_pat = r"^" + "".join(pieces) + r"$"
            result[sf_id] = re.compile(full_pat)

            if self.debug:
                print(f"[build] {sf_id}: {full_pat}")

        return result

    # ------------------------------------------------------------------
    # 3. Public API
    # ------------------------------------------------------------------
    def validate(self, subfield_id: str, text: str) -> bool:
        """Return True iff *text* matches the compiled regex for *subfield_id*."""
        rx = self.sub_regex.get(subfield_id)
        if rx is None:
            raise KeyError(
                f"Sub‑field '{subfield_id}' not built "
                "(contains nested sub‑fields or unknown)"
            )
        return bool(rx.match(text))

    # ------------------------------------------------------------------
    # helpers
    @staticmethod
    def _tag_in(root: ET.Element, *names: str) -> str:
        """Return the first tag name actually present in the document."""
        for n in names:
            if root.find(f".//{n}") is not None:
                return n
        raise ValueError("No AuxiliaryTerm tag found (check tag spelling)")

# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse, sys

    p = argparse.ArgumentParser(
        description="Validate an ADEXP sub‑field against XML definitions"
    )
    p.add_argument("subfield_id", help="e.g. BRNG")
    p.add_argument("text", help="the raw text to validate")
    p.add_argument("--aux", default="ADEXP_auxiliary_terms.xml")
    p.add_argument("--sub", default="ADEXP_subfields.xml")
    p.add_argument("-d", "--debug", action="store_true",
                   help="print the generated regexes")
    args = p.parse_args()

    v   = SubfieldValidator(args.aux, args.sub, debug=args.debug)
    ok  = v.validate(args.subfield_id, args.text)
    sys.exit(0 if ok else 1)
