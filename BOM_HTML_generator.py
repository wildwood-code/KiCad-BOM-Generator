# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
#
#  Filename   : BOM_HTML_generator.py
#  Description:
#    Bill-of-material (BOM) generator for KiCad
#
#    This utility is run from within KiCad Schematic Editor (EESCHEMA) using the
#    "Generate Legacy Bill of Materials..." command under the Tools menu.
#    When using parts out of a compatible library, this utility will attempt to
#    generate manufacturer part numbers for common parts (thick-file resistors,
#    MLCC capacitors, etc.) from the value field.
#    For instance, if the value of a R0805 resistor is '10.0k 1%', it will
#    generate MFN=SEI and MPN=RMCF0805F_10K0, assuming it is configured for SEI
#    chip resistors.
#
#    This borrows from earlier work done by the author for a similar BOM
#    generator for EAGLE. It also borrows from the BOM generator Python scripts
#    that came with KiCad.
#
#  Created    : 03/21/2025
#  Modified   : 04/12/2026
#  Author     : Kerry S. Martin, martin@wild-wood.net
# ******************************************************************************

"""
@package
Output: HTML
Grouped By: IPN, MFN, MFN, ...
Sorted By: Ref
Fields: Qty, Refs, IPN, MFN, AML1, AML2, Value, Package, Description, Datasheet

Automatic BOM part number generator for some components (ceramic and tantalum
capacitors; thick-film, carbon-film, and metal-film resistors)

Optional "variant" supplied on command line chooses the variant
If "variant" is not supplied or is not an exact match of a defined variant for
the schematic, the default will be used.

Command line:
python "pathToFile/BOM_enhanced.py" "%I" "%O.html" {"variant"}
"""

import re
import sys
from BOM.kicad_netlist_reader import netlist, comp
from BOM.kicad_netlist_reader_extension import comp_variants
from BOM.kicad_utils import open_file_write
from BOM.BOM_utilities import BOM_ref_count as BOM_ref_count
from BOM.BOM_capacitor import BOM_MLCC_capacitor as MLCC
from BOM.BOM_capacitor import BOM_tantalum_capacitor as CTAN
from BOM.BOM_resistor import BOM_SMT_resistor as RTHICK
from BOM.BOM_resistor import BOM_THT_resistor as RCF
from BOM.BOM_resistor import BOM_RMF_resistor as RMF
from BOM.BOM_settings import BOM_settings
from BOM.BOM import BOM, BOM_Entry


# <-- BEGIN CONFIGURATION -->

# defined generator class list (in order of "generally most to least common")
GENERATORS = \
[
	MLCC,		# multi-layer ceramic SMT chip capacitors
	RTHICK,		# thick-film SMT chip resistors
	RCF,		# carbon-film THT resistors
	CTAN,		# tantalum SMT capacitors
	RMF			# metal-film SMT MELF resistors
]

# <-- END CONFIGURATION -->


def coerce_str(arg) -> str:
	if isinstance(arg, str):
		return arg
	elif isinstance(arg, bytes):
		return arg.decode("utf-8")
	else:
		return "?"


