#!/usr/bin/env python2

## Library that provides classes
## to handle rectangular hierarchy of figure objects

from __future__ import division
from collections import defaultdict
from operator import add, getitem
from functools import reduce  ## forward compatibility for Python 3

import copy as cp
import inspect
import sys
import logging as log

log.basicConfig(stream=sys.stdout, level=log.WARNING)

################################################################################
################################################################################

DEFAULT = object()

class CDummy:
   pass

f_None = lambda *args,**kwargs:None
f_True = lambda *args,**kwargs:True

def is_dict(d):
   return isinstance(d, dict)

def is_tuple(t):
   return isinstance(t, tuple)

def is_str(str_):
   return isinstance(str_, str)

def is_int(int_):
   return isinstance(int_, int)

def str_is_int(str_):
   try: 
      v = int(str_)
      return is_int(v)
   except ValueError:
      return False

def str_title(str_, isep="_", osep=""):
   ret = ""
   split_ = str_.split(isep)
   for part in split_:
      ret += part.title()+osep
   if str_ and str_[-1] == isep:
      ret += isep
   return ret if osep == "" else ret[:-len(osep)]

################################################################################
################################################################################

## 'dict2' takes precedence
## Inputs don't have to be dictionaries,
## but can be also single values
def merge_2dicts_rec(dict1, dict2):
   if not (is_dict(dict1) and is_dict(dict2)):
      return dict2

   d = dict1.copy()
   for key in dict2:
      if key not in d:
         d[key] = dict2[key]
      else:
         d[key] = merge_2dicts_rec(d[key], dict2[key])
   return d

## The last of 'dicts' takes the highest precedence
## Inputs don't have to be dictionaries
## but can be also single values
def merge_dicts(*dicts):
   log.debug("MERGE inputs:")
   for d in dicts:
      log.debug(str(d))
   d0 = dicts[0]
   for d in dicts[1:]:
      d0 = merge_2dicts_rec(d0,d)
   log.debug("MERGE output: "+str(d0))
   return d0

def merge_lists(*lists):
   s = set()
   for l in lists:
      s |= set(l)
   return sorted(s)

def dict_get_nested(dict_, keys):
   return reduce(getitem, keys, dict_) if hasattr(keys, '__iter__') else dict_[keys]

def dict_set_nested(dict_, keys, value):
   dict_get_nested(dict_, keys[:-1])[keys[-1]] = value
   return dict_

################################################################################
################################################################################

################################################################################

class CCompositionBase(object):
   """
   Dummy base class that defines basic routines
   of composition objects
   """
########################################
   def __init__(self, ptr, **args):
      self.SetPtr(ptr)        #<- Pointer to composed object
      self.attrs = {}         #<- Contains all optional attributes
      self.args = None        #<- See 'SetFunctionAttrDefaults'
      self.args_stack = []    #<- Backups previous arguments
      self.SetAttrs(args)
########################################
   def __getattr__(self, attr_key):
      return getattr(self.ptr, attr_key)
########################################
   def __copy__(self):
      return self.__class__(self.ptr, **self.attrs)

   def __deepcopy__(self):
      return self.__copy__()
########################################
   def SetPtr(self, ptr):
      self.ptr = ptr
########################################
   ## All default values off class' possible attributes should be defined
   attr_defaults = {}
   
   @classmethod
   def attrDefaults(cls):
      return cls.attr_defaults

   @classmethod
   def getAttrDefault(cls, attr_key):
      return cls.attrDefaults()[attr_key]

   def AttrDefaults(self):
      return self.__class__.attrDefaults()

   def GetAttrDefault(self, attr_key):
      return self.__class__.getAttrDefault(attr_key)

   def GetAttr(self, attr_key):
      if attr_key not in self.AttrDefaults():
         return None
      else:
         return self.GetAttrDefault(attr_key) if attr_key not in self.attrs else self.attrs[attr_key]

   ## Override this only to set attributes from '**self.attrs' differently
   def SetAttrs(self, attrs=None, out_attrs_key='attrs'):
      if attrs == None:
         attrs = self.attrs
      ## Implicit set of attributes according to default values:
      for attr_key in self.AttrDefaults().keys():
         if attr_key not in attrs:
            attrs[attr_key] = self.GetAttrDefault(attr_key)
         else:
            attrs[attr_key] = merge_dicts(self.GetAttrDefault(attr_key), attrs[attr_key])
      for attr_key in attrs.keys():
         if is_str(attr_key):
            setattr(self, attr_key, attrs[attr_key])
      setattr(self, out_attrs_key, merge_dicts(getattr(self, out_attrs_key), attrs))

   ## In method definition in child classes,
   ## use this routine to set all method arguments
   ## with value of 'DEFAULT' object
   ## to its correspoding default value of object
   ## -> nearly like from 'GetAttrDefault',
   ## but also altered by input arguments when constructing objects.
   ## (It's keyword is prefixed by 'attr_default_prefix_str'+"_").
   ## However, one have to access these updated arguments
   ## through 'args' object, not directly.
   ## '**keywords' are merged with object (not class) defaults implicitly ('merge_keywords'),
   ## whereas '**keywords' takes precedence over defaults.
   def SetFunctionAttrDefaults(self, attr_default_prefix="", args_offset=1, merge_keywords=True):
      def _prefix():
         return "" if attr_default_prefix == "" else attr_default_prefix+"_"

      argvalues = inspect.getargvalues(sys._getframe(1))
      ## We want to iterate only through function arguments
      ## starting from 'args_offset' (ommit first arguments)
      args_ = argvalues.args[args_offset:]
      ## .. but locals contain their values
      locals_ = argvalues.locals
      
      ## Initialize arguments
      self.args_stack.append(self.args)
      self.args = CDummy()
      for arg_key in args_:
         default_arg_key = _prefix()+arg_key
         setattr(self.args, arg_key, (
            locals_[arg_key] if locals_[arg_key] != DEFAULT
            else getattr(self, default_arg_key) if hasattr(self, default_arg_key)
            else getattr(self, arg_key) if hasattr(self, arg_key)
            else None
         ))
      keywords_ = argvalues.keywords
      if merge_keywords and keywords_ != None:
         default_keywords = _prefix()+keywords_
         setattr(self.args, keywords_, merge_dicts((
               getattr(self, default_keywords) if hasattr(self, default_keywords)
               else getattr(self, keywords_) if hasattr(self, keywords_)
               else {}
            ), locals_[keywords_]
         ))
      ## You better call 'CleanFunctionAttrDefaults' after use of 'self.args'

   ## Call this at the end of each function where you call 'SetFunctionAttrDefaults'
   def CleanFunctionAttrDefaults(self):
      self.args = self.args_stack.pop()
