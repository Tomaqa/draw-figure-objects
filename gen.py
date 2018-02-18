#!/usr/bin/env python2

from __future__ import division
from gimpfu import *

import logging as log
import sys

log.basicConfig(stream=sys.stdout, level=log.WARNING)
# log.basicConfig(stream=sys.stdout, level=log.DEBUG)
# log.basicConfig(stream=sys.stdout, level=log.NOTSET)

import figure as fig
import layout_mysteria as lm
import draw_gimp as dg
import fig_collection as fc


def Gen(resolution):
   height_mm = 85
   width_mm = 55

   fns = [
      "in/mysteria_basic.tsv",
      "in/mysteria_shared.tsv",
      "in/mysteria_risc.tsv",
   ]

   collection = fc.CFigCollection(resolution_ppi=resolution,
      width_mm=width_mm, height_mm=height_mm,
      draw_figure_class=dg.CDrawFigureGimp,
      layout_figure_class=lm.CLayoutFigureMysteriaCard,
   )
   collection.SetLoader(fc.CLoaderDSV, delim='\t')
   
   for fn in fns:
      print "\n<Processing '%s' ...>\n" % (fn)
      collection.LoadAndDoFigures(fn)

register(
   "python-fu-Mysteria-gen",                        #<- this is plugin name
   N_("Mysteria cards generating"),                 #<- brief description
   "Generates all Mysteria cards from DB",          #<- long description
   "Tomo Stroj",                                    #<- author
   "@Copyright 2017",                               #<- copyright info
   "2017/09/14",                                    #<- creation date
   N_("_Mysteria Gen"),                             #<- label shown in gimp's menu
   "",  #<- kind of image requested from your script (INDEX,RGB,...and so on)
   [                                                #<- input parameters array
      (PF_INT, "resolution", "Cards resolution", 300)
   ],
   [],                                                  #<- output parameters array (usually empty)
   Gen,                                                 #<- main method to call 
   menu="<Image>/Create/Image/"                         #<- Where add your plugin
)

main()
