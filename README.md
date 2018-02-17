# POC: Simple EUROCONTROL ASTERIX blob validator

EUROCONTROL defines a simple binary container format (ASTERIX) that is used in the ATC business for exchanging air traffic service information
such as track data, datalink message, station monitoring and control information.

Decoding a given Data Block can be a hazzle as you would have to implement all the Data Item de-coding logic and you would have to
grasp all the semantics of the received data.

However, if you only want to check whether or not the given binary message is valid/complete you would just have to quick-check the
structure of the given message, comparing the received message with the expected structure from the UAP.

This seemed to be quite doable, so I thought I would give it a shot.


## The generic ASTERIX container format

The generic ASTERIX container format is actually quite simple. It operates on minimal data chunks of 8Bits called Octets. There are
some standardized methods for grouping those octects, making up the Data Fields. For instance you can have a fixed number of Octets, a variable number of octets, a sequence of a fixed number of octets and so on.

In the real application those Data Fields are actually carrying the information, meaning that a single Data Field is used for storing a specific
Data Item.

Several Data Fields combined are called a record and a record is basically the real message. At the start of every record there is bitmask of
variable length which indicates whether or not the Data Field corresponding to a specific bit is contained in the message.

There is an envelope for potentially multiple records of the same type, called Data Block. This Data Block is just adding a header
giving the information on the message category and giving the length information.

[ASTERIX Container Format](https://www.eurocontrol.int/sites/default/files/field_tabs/content/documents/single-sky/specifications/20120401-asterix-spec-v2.0.pdf)


## Categories - The Data Model

For every application there is an additional standard that defines the data model using sequences of the data types from the generic
container format. They use to call those types of message "Categories".

It's quiet obvious that the Data Model needs to define the content and interpretation of the Data Items, for instance if a range information
is given the Data Model needs to define the unit and the precision of the range information.

But because of the generic container format of simple octet sequences that are not carrying any information on the data type or ordering, the
data model is also needed for a correct interpretation of the given binary message. The sole message does not carry any information
on it's internal structure that could be used to de-serialize the message without additional information.

So every Categoy is actually defining two types of information: The content and interpretation of data is defined by the Data Items,
the structure of the resulting message is defined by the User Application Profile.

[ASTERIX Category Spec library](https://www.eurocontrol.int/asterix-specifications-library?title=)


## The Google Protocol Buffers analogy

The whole concept reminded me of the binary encoding of messages in [Google Protocol Buffers](https://developers.google.com/protocol-buffers/docs/encoding). Without a Descriptor there is no way of de-serializing an unknown message as the messages are not self-describing. On the plus side, the binary message encoding is both simple and efficient.

EUROCONTROL does not provide a similar technical solution for defining the messages in some kind of descriptor format and there are no code generation tools and there is no framework for message de-/serialization.

I think it should be doable to create a protobuf-like project on top of the ASTERIX binary message format. Sounds like fun to me, any takers?

Since I am only interested in a quick way to validate recevied binary ASTERIX messages I will just code a simple mechanism which allows me to do exactly that.

## So... what does this POC do?

In a nutshell:
- I have translated the UAP from the CAt34 spec to a machine readable json representation
- I have created a dummy cat34 message. The content of the Data Items is nonsense. But the structure should be valid.
- There is this python script that will use the UAP to walk over the given message, assuming the sizes of the Data Items from the UAP
- The message is valid if the size of the message matches exactly the expected size from the UAP


### Sample invocation

```
dgrafe@amd64-X2:~/git/asterix-validator$ ./astval.py testdata/cat34.bin 
Item Item010 defined in FSPEC
   content: b'\x00\x11'
Item Item000 defined in FSPEC
   content: b'\x01'
Item Item030 defined in FSPEC
   content: b'\x02\x03\x01'
Item Item020 defined in FSPEC
   content: b'\x01'
Item Item041 defined in FSPEC
   content: b'\x124'
Item Item050 defined in FSPEC
   Subfield COM defined in primary subfield
   content: b'\xff'
   Subfield PSR defined in primary subfield
   content: b'\xf8'
   Subfield SSR defined in primary subfield
   content: b'\xf8'
   Subfield MDS defined in primary subfield
   content: b'\xff\x80'
Item Item060 defined in FSPEC
   Subfield COM defined in primary subfield
   content: b'~'
   Subfield PSR defined in primary subfield
   content: b'\xfc'
   Subfield SSR defined in primary subfield
   content: b'\xe0'
   Subfield MDS defined in primary subfield
   content: b'\xf0'
Item Item070 defined in FSPEC
   content: b'\xff\xff\xff\xff\xff'
Item Item100 defined in FSPEC
   content: b'\x08\x08\x08\x08\x08\x08\x08\x08'
Item Item110 defined in FSPEC
   content: b'\x01'
Item Item120 defined in FSPEC
   content: b'\x08\x08\x08\x08\x08\x08\x08\x08'
Item Item090 defined in FSPEC
   content: b'\x02\x02'
Item REF defined in FSPEC
   content: b'\x10\x10\x10\x10\x10\x10\x10\x10\x10\x10'
Item SPF defined in FSPEC
   content: b'\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11'
Stream position 78 matching total blob size of 78 -> Structure valid
```
