# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : BOM.py
#  Description:
#    Bill-of-material (BOM) class and supporting classes (Part_Identity,
#    BOM_Entry)
#
#    The BOM class contains methods for storing and manipulating BOMs
#
#  Created    : 04/02/2026
#  Modified   : 04/11/2026
#  Author     : Kerry S. Martin, martin@wild-wood.net
# ******************************************************************************

"""BOM class: object to hold BOMs"""

import re
from copy import copy
from collections.abc import Iterable, Iterator
from BOM.static_init import static_init
from BOM.BOM_utilities import BOM_ref_expand, BOM_ref_compress, BOM_ref_count


@static_init
class Part_Identity:

	@classmethod
	def static_init(cls):
		# WARNING: changing TAG_SEPARATOR requires changing RE_SPLIT_TAG
		cls.TAG_SEPARATOR : str = "::"
		cls.RE_SPLIT_TAG = re.compile(r"^([^:]*):{1,2}([^:]*)$", re.IGNORECASE)


	def __init__(self, arg1:"str|Part_Identity|None"=None, arg2:str|None=None):
		"""Part_Identity constructor

		Args:
			arg1: see behavior below
			arg2: see behavior below

		Behavior:
			Part_Identity("MFN", "MPN")    # 2 args -> order is mfn mpn
			Part_Identity("MFN::MPN")      # 1 arg tagged -> order is mfn mpn
			Part_Identity("MPN")           # 1 arg tagged -> mpn given, mfn=""
			Part_Identity()                # args blank -> mfn = "", mpn = ""
			Part_Identity(Part_Identity(...))  # copy constructor
		"""
		if isinstance(arg1, Part_Identity):
			# copy constructor
			self._mfn = arg1._mfn
			self._mpn = arg1._mpn
		elif arg2 is None and arg1 is not None:
			# look for a single tag (ex/ TI::CD4017BE)
			if m := Part_Identity.RE_SPLIT_TAG.match(arg1):
				# convert from the tag
				self._mfn = m.group(1)
				self._mpn = m.group(2)
			else:
				# assume mpn was specified and leave mfn blank
				self._mfn = ""
				self._mpn = arg1
		else:
			# they are either specified individually or not specified
			self._mfn : str = "" if arg1 is None else arg1
			self._mpn : str = "" if arg2 is None else arg2


	def __bool__(self) -> bool:
		"""Check to see if the Part_Identity is defined
		
		Returns:
			True if the Part_Identity has mfn or mpn defined;
			False if neither mfn nor mpn is defined
		"""
		return (self._mfn or self._mpn)


	def __eq__(self, src:"Part_Identity") -> bool:
		"""Part_Identity comparison

		Args:
			src: [Part_Identity]   object to compare

		Returns:
			True if all fields match exactly; False otherwise
		"""
		result = True
		if not isinstance(src, Part_Identity):
			result = False
		elif self._mfn != src._mfn or self._mpn != src._mpn:
			result = False

		return result


	@property
	def mfn(self) -> str:
		"""mfn property: manufacturer (or distributor) name

		Returns:
			str: manufacturer/distributor name
		"""
		return self._mfn
		
		
	@property
	def mpn(self) -> str:
		"""mpn property: manufacturer (or distributor) part number

		Returns:
			str: manufacturer/distributor part number
		"""
		return self._mpn


	@property
	def tag(self) -> str:
		"""tag property: representation of manufacturer and part number

		Returns:
			str: example/ "Digikey::MC74LVX125DGOS-ND"
		"""
		return f"{self._mfn}{Part_Identity.TAG_SEPARATOR}{self._mpn}"


	@property
	def aml(self) -> list["Part_Identity"]:
		"""aml property: list of approved manufacturers

		Returns:
			list: simply wraps this part identity object in a one-item list
		"""
		return [self]


	def __repr__(self) -> str:
		"""string representation of this part identity object

		Returns:
			str: example/ 'Part_Identity("Digikey", "MC74LVX125DGOS-ND")'
		"""
		return f'Part_Identity("{self._mfn}", "{self._mpn}")'


