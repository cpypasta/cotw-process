from deca.ff_sarc import FileSarc
from pathlib import Path

def load_sarc(filename: Path) -> None:
  sarc = FileSarc()
  print(filename)
  with filename.open('rb') as fp:
    sarc.header_deserialize(fp)
    for sarc_file in sarc.entries:
      print(sarc_file.v_path, sarc_file.length, sarc_file.offset, hex(sarc_file.offset))