########################################
   ## Filter certain items from 'attrs'
   ## and sort them.
   ## Each item filtered by key is removed from 'attrs'
   ## and only items filtered by value are inserted into result.
   ## Because dictionaries are unordered,
   ## and since it can depend on the order
   ## of items' application,
   ## it can be necessary to be the order defined somehow:
   ## rank system can be used,
   ## i.e. the less is the item's rank,
   ## the higher priority it has.
   def ItemsFromAttrs(self, select_key_f, sort_f=f_None, select_value_f=f_True):
      attrs = self.attrs
      attrs_copy = attrs.copy()
      items = []
      for attr_key in attrs_copy:
         if select_key_f(attr_key):
            attr = attrs[attr_key]
            if select_value_f(attr):
               items.append((attr_key,attr))
            del attrs[attr_key]
      items.sort(key=sort_f)
      return items

   ## To disable items that are set by default,
   ## do not assign dict to them (i.e. 'None').
   def DictsFromAttrs(self, item_key, sort_f=f_None):
      f_split = lambda key: key.split("_",1)
      items = self.ItemsFromAttrs(select_key_f=lambda key: f_split(key)[0] == item_key, select_value_f=lambda val: is_dict(val))
      for idx in range(len(items)):
         items[idx] = ( f_split(items[idx][0])[1], items[idx][1] )
      items.sort(key=sort_f)
      return items
################################################################################

################################################################################
class CDrawEffect(object):
   """
   Class with user defined function and its arguments.
   """
########################################
   def __init__(self, draw, effect_key, type_='', **args):
      self.draw = draw
      self.key = effect_key
      self.SetType(type_)
      self.attrs = {}
      self.SetAttrs(**args)
########################################
   def SetType(self, type_=''):
      self.type = type_

   def SetAttrs(self, **args):
      if 'type' in args:
         self.SetType(args['type'])
         del args['type']

      self.attrs = merge_dicts(self.attrs, args)
########################################
   ## 'f_key' is an 'DrawObject...' method
   ## Pass dummy keywords in method's parameters
   ## as this object can contain additional attributes
   ## due to merge from arguments (see 'SeeAttrs' in 'CCompositionBase')
   ## with different effect type
   def Apply(self):
      f_key = 'Effect'+str_title(self.key)+str_title(self.type)
      if hasattr(self.draw, f_key):
         getattr(self.draw, f_key)(**self.attrs)
################################################################################

################################################################################
class CDrawObjectBase(CCompositionBase):
   """
   Dummy draw object base class that defines interface
   between 'CFigObject' and 'CDrawObject..' objects
   """
########################################
   ## Do not override contructor
   ## More attributes are possible to set through '**args',
   ## concrete attributes are set in 'SetAttrs',
   ## default values should be defined in class variable 'attr_defaults'
   def __init__(self, object_, **args):
      self.shared_draw_attrs_create = False
      self.local_draw_attrs_create = False
      self.shared_draw_attrs = {}
      self.local_draw_attrs = {}
      self.ClearEffects()
      CCompositionBase.__init__(self, object_, **args)
########################################
   def ClearEffects(self):
      self.effects = {}
      self.effects_ordered = []

   def ClearEffect(self, effect_key):
      if effect_key not in self.effects:
         return
      del self.effects[effect_key]
      for idx in range(len(self.effects_ordered)):
         if self.effects_ordered[idx].key == effect_key:
            del self.effects_ordered[idx]
            break
########################################
   def AttrsFromEffects(self):
      attrs = {}
      for effect_key in self.effects.keys():
         effect = self.effects[effect_key]
         attrs['effect_'+effect_key] = merge_dicts({'type':effect.type}, effect.attrs)
      return attrs

   def AttrsWithEffects(self):
      return merge_dicts(self.AttrsFromEffects(), self.attrs)

   def DrawAttrs(self):
      return merge_dicts(self.shared_draw_attrs, self.local_draw_attrs)

   def AllAttrs(self):
      return merge_dicts(self.AttrsWithEffects(), self.DrawAttrs())

   def AddEffectsFromAttrs(self):
      self.attrs = self.AttrsWithEffects()
      self.ClearEffects()
      effects = self.DictsFromAttrs('effect', sort_f=lambda eff: self.GetEffectRank(eff[0]))
      for effect in effects:
         self.AddEffect(effect[0], **effect[1])
