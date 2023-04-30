import struct, json, re
from pathlib import Path
from typing import Tuple, List

typedef_s8 = 1477249634
typedef_u8 = 211976733
typedef_s16 = 3510620051
typedef_u16 = 2261865149
typedef_s32 = 422569523
typedef_u32 = 123620943
typedef_s64 = 2940286287
typedef_u64 = 2704924703
typedef_f32 = 1964352007
typedef_f64 = 3322541667
PRIMITIVES = [typedef_s8, typedef_u8, typedef_s16, typedef_u16, typedef_s32, typedef_u32, typedef_s64, typedef_u64, typedef_f32, typedef_f64]
PRIMITIVE_1 = [typedef_s8, typedef_u8]
PRIMITIVE_2 = [typedef_s16, typedef_u16]
PRIMITIVE_8 = [typedef_s64, typedef_u64, typedef_f64]
STRUCTURE = 1
ARRAY = 3
STRINGHASH = 9

def read_u32(data: bytearray) -> int:
  return struct.unpack("I", data)[0]

def create_u32(value: int) -> bytearray:
  return bytearray(struct.pack("I", value))

def read_u8(data: bytearray) -> int:
  return struct.unpack("B", data)[0]

def create_u8(value: int) -> bytearray:
  return bytearray(struct.pack("B0I", value))

def create_f32(value: float) -> bytearray:
  return bytearray(struct.pack("f", value))

def read_u64(data: bytearray) -> int:
  return struct.unpack("Q", data)[0]

def read_str(data: bytearray) -> str:
  value = data[0:-1]
  return value.decode("utf-8")

def write_value(data: bytearray, new_data: bytearray, offset: int) -> None:
  data[offset:offset+len(new_data)] = new_data

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
  type_hash = read_u32(data[8:12])
  size = read_u32(data[12:16])
  offset = read_u32(data[16:20])
  return {
    "name": name,
    "type_hash": type_hash,
    "size": size,
    "offset": offset
  }

