#!/usr/bin/env python2

## Library that provides 'CFigObject's wrapper 'CFigure'
## to collect root figure object's and it's subobjects
## and define interface

from __future__ import division
from collections import defaultdict
from collections import OrderedDict

import copy as cp
import sys

import fig_object as fo

################################################################################
################################################################################

################################################################################
class CDrawFigureBase(fo.CCompositionBase):
   """
   Dummy draw figure class that defines interface
   between 'CFigure' and 'CDrawFigure..' objects.
   Its purpose is to set draw routines independently
   on figure layout - i.e. it should set
   concrete draw tool specific attributes
   and functions.
   It should not contain attributes that are
   under layout responsibility nor those
   which indeed relates to draw but it is certain
   that they should be used by all kinds of draw tool
   (i.e. fill color, pattern or image of background).
   """
########################################
   default_draw_object_class = fo.CDrawObjectBase
########################################
   ## Do not override contructor
   ## More attributes are possible to set through '**args',
   ## concrete attributes are set in 'SetAttrs',
   ## default values should be defined in class variable 'attr_defaults'
   def __init__(self, figure, draw_object_class, **args):
      fo.CCompositionBase.__init__(self, figure, **args)
      self.draw_object_class = draw_object_class
########################################
   def __copy__(self):
      return self.__class__(self.ptr, self.draw_object_class, **self.attrs)
########################################
   ## All default values off class' possible attributes should be defined
   ## Beware - 'CLayoutFigure...' defaults takes precedence over these !
   attr_defaults = fo.merge_dicts(fo.CCompositionBase.attrDefaults(),{
   })
########################################
   ## Override this - things that need to be set up before any drawing done
   def PreDrawFigure(self):
      pass

   ## Override this - things that need to be set up after all drawing done
   def PostDrawFigure(self):
      pass
################################################################################

################################################################################
class CDrawFigurePrint(CDrawFigureBase):
   """
   Draw figure class that uses terminal printing as draw
   """
########################################
   default_draw_object_class = fo.CDrawObjectPrint
########################################
   ## All default values off class' possible attributes should be defined
   ## Beware - 'CLayoutFigure...' defaults takes precedence over these !
   attr_defaults = fo.merge_dicts(CDrawFigureBase.attrDefaults(),{
   })
########################################
   def PreDrawFigure(self):
      print "\n"+"^"*40

   def PostDrawFigure(self):
      print "+"*40
################################################################################

################################################################################
################################################################################

################################################################################
class CLayout(fo.CCompositionBase):
   """
   Class of single layout that is or is not applied
   to figure layout
   -> it adds methods to create objects relating to layout
   and inserts the most common ones automatically.
   One can inherit layout classes in two ways:
     1) Inherit only superclass' default attributes and methods,
        but do not use superclass' 'Layout'. These classes are treated as 'additional'
        as their behaviour does not overlay with superclass.
        One may possibly have included sth. like 'Add' to class' identifier to notify this feature.
     2) As 1), but use superclass' 'Layout'. These classes should represent
        concrete end standalone layouts, that are mutually disjunct,
        thus one should use only one class 'chain',
        but additional layouts should be still used at no harm.
   In both cases, one may want to define an 'incomplete' class
   that is to be extended. These classes should have set 'flag' to 'False'
   to avoid multiple calls of 'Layout' from its subclasses
   and possibly have appended an '_' to its identifier to notify this feature.

   Each layout can contain multiple branches that will be executed in order
   according to rank among other layouts - lesser ranks are executed first
   in all layouts. This is necessary when there are any dependencies between figure objects,
   e.g. when one wants to deepcopy figure object,
   it has to be done after insertion of all subobjects into copied object.
   Also, whole layout can have rank, which defines order of layouts
   within an branch rank iteration. This is useful only in cases
   when for some reason multiple layouts has same rank of branch
   and one wants certain layouts to take precedence,
   typically root objects at branch rank 0.
   """