########################################
   def AddEffectFromDrawObject(self, draw, effect_key, **args):
      draw_attrs = draw.AttrsFromEffects()
      effect_key = 'effect_'+effect_key
      if effect_key not in draw_attrs:
         return
      self.attrs[effect_key] = merge_dicts(draw_attrs[effect_key], args)
      self.AddEffectsFromAttrs()

   def AddEffectsFromDrawObject(self, draw, **args):
      self.attrs = merge_dicts(self.attrs, draw.AttrsFromEffects(), args)
      self.AddEffectsFromAttrs()

   ## Do not use copy
   def __copy__(self):
      return None
   def __deepcopy__(self, memo):
      return None
########################################
   ## Do not override this
   def SetAttrs(self, attrs=None):
      CCompositionBase.SetAttrs(self, self.sharedDrawObjectAttrs(), 'shared_draw_attrs')
      CCompositionBase.SetAttrs(self, self.localDrawObjectAttrs(), 'local_draw_attrs')
      CCompositionBase.SetAttrs(self, attrs)
      self.AddEffectsFromAttrs()

   ## Do not override this
   def sharedDrawObjectAttrs(self):
      if self.IsRoot:
         self.createSharedDrawObjectAttrs()
      else:
         self.linkSharedDrawObjectAttrs()
      return self.shared_draw_attrs

   ## Do not override this
   def createSharedDrawObjectAttrs(self):
      if self.shared_draw_attrs_create:
         return
      self.shared_draw_attrs_create = True
      self.shared_draw_attrs = self.CreateSharedDrawObjectAttrs()
      ## Invalidate local attributes
      self.cleanLocalDrawObjectAttrs()
      log.info("create shared: " + str(self.ptr) + " " + str(self.shared_draw_attrs))
   
   ## Do not override this
   def cleanSharedDrawObjectAttrs(self, force=False):
      if not force and not self.shared_draw_attrs_create:
         return
      log.info("clean shared: " + str(self.ptr) + " " + str(self.shared_draw_attrs))
      self.CleanSharedDrawObjectAttrs()
      self.shared_draw_attrs_create = False

   ## Override this
   def CreateSharedDrawObjectAttrs(self):
      return {}

   ## Override this
   def CleanSharedDrawObjectAttrs(self):
      pass

   ## No need to override this
   def linkSharedDrawObjectAttrs(self):
      if self.shared_draw_attrs == self.RootObject.draw.shared_draw_attrs:
         return
      self.cleanSharedDrawObjectAttrs()
      self.shared_draw_attrs_create = True
      self.shared_draw_attrs = self.RootObject.draw.shared_draw_attrs
      ## Invalidate local attributes
      self.cleanLocalDrawObjectAttrs()
      log.info("link shared: " + str(self.ptr) + " " + str(self.shared_draw_attrs))

   ## Do not override this
   def localDrawObjectAttrs(self):
      self.createLocalDrawObjectAttrs()
      return self.local_draw_attrs

   ## Do not override this
   def createLocalDrawObjectAttrs(self):
      if self.local_draw_attrs_create:
         return
      self.local_draw_attrs_create = True
      self.local_draw_attrs = self.CreateLocalDrawObjectAttrs()
      log.info("create local: " + str(self.ptr) + " " + str(self.local_draw_attrs))

   ## Do not override this
   def cleanLocalDrawObjectAttrs(self, force=False):
      if not force and not self.local_draw_attrs_create:
         return
      log.info("clean local: " + str(self.ptr) + " " + str(self.local_draw_attrs))
      self.CleanLocalDrawObjectAttrs()
      self.local_draw_attrs_create = False

   ## Override this
   def CreateLocalDrawObjectAttrs(self):
      return {}
   ## Override this
   def CleanLocalDrawObjectAttrs(self):
      pass
########################################
   ## All default values off class' possible attributes should be defined
   attr_defaults = merge_dicts(CCompositionBase.attrDefaults(),{
   })

   ## It is not possible to have more effects with the same key !
   effects_attr_defaults = {
      'fill': {
         'color': {'color':"white"},
         'pattern': {},
         'picture': {'path':"/home/tomaqa/Data/Pics/Hry/Mysteria/v1.10/Karty/invalid.png"},
         'gradient': {},
      },
      'border': {
         'color': {'color':"black"},
         'pattern': {},
      },
      'text': {
         '': {'text':"Default text", 'size_pt':None, 'fg_color':"black", 'bg_color':"white"},
      },
      'rotate':  {
         '': {'angle':0},
      },
      'shear':  {
         '': {'mag_x':0, 'mag_y':0},
      },
      'mask': {
         '': {},
      },
   }

   effects_ranks = {
      'fill': 1,
      'border': 3,
      'text': 5,
      'rotate': 7,
      'shear': 7,
      'mask': 9,
   }

   @classmethod
   def effectsAttrDefaults(cls):
      return cls.effects_attr_defaults

   @classmethod
   def getEffectAttrDefaults(cls, effect_key):
      return cls.effectsAttrDefaults()[effect_key]

   @classmethod
   def getEffectTypeAttrDefaults(cls, effect_key, effect_type):
      return cls.getEffectAttrDefaults(effect_key)[effect_type]

   def EffectsAttrDefaults(self):
      return self.__class__.effectsAttrDefaults()

   def GetEffectAttrDefaults(self, effect_key):
      return self.__class__.getEffectAttrDefaults(effect_key)

   def GetEffectTypeAttrDefaults(self, effect_key, effect_type):
      return self.__class__.getEffectTypeAttrDefaults(effect_key, effect_type)

   @classmethod
   def effectsRanks(cls):
      return cls.effects_ranks

   @classmethod
   def getEffectRank(cls, effect_key):
      return cls.effectsRanks()[effect_key]

   def EffectsRanks(self):
      return self.__class__.effectsRanks()

   def GetEffectRank(self, effect_key):
      return self.__class__.getEffectRank(effect_key)
