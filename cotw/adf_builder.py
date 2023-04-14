import struct, json
from pathlib import Path
from typing import Tuple, List

# get the parts of the file that are logically related
# modify the bytes
# update offsets
# put back together and save

"""
Known Parts:

header
typedef
stringhash
nametable
instance
"""

def read_u32(data: bytearray) -> int:
  return struct.unpack("I", data)[0]

def read_u8(data: bytearray) -> int:
  return struct.unpack("B", data)[0]

def read_u64(data: bytearray) -> int:
  return struct.unpack("Q", data)[0]

def read_str(data: bytearray) -> str:
  value = data[0:-1]
  return value.decode("utf-8")

def find_length_of_string(data: bytearray) -> bytearray:
  for i in range(len(data)):
    if data[i:i+1] == b'\00':
      return i
  return 0

def find_nametable_size(data: bytearray, count: int) -> int:
  size = 0
  eos = 1
  for i in range(count):
    i_length = read_u8(data[i:i+1])
    size += 1 + i_length + eos
  return size

def read_nametables(data: bytearray, count: int) -> List[str]:
  nametable_sizes = []
  nametables = []
  for i in range(count):
    i_length = read_u8(data[i:i+1])
    nametable_sizes.append(i_length)
  
  table_offset = count
  pointer = table_offset
  
  for i in range(count):
    i_length = nametable_sizes[i]
    nametables.append(read_str(data[pointer:pointer+i_length+1]))
    pointer += i_length + 1
  
  return nametables

def read_typemember(data: bytearray, nametables: List[str]) -> dict:
  name_index = read_u64(data[0:8]) 
  name = nametables[name_index]
  size = read_u32(data[12:16])
  offset = read_u32(data[16:20])
  return {
    "name": name,
    "size": size,
    "offset": offset
  }

def read_typedef(header: bytearray, offset: int, nametables: List[str]) -> Tuple[int, dict]:
  header_size = 36
  member_size = 32
  metatype = read_u32(header[0:4])
  name_index = read_u64(header[16:24])
  name = nametables[name_index]
  
  if metatype == 1:
    member_count = read_u32(header[header_size:header_size+4])
    structure_size = header_size + 4 + (member_size * member_count)
    members = []
    for i in range(member_count):
      pointer = i * member_size
      members.append(read_typemember(header[header_size+4+pointer:], nametables))
    return (structure_size, {
      "name": name, 
      "metatype": metatype,
      "start": offset, 
      "end": offset + structure_size,
      "members": members
    })
  elif metatype == 0:
    return (header_size, {
      "name": name, 
      "metatype": metatype,
      "start": offset, 
      "end": offset + header_size
    })
  else:
    return (header_size+4, {
      "name": name, 
      "metatype": metatype,
      "start": offset, 
      "end": offset+header_size+4
    })

def find_typedef_offset(data: bytearray, typedef_offset: int, count: int, nametables: List[str]) -> dict:
  pointer = typedef_offset
  offsets = []
  for i in range(count):
    read_size, info = read_typedef(data[pointer:], pointer, nametables)
    pointer += read_size
    offsets.append(info)
  return {
    "start": typedef_offset,
    "end": pointer,
    "offsets": offsets
  }

def find_instance_offset(data: bytearray, offset: int, count: int, nametables: List[str]) -> dict:
        # self.META_position = f.tell()
        # self.name_hash = f.read_u32()
        # self.type_hash = f.read_u32()
        # self.offset = f.read_u32()
        # self.size = f.read_u32()
        # self.name = nt[f.read_u64()][1]
  instance_header_size = 24
  instances = []
  for i in range(count):
    pointer = offset + i * count
    instance_offset = read_u32(data[pointer+8:pointer+12])
    instance_size = read_u32(data[pointer+12:pointer+16])
    instance_name = nametables[read_u64(data[pointer+16:pointer+24])]
    instances.append({ "name": instance_name, "offset": instance_offset, "size": instance_size })
  
  return {
    "start": offset,
    "end": offset + count*instance_header_size,
    "instances": instances
  }

def break_apart(filename: Path) -> None:
  data = bytearray(filename.read_bytes())
  header = data[:64]
  instance_count = read_u32(header[8:12])
  instance_offset = read_u32(header[12:16])
  typedef_count = read_u32(header[16:20])
  typedef_offset = read_u32(header[20:24])
  nametable_count = read_u32(header[32:36])
  nametable_offset = read_u32(header[36:40])
  total_size = read_u32(header[40:44])
  
  comment_size = find_length_of_string(data[64:])
  comment = data[64:64+comment_size]
  
  nametable_size = find_nametable_size(data[nametable_offset:], nametable_count)
  nametable = data[nametable_offset:nametable_offset+nametable_size]
  nametables = read_nametables(data[nametable_offset:], nametable_count)
  
  typedef_offsets = find_typedef_offset(data, typedef_offset, typedef_count, nametables)
  typedef = data[typedef_offsets["start"]:typedef_offsets["end"]]
  
  instance_offsets = find_instance_offset(data, instance_offset, instance_count, nametables)
  instances = data[instance_offsets["start"]:instance_offsets["end"]]
  
  # print(json.dumps(instance_offsets, indent=2))
  
  print(total_size)
  print(json.dumps({
    "header_start": 0,
    "header_end": 64,
    "comment_start": 64,
    "comment_end": 64 + comment_size,
    "instance_start": instance_offsets["instances"][0]["offset"],
    "instance_end": instance_offsets["instances"][0]["offset"] + instance_offsets["instances"][0]["size"],
    "instance_header_start": instance_offset,
    "instance_header_end": instance_offsets["end"],    
    "typedef_start": typedef_offset,
    "typedef_end": typedef_offsets["end"],    
    "nametable_start": nametable_offset,
    "nametable_end": nametable_offset+nametable_size
  }, indent=2))
  
  
if __name__ == "__main__":
  break_apart(Path().cwd() / "animal_population_0_sliced")
  