########################################
   ## All default values off class' possible attributes should be defined
   ## These defaults takes precedence over 'CDrawFigure...' defaults
   attr_defaults = fo.merge_dicts(fo.CCompositionBase.attrDefaults(),{
      'flag' : True,

      'width_mm' : 0,
      'height_mm' : 0,
      'xalign' : 'left',
      'yalign' : 'top',
      'xoffs_mm' : 0,
      'yoffs_mm' : 0,
      'xloc' : 'sameas',
      'yloc' : 'sameas',
      'add_xoffs_mm' : 0,
      'add_yoffs_mm' : 0,
      'parent' : None,
      'margin_mm' : 0,
      'opacity' : 100,
      'new_opacity' : None,
      'new_width_mm' : None,
      'new_height_mm' : None,
      'new_margin_mm' : None,
      'scale' : 1,
      'draw_object_args' : {},
   })

   ## Branch ranks used only within this class' 'Layout'
   local_ranks = [0]
   ## Disable inheritance if 'ranks_' as it will be merged in 'ranks()'
   ranks_ = None
########################################
   @classmethod
   def ranks(cls):
      if not cls.ranks_:
         superclass = cls.__bases__[0]
         cls.ranks_ = fo.merge_lists([] if not hasattr(superclass, 'ranks') else superclass.ranks(), cls.local_ranks)
         cls.local_ranks = None
      return cls.ranks_

   def Ranks(self):
      return self.__class__.ranks()
########################################
   @property
   def LayoutKey(self):
      id_ = self.__class__.__name__[len('CLayout'):]
      key = ''
      for c in id_:
         if c.islower():
            key += c
         else:
            key += "_"+c.lower()
      return key[1:] if key[-1] != "_" else key[1:-1]
########################################
   ## Insert figure object to layout,
   ## i.e. insert it into its parent
   ## that may not have been inserted yet,
   ## or into explicit parent
   def InsertObject(self, object_, parent=None):
      if parent == None:
         parent = object_.parent
      if parent != None:
         parent.InsertObject(object_)