########################################
   ## Updates only effects that already exists in object
   ## from 'effects_attr_defaults' by effect key and type
   def SetEffectsAttrDefaults(self):
      for effect_key in self.effects.keys():
         effect = self.effects[effect_key]
         if effect_key in self.EffectsAttrDefaults() and effect.type in self.GetEffectAttrDefaults(effect_key):
            mdicts = merge_dicts(self.GetEffectTypeAttrDefaults(effect_key, effect.type), effect.attrs)
            effect.SetAttrs(**mdicts)
########################################
   ## Override this - things that need to be set up right bedore each root object draw (e.g. image creation)
   def PreDrawRootObject(self):
      pass
   
   ## Override this - things that need to be set up right bedore each object draw (e.g. layer creation)
   def PreDrawObject(self):
      pass

   ## There should not be need to override this
   def DrawObject(self):
      for effect in self.effects_ordered:
         effect.Apply()
   
   ## Override this - things that need to be set up right after each object draw
   def PostDrawObject(self):
      pass

   ## Override this - things that need to be set up right after each root object draw (e.g. image save)
   def PostDrawRootObject(self):
      pass
########################################
   def AddEffect(self, effect_key, type_='', **args):
      if effect_key in self.effects:
         self.ClearEffect(effect_key)
      effect = CDrawEffect(self, effect_key, type_, **args)
      self.effects_ordered.append(effect)
      self.effects[effect_key] = effect
      self.SetEffectsAttrDefaults()

   def SetEffectAttrs(self, effect_key, **args):
      self.effects[effect_key].SetAttrs(**args)
########################################
   def SetFontSizeFromObject(self):
      if 'text' in self.effects:
         size_pt = self.mm_to_pt(self.CanvasSize_mm[1])
         self.effects['text'].attrs['size_pt'] = size_pt
         return size_pt

   def ScaleEffectAttr(self, effect_key, attr_key, scale=1):
      if effect_key in self.effects and attr_key in self.effects[effect_key].attrs and self.effects[effect_key].attrs[attr_key]:
         self.effects[effect_key].attrs[attr_key] *= scale

   ## It can be necessary to scale whole object
   ## during its creation,
   ## so scaling is solved apart from effects
   ## Extend this
   def ScaleDraw(self, scale=1):
      if scale == 1:
         return
      self.ScaleEffectAttr('text', 'size_pt', scale)
      self.ScaleEffectAttr('shear', 'mag_x', scale)
      self.ScaleEffectAttr('shear', 'mag_y', scale)
########################################
########################################
   ## Simple terminal text effect
   def EffectText(self, text, bold=True, fg_color="black", bg_color="white", underline=False, blink=False, **dummy):
      ENDC = "\033[0m"
      BOLD = "\033[1m"
      UNDERLINE = "\033[4m"
      BLINK = "\033[5m"

      fg_color_code = "\033[3"+str((defaultdict(lambda:0,{
         "black": 0,
         "red": 1,
         "green": 2,
         "yellow": 3,
         "blue": 4,
         "magenta": 5,
         "cyan": 6,
         "white": 7,
      })[fg_color]))+"m"
      bg_color_code = "\033[4"+str((defaultdict(lambda:0,{
         "black": 0,
         "red": 1,
         "green": 2,
         "yellow": 3,
         "blue": 4,
         "magenta": 5,
         "cyan": 6,
         "white": 7,
      })[bg_color]))+"m"

      header = fg_color_code+bg_color_code
      if bold:
         header += BOLD
      if underline:
         header += UNDERLINE
      if blink:
         header += BLINK

      print header+text+ENDC
################################################################################

################################################################################
class CDrawObjectPrint(CDrawObjectBase):
   """
   Draw object class that only prints object and its contents
   """
########################################
   def PreDrawRootObject(self):
      print "['%s' root figure object's draw]" % self.key

   def PreDrawObject(self):
      print self.depth*"  "+"<%s>" % (self.ptr)
################################################################################

################################################################################
################################################################################

################################################################################
class CFigObject(object):
   """
   Class of separate components of drawable.
   Offset start depends on alignment,
   but value is always counted from top/left!
   I.e., one usually want to use negative offset
   for bottom/right y/x offset alignment.
   """
########################################
   ## '0' height/width means that object's size may be calculated
   ## from its subobjects -> it acts as dynamic group of objects
   ##! Groups does not update their offsets if its subobjects left bound
   ##! is more on left. Also, evaluation of width with right-aligned objects
   ##! that are more on right is incorrect. (Same for y axis).
   def __init__(self, key='object', resolution_ppi=300,
      width_mm=0, height_mm=0,
      xalign='left', yalign='top', xoffs_mm=0, yoffs_mm=0,
      parent=None,
      margin_mm=0, opacity=100,
      figure=None,
      draw_class=CDrawObjectPrint,
      **draw_args
   ):
      self.key = key
      self.figure = figure

      self.resolution_ppi = resolution_ppi
      self.size_mm = [0,0]
      self.SetSize(width_mm=width_mm, height_mm=height_mm, margin_mm=margin_mm)

      self.offs_mm = [xoffs_mm, yoffs_mm]
      self.align = [0,0]
      self.SetAlign(xalign, 0)
      self.SetAlign(yalign, 1)

      self.objects = {}
      self.objects_ordered = []
      self.objects_cnt = 0

      self.draw = None

      self.InitParent()
      self.SetParent(parent)
      self.SetOpacity(opacity)

      ## Draw is not being checked whether it is 'None' !
      if draw_class != None:
         self.SetDrawByClass(draw_class, **draw_args)
