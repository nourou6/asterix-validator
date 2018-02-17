#!/usr/bin/env python3

from mmap import ACCESS_READ, mmap
import argparse
import os
import sys
import json
import collections




######### validation helpers ##########

def validate_SPF_type(stream, stream_position, uap_item):

    spf_length = int.from_bytes(stream[stream_position:stream_position+1], byteorder="big", signed=False)
    
    print("   content:", stream[stream_position+1:stream_position+1+spf_length])

    return 1 + spf_length

def validate_REF_type(stream, stream_position, uap_item):

    ref_length = int.from_bytes(stream[stream_position:stream_position+1], byteorder="big", signed=False)

    print("   content:", stream[stream_position+1:stream_position+1+ref_length])

    return 1 + ref_length

def validate_repetitive_type(stream, stream_position, uap_item):

    rep_length = int.from_bytes(stream[stream_position:stream_position+1], byteorder="big", signed=False)

    print("   content:", stream[stream_position+1:stream_position+1+rep_length])

    return 1 + rep_length * int(uap_item["Length"])

def validate_compound_type(stream, stream_position, uap_item):

    subfield_number = 0
    primary_subfield_position = stream_position

    stream_position += int(FSPEC_Length(stream_position, stream) / 7)

    for key,subfield in uap_item.items():
        
        # Do we have to handle the subfield because it is listed in the primary subfield?
        if FSPEC_listed(primary_subfield_position, stream, subfield_number):
            print("   Subfield", key, "defined in primary subfield")
            if subfield["Type"] == "Fixed":
                stream_position += validate_fixed_type(stream, stream_position, subfield)

        subfield_number += 1

    return stream_position - primary_subfield_position


def validate_fixed_type(stream, stream_position, uap_item):

    # increasing the pointer
    fixed_length = int(uap_item["Length"])

    print("   content:", stream[stream_position:stream_position+fixed_length])

    return fixed_length


def FSPEC_listed(stream_offset, blob, pos):

    fspec_octet = int(pos / 7);
    fspec_bitmask = int(128 >> (pos % 7))

    return int.from_bytes(blob[stream_offset+fspec_octet:stream_offset+1+fspec_octet], byteorder="big", signed=False) & fspec_bitmask == fspec_bitmask

def FSPEC_Length(stream_offset, blob):
    number_of_items = 7
    octet_pos = 0

    while int.from_bytes(blob[stream_offset+octet_pos:stream_offset+1+octet_pos], byteorder="big", signed=False) & int(1) == int(1):
        octet_pos += 1
        number_of_items += 7

    return number_of_items
#######################################



def validate_asterix_blob(blob):

    with open(blob, 'rb', 0) as f, mmap(f.fileno(), 0, access=ACCESS_READ) as s:

        # does the content of the length field match the actual size?
        record_length=int.from_bytes(s[1:3], byteorder="big", signed=False)
        file_size=os.fstat(f.fileno()).st_size
        if record_length != file_size:
            print("The length field (", record_length, ") and the actual file size (", file_size, ") do not match")
            sys.exit(-1)

        # loading the schema definition (UAP) for the indicated category
        category = int.from_bytes(s[0:1], byteorder="big", signed=False)
        schema_file_name="UAPs/cat_" + str(category) + ".json"
        schema = json.load(open(schema_file_name), object_pairs_hook=collections.OrderedDict)

        # check whether or not the length of the FSPEC matches the UAP definition
        number_of_fields_expected = len(schema)
        if number_of_fields_expected != FSPEC_Length(3, s):
            print("The number of fields defined in the FSPEC", FSPEC_Length(3, s), "does not match the UAP definition", number_of_fields_expected)
            sys.exit(-1)

        # starting to validate the given input at the position of the first item
        stream_position = 3 + int(FSPEC_Length(3, s) / 7)
        item_position = 0
        for key, subdict in schema.items():

            # Do we have to handle the item because it is listed in the FSPEC?
            if FSPEC_listed(3, s, item_position):

                print("Item", key, "defined in FSPEC")

                if subdict["Type"] == "Fixed":
                    stream_position += validate_fixed_type(s, stream_position, subdict)
                if subdict["Type"] == "Compound":
                    stream_position += validate_compound_type(s, stream_position, subdict["Subfields"])
                if subdict["Type"] == "Rep":
                    stream_position += validate_repetitive_type(s, stream_position, subdict)
                if subdict["Type"] == "REF":
                    stream_position += validate_REF_type(s, stream_position, subdict)
                if subdict["Type"] == "SPF":
                    stream_position += validate_SPF_type(s, stream_position, subdict)

            # did we run over the maximum langth?
            if stream_position > file_size:
                print("decoded position", stream_position, "exceeds the actual file size", file_size)
                sys.exit(-1)

            item_position += 1

    print("Stream position", stream_position, "matching total blob size of", file_size, "-> Structure valid")


def main():
    parser = argparse.ArgumentParser(description="Processing our simple arguments")
    parser.add_argument("blobs", metavar="asterix blob", nargs="+",
                        help="An ASTERIX binary message file")

    args=parser.parse_args()
    for blob in args.blobs:
        validate_asterix_blob(blob)

if __name__ == '__main__':
    main()