########################################
   ## Returns newly created figure object,
   ## which is automatically added into layout
   ## and will be inserted in next 'DoLayout' call
   ## 'SetDrawObjectClass' should have beeen called before
   def AddObjectToLayout(self, key, width_mm=fo.DEFAULT, height_mm=fo.DEFAULT,
      parent=fo.DEFAULT,
      xalign=fo.DEFAULT, yalign=fo.DEFAULT, xoffs_mm=fo.DEFAULT, yoffs_mm=fo.DEFAULT,
      margin_mm=fo.DEFAULT, opacity=fo.DEFAULT,
      **draw_object_args
   ):
      self.SetFunctionAttrDefaults(key,2)
      parent = self.args.parent
      root_object = self._dummy_object if parent == None else parent.RootObject
      if parent == None:
         parent = root_object

      obj = fo.CFigObject(key, figure=self.ptr, resolution_ppi=self.Resolution_ppi, width_mm=self.args.width_mm, height_mm=self.args.height_mm,
         xalign=self.args.xalign, yalign=self.args.yalign, xoffs_mm=self.args.xoffs_mm, yoffs_mm=self.args.yoffs_mm,
         parent=parent,
         margin_mm=self.args.margin_mm,
         opacity=self.args.opacity,
         draw_class=self.draw.draw_object_class,
         **self.args.draw_object_args
      )

      self.InsertObject(obj)
      self.CleanFunctionAttrDefaults()
      return obj

   def AddRootObjectToLayout(self, key,
      margin_mm=fo.DEFAULT,
      opacity=fo.DEFAULT,
      **draw_object_args
   ):
      return self.AddObjectToLayout(key, width_mm=self.Width_mm, height_mm=self.Height_mm,
         margin_mm=margin_mm,
         opacity=opacity,
         **draw_object_args
      )

   def AddObjectCopyToLayout(self, object_, deepcopy=True, new_key=None, new_parent=None,
      xloc=fo.DEFAULT, yloc=fo.DEFAULT, add_xoffs_mm=fo.DEFAULT, add_yoffs_mm=fo.DEFAULT,
      new_opacity=fo.DEFAULT,
      new_width_mm=fo.DEFAULT, new_height_mm=fo.DEFAULT, new_margin_mm=fo.DEFAULT,
      scale=fo.DEFAULT,
      **draw_object_args
   ):
      obj = cp.copy(object_) if not deepcopy else cp.deepcopy(object_)
      obj.SetKey(new_key)
      if new_parent != None:
         obj.SetParent(new_parent)

      self.SetFunctionAttrDefaults(obj.key,2)
      obj.SetOpacity(self.args.new_opacity)
      
      obj.SetSize(scale=self.args.scale, width_mm=self.args.new_width_mm, height_mm=self.args.new_height_mm, margin_mm=self.args.new_margin_mm)
      obj.SetPosFromObject(object_, xloc=self.args.xloc, yloc=self.args.yloc, add_xoffs_mm=self.args.add_xoffs_mm, add_yoffs_mm=self.args.add_yoffs_mm)
      obj.SetDrawObjectAttrs(**self.args.draw_object_args)

      self.InsertObject(obj)
      self.CleanFunctionAttrDefaults()
      return obj

   def AddObjectGroupToLayout(self, key_prefix, parent,
      xalign=fo.DEFAULT, yalign=fo.DEFAULT, xoffs_mm=fo.DEFAULT, yoffs_mm=fo.DEFAULT,
      opacity=fo.DEFAULT,
      **draw_object_args
   ):
      if key_prefix[-1] == '_':
         key_prefix = key_prefix[:-1]
      key = key_prefix+'_group'
      obj = self.AddObjectToLayout(key,
         parent=parent,
         xalign=xalign, yalign=yalign,
         xoffs_mm=xoffs_mm, yoffs_mm=yoffs_mm,
         opacity=opacity,
         **draw_object_args
      )
      return obj

   ## One often wants to use 'None' in 'xloc' and 'yloc'
   ## (do not discard previous position by default)
   def addObjectToGroup(self, parent, object_,
      xloc=fo.DEFAULT, add_xoffs_mm=fo.DEFAULT,
      yloc=fo.DEFAULT, add_yoffs_mm=fo.DEFAULT,
   ):
      self.SetFunctionAttrDefaults(object_.key,3)
      object_.SetParent(parent)
      if parent.ObjectsCount > 1:
         object_.SetPosFromObject(parent.objects_ordered[-1],
            xloc=self.args.xloc, add_xoffs_mm=self.args.add_xoffs_mm,
            yloc=self.args.yloc, add_yoffs_mm=self.args.add_yoffs_mm,
         )
      self.InsertObject(object_)
      self.CleanFunctionAttrDefaults()
      return object_

   def AddObjectToGroup(self, key, parent,
      width_mm=fo.DEFAULT, height_mm=fo.DEFAULT,
      xalign=fo.DEFAULT, xoffs_mm=fo.DEFAULT,
      yalign=fo.DEFAULT, yoffs_mm=fo.DEFAULT,
      xloc=fo.DEFAULT, add_xoffs_mm=fo.DEFAULT,
      yloc=fo.DEFAULT, add_yoffs_mm=fo.DEFAULT,
      margin_mm=fo.DEFAULT,
      opacity=fo.DEFAULT,
      **draw_object_args
   ):
      obj = self.AddObjectToLayout(key=key,
         width_mm=width_mm, height_mm=height_mm,
         xalign=xalign, xoffs_mm=xoffs_mm,
         yalign=yalign, yoffs_mm=yoffs_mm,
         margin_mm=margin_mm,
         opacity=opacity,
         **draw_object_args
      )
      obj = self.addObjectToGroup(parent, obj,
         xloc=xloc, add_xoffs_mm=add_xoffs_mm,
         yloc=yloc, add_yoffs_mm=add_yoffs_mm,
      )
      return obj
########################################
   def ReturnRank(self, act_rank):
      for rank in self.Ranks():
         if act_rank < rank:
            return rank
      return None

   ## Each rank is called only once.
   ## Return next rank that is to be called,
   ## or current rank if there it no one.
   ## Override this to set and insert all common objects according to layout
   def Layout(self, rank=0):
      ##! It would be better to use 'cls.local_ranks' to remove redundancy.
      ##! But how to access it independently of the object?
      ##! (Object of some subclass knows only 'local_ranks' of its class,
      ##! not of its superclasses.)
      if rank == 0:
         pass
      return self.ReturnRank(rank)
########################################

########################################
class CLayoutFront(CLayout):
   """
   Layout that adds front root object
   """
########################################
   attr_defaults = fo.merge_dicts(CLayout.attrDefaults(),{
   })

   local_ranks = [0]
   ranks_ = None