########################################
   def __copy__(self):
      obj = self.__class__(
         ## Key will be possibly incremented when inserting into parent object
         key               = self.ObjectKeyBase,
         resolution_ppi    = self.Resolution_ppi,
         width_mm          = self.Width_mm,
         height_mm         = self.Height_mm,
         margin_mm         = self.Margin_mm,
         xoffs_mm          = self.offs_mm[0],
         yoffs_mm          = self.offs_mm[1],
         xalign            = self.align[0],
         yalign            = self.align[1],
         opacity           = self.Opacity,
         parent            = self.parent,
         figure            = self.figure,
         draw_class        = None,
      )
      obj.SetDrawFromObject(self)
      return obj
   
   def __deepcopy__(self, memo):
      obj = self.__copy__()
      for subobj in self.objects_ordered:
         obj.InsertObject(cp.deepcopy(subobj))
      return obj
########################################
   def __str__(self):
      return "%s%s: %.1fx%.1f%+.1f%+.1f" % ("" if self.idx == None else "["+str(self.idx)+"] ", self.key, self.Width_mm, self.Height_mm, self.AbsBegin_mm[0], self.AbsBegin_mm[1])
########################################
   def SetKey(self, key):
      if key != None:
         self.key = key

   ## 'None' values means not to modify this attribute
   ## Scale only before or after setting sizes.
   def SetSize(self, width_mm=None, height_mm=None, margin_mm=None, scale=1, scale_pre=True):
      if scale_pre:
         self.ScaleObject(scale)
      if width_mm == None:
         width_mm = self.size_mm[0]
      if height_mm == None:
         height_mm = self.size_mm[1]
      self.size_mm = [width_mm, height_mm]
      if margin_mm != None:
         self.margin_mm = margin_mm
      if not scale_pre:
         self.ScaleObject(scale)

   def SetSizeFromObject(self, object_, set_margin=True, scale=1):
      self.SetSize(width_mm=object_.Width_mm, height_mm=object_.Height_mm,
         margin_mm=None if not set_margin else object_.margin_mm,
         scale=scale, scale_pre=False,
      )

   def SetSizeFromFontSize(self):
      if 'text' in self.effects and 'size_pt' in self.effects['text'].attrs:
         height_pt = self.effects['text'].attrs['size_pt']
         self.SetSize(width_mm=self.pt_to_mm(height_pt/1.5 + 0.5),
            height_mm=self.pt_to_mm(height_pt)
         )

   ## 'yloc' and 'xloc' are meant relative to 'object_' or absolute according to their value
   ## - values that correspond with 'self.align' possible values are absolute
   ## - 'None' value means to keep previous align
   def SetPosFromObject(self, object_, xloc='sameas', yloc='sameas', add_xoffs_mm=0, add_yoffs_mm=0):
      rel_locs = [['sameas','leftof','rightof','centerof'],['sameas','above','below','centerof']]
      loc = [xloc, yloc]
      add_offs_mm = [add_xoffs_mm, add_yoffs_mm]

      for idx in range(2):
         l = loc[idx]
         if l == 'mirror':
            self.SetOppositeAlign(object_.align[idx], idx)
            object_offs_mult = -1
         elif l in rel_locs[idx]:
            self.SetAlign(object_.align[idx], idx)
            object_offs_mult = 1
         else:
            self.SetAlign(l, idx)
            object_offs_mult = 0

         self.offs_mm[idx] = object_offs_mult*object_.offs_mm[idx]+add_offs_mm[idx] + (defaultdict(lambda:0,{
               None: self.offs_mm[idx],
               rel_locs[idx][1] : -self.Size_mm[idx],
               rel_locs[idx][2] : object_.Size_mm[idx],
               rel_locs[idx][3] : (object_.Size_mm[idx]-self.Size_mm[idx])/2,
            })[l])

   ## It should scale all numeric attributes of figure object
   ## except offsets
   def ScaleObject(self, scale=1, root=True):
      if scale == 1:
         return
      for idx in range(2):
         self.size_mm[idx] *= scale
         if not root:
            self.offs_mm[idx] *= scale
      self.margin_mm *= scale
      
      self.draw.ScaleDraw(scale)
      
      for obj in self.objects_ordered:
         obj.ScaleObject(scale, root=False)
########################################
   c_inch = 25.4
   c_pt = 72
   
   @property
   def mm_coef(self):
      return self.resolution_ppi/CFigObject.c_inch

   def mm_to_px(self, val_mm):
      return int(val_mm*self.mm_coef)

   def px_to_mm(self, val_px):
     return val_px/self.mm_coef

   @property
   def pt_coef(self):
      return self.resolution_ppi/CFigObject.c_pt

   def pt_to_px(self, val_pt):
      return int(val_pt*self.pt_coef)

   def px_to_pt(self, val_px):
      return val_px/self.pt_coef

   def mm_to_pt(self, val_mm):
      return val_mm*(CFigObject.c_pt/CFigObject.c_inch)

   def pt_to_mm(self, val_pt):
      return val_pt*(CFigObject.c_inch/CFigObject.c_pt)
