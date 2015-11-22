#!/usr/bin/python

#
#	This program generates a levenshtein automaton for a given input string and edit distance
#	The two stipulations are:
#		that len(string) > edit distance + 1
#		that edit distance > 0
#	The output of this program is ANML code for the resulting automaton.
#

from jinja2 import Environment, FileSystemLoader
import argparse

width = 0
height = 0
edit_distance = 0

# Generates a unique ID for each block in the Levenshtein automaton (row index, height index)
def generate_id(i,j):

	if i < 0 or i >= height or j < 0 or j >= width:
		print "ERROR: out of bounds indexes ", i, j
		return -1
	else:
		return i * width + j

# Print out the nodes contained in the Levenshtein automaton (used for debugging purposes)
def print_blocks(blocks):

	for i in range(height-1, -1, -1): # For each row

		for j in range(width): # For each column

			print (i,j),

			if (i, j) in blocks:
				print(blocks[(i,j)]),"\t\t",
			else:
				print "\t\t\t\t",
			if j == width - 1 and i != 0:
				print
		print

if __name__ == '__main__':

	# Parse arguments
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('-n', '--name', required=True, help='Name of the Automata Network')
	parser.add_argument('-s', '--string', required=True, help='Input Directory') # The search string
	parser.add_argument('-e', '--edit_distance', required=True, type=int, help='Maximum Edit Distance Accepted') # Edit distance
	parser.add_argument('-o', '--output_filename', required=True, help='Output Filename') # Output file name for the ANML output
	parser.add_argument('-d', '--description', required=False, help='Description of the Automata Network') # Description of the AP network
	args = parser.parse_args() # Parse the input arguments

	# If the string length is shorter than edit distance or edit distance < 1, report an Error
	if (len(args.string) <= (args.edit_distance + 1)) or (args.edit_distance < 1):
		print "\tError: The edit distance must be < the length of the search string and greater than 0"
		print "\tArguments: ", args
		exit(1)

	# BLOCKS
	blocks = {} # Dictionary to keep track of the blocks that make up the Levenshtein Automaton

	#
	# -Format-
	# blocks [ (row_id, column_id)] = (index, block_type)
	#

	ste_blocks = [] # block ids of STEs; not macros (no input ports)
	
	# Get the dimmensions of the Levenshtein Automaton's main rectangle (sans insertion column)	
	height = args.edit_distance + 1 # Height of the Levenshtein Automaton (one row for each error possible; including 0)
	width = len(args.string) + 1 # Width of the Levenshtein Automaton
	edit_distance = args.edit_distance

	# Iterate throught every row
	for i in range(height):

		for j in range(width): # For each column

			if j == 0 and i == 0: # Nothing here
				continue

			else:
				# Give each block a unique ID
				blocks[(i,j)] = (generate_id(i,j),)

			if i == 0: # If on the bottom row

				if j == 1:
					blocks[(i,j)] += ("StMB",) # This is the first block on the bottom-most row, and must be a Starting Match Block

				elif j >= (width - 1 - edit_distance): # If the index is within edit_distance of the end of the bottom row, make it reporting
					blocks[(i,j)] += ("RMB",) # This is a reporting match block on the bottom row

				else:
					blocks[(i,j)] += ("SiMB",) # If this block is on the bottom row but not a starting or reporting block, its a simple match block

			elif i == 1 and j == 0:
				blocks[(i,j)] += ("SSEB",) #The bottom-most block in the 0th column must be a Simple Starting Error Block

			elif j == 0:
				blocks[(i,j)] += ("CSTE",) # The first column is a stack of Error Accept STEs on top of a Simple Starting Error Block
				ste_blocks.append(blocks[(i, j)][0]) # This is a raw STE

			elif j == i: # If in the starting error diagonal, make a starting error block
				blocks[(i,j)] += ("SEB",)

			elif j == i + 1: # If in the late start match diagonal, make a late start match block
				blocks[(i,j)] += ("LSMB",)

			elif j >= (width - 1) - edit_distance + i: # We are within edit distance ( - current height) of the end of the string, therefore make reporting element
				blocks[(i,j)] += ("SERB",)

			else:
				blocks[(i,j)] += ("SiEB",) # If not a Starting Error block or Starting Match Block or Reporting Block, this must be a Simple Error Block


	# CONNECTIONS
	blocks_connections = {}

	#
	# -Format-
	# blocks_connections [ (row_id, column_id)] = [(connected_block_id, (out_ports), in_port), (connected_block_id, (out_ports), in_port),...]
	#


	for i in range(height): # For each row

		for j in range(width): # For each column, including the leading column

			if(i == 0 and j == 0): # This block doesn't exist; continue
				continue
			
			blocks_connections[(i,j)] = [] # Each entry in the blocks_connections dictionary is a list of nodes to be connected to, and the port they are connected to

			# All out ports from each block must connect to all connecting blocks; there are three types of blocks
			if (i == 0): # All bottom blocks only have match_out ports
				out_ports = ("match_out",)

			elif (i == 1 and j == 0): # The Simple Start Error Block only has an error_out port
				out_ports = ("error_out",)

			else: # All other blocks have both match_out and error_out ports
				out_ports = ("match_out", "error_out")

			# INSERTIONS (UP)
			if i != (height - 1): # If not in the top row, add connections for insertions (UP); 
				
				blocks_connections[(i,j)].append((generate_id(i+1, j), out_ports, "error_in"))

			# MATCH (RIGHT)
			if j < (width - 1): # If not in the right-most column, add connection to right match

				blocks_connections[(i,j)].append((generate_id(i, j+1), out_ports, "match_in"))
				
			# REPLACEMENT (1 right - 1 up :: DIAGONAL)
			if ( (i < (height - 1)) and (j < (width - 1)) ): # If not in the top row or right-most column, we can do a replacement

				blocks_connections[(i,j)].append((generate_id(i+1, j+1), out_ports, "error_in"))

			# N-DELETION then MATCH(2+k Right - k Up :: DIAGONAL)
			diagonals = min(((height - 1) - i), ((width - 1) - j - 1)) # Number of characters we can skip and match

			for k in range(diagonals):
				
				blocks_connections[(i,j)].append((generate_id(i+k+1, j+k+2), out_ports, "match_in"))


			# N-DELETION then ERROR(2+k Right - 1+k Up :: DIAGONAL)
			diagonals = min(((height - 1) - i - 1), ((width - 1) - j - 1)) # Number of characters we can skip and then error-match

			for k in range(diagonals):
				
				blocks_connections[(i,j)].append((generate_id(i+k+2, j+k+2), out_ports, "error_in"))

    # Populate the dictionary translating abbreviations of blocks to their definitions.
    # It is necessary to keep the macros directory in the same directory as this file.
	block_lookup_table = {}
	block_lookup_table["CSTE"] = "ste:*"
	block_lookup_table["SERB"] = "macros/Simple_Error_Report_Block.anml"
	block_lookup_table["RMB"] = "macros/Reporting_Match_Block.anml"
	block_lookup_table["StMB"] = "macros/Starting_Match_Block.anml"
	block_lookup_table["SSEB"] = "macros/Simple_Starting_Error_Block.anml"
	block_lookup_table["SiMB"] = "macros/Simple_Match_Block.anml"
	block_lookup_table["SiEB"] = "macros/Simple_Error_Block.anml"
	block_lookup_table["LSMB"] = "macros/Late_Start_Match_Block.anml"
	block_lookup_table["SEB"] = "macros/Starting_Error_Block.anml"

    # Populate the context dictionary with everything necessary to build the ANML file
	context = {} #Dictionary
	context['name'] = args.name
	context['string'] = args.string
	context['edit_distance'] = args.edit_distance
	context['width'] = width
	context['height'] = height
	context['blocks'] = blocks
	context['blocks_connections'] = blocks_connections
	context['block_lookup_table'] = block_lookup_table
	context['ste_blocks'] = ste_blocks

	if args.description:
		context['description'] = args.description
	else:
		context['description'] = ""

    # Set the environment and template to render
	env = Environment(loader=FileSystemLoader('./templates'), trim_blocks=True, lstrip_blocks=True)
	template = env.get_template('toplevel.anml.template')

    # Render the template.
	rendered_file = template.render(context=context)

    # Finally, write the result to a file.
	with open(args.output_filename, 'w') as outFile:
		outFile.write(rendered_file)