########################################
   ## Creates very common root figure object
   def Layout(self, rank=0):
      if rank == 0:
         self.ptr.ptr.front = self.AddRootObjectToLayout('front')
      return self.ReturnRank(rank)
########################################
class CLayoutBack(CLayout):
   """
   Layout that adds back root object
   """
########################################
   attr_defaults = fo.merge_dicts(CLayout.attrDefaults(),{
   })

   local_ranks = [0]
   ranks_ = None
########################################
   ## Creates very common root figure object
   def Layout(self, rank=0):
      if rank == 0:
         self.ptr.ptr.back = self.AddRootObjectToLayout('back')
      return self.ReturnRank(rank)
################################################################################

################################################################################
class CLayoutFigureBase(fo.CCompositionBase):
   """
   Dummy figure layout class that defines interface
   between 'CFigure' and 'CLayoutFigure...' objects.
   It should contain attributes
   that are common for any used draw tool.
   """
########################################
   ## Do not override contructor
   ## More attributes are possible to set through '**args',
   ## concrete attributes are set in 'SetAttrs',
   ## default values should be defined in class variable 'attr_defaults'
   def __init__(self, figure, **args):
      self.ClearLayouts()
      fo.CCompositionBase.__init__(self, figure, **args)
########################################
   def __copy__(self):
      layout = self.__class__(self.ptr, **self.attrs)
########################################
   def __getattr__(self, attr_key):
      try:
         return fo.CCompositionBase.__getattr__(self, attr_key)
      except AttributeError:
         if hasattr(self.LastLayout, attr_key):
            return getattr(self.LastLayout, attr_key)
         raise
########################################
   def ClearLayouts(self):
      self.layouts = {}
      self.layouts_ordered = []
      self.layouts_pos = -1
      self.layouts_rank = 0
      self.layouts_next_rank = None
########################################
   def CreateLayout(self, layout_class, **layout_args):
      return layout_class(self, **layout_args)

   def AddLayoutByClass(self, layout_class, **layout_args):
      self.AddLayout(self.CreateLayout(layout_class, **layout_args))

   def AddLayout(self, layout):
      self.layouts[layout.LayoutKey] = layout
      self.layouts_ordered.append(layout)
########################################
   def AttrsFromLayouts(self):
      attrs = {}
      for layout_key in self.layouts:
         attrs['layout_'+layout_key] = self.layouts[layout_key].attrs
      return attrs

   def AttrsWithLayouts(self):
      return fo.merge_dicts(self.AttrsFromLayouts(), self.attrs)

   def AddLayoutsFromAttrs(self):
      self.attrs = self.AttrsWithLayouts()
      self.ClearLayouts()
      layouts = self.DictsFromAttrs('layout', sort_f=lambda l: 0 if not 'rank' in l[1] else l[1]['rank'])
      for l in layouts:
         key = l[0]
         attrs = l[1]
         if 'module' in attrs:
            module = __import__(attrs['module'])
         else:
            module = sys.modules[__name__]
         class_ = getattr(module, "CLayout"+fo.str_title(key))
         self.AddLayoutByClass(class_, **attrs)
########################################
   ## Do not override this
   def SetAttrs(self, attrs=None):
      fo.CCompositionBase.SetAttrs(self, attrs)
      self.AddLayoutsFromAttrs()
########################################
   ## All default values off class' possible attributes should be defined
   ## These defaults takes precedence over 'CDrawFigure...' defaults
   attr_defaults = fo.merge_dicts(fo.CCompositionBase.attrDefaults(),{
      'layout_front' : {'rank':1},
      'layout_back' : {'rank':2},
   })
