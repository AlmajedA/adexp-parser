# primary_field_validator.py
# ---------------------------------------------------------------
# Needs:  adexp_subfield_validator.SubfieldValidator  (from earlier step)
#         ADEXP_auxiliary_terms.xml
#         ADEXP_subfields.xml
#         ADEXP_primary_fields.xml   (see previous message)
#
# Example -------------------------------------------------------
# pfv = PrimaryFieldValidator("config/ADEXP_auxiliary_terms.xml",
#                             "config/ADEXP_subfields.xml",
#                             "config/ADEXP_primary_fields.xml")
#
# pfv.validate("EOBT", "-EOBT 0930")                        # True
# pfv.validate("AD",
#   "-AD -ADID OMDB -ETO 0930 -FL F350")                    # True
# pfv.validate("LRCA",
#   "-BEGIN LRCA -AIRSPACE OBBB -AIRSPACE OIRR -END LRCA")  # True
# ---------------------------------------------------------------

from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Callable, List

from adexp_subfield_validator import SubfieldValidator, SEP_PATTERN, DASH_SEP_PATTERN

# ---------------------------------------------------------------------------
class PrimaryFieldValidator:
    """Validate the three example primary fields:  EOBT, AD, LRCA."""

    def __init__(
        self,
        aux_xml: str | Path,
        sub_xml: str | Path,
        prim_xml: str | Path,
        *,
        debug: bool = False,
    ) -> None:
        self.debug  = debug
        self.subval = SubfieldValidator(aux_xml, sub_xml, debug=debug)
        self.primary_specs = self._load_primary_specs(prim_xml)

        # dispatch table   id -> validator‑function
        self.handlers: Dict[str, Callable[[str], bool]] = {
            "EOBT": self._validate_eobt,
            "AD":   self._validate_ad,
            "LRCA": self._validate_lrca,
        }

    # -----------------------------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------------------------
    def validate(self, primary_id: str, text: str) -> bool:
        if primary_id not in self.handlers:
            raise KeyError(f"Primary field '{primary_id}' not supported yet")

        ok = self.handlers[primary_id](text)
        if self.debug:
            print(f"[{primary_id}] {text!r} -> {ok}")
        return ok

    # -----------------------------------------------------------------------
    # LOAD PRIMARY SPECS (only three rows at present)
    # -----------------------------------------------------------------------
    def _load_primary_specs(self, prim_xml: str | Path) -> Dict[str, ET.Element]:
        tree = ET.parse(prim_xml)
        return {pf.get("id"): pf for pf in tree.iter("PrimaryField")}

    # -----------------------------------------------------------------------
    # VALIDATORS
    # -----------------------------------------------------------------------
    # 1. BASIC  --------------------------------------------------------------
    def _validate_eobt(self, text: str) -> bool:
        """
        -EOBT <timehhmm>
        Accept 0+ blanks after dash, 1+ blank between keyword and value.
        """
        pat_keyword  = r"EOBT"
        pat_value    = self.subval.aux_regex["timehhmm"]
        full_rx = re.compile(
            r"^-" + DASH_SEP_PATTERN + pat_keyword +
            SEP_PATTERN + pat_value + r"$"
        )
        return bool(full_rx.match(text))

    # 2. COMPOUND  ----------------------------------------------------------
    def _validate_ad(self, text: str) -> bool:
        """
        Syntax: -AD <unordered bag of subfields>
        Each sub‑field itself starts with '-' <SUBID> …
        """
        # strip primary keyword --------------------------
        m = re.match(r"^-"+DASH_SEP_PATTERN+r"AD\b(.*)$", text, flags=re.I)
        if not m:
            return False
        rest = m.group(1).lstrip()

        # split on ' -' (dash that starts a new sub‑field)
        # keep the leading '-' for each chunk
        chunks = re.findall(r"(?:-(?:.|\r|\n)*?)(?=(?: -|$))", rest)
        seen: Dict[str, int] = {}
        for chunk in chunks:
            # the sub‑field id is first token after dash
            sf_match = re.match(r"^-"+DASH_SEP_PATTERN+r"([A-Z0-9]+)\b(.*)$", chunk.strip(), flags=re.I)
            if not sf_match:
                return False
            sf_id, body = sf_match.group(1).lower(), sf_match.group(0)
            # validate with SubfieldValidator (case insensitive)
            try:
                ok = self.subval.validate(sf_id.upper(), chunk.strip())
            except KeyError:
                ok = False
            if not ok:
                return False
            seen[sf_id] = seen.get(sf_id, 0) + 1

        # enforce min/max from XML ------------------------------------------
        spec = self.primary_specs["AD"]
        for sfref in spec.findall("./SubFieldRef"):
            ref = sfref.get("ref").lower()
            mn  = int(sfref.get("min", "0"))
            mx  = sfref.get("max")
            mx  = float("inf") if mx == "*" else int(mx)
            cnt = seen.get(ref, 0)
            if not (mn <= cnt <= mx):
                return False
        return True

    # 3. LIST  --------------------------------------------------------------
    def _validate_lrca(self, text: str) -> bool:
        """
        -BEGIN LRCA { -AIRSPACE … }+ -END LRCA
        """
        # BEGIN wrapper -----------------------------------------------------
        begin = r"^-"+DASH_SEP_PATTERN+r"BEGIN"+SEP_PATTERN+r"LRCA\b"
        end   = r"-"+DASH_SEP_PATTERN+r"END"+SEP_PATTERN+r"LRCA\b$"
        m = re.match(begin, text)
        if not m:
            return False
        if not re.search(end, text):
            return False
        middle = re.sub(begin, "", text, count=1)
        middle = re.sub(end, "", middle, count=1).strip()

        # split into list items --------------------------------------------
        items = re.findall(r"(?:-(?:.|\r|\n)*?)(?=(?: -|$))", middle)
        if not items:
            return False

        for item in items:
            if not self.subval.validate("AIRSPACE", item.strip()):
                return False
        return True


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse, sys

    p = argparse.ArgumentParser(
        description="Validate EOBT / AD / LRCA primary fields"
    )
    p.add_argument("primary_id", choices=["EOBT", "AD", "LRCA"])
    p.add_argument("text", help="raw text to validate (quote it)")
    p.add_argument("--aux", default="config/ADEXP_auxiliary_terms.xml")
    p.add_argument("--sub", default="config/ADEXP_subfields.xml")
    p.add_argument("--prim", default="config/ADEXP_primary_fields.xml")
    p.add_argument("-d", "--debug", action="store_true")
    args = p.parse_args()

    pfv = PrimaryFieldValidator(args.aux, args.sub, args.prim, debug=args.debug)
    ok  = pfv.validate(args.primary_id, args.text)
    sys.exit(0 if ok else 1)
