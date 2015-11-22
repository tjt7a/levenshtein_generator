#!/usr/bin/python

import argparse
import random
import string

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('-s', '--symbol_set', required=False, help='The symbol set used to generate the string')
	parser.add_argument('-l', '--length', required=True, help='The length of the string')
	args = parser.parse_args()

	output = ""

	alphabet = []

	if args.symbol_set == "dna" or args.symbol_set == "DNA":
		alphabet = ['a','t','g','c']
	else:
		alphabet = list(string.printable)

	for i in range(int(args.length)):
		output += random.choice(alphabet)
	
	print output
