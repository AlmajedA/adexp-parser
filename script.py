import re
import xml.etree.ElementTree as ET

# 1) Load aux terms
aux_tree = ET.parse("config/ADEXP_auxiliary_terms.xml")
aux_terms = {
    elm.get("id"): elm.get("regexp")
    for elm in aux_tree.findall(".//AuxilliaryTerm")
}

# 2) Load subfields
sub_tree = ET.parse("config/ADEXP_subfields.xml")
for sf in sub_tree.findall(".//SubField"):
    sf_id   = sf.get("id")
    err_msg = sf.get("errmsg", "invalid value")

    # find the referenced AuxTerm
    ref_id  = sf.find("AuxTermRef").get("ref")
    pattern = aux_terms.get(ref_id)
    if pattern is None:
        raise KeyError(f"AuxTerm '{ref_id}' not found for SubField {sf_id}")

    regex = re.compile("^" + pattern + "$")

    # Example: validate a value (e.g. parsed from your ADEXP message)
    test_value = "123"  # replace with the actual text you extracted
    if not regex.match(test_value):
        print(f"{sf_id!r} failed validation: {err_msg!r}")
    else:
        print(f"{sf_id!r} OK ✓")
