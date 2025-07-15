# ADEXP Parser Script

def decode_basic(line):
    line = line.strip()
    
def parse_adexp(message):
    lines = message.strip().splitlines()
    result = {}
    stack = []
    current_list = None
    current_key = None

    for line in lines:
        line = line.strip()
        if not line.startswith('-'):
            continue

        tokens = line.split()
        if not tokens:
            continue

        key = tokens[0][1:] # [1:] to remove the -
        values = tokens[1:]
        if key == 'BEGIN':
            current_list = []
            current_key = values[0]
            stack.append((current_key, current_list))
        elif key == 'END':
            if stack:
                k, v = stack.pop()
                result[k] = v
            current_list = None
            current_key = None
        elif current_list is not None:
            subfields = {}
            i = 0
            while i < len(tokens):
                if tokens[i].startswith('-'):
                    subkey = tokens[i][1:]
                    i += 1
                    subval = []
                    # Basic Fields
                    while i < len(tokens) and not tokens[i].startswith('-'): # Add subvalues until the next subkey
                        subval.append(tokens[i])
                        i += 1

                    subfields[subkey] = ' '.join(subval)
                else:
                    i += 1
            current_list.append(subfields)
        else:
            result[key] = ' '.join(values)

    return result

# Sample ADEXP message
sample_adexp = '''\
-TITLE FPL
-ARCID ABC123
-EOBT 1200
-ADEP EGLL
-ADES LEMD
-BEGIN RTEPTS
-PT -PTID CPT -ETO 9305091200 -RFL F350
-PT -PTID BCN -ETO 9305091300 -RFL F370 
-END RTEPTS
-ORIGIN -NETWORKTYPE SITA -FAC FRAOXLH
-ROUTE N0417F330 ANEKI8L ANEKI Y163 NATOR UN850 TRA UP131 RESIA Q333 BABAG UN606 PEVAL DCT PETAK UL607 PINDO UM603 EDASI
'''

parsed = parse_adexp(sample_adexp)
print(parsed)
