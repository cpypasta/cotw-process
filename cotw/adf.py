import zlib
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
      obj.deserialize(f)
    content = obj.dump_to_string()
    suffix = f"_{suffix}.txt" if suffix else ".txt"
    txt_filename = Path.cwd() / f"{filename.name}{suffix}"
    _save_file(txt_filename, bytearray(content, 'utf-8'), verbose)            
    return obj

def _decompress_adf_file(filename: Path, verbose = False) -> Path:
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
    decompressed_data_bytes = decompressed_data_bytes[5:]

    # save uncompressed adf data to file
    parsed_basename = filename.name
    adf_file = Path.cwd() / f".working/{parsed_basename}_sliced"
    _save_file(adf_file, decompressed_data_bytes, verbose) 

    return adf_file 

def _cell_format(type: int) -> str:
  if type == 0:
    return "boolean"
  elif type == 1:
    return "string"
  elif type == 2:
    return "number"
  else:
    return "unknown"

def _column_format(n: int) -> str:
  name = ''
  while n > 0:
    n, r = divmod(n - 1, 26)
    name = chr(r + ord('A')) + name
  return name

class CellReference:
  def __init__(self, data_offset: int, data_hex_offset: str, cell_index: int, ref: str) -> None:
     self.data_offset = data_offset
     self.data_hex_offset = data_hex_offset
     self.cell_index = cell_index
     self.refs = [ref]
     
  def reference(self, ref: str) -> None:
    self.refs.append(ref)
  
  def __repr__(self) -> str:
     return f"I:{self.cell_index}, D:{self.data_offset},{self.data_hex_offset} ({len(self.refs)})"


def parse_adf(filename: Path, suffix: str = None, verbose = False) -> Adf:
    if verbose:
        print(f"Parsing {filename}")
    return _parse_adf_file(filename, suffix, verbose=verbose)

def load_adfc(filename: Path, verbose = False) -> Adf:
    data_filename = _decompress_adf_file(filename, verbose=verbose)
    adf = parse_adf(data_filename, verbose=verbose)
    # data_filename.unlink()
    # data_filename.parent.rmdir()
    return adf

def load_adf(filename: Path, verbose = False) -> Adf:
    adf = parse_adf(filename, verbose=verbose)
    return adf
  
def load_adf_xls(filename: Path) -> None:
  adf = load_adf(filename)
  src = adf.table_instance_values[0]
  src_full = adf.table_instance_full_values[0]
  
  cell_data_indices = src["Cell"]
  if "BoolData" in src:
    bool_data = src["BoolData"]
  if "StringData" in src:    
    string_data = src["StringData"]
  if "ValueData" in src:
    number_data = src["ValueData"]
    
  sheets = {}
  numbers = {}
  
  for i, sheet in enumerate(src["Sheet"]):
    col_cnt = sheet["Cols"].item()
    row_cnt = sheet["Rows"].item()
    name = sheet["Name"].decode("utf-8")
    cell_indices = sheet["CellIndex"]  
    cell_index_full = src_full.value["Sheet"].value[i].value["CellIndex"]
    cell_index_base_offset = cell_index_full.data_offset.item()
    sheets[name] = []
    print(name)
    for row in range(row_cnt):
      for col in range(col_cnt):
        cell_index = cell_indices[col + col_cnt * row].item()
        cell_info = cell_data_indices[cell_index]
        cell_type = cell_info["Type"]
        cell_format = _cell_format(cell_type)
        cell_data_index = cell_info["DataIndex"].item()
        cell_lookup = f"{_column_format(col+1)}{row+1}"
        cell_index_offset = cell_index_base_offset + (4 * (col + col_cnt * row))
        
        if cell_format == "bool":
          cell_data = bool_data[cell_data_index]
          cell_data_offset = src_full.value["BoolData"].value[cell_data_index].data_offset.item()
        elif cell_format == "string":
          cell_data = string_data[cell_data_index].decode("utf-8")
          cell_data_offset = src_full.value["StringData"].value[cell_data_index].data_offset.item()
        elif cell_format == "number":
          cell_data = number_data[cell_data_index].item()
          cell_data_offset = src_full.value["ValueData"].data_offset.item() + 4 * cell_data_index
          
          # ref = f"{i}_{cell_lookup}"
          # if str(cell_data) not in numbers:
          #   numbers[str(cell_data)] = CellReference(cell_data_offset, hex(cell_data_offset), cell_index, ref)
          # else:
          #   numbers[str(cell_data)].reference(ref)          
          if str(cell_data) not in numbers:
            numbers[str(cell_data)] = int(cell_index)
        else:
          cell_data = None
        
        if cell_data:
          sheets[name].append({ 
            "sheet": name,
            "value": cell_data, 
            "format": cell_format, 
            "cell": cell_lookup, 
            "cell_index": cell_index,
            "cell_index_offset": cell_index_offset,
            "cell_index_hex_offset": hex(cell_index_offset),
            "data_offset": cell_data_offset,
            "data_hex_offset": hex(cell_data_offset)
          })
  
  number_keys = list(numbers.items())
  number_keys = sorted(number_keys, key=lambda x: float(x[0]))
  numbers = {key[0]: str(key[1]) for key in number_keys}
  
  return {
    "sheets": sheets,
    "numbers": numbers
  }
  
def load_global_gdcc(filename: Path) -> None:
  adf = parse_adf(filename)
  for i, instance in enumerate(adf.table_instance_values):
    for item in instance:
      offset = item.offset + adf.table_instance[i].offset
      print(item.v_path, offset, hex(offset))
  None
