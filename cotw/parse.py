import sys, json
from pathlib import Path
from cotw import adf, sarc, rtpc

def main():  
  type = sys.argv[1]
  filename = sys.argv[2]
  if type == "adf":
    adf.load_adf(Path.cwd() / filename)
  elif type == "gdcc":
    adf.load_global_gdcc(Path.cwd() / filename)
  elif type == "sarc":
    src_filename = Path().cwd() / filename
    do_extract = len(sys.argv) == 4
    data = sarc.load_sarc(src_filename, debug=(not do_extract))
    if do_extract:
      extract_filename = sys.argv[3]
      sarc.extract_file(data, src_filename, extract_filename)
  elif type == "adf_xls":
    data = adf.load_adf_xls(Path().cwd() / filename)
    output = Path().cwd() / f"{filename}.json"
    output.write_text(json.dumps(data, indent=2))
    print(output)
  elif type == "rtpc":
    rtpc.load_rtpc(Path().cwd() / filename)
  else:
    print("unknown type", type)