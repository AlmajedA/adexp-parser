from adexp_subfield_validator import SubfieldValidator

v = SubfieldValidator("config/ADEXP_auxiliary_terms.xml",
                      "config/ADEXP_subfields.xml")

print(v.validate("NETWORKTYPE", "- NETWORKTYPE SITA"))  # → True
print(v.validate("NETWORKTYPE", "- NETWORKTYPE X"))     # → False (only 1 char)
print(v.validate("NETWORKTYPE", "- NETWORKTYPE SITA1234"))  # → True
print(v.validate("NETWORKTYPE", "- NETWORKTYPE SITA1234567"))  # → False (>10)
# ---------- BRNG (3 aux‑terms) ------------------------------------
print(v.validate("BRNG", "-    BRNG 045"))    # ✅ True
print(v.validate("BRNG", "- BRNG 359"))    # ✅ True
print(v.validate("BRNG", "- BRNG 12"))     # ❌ False  (only 2 digits)
print(v.validate("BRNG", "BRNG 045"))      # ❌ False  (missing dash)

# # # # ---------- ADID (1 aux‑term) -------------------------------------
print(v.validate("ADID", "- ADID OMDB"))          # ✅ True   (ICAO aerodrome)
print(v.validate("ADID", "ZZZZ"))          # ✅ True   ('ZZZZ' is 4 letters)
print(v.validate("ADID", "OMA"))           # ❌ False  (3 letters)
print(v.validate("ADID", "OM4A"))          # ❌ False  (digit not allowed)

# print(v.validate("EOBT", "-EOBT 0930"))                        # True
# v.validate("AD",
#   "-AD -ADID OMDB -ETO 0930 -FL F350")                    # True
# v.validate("LRCA",
#   "-BEGIN LRCA -AIRSPACE OBBB -AIRSPACE OIRR -END LRCA")  # True
