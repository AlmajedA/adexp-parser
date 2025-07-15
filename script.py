import xml.etree.ElementTree as ET

# Load and parse the XML
tree = ET.parse('config/ADEXP_auxiliary_terms.xml')  # Replace with your XML file path
root = tree.getroot()
# Find the element and get its attributes
for term in root.findall('AuxilliaryTerm'):
    name = term.get('name')
    regexp = term.get('regexp')
    print(f"Name: {name}, Regexp: {regexp}")
