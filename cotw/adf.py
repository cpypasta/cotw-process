import zlib
import contextlib
from deca.file import ArchiveFile
from deca.ff_adf import Adf
from pathlib import Path 

def _read_file(filename: Path, verbose = False):
    if verbose:
        print(f"Reading {filename}")
    return filename.read_bytes()

def _decompress_bytes(data_bytes: bytearray) -> bytearray:
    decompress = zlib.decompressobj()
    decompressed = decompress.decompress(data_bytes)
    decompressed = decompressed + decompress.flush()
    return decompressed

def _save_file(filename: Path, data_bytes: bytearray, verbose = False):
    Path(filename.parent).mkdir(exist_ok=True)
    filename.write_bytes(data_bytes)
    if verbose:
        print(f"Saved {filename}")

def _parse_adf_file(filename: Path, suffix: str = None, verbose = False) -> Adf:
    obj = Adf()
    with ArchiveFile(open(filename, 'rb')) as f:
        with contextlib.redirect_stdout(None):
            obj.deserialize(f)
    content = obj.dump_to_string()
    suffix = f"_{suffix}.txt" if suffix else ".txt"
    txt_filename = Path.cwd() / f"{filename.name}{suffix}"
    _save_file(txt_filename, bytearray(content, 'utf-8'), verbose)            
    return obj

def _decompress_adf_file(filename: Path, verbose = False) -> None:
    # read entire adf file
    data_bytes = _read_file(filename, verbose)
    data_bytes = bytearray(data_bytes)

    # split out header
    header = data_bytes[0:32]
    data_bytes = data_bytes[32:]

    # decompress data
    decompressed_data_bytes = _decompress_bytes(data_bytes)
    decompressed_data_bytes = bytearray(decompressed_data_bytes)

    # split out compression header
    decompressed_header = decompressed_data_bytes[0:5]
    decompressed_data_bytes = decompressed_data_bytes[5:]

    # save uncompressed adf data to file
    parsed_basename = filename.name
    adf_file = Path.cwd() / f".working/{parsed_basename}_sliced"
    _save_file(adf_file, decompressed_data_bytes, verbose)

def parse_adf(filename: Path, suffix: str = None, verbose = False) -> Adf:
    if verbose:
        print(f"Parsing {filename}")
    return _parse_adf_file(filename, suffix, verbose=verbose)

def load_adfb(filename: Path, verbose = False) -> Adf:
    data = _decompress_adf_file(filename, verbose=verbose)
    adf = parse_adf(data.filename, verbose=verbose)
    (Path.cwd() / f".working/{filename.name}_sliced").unlink()
    return adf

def load_adf(filename: Path, verbose = False) -> Adf:
    adf = parse_adf(filename, verbose=verbose)
    return adf
  
def load_global_gdcc(filename: Path) -> None:
  adf = parse_adf(filename)
  for i, instance in enumerate(adf.table_instance_values):
    for item in instance:
      offset = item.offset + adf.table_instance[i].offset
      print(item.v_path, offset, hex(offset))
  None
