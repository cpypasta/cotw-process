import sys, json, struct
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
    compressed_data = sarc.load_sarc(src_filename, debug=(not do_extract))
    if do_extract:
      extract_filename = sys.argv[3]
      sarc.extract_file(compressed_data, src_filename, extract_filename)
  elif type == "adf_xls":
    compressed_data = adf.load_adf_xls(Path().cwd() / filename)
    output = Path().cwd() / f"{filename}.json"
    output.write_text(json.dumps(compressed_data, indent=2))
    print(output)
  elif type == "rtpc":
    rtpc.load_rtpc(Path().cwd() / filename)
  elif type == "profile":
    profile = adf_builder.create_profile(Path().cwd() / filename)
    (Path().cwd() / f"{Path(filename).name}_profile.json").write_text(json.dumps(profile, indent=2))
  elif type == "profile_header":
    compressed_data = bytearray((Path().cwd() / filename).read_bytes())
    profile = adf_builder.profile_header(compressed_data)
    (Path().cwd() / f"{Path(filename).name}_header_profile.json").write_text(json.dumps(profile, indent=2)) 
  elif type == "test":
    # data = bytearray((Path().cwd() / filename).read_bytes()) 
    # print("Compressed", len(data[32:]))
    # print("Decompressed", len(adf._decompress_bytes(data[32:])))
    # (Path().cwd() / f"{Path(filename).name}_bytes").write_bytes(data[0:32] + adf._decompress_bytes(data[32:])[0:5]) 
    # (Path().cwd() / f"{Path(filename).name}_u").write_bytes(data[0:32] + adf._decompress_bytes(data[32:])) 
    file = Path.cwd() / filename
    adf_builder.insert_array_data(file, bytearray(file.read_bytes())[35928:35976], 320, 35976, 35, 34)
  elif type == "test2":
    file = Path.cwd() / filename
    file_header, header = adf._decompress_adf_headers(file)
    sliced = Path.cwd() / f"{filename}_sliced_u"
    print(file, sliced)
    data = header + bytearray(sliced.read_bytes())
    compressed_data = adf._compress_bytes(data)
    decompressed_size = struct.pack("I", len(data))
    file_header[8:12] = decompressed_size
    file_header[24:28] = decompressed_size
    file.write_bytes(file_header + compressed_data)
    print(len(data))
  else:
    print("unknown type", type)