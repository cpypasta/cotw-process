from deca.ff_sarc import FileSarc
from pathlib import Path

def extract_file(sarc: FileSarc, src_filename: Path, filename: str) -> None:  
  for sarc_file in sarc.entries:
    file = sarc_file.v_path.decode("utf-8")
    if file == filename:
      byte_start = sarc_file.offset
      byte_size = sarc_file.length
      break
  if byte_start:
    dest_filename = Path(filename).name
    with src_filename.open("rb") as fp:
      fp.seek(byte_start)
      data = fp.read(byte_size)
      (Path().cwd() / dest_filename).write_bytes(data)
      print("Extractd: ", dest_filename)

def load_sarc(filename: Path, debug=True) -> FileSarc:
  sarc = FileSarc()
  with filename.open('rb') as fp:
    sarc.header_deserialize(fp)
    if debug:
      for sarc_file in sarc.entries:
        print(sarc_file.v_path, f"[{sarc_file.offset} - {sarc_file.offset + sarc_file.length}]", f", Offset: {sarc_file.offset}, {hex(sarc_file.offset)}")
  return sarc  