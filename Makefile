
ROOT = /data/lenin2/Scripts/MyStuff/ciao46/ciao-4.6/contrib
DEST = lib/python2.7/site-packages/chips_contrib/lut
DEV  = /data/da/Docs/scripts/dev

CP_FV = /bin/cp -fv

PY_SRC = __init__.py all.py color_curves.py hexify.py lutbox_whisker.py lutcolors.py lutplot.py pick_lut.py

all: 
	@mkdir -p $(ROOT)/$(DEST)/
	@$(CP_FV) $(PY_SRC) $(ROOT)/$(DEST)/


install: all


dev: 
	@mkdir -p $(DEV)/$(DEST)/
	@$(CP_FV) $(PY_SRC) $(DEV)/$(DEST)/