@static_init
class BOM_Entry:
	"""BOM_Entry: class to hold one line of a BOM

	Properties:
		qty     number of reference designators
		refs    part reference designator(s)
		value   part value (displayed on schematic)
		desc    part description
		pkg     part package
		ipn     internal part number
		data    datasheet URL
		mfn     manufacturer name
		mpn     manufacturer part number
		aml     approved manufacturer list

	The BOM entry may represent a single reference designator, multiple reference
	designators, or no reference designators.

	The BOM entry may contain zero or more part identites. Each part identity
	represents a manufacturer (or distributor) and part number. The set of part
	identities is known as the AML (approved manufacturer list).

	Example AML:
		[ Part_Identity("ON", "MC74LVX125DG"),
		  Part_Identity("Digikey", "MC74LVX125DGOS-ND"),
		  Part_Identity("Mouser", "863-MC74LVX125DG") ]
	"""

	@classmethod
	def static_init(cls):
		cls._RE_REF_RANGE = re.compile(r"\s*([A-Z]+)([0-9]+)\s*(?:-\s*(?:\1)?([0-9]+))?\s*(?:,?)\s*", re.IGNORECASE)


	def __init__(self, refs:str|list[str]|None=None, value:str|None=None, desc:str|None=None, pkg:str|None=None, ipn:str|None=None, mfn:str|None=None, mpn:str|None=None, data:str|None=None):
		"""Creates a BOM_Entry object

		Args:
			refs: reference designator(s) as a str or list
			value: value of the part represented by this entry
			desc: description of the part represented by this entry
			pkg: package of the part represented by this entry
			ipn: internal part number of the part represented by this entry
		"""
		self._qty : int = 0  # calculated later
		self._refs : str = ""  # calculated later
		self._value : str = "" if value is None else value
		self._desc : str = "" if desc is None else desc
		self._pkg : str = "" if pkg is None else pkg
		self._ipn : str = "" if ipn is None else ipn
		self._data : str = "" if data is None else data
		self._mfn : str = "" if mfn is None else mfn
		self._mpn : str = "" if mpn is None else mpn
		self._aml : list[Part_Identity] = []
		if refs is None:
			self._refs = ""
		elif isinstance(refs, list):
			self._refs = ",".join(refs)
		else:
			self._refs = refs

		self._qty = BOM_Entry.__count_references(self._refs)


	def __eq__(self, src:"BOM_Entry") -> bool:
		"""Compares if the target matches us, except for refdes which is not compared

		Args:
			src: [BOM_Entry]   object to compare

		Returns:
			True if fields match, except for refs; False otherwise

		Notes:
			AML list is compared item-for-item and must match exactly
		"""
		result = True
		if not isinstance(src, BOM_Entry):
			result = False
		else:
			while True:  # one-pass loop
				if self._value != src._value:
					result = False
					break
				if self._desc != src._desc:
					result = False
					break
				if self._pkg != src._pkg:
					result = False
					break
				if self._ipn != src._ipn:
					result = False
					break
				if self._mfn != src._mfn:
					result = False
					break
				if self._mpn != src._mpn:
					result = False
					break
				if self._data != src._data:
					result = False
					break
				if (n := len(self._aml)) != len(src._aml):
					result = False
					break
				for i in range(n):
					if self._aml[i] != src._aml[i]:
						result = False
						break
				break # if we hit this, there were no False conditions

		return result


	@property
	def qty(self) -> int:
		"""qty property: number of references in the entry

		Returns:
			int: number of entries, 0 if no entries
		"""
		return self._qty


	@property
	def refs(self) -> str:
		"""refs property: reference designator(s)

		Returns:
			str: reference designators as stored in entry
		"""
		return self._refs


	@refs.setter
	def refs(self, refs:str):
		"""refs property setter: reference designator(s)

		Args:
			refs: [str]  new reference to set
		"""
		if isinstance(refs, str):
			self._refs = refs
			self._qty = BOM_Entry.__count_references(self._refs)


	@property
	def value(self) -> str:
		"""value property: value of part in entry

		Returns:
			str: value of the part as stored in entry
		"""
		return self._value


	@property
	def desc(self) -> str:
		"""desc property: part description

		Returns:
			str: description of the part in the entry
		"""
		return self._desc


	@property
	def pkg(self) -> str:
		"""pkg property: part package (device package)

		Returns:
			str: package name (example/ "SO-8")
		"""
		return self._pkg


	@property
	def ipn(self) -> str:
		"""ipn property: internal part number

		Returns:
			str: part number used by the BOM owner to track the part
		"""
		return self._ipn


	@property
	def mfn(self) -> str:
		return self._mfn


	@property
	def mpn(self) -> str:
		return self._mpn


	@property
	def data(self) -> str:
		return self._data


	@property
	def aml(self) -> Iterator[Part_Identity]:
		"""aml property: approved manufacturer list iterator

		Yields:
			AML entries
		"""
		for part in self._aml:
			yield part


	@property
	def aml_list(self) -> list[Part_Identity]:
		"""aml_list property: approved manufacturer list

		Returns:
			list[...]: the list of all MFN::MPN for the part
		"""
		return copy(self._aml)


	@property
	def num_aml(self) -> int:
		"""num_aml property: number of items in the AML list

		Returns:
			int: number of items in the AML list, 0 if empty
		"""
		return len(self._aml)


	def add_aml(self, aml:str|Part_Identity|list[Part_Identity|str]):
		"""Add an item or items to the AML list

		Args:
			aml: str:  tag indicating mfn and mpn (example/ "ON:MC74LVX04DR2G")
			Part_Identity: a single part identity object
			list[Part_Identity]: a list of part identity objects
			list[str]: a list of tags
		"""
		if isinstance(aml, str):
			# assume this is a tag string
			my_aml = Part_Identity(aml).aml

		elif isinstance(aml, list):
			my_aml = []
			for entry in aml:
				if isinstance(entry, str):
					my_aml.append(Part_Identity(entry))
				elif isinstance(entry, Part_Identity):
					my_aml.append(entry)

		elif isinstance(aml, Part_Identity):
			my_aml = [aml]

		else:
			my_aml = []

		for entry in my_aml:
			self._aml.append(entry)


	@staticmethod
	def __count_references(refs:str) -> int:
		matched_refs = BOM_Entry._RE_REF_RANGE.findall(refs)

		# extract all matched references and ranges into a list with extra info for sorting
		n_refs = 0
		for entry in matched_refs:
			r1 = int(entry[1])
			if not entry[2]:
				# individual ref X#, append it to the list
				n_refs += 1
			else:
				# range ref X#-X# or X#-#, append each to the list
				r2 = int(entry[2])
				n_refs += r2-r1+1

		return n_refs


	def __repr__(self) -> str:
		"""String representation of BOM_Entry object

		Returns:
			str: string representation of BOM_Entry object
		"""
		my_str = f"BOM_Entry({self._qty},[{self._refs}],{self._value},{self._desc},{self._pkg},{self._ipn},"
		if len(self._aml)>0:
			my_str = my_str + "[\n"
			for pi in self._aml:
				my_str = my_str + "  " + str(pi) + "\n"

			my_str = my_str + "])"
		else:
			my_str = my_str + "[])"
		return my_str