def read_typedef(header: bytearray, offset: int, nametables: List[str]) -> Tuple[int, dict]:
  header_size = 36
  member_size = 32
  metatype = read_u32(header[0:4])
  size = read_u32(header[4:8])
  type_hash = read_u32(header[12:16])
  name_index = read_u64(header[16:24])
  element_type_hash = read_u32(header[28:32])
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
      "type_hash": type_hash,
      "start": offset, 
      "end": offset + structure_size,
      "size": size,
      "members": members
    })
  elif metatype == 0:
    return (header_size, {
      "name": name, 
      "metatype": metatype,
      "type_hash": type_hash,
      "start": offset, 
      "end": offset + header_size
    })
  else:
    return (header_size+4, {
      "name": name, 
      "metatype": metatype,
      "type_hash": type_hash,
      "element_type_hash": element_type_hash,
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
  
  type_map = {}
  for offset in offsets:
    type_map[offset["type_hash"]] = { 
      "name": offset["name"], 
      "metatype": offset["metatype"],
      "size": offset["size"] if "size" in offset else None,
      "element_type_hash": offset["element_type_hash"] if "element_type_hash" in offset else None,
      "members": offset["members"] if "members" in offset else []
    }
  
  return {
    "start": typedef_offset,
    "end": pointer,
    "offsets": offsets,
    "type_map": type_map
  }

def get_primitive_size(type_id: int) -> int:
  if type_id in PRIMITIVE_1:
    return 1
  elif type_id in PRIMITIVE_2:
    return 2
  elif type_id in PRIMITIVE_8:
    return 8
  else:
    return 4

def read_instance(data: bytearray, offset: int, pointer: int, type_id: int, type_map: dict) -> dict:
  value = None
  pos = offset+pointer
  
  if type_id in PRIMITIVES:
    primitive_size = get_primitive_size(type_id)
    value = f"Primitive ({primitive_size}, {pos})"
    pointer += primitive_size # TODO: READ
  else:
    type_def = type_map[type_id]
    if type_def["metatype"] == STRUCTURE:
      value = {}
      value["structure_offset"] = (pos, pos+type_def["size"])
      org_pointer = pointer
      for m in type_def["members"]:
        m_offset = m["offset"]
        pointer = org_pointer + m_offset
        v = read_instance(data, offset, pointer, int(m["type_hash"]), type_map)
        value[m["name"]] = { 
          "value": v[0]
        }
      pointer = org_pointer + type_def["size"] # TODO: READ
    elif type_def["metatype"] == ARRAY:
      array_offset = read_u32(data[pos:pos+4])
      length = read_u32(data[pos+8:pos+12]) 
      array_header_size = 12
      org_pos = pos
      pointer += array_header_size # TODO: READ
      org_pointer = pointer
      pos = offset+pointer
      value = { "Array": { 
        "name": type_def["name"], 
        "header_offset": (org_pos, org_pos+array_header_size),
        "length": length
      }}
      pointer = array_offset
      
      if length > 0:
        element_type = type_def["element_type_hash"]
        new_pointer = pointer
        values = []
        for i in range(length):
          v, new_pointer = read_instance(data, offset, new_pointer, int(element_type), type_map)
          values.append(v)
        value["Array"]["type"] = "Primitives" if element_type in PRIMITIVES else "Structures"
        value["Array"]["array_offset"] = (offset+pointer, offset+new_pointer)
        value["Array"]["values"] = values
      
      pointer = org_pointer
    elif type_def["metatype"] == STRINGHASH:
      print(type_def["name"], type_def["size"])
      if type_def["size"] == 4:
        value = f"String Hash (4, {pos})"
        pointer += 4      
    else:
      print(f"Unknown metatype: {type_def['metatype']}")
  
  return (value, pointer)

def find_instance_offset(data: bytearray, offset: int, count: int, nametables: List[str], type_map: dict) -> dict:
  instance_header_size = 24
  instances = []
  for i in range(count):
    pointer = offset + i * count
    instance_type = read_u32(data[pointer+4:pointer+8])
    instance_offset = read_u32(data[pointer+8:pointer+12])
    instance_size = read_u32(data[pointer+12:pointer+16])
    instance_name = nametables[read_u64(data[pointer+16:pointer+24])]
    instances.append({ 
      "offset": (instance_offset, instance_offset + instance_size), 
      "size": instance_size, 
      f"{instance_name}": read_instance(data, instance_offset, 0, instance_type, type_map)[0]
    })
  
  return {
    "offset": (offset, offset + count*instance_header_size),
    "instances": instances
  }
  
def find_population_array_offsets(offsets: dict, result: List[dict] = [], org_path: str = "", prev_key: str = "", index: int = 0) -> List[dict]:
  for key, v in offsets.items():
    if org_path == "":
      path = ""
    else:
      path = org_path
    if isinstance(v, dict):
      if prev_key != "":
        path += f"{prev_key}[{index}];"
      value = v["value"]
      if isinstance(v, dict) and "Array" in value:
        array_details = value["Array"]
        result.append({
          "path": path,
          "key": key,
          "name": array_details["name"],
          "index": index,
          "length": array_details["length"],
          "header": array_details["header_offset"],
          "values": array_details["array_offset"] if "array_offset" in array_details else None
        })
                
        if "values" in array_details:
          array_values = array_details["values"]
          if len(array_values) > 0 and isinstance(array_values[0], dict):
            for i, value in enumerate(array_details["values"]):
              find_population_array_offsets(value, result, path, key, i)
  return result

def sort_array_offsets(array_offsets: List[dict]) -> Tuple[dict, dict]:
  header_sorted = sorted(array_offsets, key=lambda x: x["header"][1])
  values_sorted = sorted(array_offsets, key=lambda x: 999999 if x["values"] is None else x["values"][1])
  return (header_sorted, values_sorted)

class AdfArray:
  def __init__(self, name: str, population: int, group: int, length: int, header_start_offset: int, header_length_offset: int, header_array_offset: int, array_start_offset: int, array_end_offset: int, rel_array_start_offset: int, rel_array_end_offset: int) -> None:
    self.name = name
    self.population = population
    self.group = group
    self.length = length
    self.header_start_offset = header_start_offset
    self.header_length_offset = header_length_offset
    self.header_array_offset = header_array_offset
    self.array_start_offset = array_start_offset
    self.array_end_offset = array_end_offset
    self.rel_array_start_offset = rel_array_start_offset
    self.rel_array_end_offset = rel_array_end_offset
    
  def __repr__(self) -> str:
    return f"Population[{self.population}].Group[{self.group}];{self.name} ; Header Offset: {self.header_start_offset},{hex(self.header_start_offset)}; Data Offset: {self.array_start_offset},{hex(self.array_start_offset)}"

class Animal:
  def __init__(self) -> None:
    self.gender = 1
    self.weight = 1.48
    self.score = 1.5
    self.is_great_one = 1
    self.visual_variation_seed = 2
    self.id = 1
    self.map_position_x = 1.0
    self.map_position_y = 2.0
    self.size = len(self.to_bytes())
    
  def to_bytes(self) -> bytearray:
    gender = create_u8(self.gender)
    weight = create_f32(self.weight)
    score = create_f32(self.score)
    is_great_one = create_u8(self.is_great_one)
    visual_variation_seed = create_u32(self.visual_variation_seed)
    id = create_u32(self.id)
    map_position_x = create_f32(self.map_position_x)
    map_position_y = create_f32(self.map_position_y)
    return gender+weight+score+is_great_one+visual_variation_seed+id+map_position_x+map_position_y

def create_array(offset: dict, instance_offset: int, population: int = 0, group: int = 0) -> AdfArray:
  header_start_offset = offset["header"][0]
  value_start_offset, value_end_offset = offset["values"] if offset["values"] else (0,0)
  return AdfArray(
    f"{offset['path']}{offset['key']};{offset['name']}",
    int(population), 
    int(group), 
    offset["length"], 
    header_start_offset, 
    header_start_offset+8, 
    header_start_offset, 
    value_start_offset, 
    value_end_offset,
    value_start_offset-instance_offset, 
    value_end_offset-instance_offset
  )  

def create_animal_array(offset: dict, instance_offset: int) -> AdfArray:
  population, group = re.findall(r'\d+', offset["path"])
  return create_array(offset, instance_offset, population, group)

def profile_header(data: bytearray) -> dict:
  header = data[:64]
  instance_count = read_u32(header[8:12])
  instance_offset = read_u32(header[12:16])
  typedef_count = read_u32(header[16:20])
  typedef_offset = read_u32(header[20:24])
  stringhash_count = read_u32(header[24:28])
  stringhash_offset = read_u32(header[28:32])
  nametable_count = read_u32(header[32:36])
  nametable_offset = read_u32(header[36:40])
  total_size = read_u32(header[40:44])  
  
  return {
    "total_size": total_size,
    "typedef_count": typedef_count,
    "typedef_offset": typedef_offset,
    "nametable_count": nametable_count,
    "nametable_offset": nametable_offset,
    "instance_count": instance_count,
    "instance_offset": instance_offset,
    "stringhash_count": stringhash_count,
    "stringhash_offset": stringhash_offset,
    "header_start": 0,
    "header_instance_offset": 12,
    "header_typedef_offset": 20,
    "header_stringhash_offset": 28,
    "header_nametable_offset": 36,
    "header_total_size_offset": 40,
    "header_end": 64
  } 

def create_profile(filename: Path) -> None:
  data = bytearray(filename.read_bytes())
  header_profile = profile_header(data)
  instance_count = header_profile["instance_count"]
  instance_offset = header_profile["instance_offset"]
  typedef_count = header_profile["typedef_count"]
  typedef_offset = header_profile["typedef_offset"]
  stringhash_count = header_profile["stringhash_count"]
  stringhash_offset = header_profile["stringhash_offset"]  
  nametable_count = header_profile["nametable_count"]
  nametable_offset = header_profile["nametable_offset"]
  total_size = header_profile["total_size"]
  comment_size = find_length_of_string(data[64:])
  nametable_size = find_nametable_size(data[nametable_offset:], nametable_count)
  nametables = read_nametables(data[nametable_offset:], nametable_count)
  typedef_offsets = find_typedef_offset(data, typedef_offset, typedef_count, nametables)
  type_map = typedef_offsets["type_map"]
  instance_offsets = find_instance_offset(data, instance_offset, instance_count, nametables, type_map)
  
  return {
    "total_size": total_size,
    "header_start": 0,
    "header_instance_offset": 12,
    "header_typedef_offset": 20,
    "header_stringhash_offset": 28,
    "header_nametable_offset": 36,
    "header_total_size_offset": 40,
    "header_end": 64,
    "comment_start": 64,
    "comment_end": 64 + comment_size,
    "instance_start": instance_offsets["instances"][0]["offset"][0],
    "instance_end": instance_offsets["instances"][0]["offset"][0] + instance_offsets["instances"][0]["size"],
    "instance_header_start": instance_offsets["offset"][0],
    "instance_header_end": instance_offsets["offset"][1],    
    "typedef_start": typedef_offset,
    "typedef_end": typedef_offsets["end"],    
    "stringhash_start": stringhash_offset,
    "stringhash_end": nametable_offset,
    "nametable_start": nametable_offset,
    "nametable_end": nametable_offset+nametable_size,
    "details": {
      "instance_offsets": instance_offsets
    }
  }
  
def find_arrays(instance_offsets: dict) -> Tuple[List[AdfArray], List[AdfArray]]:
  instance_offset = instance_offsets["instances"][0]["offset"][0]
  array_offsets = find_population_array_offsets(instance_offsets["instances"][0]["0"])
  animal_arrays = [create_animal_array(x, instance_offset) for x in array_offsets if x["key"] == 'Animals']
  other_arrays = [create_array(x, instance_offset) for x in array_offsets if x["key"] != 'Animals']
  return (animal_arrays, other_arrays)

def update_non_instance_offsets(data: bytearray, profile: dict, added_size: int) -> None:
  offsets_to_update = [
    (profile["header_instance_offset"], profile["instance_header_start"]),
    (profile["header_typedef_offset"], profile["typedef_start"]),
    (profile["header_nametable_offset"], profile["nametable_start"]),
    (profile["header_total_size_offset"], profile["total_size"]),
    (profile["instance_header_start"]+12, profile["details"]["instance_offsets"]["instances"][0]["size"])
  ]
  for offset in offsets_to_update:
    write_value(data, create_u32(offset[1] + added_size), offset[0])

def insert_animal(data:bytearray, animal: Animal, array: AdfArray) -> None:
  write_value(data, create_u32(array.length+1), array.header_length_offset) 
  animal_bytes = animal.to_bytes()
  data[array.array_end_offset:array.array_end_offset] = animal_bytes # TODO: only time we shift bytes

def update_instance_arrays(data: bytearray, animal_arrays: List[AdfArray], target_array: AdfArray, size: int):
  for animal_array in animal_arrays:
    if animal_array.array_start_offset >= target_array.array_end_offset and animal_array.array_start_offset != 0:
      print(animal_array)
      write_value(data, create_u32(animal_array.rel_array_start_offset + size), animal_array.header_array_offset)

def compare_headers() -> None:
  org_filename = Path().cwd() / "animal_population_0_sliced"
  new_filename = Path().cwd() / "animal_population_0_updated"
  org_header_profile = profile_header(bytearray(org_filename.read_bytes()))
  new_header_profile = profile_header(bytearray(new_filename.read_bytes()))
  (Path.cwd() / "header_org.json").write_text(json.dumps(org_header_profile, indent=2))
  (Path.cwd() / "header_new.json").write_text(json.dumps(new_header_profile, indent=2))

def compare_file_sizes() -> None:
  org_filename = Path().cwd() / "animal_population_0_sliced"
  new_filename = Path().cwd() / "animal_population_0_updated"
  org_size = len(bytearray(org_filename.read_bytes()))
  new_size = len(bytearray(new_filename.read_bytes()))
  print(org_size, new_size, f"diff: {new_size - org_size}")

def update_existing() -> None:
  base_name = "animal_population_0_sliced"
  filename = Path().cwd() / base_name
  profile = create_profile(filename)
  (Path.cwd() / f"{base_name}_profile.json").write_text(json.dumps(profile, indent=2))
  animal_arrays, other_arrays = find_arrays(profile["details"]["instance_offsets"])

  data = bytearray(filename.read_bytes())
  animal = Animal()
  update_non_instance_offsets(data, profile, animal.size)
  target_array = animal_arrays[-2]
  print(target_array, "[target]")
  update_instance_arrays(data, animal_arrays+other_arrays, target_array, animal.size)
  insert_animal(data, animal, target_array)
  (Path().cwd() / "animal_population_0_updated").write_bytes(data)  

def profile_existing() -> None:
  base_name = "animal_population_0_sliced"
  filename = Path().cwd() / base_name
  profile = create_profile(filename)
  (Path.cwd() / f"{base_name}_profile.json").write_text(json.dumps(profile, indent=2))  

def profile_new() -> None:
  base_name = "animal_population_0_updated"
  filename = Path().cwd() / base_name
  profile = create_profile(filename)
  (Path.cwd() / f"{base_name}_profile.json").write_text(json.dumps(profile, indent=2))  

if __name__ == "__main__":
  update_existing()
  # profile_existing()
  # profile_new()
  # compare_file_sizes()
  
  # 193,720 we update length
  # what changed at 217,192? 12 bytes
  # 150,924 ? 32 bytes removed it says