########################################
   def evalGroupSize(self, idx):
      max_ = 0
      for obj in self.objects_ordered:
         ## 'RelRight' is not used to avoid circular recursion
         ## Avoid using positive 'xoffs_mm' with 'xalign=='right'' in group
         ## as it does not make sense at all
         bound_mm = obj.Size_mm[idx] + obj.offs_mm[idx]
         max_ = max(max_, bound_mm)
      return max_

   @property
   def Size_mm(self):
      return [self.size_mm[idx] if self.size_mm[idx] else self.evalGroupSize(idx) for idx in range(2)]

   @property
   def Size_px(self):
      return map(self.mm_to_px, self.Size_mm)

   @property
   def Width_mm(self):
      return self.Size_mm[0]

   @property
   def Height_mm(self):
      return self.Size_mm[1]

   @property
   def Width_px(self):
      return self.Size_px[0]

   @property
   def Height_px(self):
      return self.Size_px[1]

   @property
   def Resolution_ppi(self):
      return self.resolution_ppi
########################################
   def IsAlignValid(self, align, idx):
      return align in [['left','right','center'],['top','bottom','center']][idx]

   def SetAlign(self, align, idx):
      if align == None:
         return
      if not self.IsAlignValid(align, idx):
         raise ValueError("Invalid value for '%salign': \""+align+"\"" % ["x","y"][idx])
      self.align[idx] = align

   def SetOppositeAlign(self, align, idx):
      self.SetAlign(defaultdict(lambda:align,{
            'left': 'right',
            'right': 'left',
            'top': 'bottom',
            'bottom': 'top',
         })[align]
      , idx)
########################################
   ## According to border width
   @property
   def Margin_mm(self):
      return self.margin_mm

   @property
   def Margin_px(self):
      return self.mm_to_px(self.Margin_mm)

   @property
   def CanvasBegin_mm(self):
      return (self.Margin_mm,)*2

   @property
   def CanvasEnd_mm(self):
      return [self.Size_mm[idx] - self.Margin_mm for idx in range(2)]

   @property
   def CanvasSize_mm(self):
      return [self.Size_mm[idx] - 2*self.Margin_mm for idx in range(2)]

   @property
   def CanvasBegin_px(self):
      return map(self.mm_to_px, self.CanvasBegin_mm)

   @property
   def CanvasEnd_px(self):
      return map(self.mm_to_px, self.CanvasEnd_mm)

   @property
   def CanvasSize_px(self):
      return map(self.mm_to_px, self.CanvasSize_mm)

   @property
   def RelBegin_mm(self):
      if self.parent == None:
         return 0

      aligns = [['left','right','center'],['top','bottom','center']]
      begin = [0,0]
      for idx in range(2):
         par_begin = self.parent.CanvasBegin_mm[idx]
         par_end = self.parent.CanvasEnd_mm[idx]
         par_size = self.parent.CanvasSize_mm[idx]
         begin[idx] = self.offs_mm[idx] + {
              aligns[idx][0] : par_begin,
              aligns[idx][1] : par_end-self.Size_mm[idx],
              aligns[idx][2] : par_begin+(par_size-self.Size_mm[idx])/2
            }[self.align[idx]]
      return begin

   @property
   def AbsBegin_mm(self):
      return [0,0] if self.parent == None else map(add, self.RelBegin_mm, self.parent.AbsBegin_mm)

   @property
   def RelEnd_mm(self):
      return map(add, self.RelBegin_mm, self.Size_mm)

   @property
   def AbsEnd_mm(self):
      return map(add, self.AbsBegin_mm, self.Size_mm)

   @property
   def RelBegin_px(self):
      return map(self.mm_to_px, self.RelBegin_mm)

   @property
   def AbsBegin_px(self):
      return map(self.mm_to_px, self.AbsBegin_mm)

   @property
   def RelEnd_px(self):
      return map(self.mm_to_px, self.RelEnd_mm)

   @property
   def AbsEnd_px(self):
      return map(self.mm_to_px, self.AbsEnd_mm)
########################################
   @property
   def Opacity(self):
      return self.opacity

   def SetOpacity(self, opacity=100):
      if opacity != None:
         self.opacity = opacity
