# Application component library.
# Copyright 2010-2021 runphase.com .  All rights reserved.
# --
# The core library made out of components and frameworks for building applications.
# Applications are rather specific, but most of the system or platform features are
# provided for as component layers.  And although specific server architectures
# might be more heavily rooted in peripheral projects, much of that framework is
# provided by the contained network components.  Most everything works towards the
# purposes of the application.

# Relative imports are done for modules within the same subdirectory under any
# single one of the top-level stuphos subpackages.  Between code in these top-
# level packages, an absolute import should be used.

# This should be removed to the specific implementation configuration compartment.
from .runtime.core import *


# try: wmc = io.here.resources('site.wmc').loading.structure
# except: pass
# else: globals().update(dictOf(wmc))
