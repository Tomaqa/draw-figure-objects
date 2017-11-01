#!/usr/bin/env python2

## Library that defines 'CFigCollection' container
## that handles a list of 'CFigure's

from __future__ import division
import copy as cp

import sys
import logging as log

log.basicConfig(stream=sys.stdout, level=log.WARNING)

import fig_object as fo
import figure as fig

import csv



################################################################################
################################################################################


##! Automatic adding of attributes based on provided rules
##! has been postponed due to its quite difficult implementation
##! due to necessity of possibility of nested keys handle.
################################################################################
class CLoader(fo.CCompositionBase):
   """
   Base class of collection loader
   that is to be used to set figures' attributes
   from some external data source,
   e.g. file of database
   """
########################################
   def __init__(self, collection, **args):
      fo.CCompositionBase.__init__(self, collection, **args)
      self.srcs = []
      self.tmp_draw_attrs = {}
      self.tmp_layout_attrs = {}
########################################
   ## All default values off class' possible attributes should be defined
   ## These defaults takes precedence over 'CDrawFigure...' defaults
   attr_defaults = fo.merge_dicts(fo.CCompositionBase.attrDefaults(),{
   })
########################################
   def HasSource(self, src):
      return src in self.srcs

   def AddSource(self, src):
      if self.HasSource(src):
         return False
      self.srcs.append(src)
      return True
########################################
   ## Override this
   def AcceptFigureAttr(self, attrs, attr_key, attr_val):
      return attr_val

   ## No need to override this
   def SetFigureAttr(self, attrs_key, attr_key, attr_val):
      attrs = getattr(self, attrs_key)
      
      if self.AcceptFigureAttr(attrs, attr_key, attr_val):
         attrs[attr_key] = fo.merge_dicts(attrs[attr_key], attr_val) if attr_key in attrs else attr_val
########################################
   ## Fill collection with figures attributes
   ## by calling 'AddFigureAttrs'.
   ## Override this - only dummy usage example
   def loadFiguresAttrs(self, src, **args):
      self.SetFigureAttr('tmp_layout_attrs', 'layout_key', 'value')
      self.SetFigureAttr('tmp_draw_attrs', 'draw_key', 'value')
      self.AddFigureAttrs()

   ## Check if this 'src' has not been already loaded.
   ## If not, call 'loadAttrs'.
   ## Do not override this
   def LoadFiguresAttrs(self, src, **args):
      if not self.AddSource(src):
         return False
      self.loadFiguresAttrs(src, **args)
      return True
################################################################################

################################################################################
class CLoaderDSV(CLoader):
   """
   Collection loader class
   for files with delimiter-separated values (DSV).
   Each record has to be delimited with newline.
   First line is considered as keys.
   It is also possible to load 'dict's
   with the same syntax as in Python,
   but delimiter has to be different from 'dict' symbols [{,:}]
   and the value must start with '{'.
   """
########################################
   ## All default values off class' possible attributes should be defined
   ## These defaults takes precedence over 'CDrawFigure...' defaults
   attr_defaults = fo.merge_dicts(CLoader.attrDefaults(),{
      'delim' : '\t',
   })
########################################
   ## Draw figure attributes should be prefixed with 'd'.
   ## Layout figure attributes can be prefixed with 'l',
   ## but don't have to - it acts as default.
   def loadFiguresAttrs(self, src, delim=None):
      if not delim:
         delim = self.delim
      with open(src) as csvfile:
         reader = csv.DictReader(csvfile, delimiter=delim)
      
         for row in reader:
            for key in row.keys():
               split_ = key.split("_",1)
               val = row[key]
               ## Possibly convert to dict
               if val and val[0] == '{':
                  val = eval(val)

               is_default = len(split_) == 1 or split_[0] not in ['d','l']
               is_layout = split_[0] == 'l'
               attrs_key = 'tmp_layout_attrs' if is_default or is_layout else 'tmp_draw_attrs'
               attr_key = key if is_default else split_[1]
               
               self.SetFigureAttr(attrs_key, attr_key, val)
            self.AddFigureAttrs()
################################################################################

################################################################################
################################################################################

################################################################################
class CFigCollection(object):
   """
   Class that handles a list of 'CFigure's
   and provides routines to fill them
   with variable parameters somehow,
   e.g. from text file.
   """