########################################
   @property
   def LayoutsPos(self):
      return self.layouts_pos
      
   @property
   def LayoutsCount(self):
      return len(self.layouts_ordered)

   @property
   def LastLayout(self):
      return self.layouts_ordered[self.LayoutsPos]

   ## Executes range of layouts,
   ## if there are any left,
   ## which inserts figure objects.
   ## It is designed to be called multiple times
   ## and to step either by layout or whole rank.
   ## Do not override this.
   ## By default, process all layouts and ranks
   ## (when step is 'None').
   ## Returns whether any layout was processed.
   def LayoutFigure(self, rank_step=None, layout_step=None):
      start = self.LayoutsPos+1
      end = self.LayoutsCount if layout_step == None else min(start+layout_step, self.LayoutsCount)
      layouts = self.layouts_ordered[start:end]

      if not layouts or (rank_step != None and rank_step <= 0):
         return False
      
      flag = False
      for layout in layouts:
         if layout.flag:
            flag = True
            next_rank = layout.Layout(self.layouts_rank)
            if (next_rank != None
               and next_rank > self.layouts_rank
               and (self.layouts_next_rank == None or next_rank < self.layouts_next_rank)
            ):
               self.layouts_next_rank = next_rank
      self.layouts_pos = end-1

      if (self.LayoutsPos == self.LayoutsCount-1
         and self.layouts_next_rank != None and self.layouts_next_rank > self.layouts_rank
      ):
         ## All layouts processed, but not all ranks -> next cycle
         self.layouts_rank = self.layouts_next_rank
         self.layouts_next_rank = None
         self.layouts_pos = -1
         if rank_step != None:
            rank_step -= 1
            if rank_step <= 0:
               ## Given step of ranks exceeded
               return flag
         flag |= self.LayoutFigure(rank_step, layout_step)
      return flag
################################################################################

################################################################################
################################################################################

################################################################################
class CFigure(object):
   """
   Class that gathers several root figure objects
   and provides configurable draw tool and layouts above them
   """
########################################
   def __init__(self, resolution_ppi, width_mm, height_mm, name="", idx=None):
      self._dummy_object = fo.CFigObject('dummy', resolution_ppi=resolution_ppi, width_mm=width_mm, height_mm=height_mm)
      self._dummy_object.depth = -1

      self.root_objects = self._dummy_object.objects_ordered

      self.draw = None
      self.layout = None

      self.draw_flag = False

      self.name = name
      self.idx = idx
########################################
   ## Do not use copy
   def __copy__(self):
      return None
   def __deepcopy__(self, memo):
      return None
########################################
   def __str__(self):
      ret = str(self.root_objects[0])
      for obj in self.root_objects[1:]:
         ret += " | " + str(obj)
      return ret
########################################
   def GetRootObjectByKeyBase(self, key_base, idx=0):
      return self._dummy_object.GetObjectByKeyBase(key_base, idx)

   def GetRootObjectByIdx(self, idx):
      return self.root_objects[idx]

   @property
   def RootObjectsCount(self):
      return self._dummy_object.ObjectsCount

   def GetFirstObjectByKeyBase(self, key_base, idx=0, parent=None):
      if parent == None:
         parent = self._dummy_object
      obj = parent.GetObjectByKeyBase(key_base, idx)
      if obj != None:
         return obj
      for obj in parent.objects_ordered:
         ret = self.GetFirstObjectByKeyBase(key_base, idx, obj)
         if ret != None:
            return ret
      return None
########################################
   @property
   def Width_mm(self):
      return self._dummy_object.Width_mm

   @property
   def Height_mm(self):
      return self._dummy_object.Height_mm

   @property
   def Width_px(self):
      return self._dummy_object.Width_px

   @property
   def Height_px(self):
      return self._dummy_object.Height_px

   @property
   def Resolution_ppi(self):
      return self._dummy_object.Resolution_ppi
########################################
   @property
   def IdxNamePrefix(self):
      fig_idx_str = "" if self.idx == None else "%03d-" % (self.idx+1)
      fig_name_str = "" if not self.name else self.name+"_"
      return fig_idx_str+fig_name_str
########################################
   ## Should be called before creating any objects
   ## All attributes must be contained
   def SetDrawFigure(self, draw_figure_class=None, draw_object_class=None, **draw_figure_args):
      if draw_figure_class == None:
         draw_figure_class = CDrawFigurePrint
      if draw_object_class == None:
         draw_object_class = draw_figure_class.default_draw_object_class
      self.draw = draw_figure_class(self, draw_object_class, **draw_figure_args)

   ## 'SetDrawFigure' should be called before
   ## All attributes must be contained
   def SetLayoutFigure(self, layout_figure_class=None, **layout_figure_args):
      if layout_figure_class == None:
         layout_figure_class = CLayoutFigureBase
      self.layout = layout_figure_class(self, **layout_figure_args)

   ## Set everything with all attributes,
   ## but one often wants to do these steps separately
   def Set(self,
      draw_figure_class=None, draw_object_class=None, draw_figure_args={},
      layout_figure_class=None, layout_figure_args={}
   ):
      self.SetDrawFigure(draw_figure_class, draw_object_class, **draw_figure_args)
      self.SetLayoutFigure(layout_figure_class, **layout_figure_args)
