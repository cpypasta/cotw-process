from deca.ff_rtpc import RtpcVisitorDumpToString
from pathlib import Path

def load_rtpc(filename: Path) -> None:
  data = filename.read_bytes()
  dump = RtpcVisitorDumpToString()
  dump.visit(data)
  parsed = dump.result()
  (Path.cwd() / f"{filename.name}.txt").write_text(parsed)  