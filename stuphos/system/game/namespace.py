# Provides an import shelter for loading from certain package modules.
try: from game import lookAtRoom
except ImportError:
	# Remove reliance on game and instead rely on world.
	from world.player.commands import lookAtRoom
