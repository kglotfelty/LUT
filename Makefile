
ROOT = /data/lenin2/Scripts/MyStuff/ciao46/ciao-4.6/contrib
DEST = lib/python2.7/site-packages/chips_contrib/
DEV  = /data/da/Docs/scripts/dev

CP_F = /bin/cp -f

all: $(ROOT)/$(DEST)/lutplot.py $(ROOT)/$(DEST)/lutbox_whisker.py

install: all

$(ROOT)/$(DEST)/lutplot.py : lutplot.py
	$(CP_F) $< $@

$(ROOT)/$(DEST)/lutbox_whisker.py : lutbox_whisker.py
	$(CP_F) $< $@

dev: $(DEV)/$(DEST)/lutplot.py  $(DEV)/$(DEST)/lutbox_whisker.py

$(DEV)/$(DEST)/lutplot.py : lutplot.py
	$(CP_F) $< $@

$(DEV)/$(DEST)/lutbox_whisker.py : lutbox_whisker.py
	$(CP_F) $< $@


