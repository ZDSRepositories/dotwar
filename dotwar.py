#!/usr/bin/env python3

## Do not call as a library. This is a CLI script.

import sys
import inspect
from dotwar_classes import *

commands = {}

def cli(function):
	global commands
	commands[function.__name__] = function
	return function


def print_help(command_name=None):
	if command_name:
		parameters_string = '> <'.join(inspect.getfullargspec(commands[command_name]).args).join('<>')
		print(f'  {command_name} {parameters_string}')
	else:
		print('Commands:')
		for command_name, command_function in commands.items():
			parameters_string = '> <'.join(inspect.getfullargspec(command_function).args).join('<>')
			print(f'  {command_name} {parameters_string}')


game_path = os.getcwd()

@cli
def add_game(game_name):
	g = Game(game_name, game_path, force_new=True)
	## Can't use `with` because of `g.new` must come before `g.load`.
	g.new(overwrite=True)
	g.load()

	g.add_entity("Earth", None, [0, 0, 0], [0, 0, 0], [0, 0, 0], "planet", [], -1)
	g.edit_entity("Earth", "captured", False)

	g.update(datetime.timedelta(seconds=1))
	g.save()

@cli
def add_ship(game_name, ship_name, captain, team, x, y, z):
	with Game(game_name, game_path) as g:
		g.add_entity(ship_name, captain, [int(x), int(y), int(z)], [0, 0, 0], [0.0, 0, 0], "craft", [], int(team), True)


if '__main__' == __name__:
	## Dispatch.
	argv = sys.argv
	if 2 > len(argv):
		print('Requires a subcommand name.')
		print_help()
		exit(1)
	command_name = argv[1]
	command_args = argv[2:]
	if command_name not in commands:
		print(f'Command "{command_name}" is not supported.')
		print_help(command_name)
		exit(1)
	command_function = commands[command_name]
	command_args_length = len(command_args)
	command_parameters_length = len(inspect.getfullargspec(command_function).args)
	if command_args_length != command_parameters_length:
		print(f'Incorrect number of arguments. Got {command_args_length} arguments but expected {command_parameters_length}.')
		print_help(command_name)
		exit(1)
	commands[command_name](*command_args)
	exit(0)
