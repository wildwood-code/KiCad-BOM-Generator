# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : BOM_utilities.py
#  Description:
#    Utilities for working with bills-of-material (BOMs)
#
#  Created    : 03/15/2025
#  Modified   : 04/11/2026
#  Author     : Kerry S. Martin, martin@wild-wood.net
# ******************************************************************************

"""BOM utilities: Utilities for working with bills-of-material (BOMs)"""

import re


# ------------------------------------------------------------------------------
# Reference designator utilities
# ------------------------------------------------------------------------------

__RE_REF_RANGE = re.compile(r"\s*([A-Z]+)([0-9]+)\s*(?:-\s*(?:\1)?([0-9]+))?\s*(?:,?)\s*", re.IGNORECASE)
__RE_REF_DISSECT = re.compile(r"^([A-Z]+)([0-9]+)$", re.IGNORECASE)


def BOM_ref_expand(refs:str) -> list:
	"""BOM reference list expander. Expands reference string to a list.

	Args:
		refs: Reference string ex/ "R1-R5,R10,R22"

	Returns:
		List with all individual references.
	"""

	# match all occurrences of reference forms: X#, X#-X#, and X#-#
	matched_refs = __RE_REF_RANGE.findall(refs)

	# extract all matched references and ranges into a list with extra info for sorting
	my_refs = []
	for entry in matched_refs:
		rn = entry[0].upper()
		r1 = int(entry[1])
		if not entry[2]:
			# individual ref X#, append it to the list
			my_refs.append((rn, r1, f"{rn}{r1}"))
		else:
			# range ref X#-X# or X#-#, append each to the list
			r2 = int(entry[2])
			for i in range(r1,r2+1):
				my_refs.append((rn, i, f"{rn}{i}"))

	# sort primary key = tuple[0], secondary key = tuple[1], then keep only sorted = tuple[2]
	my_refs = sorted(my_refs, key = lambda field: field[1])
	my_refs = sorted(my_refs, key = lambda field: field[0])
	my_refs = [item[2] for item in my_refs]

	return my_refs


def BOM_ref_compress(refs:str|list, compress_prefix:bool=False) -> tuple[str,int]:
	"""BOM reference compressor. Compresses references to a string with ranges.

	Args:
		refs: List or string of references. ex/ ['R1', 'R2', 'R4']  or "R1-R2,R4"
		compress_prefix: Compress range prefix. Defaults to False.
			False =>  "R1-R2,R4"
			True  =>  "R1-2,R4"

	Returns:
		Tuple with the following elements:
		  String with all references compressed. ex/ "R1-R2,R4"
		  Number of references
	"""

	if isinstance(refs, str):
		# expand to a sorted list
		refs = BOM_ref_expand(refs)
	elif isinstance(refs, list):
		# this will in effect sort the existing list properly
		refs = BOM_ref_expand(','.join(refs))

	# compression algorithm
	refstr = ""
	n_refs = len(refs)
	i = 0
	while i<n_refs:
		# from current position i...
		if matched_ref := __RE_REF_DISSECT.match(refs[i]):
			rn, ri = matched_ref.group(1), int(matched_ref.group(2))
			j = 0
			while True:
				# look ahead for continuous match...
				if i+j+1>=n_refs:
					# hit end of the list... wrap up with the last reference
					if j==0:
						refstr = refstr + f",{rn}{ri}"
					elif compress_prefix:
						refstr = refstr + f",{rn}{ri}-{ri+j}"
					else:
						refstr = refstr + f",{rn}{ri}-{rn}{ri+j}"
					break

				if matched_ref := __RE_REF_DISSECT.match(refs[i+j+1]):
					rjn, rji = matched_ref.group(1), int(matched_ref.group(2))
					if rjn==rn and rji==ri+j+1:
						# consecutive reference found... continue to the next
						j += 1
						continue
					else:
						# non-consecutive reference found... add what we already found
						if j==0:
							refstr = refstr + f",{rn}{ri}"
						elif compress_prefix:
							refstr = refstr + f",{rn}{ri}-{ri+j}"
						else:
							refstr = refstr + f",{rn}{ri}-{rn}{ri+j}"
						break
		i += j+1

	refstr = refstr.lstrip(",")
	return (refstr, n_refs)


def BOM_ref_count(refs:str|list) -> int:
	"""BOM reference counter. Count the number of references.

	Args:
		refs: Reference string ex/ "R1-R5,R10,R22"

	Returns:
		Number of references.
	"""
	if isinstance(refs, str):
		# match all occurrences of reference forms: X#, X#-X#, and X#-#
		matched_refs = __RE_REF_RANGE.findall(refs)

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

	elif isinstance(refs, list):

		return len(refs)


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************