########################################
   ## By default, process all layouts
   ## (when steps are 'None').
   def DoLayout(self, rank_step=None, layout_step=None):
      if self.layout == None:
         return None
      ret = self.layout.LayoutFigure(rank_step, layout_step)
      self.draw_flag |= ret
      return ret

   ## Whole object and all its subobjects must be properly set at this moment!
   ## 'SetDrawFigure', 'SetLayout' must have been called before
   def DoDraw(self, force_draw=False):
      if self.draw == None or (not force_draw and not self.draw_flag):
         return
      
      self.draw.PreDrawFigure()
      for obj in self.root_objects:
         obj.Draw()
      self.draw.PostDrawFigure()

      self.draw_flag = False

   ## 'Set' should have been called before.
   ## Draw only when any layout was processed,
   ## or if said explicitly.
   ## Returns whether any layout was processed.
   def Do(self, rank_step=None, layout_step=None, force_draw=False):
      ret = self.DoLayout(rank_step, layout_step)
      self.DoDraw(force_draw)
      return ret
########################################
   ## Set and do everything with all attributes,
   ## but one often wants to do these steps separately
   def SetAndDo(self,
      draw_figure_class=None, draw_object_class=None, draw_figure_args={},
      layout_figure_class=None, layout_figure_args={},
      rank_step=None, layout_step=None
   ):
      self.Set(draw_figure_class, draw_object_class, draw_figure_args,
         layout_figure_class, layout_figure_args
      )
      return self.Do(rank_step, layout_step)
################################################################################


################################################################################
################################################################################

if __name__ == "__main__":
   print "<<CFigure tests>>\n"

   x = CFigure(300, height_mm=80, width_mm=58)
   y = CFigure(300, height_mm=80, width_mm=58)
   x.Set(draw_object_class=fo.CDrawObjectBase)
   y.Set()

   print "CDrawObjectBase:"
   x.Do()
   print

   print "CDrawObjectPrint:"
   y.Do()
   print

   print "Add object:"
   obj1 = y.layout.AddObjectToLayout(parent=y.front, key='test', height_mm=8, width_mm=12, yalign='center', xalign='right', xoffs_mm=1)
   y.Do(force_draw=True)
   print

   print "Add object deep copy:"
   y.layout.AddObjectCopyToLayout(obj1)
   y.Do(force_draw=True)
   print

   print "Add root object deep copy:"
   y.layout.AddObjectCopyToLayout(y.front)
   y.Do(force_draw=True)
   print

   print "Add object deep copy:"
   y.layout.AddObjectCopyToLayout(obj1)
   y.Do(force_draw=True)
   print

   print "Figure without front:"
   z = CFigure(500, height_mm=100, width_mm=50)
   z.Set(layout_figure_args={'layout_front':None})
   z.Do()
   print

   print "Figure with forced front before back:"
   w = CFigure(500, height_mm=100, width_mm=50)
   w.Set(layout_figure_args={'layout_front':{'rank':0}})
   w.Do()
   print

   print "-"*50
   print "\n*Group tests*\n"
   f1 = CFigure(300, height_mm=100, width_mm=100)
   f1.SetAndDo(layout_figure_args={'layout_back' : {'flag':False}})
   print

   group = f1.layout.AddObjectGroupToLayout('test', f1.front)
   f1.Do(force_draw=True)
   print

   f1.layout.AddObjectToGroup('obj', group, width_mm=10, height_mm=20, xoffs_mm=10, xloc='rightof')
   f1.Do(force_draw=True)

   f1.layout.AddObjectToGroup('obj', group, width_mm=20, height_mm=30, xloc='rightof')
   f1.Do(force_draw=True)

   f1.layout.AddObjectToGroup('obj', group, width_mm=10, height_mm=30, yoffs_mm=10, yloc=None, xloc='rightof', add_xoffs_mm=10)
   f1.Do(force_draw=True)

   print "\n<</CFigure tests>>"

################################################################################
################################################################################