import re
from pprint import pprint

class AdexpParser:
    def __init__(self) -> None:
        pass

    def basic_field(self, chunk: str):
        # "-KEY A B C" → ['-','KEY','A','B','C']
        return ['-'] + chunk[1:].split()

    def structured_field(self, line: str):
        tokens = line.strip().split()
        if not tokens or not tokens[0].startswith('-'):
            raise ValueError("structured_field expects line starting with '-'")

        # HEAD → ['-','XXX']
        head_token = tokens[0]
        record = self.basic_field(head_token)
        i = 1

        while i < len(tokens):
            if tokens[i].startswith('-'):
                key = tokens[i]
                i += 1
                vals = []
                while i < len(tokens) and not tokens[i].startswith('-'):
                    vals.append(tokens[i])
                    i += 1
                chunk = key + ('' if not vals else ' ' + ' '.join(vals))
                record.append(self.basic_field(chunk))
            else:
                i += 1

        return record

    def list_field(self, text: str):
        lines = text.strip().splitlines()
        # header
        hdr = lines[0].lstrip('-').split()
        out = ['-'] + hdr

        # body
        for ln in lines[1:-1]:
            ln = ln.strip()
            if ln:
                out.append(self.structured_field(ln))

        # footer
        ftr = lines[-1].lstrip('-').split()
        out += ['-'] + ftr

        return out

    def parse(self, text: str):
        text = text.strip()
        lines = text.splitlines()
        # if there's more than one line, handle root-level multiline
        if len(lines) > 1:
            out = []
            i = 0
            while i < len(lines):
                ln = lines[i].strip()
                if not ln:
                    i += 1
                    continue

                # begin a list block?
                if ln.startswith('-BEGIN'):
                    # find matching END
                    j = i + 1
                    while j < len(lines) and not lines[j].strip().startswith('-END'):
                        j += 1
                    if j < len(lines):
                        block = '\n'.join(lines[i : j + 1])
                        out.append(self.list_field(block))
                        i = j + 1
                        continue
                    # if no END found, fall through to basic

                # count how many dash‑chunks
                tokens = ln.split()
                dash_chunks = sum(1 for t in tokens if t.startswith('-'))

                if dash_chunks > 1:
                    out.append(self.structured_field(ln))
                else:
                    out.append(self.basic_field(ln))

                i += 1

            return out

        # single-line input
        ln = lines[0]
        if ln.startswith('-BEGIN'):
            return self.list_field(text)

        tokens = ln.split()
        dash_chunks = sum(1 for t in tokens if t.startswith('-'))
        if dash_chunks > 1:
            return self.structured_field(ln)
        else:
            return self.basic_field(ln)


if __name__ == "__main__":
    parser = AdexpParser()
    mm = """\
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
"""
    pprint(parser.parse(mm))
    # [
    #   ['-','TITLE','FPL'],
    #   ['-','ARCID','ABC123'],
    #   ['-','EOBT','1200'],
    #   ['-','ADEP','EGLL'],
    #   ['-','ADES','LEMD'],
    #   ['-','BEGIN','RTEPTS',
    #       ['-','PT',
    #           ['-','PTID','CPT'],
    #           ['-','ETO','9305091200'],
    #           ['-','RFL','F350']
    #       ],
    #       ['-','PT',
    #           ['-','PTID','BCN'],
    #           ['-','ETO','9305091300'],
    #           ['-','RFL','F370']
    #       ],
    #     '-','END','RTEPTS'
    #   ],
    #   ['-','ORIGIN',
    #       ['-','NETWORKTYPE','SITA'],
    #       ['-','FAC','FRAOXLH']
    #   ],
    #   ['-','ROUTE',
    #       'N0417F330','ANEKI8L','ANEKI','Y163','NATOR','UN850',
    #       'TRA','UP131','RESIA','Q333','BABAG','UN606','PEVAL',
    #       'DCT','PETAK','UL607','PINDO','UM603','EDASI'
    #   ]
    # ]
