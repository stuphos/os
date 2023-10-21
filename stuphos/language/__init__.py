# The lang package.  This should be renamed to 'interface', and import certain format-related
# packages from component (like structural).
#
# The 'layer' package can be renamed to the generic 'language', as a layer nomination is better
# suited to the runtime package.  The web package could be considered a part of the interface
# package, but because it represents a core application feature (a server), it isn't a priority.
#
# The purpose is not to generate packages with gigantic numbers of submodules, but rather to
# distributed component functionality evenly across a balanced tree, so that the features of
# the application are rationaly organized and only complex and involved algorithms need take
# up large module sizes.