########################################
   def InitParent(self):
      self.parent = None
      self.idx = None
      self.depth = 0
      self.root_object = None

   def HasObject(self, object_):
      return object_.key in self.objects and id(self.objects[object_.key]) == id(object_)

   def actObjectAfterParentChange(self):
      if self.parent != None:
         self.idx = self.parent.ObjectsCount
         self.parent.objects_cnt += 1
         self.depth = self.parent.depth+1
         self.root_object = self.parent.RootObject

      if self.draw != None:
         self.draw.cleanSharedDrawObjectAttrs(force=True)
         self.draw.SetAttrs()

      for obj in self.objects_ordered:
         obj.actObjectAfterParentChange()

   def rmObjectFromParent(self):
      if self.parent == None:
         return
      self.parent.objects_cnt -= 1
      ## And remove from objects if it was already inserted ..
      if self.parent.HasObject(self):
         del self.parent.objects[self.key]
         del self.parent.objects_ordered[self.idx]
         for obj in self.parent.objects_ordered[self.idx:]:
            obj.idx -= 1
            if obj.ObjectKeyBase == self.ObjectKeyBase:
               obj.setObjectIdxSuffix(-1)
         similar_objects = self.parent.SimilarObjects(self.ObjectKeyBase)
         if len(similar_objects) == 1:
            similar_objects[0].setObjectIdxSuffix(-1)

   ## Can be set even before insertion !
   ## -> when so, 'objects_cnt' does not match
   ## with 'objects' length.
   ## Set only if it is not set yet
   def SetParent(self, parent):
      if self.parent == parent:
         return

      self.rmObjectFromParent()
      if parent == None:
         self.InitParent()
      else:
         self.parent = parent

      self.actObjectAfterParentChange()

   def UnsetParent(self):
      self.SetParent(None)

   @property
   def IsRoot(self):
      return True if self.depth == 0 or self.parent == None else False

   @property
   def RootObject(self):
      if self.IsRoot:
         return self
      return self.root_object

   @property
   def ObjectsCount(self):
      return self.objects_cnt
   
   @property
   def ObjectKeySplit(self):
      return self.key.rsplit("_",1)

   @property
   def ObjectKeyBase(self):
      key_split = self.ObjectKeySplit
      if len(key_split) == 2 and not str_is_int(key_split[1]):
         return self.key
      return key_split[0]

   @property
   def ObjectIdxSuffix(self):
      key_split = self.ObjectKeySplit
      return None if len(key_split) == 1 or not str_is_int(key_split[1]) else int(key_split[1])

   def setObjectIdxSuffix(self, inc=0, update_parent=True):
      if self.parent == None:
         update_parent = False
      if update_parent:
         del self.parent.objects[self.key]
      idx = self.ObjectIdxSuffix
      if idx == None:
         idx = 1
      num = idx+inc
      suffix = "" if num == 0 else "_"+str(num)
      self.key = self.ObjectKeyBase+suffix
      if update_parent:
         self.parent.objects[self.key] = self

   def SimilarObjects(self, key_base):
      objs = []
      for obj in self.objects.values():
         if obj.ObjectKeyBase == key_base:
            idx = obj.ObjectIdxSuffix
            objs.insert(0 if idx == None else idx-1, obj)
      return objs

   def SimilarObjectsCount(self, key_base):
      return len(self.SimilarObjects(key_base))

   def GetObjectByKeyBase(self, key_base, idx=0):
      objs = self.SimilarObjects(key_base)
      return None if not objs else objs[idx]

   def GetObjectByIdx(self, idx):
      return self.objects_ordered[idx]

   def InsertObject(self, object_):
      if self.HasObject(object_):
         return
      
      object_.SetParent(self)
      key_base = object_.key
      num = self.SimilarObjectsCount(key_base)
      if num > 0:
         object_.setObjectIdxSuffix(num, update_parent=False)
         ## Move the first non-incremented object to incremented key
         if key_base in self.objects.keys():
            first_object = self.objects[key_base]
            first_object.setObjectIdxSuffix()
            self.objects_ordered[first_object.idx] = first_object

      self.objects[object_.key] = object_
      self.objects_ordered.append(object_)
########################################
   ## Set external composed object, which has implemented 'PreDrawObject', 'DrawObject' and 'PostDrawObject' methods
   ## -> child of 'CDrawObjectBase'
   def SetDrawByClass(self, draw_class, **draw_args):
      if draw_class == None:
         draw = None
      else:
         draw = draw_class(self, **draw_args)
      self.SetDraw(draw)

   def SetDraw(self, draw):
      self.draw = draw

   def SetDrawObjectAttrs(self, **args):
      self.draw.SetAttrs(args)

   def SetDrawFromObject(self, object_, **draw_args):
      if self.draw == None:
         self.SetDrawByClass(object_.draw.__class__)
      else:
         self.draw.SetPtr(self)
      self.SetDrawObjectAttrs(**merge_dicts(object_.draw.AttrsWithEffects(), draw_args))

   ## Setting external functions that will be part of 'draw' object
   def AddDrawEffect(self, effect_key, type_='', **effect_args):
      self.draw.AddEffect(effect_key, type_, **effect_args)

   def SetDrawEffectAttrs(self, effect_key, **args):
      self.draw.effects[effect_key].SetAttrs(**args)

   def AddDrawEffectFromObject(self, object_, effect_key, **draw_args):
      self.draw.AddEffectFromDrawObject(object_.draw, effect_key, **draw_args)

   def AddDrawEffectsFromObject(self, object_, **draw_args):
      self.draw.AddEffectsFromDrawObject(object_.draw, **draw_args)


   ## Whole object and all its subobjects must be properly set at this moment!
   def Draw(self):
      if self.IsRoot:
         self.draw.PreDrawRootObject()
      
      self.draw.PreDrawObject()
      self.draw.DrawObject()
      self.draw.PostDrawObject()

      ## We want to keep objects order (the latest object to be the uppermost)
      for obj in self.objects_ordered:
         obj.Draw()

      if self.IsRoot:
         self.draw.PostDrawRootObject()
################################################################################

################################################################################
################################################################################