@static_init
class BOM:

	@classmethod
	def static_init(cls):
		cls.RE_WILD_PATTERN = re.compile(r"(?:^|,)([a-z]+)(?=\*,|\*$)", re.IGNORECASE)
		cls.RE_FIX_COMMAS = re.compile(r",+(?=,)")
		cls.RE_GET_REFBASE = re.compile(r"^([a-z]+)[^a-z]+$", re.IGNORECASE)


	def __init__(self):
		"""BOM constructror

		Construct an empty BOM object
		"""
		self._bom : list[BOM_Entry] = []
		self._next_iter : int|None = None


	def __repr__(self) -> str:
		"""String representation of this BOM

		Returns:
			A string dump of the contents of this BOM
		"""
		if len(self._bom) == 0:
			repr = "<empty>"
		else:
			repr = ""
			for entry in self._bom:
				repr = repr + str(entry) + "\n"
		return repr


	def __iter__(self) -> "BOM":
		if len(self._bom) > 0:
			self._next_iter = 0
		else:
			self._next_iter = None
		return self


	def __next__(self) -> BOM_Entry:
		if self._next_iter is None:
			raise StopIteration
		if self._next_iter >= len(self._bom):
			raise StopIteration
		entry = self._bom[self._next_iter]
		self._next_iter += 1
		return entry


	def join(self, src:"BOM_Entry|BOM") -> "BOM":
		"""Append a BOM_Entry or join another BOM to this one

		Args:
			src: [BOM_Entry]  BOM entry to add to this one
				 [BOM]        BOM to join to this one

		Returns:
			This BOM after the operation
		"""
		if isinstance(src, BOM_Entry):
			self._bom.append(src)
		elif isinstance(src, BOM):
			self._bom.extend(src._bom)
		return self


	def validate(self) -> bool:
		"""Validates that there are no duplicate refs or other BOM issues

		Returns:
			True if the BOM has no issues; False otherwise
		"""
		result = True
		check_bom = copy(self).expand().sort()
		last_ref = None
		for entry in check_bom._bom:
			if last_ref is not None and entry.refs == last_ref:
				result = False
				break
			last_ref = entry.refs

		return result


	def compress(self) -> "BOM":
		"""Compress this BOM into like parts with refdes ranges (e.g. R1-3,R8-9)

		Returns:
			This BOM after the operation
		"""
		# start by expanding the BOM
		self.expand()

		# sort in this order mfn, mpn, value, pkg, ipn (don't sort on desc for now)
		self._bom.sort(key=lambda x: (x.mfn, x.mpn, x.value, x.pkg, x.ipn))

		# go through the entries in order and compare
		# ipn, value, pkg, desc, and sorted aml must be identical
		# if they are identical, compress the two entries together
		new_bom : list[BOM_Entry] = []
		last_entry = None
		current_refs : str = ""
		for entry in self._bom:
			if last_entry is None:
				last_entry = entry
				current_refs = entry.refs
			else:
				if entry == last_entry:
					# add this to the refs list for this matching part
					if current_refs:
						current_refs = current_refs + "," + entry.refs
					else:
						current_refs = entry.refs
				else:
					# non-matching part, put it in the BOM and start a new refs list
					(current_refs, _) = BOM_ref_compress(current_refs)
					last_entry.refs = current_refs
					new_bom.append(last_entry)
					current_refs = entry.refs
					last_entry = entry

		if current_refs and last_entry is not None:
			# need to push the last one on
			(current_refs, _) = BOM_ref_compress(current_refs)
			last_entry.refs = current_refs
			new_bom.append(last_entry)

		self._bom = new_bom

		return self


	def expand(self) -> "BOM":
		"""Expand this BOM into individual parts (e.g., "R1", "R2", "R3", "R8", "R9")

		Returns:
			This BOM after the operation
		"""
		new_bom : list[BOM_Entry] = []
		for entry in self._bom:
			refdes = entry.refs
			exp_refs = BOM_ref_expand(refdes)
			for new_ref in exp_refs:
				new_entry = copy(entry)
				new_entry.refs = new_ref
				new_bom.append(new_entry)
		self._bom = new_bom
		return self


	def sort(self) -> "BOM":
		"""Sorts this BOM based upon alphabetical reference designator

		Returns:
			This BOM after the sort operation
		"""
		self._bom.sort(key=lambda x:x.refs)
		return self


	def delete(self, tgt:str) -> "BOM":
		"""Delete refdes matched by target filter from this BOM

		Args:
			tgt: [str]  target filter (see notes)

		Notes on target filter:
			tgt may specify a single refdes:  ex/ "R1"
			tgt may specify multiple refdes:  ex/ "R2,R4,R8,C1"
			tgt may specify a ranged refdes:  ex/ "C7-10,D1-D3"
			tgt may specify simple wildcards: ex/ "R*"
			tgt may combine all of the above: ex/ "R4,C9-10,D*,CA*"
			tgt may be negated with a single caret "^" as the first character
			ex/ "^C1-5,R8-11"   matches everything except for C1-5 and R8-11

		Returns:
			This BOM with refdes matching the target filter deleted
		"""
		filt_bom = copy(self).expand()
		new_bom = BOM()
		filt_refs, wild_refs, is_negative = BOM._expand_target(tgt)
		for entry in filt_bom._bom:
			if BOM._is_match(entry.refs, filt_refs, wild_refs):
				if is_negative:
					new_bom.join(entry)
			elif not is_negative:
				new_bom.join(entry)

		new_bom.compress()
		self._bom = new_bom._bom

		return self


	def filter(self, tgt:str) -> "BOM":
		"""Copies refdes matched by target filter to a new BOM without changing this BOM

		Args:
			tgt: [str]  target filter (see notes)

		Notes on target filter:
			tgt may specify a single refdes:  ex/ "R1"
			tgt may specify multiple refdes:  ex/ "R2,R4,R8,C1"
			tgt may specify a ranged refdes:  ex/ "C7-10,D1-D3"
			tgt may specify simple wildcards: ex/ "R*"
			tgt may combine all of the above: ex/ "R4,C9-10,D*,CA*"
			tgt may be negated with a single caret "^" as the first character
			ex/ "^C1-5,R8-11"   matches everything except for C1-5 and R8-11

		Returns:
			The new BOM with refdes matching target filter
			This BOM is unchanged
		"""
		filt_bom = copy(self).expand()
		new_bom = BOM()
		filt_refs, wild_refs, is_negative = BOM._expand_target(tgt)
		for entry in filt_bom._bom:
			if BOM._is_match(entry.refs, filt_refs, wild_refs):
				if not is_negative:
					new_bom.join(entry)
			elif is_negative:
				new_bom.join(entry)

		return new_bom.compress()


	def split(self, tgt:str) -> "tuple[BOM,BOM]":
		"""Splits refdes matched by target filter into two BOMs without changing this BOM

		Args:
			tgt: [str]  target filter (see notes)

		Notes on target filter:
			tgt may specify a single refdes:  ex/ "R1"
			tgt may specify multiple refdes:  ex/ "R2,R4,R8,C1"
			tgt may specify a ranged refdes:  ex/ "C7-10,D1-D3"
			tgt may specify simple wildcards: ex/ "R*"
			tgt may combine all of the above: ex/ "R4,C9-10,D*,CA*"
			tgt may be negated with a single caret "^" as the first character
			ex/ "^C1-5,R8-11"   matches everything except for C1-5 and R8-11

		Returns:
			Tuple (bom1, bom2)
			  bom1 == parts where ref matches target filter
			  bom2 == parts where ref does not match target filter
			This BOM is unchanged
		"""
		filt_bom = copy(self).expand()
		bom1 = BOM()
		bom2 = BOM()
		filt_refs, wild_refs, is_negative = BOM._expand_target(tgt)
		for entry in filt_bom._bom:
			if BOM._is_match(entry.refs, filt_refs, wild_refs):
				if is_negative:
					bom2.join(entry)
				else:
					bom1.join(entry)
			elif is_negative:
				bom1.join(entry)
			else:
				bom2.join(entry)

		return (bom1.compress(), bom2.compress())


	@staticmethod
	def _is_match(ref:str, filt_refs:list[str], wild_refs:list[str]) -> bool:
		result = False
		if ref in filt_refs:
			result = True
		elif m := BOM.RE_GET_REFBASE.match(ref):
			refbase = m.group(1)
			if refbase in wild_refs:
				result = True
		return result


	@staticmethod
	def _expand_target(tgt:str) -> tuple[list[str],list[str],bool]:
		is_negative = False
		wildcards = []
		refs = []
		if tgt:
			if tgt[0] == '^':
				is_negative = True
				tgt = tgt[1:]
			
			if wildcards := BOM.RE_WILD_PATTERN.findall(tgt):
				tgt = BOM.RE_FIX_COMMAS.sub("", tgt)
				tgt = tgt.strip(',')

			refs = BOM_ref_expand(tgt)

		return (refs, wildcards, is_negative)


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************