########################################
   ## If all figures are to use the same sizes,
   ## one can set them only once here
   def __init__(self, resolution_ppi=None,
      width_mm=None, height_mm=None,
      draw_figure_args={},
      layout_figure_args={},
      draw_figure_class=None, draw_object_class=None,
      layout_figure_class=None,
   ):
      self.SetSharedResolution(resolution_ppi)
      self.SetSharedWidth(width_mm)
      self.SetSharedHeight(height_mm)

      self.SetSharedDrawFigureAttrs(**draw_figure_args)
      self.SetSharedLayoutFigureAttrs(**layout_figure_args)

      self.draw_figure_class = draw_figure_class
      self.draw_object_class = draw_object_class
      self.layout_figure_class = layout_figure_class

      self.figures = []
      self.figures_pos = -1
      
      self.figures_draw_figure_args = []
      self.figures_layout_figure_args = []

      self.loader = None
########################################
   ## Do not use copy
   def __copy__(self):
      return None
   def __deepcopy__(self, memo):
      return None
########################################
   def SetLoader(self, loader_class, **args):
      self.loader = loader_class(self, **args)
########################################
   @property
   def FiguresCount(self):
      return len(self.figures)

   @property
   def figuresAttrsCount(self):
      return min(len(self.figures_draw_figure_args), len(self.figures_layout_figure_args))
   
   @property
   def FiguresPos(self):
      return self.figures_pos
########################################
   def SetSharedResolution(self, resolution_ppi):
      self.shared_resolution_ppi = resolution_ppi
   def SetSharedWidth(self, width_mm):
      self.shared_width_mm = width_mm
   def SetSharedHeight(self, height_mm):
      self.shared_height_mm = height_mm

   def AttrFromShared(self, attr_key, value):
      ##! Possibly also add option to set these attributes from list for each figure like in 'AttrsFromShared'
      shared_value = getattr(self, 'shared_'+attr_key)
      if value == None:
         if shared_value == None:
            raise ValueError("Common %s for figures is not set in the collection." % attr_key.split("_")[0])
         value = shared_value
      return value
########################################
   def SetSharedDrawFigureAttrs(self, **draw_figure_args):
      self.shared_draw_figure_args = draw_figure_args
   def SetSharedLayoutFigureAttrs(self, **layout_figure_args):
      self.shared_layout_figure_args = layout_figure_args

   def AttrsFromShared(self, idx, attr_key, **args):
      shared_attrs = getattr(self, 'shared_'+attr_key)
      figures_attrs_key = 'figures_'+attr_key
      figs_attrs =  getattr(self, figures_attrs_key)
      fig_attrs = {} if idx >= len(figs_attrs) else figs_attrs[idx]
      return fo.merge_dicts(shared_attrs, fig_attrs, args)

   def addDrawFigureAttrs(self, **draw_figure_args):
      self.figures_draw_figure_args.append(draw_figure_args)
   def addLayoutFigureAttrs(self, **layout_figure_args):
      self.figures_layout_figure_args.append(layout_figure_args)

   def AddFigureAttrs(self, draw_figure_args={}, layout_figure_args={}):
      if not draw_figure_args and self.loader != None:
         draw_figure_args = self.loader.tmp_draw_attrs
         self.loader.tmp_draw_attrs = {}
      if not layout_figure_args and self.loader != None:
         layout_figure_args = self.loader.tmp_layout_attrs
         self.loader.tmp_layout_attrs = {}

      print "Adding %d. figure attributes ..." % (self.figuresAttrsCount+1)
      self.addDrawFigureAttrs(**draw_figure_args)
      self.addLayoutFigureAttrs(**layout_figure_args)
########################################
   def addFigure(self, figure):
      self.figures.append(figure)
      if self.figuresAttrsCount == self.FiguresCount-1:
         self.AddFigureAttrs()

   def AddFigure(self, resolution_ppi=None, width_mm=None, height_mm=None, draw_figure_args={}, layout_figure_args={}):
      resolution_ppi = self.AttrFromShared('resolution_ppi', resolution_ppi)
      width_mm = self.AttrFromShared('width_mm', width_mm)
      height_mm = self.AttrFromShared('height_mm', height_mm)

      idx = self.FiguresCount
      print "Adding %d. figure ..." % (idx+1)

      draw_figure_args = self.AttrsFromShared(idx, 'draw_figure_args', **draw_figure_args)
      layout_figure_args = self.AttrsFromShared(idx, 'layout_figure_args', **layout_figure_args)

      figure = fig.CFigure(resolution_ppi=resolution_ppi, width_mm=width_mm, height_mm=height_mm, idx=idx)
      figure.Set(draw_figure_class=self.draw_figure_class, draw_object_class=self.draw_object_class,
         layout_figure_class=self.layout_figure_class,
         draw_figure_args=draw_figure_args, layout_figure_args=layout_figure_args
      )
      self.addFigure(figure)
      return figure