def bom_generator(filein: str, fileout:str, target:str):
	# Open and read the netlist file
	try:
		net = netlist(filein)
	except:
		# note that netlist.load() will probably catch this and exit
		# try to catch here as an extra layer of error handling
		error = f'Unable to open "{filein}"'
		print(__file__, ":", error, file=sys.stderr)
		return -1
		

	# Open the output file for writing
	# If unsuccessful, write to the standard output stream instead
	try:
		fh_outfile = open_file_write(fileout, 'wb')
		was_outfile_opened = True
	except IOError:
		error = f'Unable to open "{fileout}" for writing'
		print(__file__, ":", error, file=sys.stderr)
		fh_outfile = sys.stdout
		was_outfile_opened = False

	# pre-compile the regex expressions
	RE_PACKAGE = re.compile(r"^(?:.+:)?([^:]+)$")
	
	# generate a list of variants
	sch_variants = comp_variants.get_variant_names(net)
	
	# read the BOM components and look for "BOM_Generator"
	settings = BOM_settings()
	components = net.getInterestingComponents(excludeBOM=False)
	
	for c in components:
		cv = comp_variants(c, target)
		if cv.getLibName()=="Drawing" and cv.getPartName()=="BOM_GENERATOR":
			# get BOM generator settings and apply them to our generators
			fields = cv.getFieldNames()
			for fname in fields:
				v = cv.getField(fname)
				settings.add_setting(fname, v)

			for generator in GENERATORS:
				generator.apply_settings(settings)

			# ignore any other BOM_GENERATOR symbols (there shall only be one)
			break
			
	# read the BOM components and generate the BOM
	components = net.getInterestingComponents(excludeBOM=True)
	bom = BOM()
	component_count = 0

	for c in components:
		
		cv = comp_variants(c, target)
		
		if cv.getDNP():
			# skip this DNP component
			continue

		lib_name = cv.getLibName()
		part_name = cv.getPartName()
		if lib_name=="Drawing" and part_name=="BOM_GENERATOR":
			# skip the BOM_GENERATOR symbol
			continue

		# reference designator(s) and keep a tally of the number of components
		refs = cv.getRef()
		qty = BOM_ref_count(refs)
		component_count += qty

		# part value, description, and datasheet link
		value = cv.getValue()
		desc = cv.getDescription()
		datasheet = cv.getDatasheet()
		
		# footprint/package - coerce this to the actual footprint name
		footprint = cv.getFootprint()
		if m := RE_PACKAGE.match(footprint):
			# strip off everything up to the actual footprint name
			footprint = m.group(1)

		# internal part number, manufacturer name, manufacturer part number
		ipn = cv.getField("IPN")
		mpn = cv.getField("MPN")
		mfn = cv.getField("MFN")

		if not mpn and value:
			# MPN not specified but value is... try to auto-generate MPN
			# if it falls through in here, the defaults from the
			# schematic will be used (i.e., nothing is overridden by
			# the generators)

			# try to check known generator types, which math by part_id:
			#   library_name:symbol_name[package_name]
			part_id = f"{lib_name}:{part_name}[{footprint}]"

			comp = None
			for generator in GENERATORS:
				if comp := generator(part_id, mfn, value):
					break
			
			if comp:
				# override these with the values obtained from the generator
				mfn       = comp.mfn
				mpn       = comp.mpn
				desc      = comp.desc
				footprint = comp.package				

		# either a generator generated mfn, mpn, desc, and footprint
		# or the values pulled directly off the schematic will be used
		entry = BOM_Entry(refs, value, desc, footprint, ipn, mfn, mpn, datasheet)
		
		# attach any supplier tags if present
		aml = cv.getField("S1PN")
		if aml:
			entry.add_aml(aml)

		aml = cv.getField("S2PN")
		if aml:
			entry.add_aml(aml)

		# add our component to the BOM
		bom.join(entry)

	# compress the reference designators then sort by reference designator`
	bom.compress()
	bom.sort()

	# Create the HTML table
	# Start with a basic HTML template
	html = """
	<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
		"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
	<html xmlns="http://www.w3.org/1999/xhtml">
		<head>
			<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
		</head>
		<body>
        <style>
        .text-cell { mso-number-format:"\@"; }
        </style>
		<h1><!--SOURCE--></h1>
		<p><!--DATE--></p>
		<p><!--TOOL--></p>
		<p><!--VARIANT--></p>
		<p><!--COMPCOUNT--></p>
		<table>
		<!--TABLEROW-->
		</table>
		</body>
	</html>
		"""

	# Output a set of rows for a header providing general information
	html = html.replace('<!--SOURCE-->', coerce_str(net.getSource()))
	html = html.replace('<!--DATE-->', coerce_str(net.getDate()))
	html = html.replace('<!--TOOL-->', coerce_str(net.getTool()))
	html = html.replace('<!--COMPCOUNT-->', "<b>Component Count:</b>" + \
		str(component_count))
		
	if sch_variants:
		# this schematic has variants...
		# add a heading stating which one is represented
		variant_tag = "< Default >"
		if target in sch_variants:
			variant_tag = target
		variant_label = f"Variant: {variant_tag}"
		html = html.replace('<!--VARIANT-->', variant_label)

	# generate table header
	row =  '<tr>'
	row += '<th>Qty</th>'
	row += '<th>Refs</th>'
	row += '<th>IPN</th>'
	row += '<th>MFN</th>'
	row += '<th>MPN</th>'
	row += '<th>AML1</th>'
	row += '<th>AML2</th>'
	row += '<th>Value</th>'
	row += '<th>Package</th>'
	row += '<th>Description</th>'
	row += '<th>Datasheet</th>'
	row += '</tr>'

	html = html.replace('<!--TABLEROW-->', row + "<!--TABLEROW-->")

	for entry in bom:
		qty = entry.qty
		refs = entry.refs
		ipn = entry.ipn
		mfn = entry.mfn
		mpn = entry.mpn
		aml_list = entry.aml_list
		n_aml = len(aml_list)
		aml1 = aml_list[0].tag if n_aml >= 1 else ""
		aml2 = aml_list[1].tag if n_aml >= 2 else ""
		value = entry.value
		package = entry.pkg
		desc = entry.desc
		data = entry.data

		row =  '<tr>'
		row += f'<td>{qty}</td>'
		row += f'<td class="text-cell">{refs}</td>'
		row += f'<td class="text-cell">{ipn}</td>'
		row += f'<td class="text-cell">{mfn}</td>'
		row += f'<td class="text-cell">{mpn}</td>'
		row += f'<td class="text-cell">{aml1}</td>'
		row += f'<td class="text-cell">{aml2}</td>'
		row += f'<td class="text-cell">{value}</td>'
		row += f'<td class="text-cell">{package}</td>'
		row += f'<td class="text-cell">{desc}</td>'
		row += f'<td class="text-cell">{data}</td>'
		row += '</tr>'

		html = html.replace('<!--TABLEROW-->', row + "<!--TABLEROW-->")

	# Write the formatted html to the file
	if sys.version_info[0] < 3:
		fh_outfile.write(html)
	else:
		fh_outfile.write(html.encode('utf-8')) # type: ignore
	fh_outfile.close()

	if not was_outfile_opened:
		return 1
		
	return 0


if __name__ == "__main__":

	nargin = len(sys.argv)-1

	if nargin < 2:
		print('Usage: BOM_HTML_generator.py "filein.xml" "fileout.html" {"variantname"}')
		result = 0

	else:
		filein = sys.argv[1]
		fileout = sys.argv[2]
		variant = sys.argv[3] if nargin >= 3 else ""
		result = bom_generator(filein, fileout, variant)
	
	sys.exit(result)


# ******************************************************************************
#  Copyright © 2026 Kerry S. Martin, martin@wild-wood.net
#  Free for usage without warranty, expressed or implied; attribution required
# ******************************************************************************