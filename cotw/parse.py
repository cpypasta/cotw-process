import sys, json
from pathlib import Path
from cotw import adf, sarc, rtpc, adf_builder

def main():  
  type = sys.argv[1]
  filename = sys.argv[2]
  if type == "adf":
    adf.load_adf(Path.cwd() / filename)
  elif type == "adfc":
    adf.load_adfc(Path.cwd() / filename)
  elif type == "gdcc":
    global_filename = Path().cwd() / filename
    do_extract = len(sys.argv) == 4
    if do_extract:
      adf.extract_global_file(global_filename, sys.argv[3])
    else:
      adf.load_global_gdcc(global_filename)
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
  elif type == "profile":
    profile = adf_builder.create_profile(Path().cwd() / filename)
    (Path().cwd() / f"{Path(filename).name}_profile.json").write_text(json.dumps(profile, indent=2))
  elif type == "profile_header":
    data = bytearray((Path().cwd() / filename).read_bytes())
    profile = adf_builder.profile_header(data)
    (Path().cwd() / f"{Path(filename).name}_header_profile.json").write_text(json.dumps(profile, indent=2))    
  else:
    print("unknown type", type)