########################################
   def LoadFiguresAttrs(self, src, **args):
      if self.loader == None:
         return False
      return self.loader.LoadFiguresAttrs(src, **args)
   
   def AddAllFigures(self):
      count = self.figuresAttrsCount - self.FiguresCount
      for idx in range(count):
         self.AddFigure()
########################################
   def DoFigures(self, rank_step=None, layout_step=None, force_draw=False):
      ret = False
      start = self.FiguresPos+1
      end = self.FiguresCount
      for fig in self.figures[start:end]:
         print "Processing %d. figure%s ..." % (fig.idx+1, "" if not fig.name else " '"+fig.name+"'")
         ret |= fig.Do(rank_step=rank_step, layout_step=layout_step, force_draw=force_draw)
      self.figures_pos = end-1
      return ret
   
   def LoadAndDoFigures(self, src, rank_step=None, layout_step=None, force_draw=False, **load_args):
      self.LoadFiguresAttrs(src, **load_args)
      self.AddAllFigures()
      return self.DoFigures(rank_step=rank_step, layout_step=layout_step, force_draw=force_draw)
################################################################################


################################################################################
################################################################################


if __name__ == "__main__":
   print "<<CFigCollection tests>>\n"

   x = CFigCollection(resolution_ppi=300, width_mm=100, height_mm=200)

   fig1 = x.AddFigure(width_mm=55, height_mm=80)
   fig2 = x.AddFigure(width_mm=20, height_mm=80)
   fig3 = x.AddFigure()
   fig3 = x.AddFigure(height_mm=100)

   fig1.DoLayout()
   fig1.layout.AddObjectToLayout(parent=fig1.front, key='test', height_mm=8, width_mm=12, yalign='center', xalign='right', xoffs_mm=1)

   x.DoAll()

   print "\n"+"-"*50+"\n"
   print "Pre-set figures attributes manually:"

   y = CFigCollection(resolution_ppi=300, width_mm=100, height_mm=100,
      layout_figure_args={'layout_front':{'front_draw_object_args': {
         'effect_text':{'text':"Shared", 'fg_color':"magenta"},
      }}},
   )

   y.AddFigure()
   y.AddFigureAttrs(layout_figure_args={'layout_front':{'front_draw_object_args': {
      'effect_text':{'text':"Local"},
   }}})
   y.AddFigure()
   y.AddFigure(layout_figure_args={'layout_front':{'front_draw_object_args': {
      'effect_text':{'text':"Args"},
   }}})

   y.AddFigureAttrs(layout_figure_args={'layout_front':{'front_draw_object_args': {
      'effect_text':{'text':"One", 'fg_color':"blue"},
   }}})
   y.AddFigureAttrs(layout_figure_args={'layout_front':{'front_draw_object_args': {
      'effect_text':{'text':"Two", 'bg_color':"yellow"},
   }}})
   y.AddFigure()
   y.AddFigure()

   y.DoAll()

   print "\n"+"-"*50+"\n"
   fn = 'data/test.csv'
   print "Load figures attributes with CSV loader from '%s':" % fn
   z = CFigCollection(resolution_ppi=300, width_mm=100, height_mm=100)
   z.SetLoader(CLoaderDSV, delim=',')
   z.LoadAndDoAll(fn)
   ## It should not do anything on second time
   z.LoadAndDoAll(fn)

   print
   for f in z.figures:
      print "Draw figure attributes:", f.draw.attrs
      print "Layout figure attributes:", f.layout.attrs
      print

   print "\n"+"-"*50+"\n"
   fn = 'data/test_dict.tsv'
   print "Load figures attributes with TSV loader from '%s' with dictionaries:" % fn
   w = CFigCollection(resolution_ppi=300, width_mm=100, height_mm=100)
   w.SetLoader(CLoaderDSV)
   w.LoadAndDoAll(fn, delim='\t')

   print
   for f in w.figures:
      print "Layout figure attributes:", f.layout.attrs
      print

   print "\n<</CFigCollection tests>>"