if __name__ == "__main__":
   class A:
      cnt1 = 0
      cnt2 = 0
      def __init__(self, x):
         self.x = x

      def __repr__(self):
         return "%d" % (self.x)

   class CDrawObjectTest(CDrawObjectPrint):
      def CreateSharedDrawObjectAttrs(self):
         A.cnt1 += 1
         return { 'g_mut' : A(A.cnt1), 'g_imm': A.cnt1 }
      def CleanSharedDrawObjectAttrs(self):
         A.cnt1 -= 1

      def CreateLocalDrawObjectAttrs(self):
         A.cnt2 += 1
         return { 'mut' : A(A.cnt2), 'imm': A.cnt2 }
      def CleanLocalDrawObjectAttrs(self):
         A.cnt2 -= 1

      def PostDrawObject(self):
         print self.AllAttrs()


   print "<<CFigObject tests>>\n"

   width=100
   height=100

   print "\nPrint before insertion:\n"
   par = CFigObject("Parent", height_mm=height, width_mm=width, margin_mm=10, draw_class=CDrawObjectTest,
      effect_text={'text':"I'm your father.", 'fg_color':"magenta", 'bg_color':"yellow"})
   print par

   print "\nChild 1 creation"
   obj = CFigObject("Child", height_mm=10, width_mm=7.5, yalign='center', xalign='right', yoffs_mm=5, xoffs_mm=-5, draw_class=CDrawObjectTest,
      parent=par,
      effect_text={'text':"Hello world!", 'fg_color':"red"}
   )
   print obj

   print "\nChild 2 creation: copy of child 1"
   obj2 = cp.copy(obj)
   print obj2

   print "\nChild 3 creation: copy of child 1 with modified position"
   obj3 = cp.copy(obj)
   obj3.SetPosFromObject(obj, add_yoffs_mm=1, xloc='rightof', add_xoffs_mm=-5)
   print obj3

   print "\nChild 4 creation: draw copy from child 1, parent not set yet"
   obj4_key = "Object with copied and modified draw"
   obj4 = CFigObject(obj4_key, height_mm=20, width_mm=13, xalign='left', xoffs_mm=3, margin_mm=2, draw_class=CDrawObjectTest)
   obj4.SetDrawFromObject(obj, effect_text={'fg_color':"yellow", 'bg_color':"black", 'blink':True})
   print obj4

   print "\nDraw after insertion:\n"
   par.InsertObject(obj)
   par.InsertObject(obj2)
   par.InsertObject(obj3)
   par.InsertObject(obj4)
   par.Draw()

   print "\nParent copy with modified copy of child:\n"
   par2 = cp.copy(par)
   par2.InsertObject(cp.copy(obj4))
   par2.objects[obj4_key].SetDrawEffectAttrs('text', fg_color="cyan")
   par2.objects[obj4_key].SetDrawObjectAttrs(effect_text={'bg_color':"red", 'blink':False})
   par.Draw()
   print
   par2.Draw()

   print "\nParent <deep> copy with modified child:\n"
   par3 = cp.deepcopy(par)
   par3.objects["Child_2"].SetDrawEffectAttrs('text', text="I'm the rebel!")
   par.Draw()
   print
   par2.Draw()
   print
   par3.Draw()

   print "\nChange of 1. parent attributes:\n"
   par.draw.shared_draw_attrs['g_mut'].x *= 10
   par.draw.shared_draw_attrs['g_imm'] *= 10
   par.draw.local_draw_attrs['mut'].x *= 20
   par.draw.local_draw_attrs['imm'] *= 20
   par.Draw()
   print
   par2.Draw()
   print
   par3.Draw()

   print "\n" + "-"*50 + "\n"
   print "Group of objects tests"

   group = CFigObject('group')
   gobj1 = CFigObject(height_mm=20, width_mm=30)
   gobj2 = CFigObject(height_mm=30, width_mm=20)
   
   print "Before insertion:"
   print group
   print gobj1
   print gobj2
   print

   group.InsertObject(gobj1)
   group.InsertObject(gobj2)

   print "After insertion:"
   group.Draw()
   print

   print "Unset 30x20 object:"
   gobj1.UnsetParent()
   group.Draw()
   print

   print "Add offsetted object:"
   gobj3 = CFigObject(height_mm=10, width_mm=20, yoffs_mm=25, xoffs_mm=40)
   group.InsertObject(gobj3)
   group.Draw()
   print

   print "Unset 20x10 object and add object next to 20x30:"
   gobj3.UnsetParent()
   gobj4 = CFigObject(height_mm=10, width_mm=20)
   gobj4.SetPosFromObject(gobj2, xloc='rightof', add_xoffs_mm=10)
   group.InsertObject(gobj4)
   group.Draw()
   print

   print "Unset all from back:"
   gobj4.UnsetParent()
   group.Draw()
   gobj2.UnsetParent()
   group.Draw()
   print

   print "Insert objects and remove the middle one; and the first one:"
   group.InsertObject(CFigObject(height_mm=1, width_mm=1))
   group.InsertObject(CFigObject(key='rebel', height_mm=5, width_mm=5))
   group.InsertObject(CFigObject(height_mm=2, width_mm=2))
   group.InsertObject(CFigObject(key='rebel', height_mm=5, width_mm=5))
   group.InsertObject(CFigObject(height_mm=3, width_mm=3))
   group.Draw()
   group.objects['object_2'].UnsetParent()
   group.Draw()
   group.objects['object_1'].UnsetParent()
   group.Draw()
   print

   print "Add subgroups:"
   subgroup = CFigObject(key='subgroup')
   group.InsertObject(subgroup)
   subgroup.InsertObject(CFigObject(key='right', width_mm=3, height_mm=3, xoffs_mm=-1, xalign='right'))
   subsubgroup = CFigObject('subsubgroup')
   subgroup.InsertObject(subsubgroup)
   subgroup.InsertObject(CFigObject(width_mm=4, height_mm=2, xoffs_mm=2))
   subsubgroup.InsertObject(CFigObject(width_mm=2, height_mm=6, xoffs_mm=3))
   group.Draw()
   print

   print "\n<</CFigObject tests>>"


################################################################################
################################################################################