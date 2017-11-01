#!/usr/bin/env python2

## Extends 'figure' and 'card' libraries of Gimp Python-Fu commands

from __future__ import division
from gimpfu import *

import copy as cp
import os.path

import logging as log
import sys

log.basicConfig(stream=sys.stdout, level=log.INFO)


import fig_object as fo
import figure as fig


################################################################################
class CDrawObjectGimp(fo.CDrawObjectBase):
   """
   Class that extends 'DrawObjectBase' routine with gimp Python-Fu commands
   """
########################################
   ## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(fo.CDrawObjectBase.attrDefaults(),{
   })

   effects_attr_defaults = fo.merge_dicts(fo.CDrawObjectBase.effectsAttrDefaults(),{
      'fill': {
         'pattern': {'name': "Canvas Covered"},
      },
   })

   effects_ranks = fo.merge_dicts(fo.CDrawObjectBase.effectsRanks(),{
   })
########################################
   def Resize(self, item):
      item.resize(max(1,self.Width_px), max(1,self.Height_px))

   def ResizeLayerRec(self):
      self.Resize(self.layer)
      if self.parent != None and isinstance(self.parent.draw, CDrawObjectGimp):
         self.parent.draw.ResizeLayerRec()

   def CreateImage(self):
      img = gimp.Image(1, 1, RGB)
      img.disable_undo()
      self.Resize(img)
      img.filename = "/home/tomaqa/Data/Pics/Hry/Mysteria/v1.10/Karty/gen/"+self.figure.IdxNamePrefix+self.key.title()+".xcf"
      return img

   def CreateLayer(self, alpha=True):
      key = self.key.title()
      ## 'add_alpha' on 'RGB_IMAGE' does not work ..
      layer = gimp.Layer(self.img, key, 1, 1, RGBA_IMAGE if alpha else RGB_IMAGE)
      self.AddLayer(layer)
      self.Resize(layer)
      return layer

   def AddLayer(self, layer=None):
      if layer == None:
         layer = self.layer
      self.img.add_layer(layer, -1)

   def CreateSharedDrawObjectAttrs(self):
      return { 'img': self.CreateImage() }

   def CreateLocalDrawObjectAttrs(self):
      return { 'layer': self.CreateLayer() }

   def CleanLocalDrawObjectAttrs(self):
      ##! Is it safe? What if other layer has already been inserted before?
      ##! Then it probably would not keep the previous order
      self.img.remove_layer(self.layer)
########################################
   def Save(self):
      pdb.gimp_file_save(
         self.img,                    #<- image
         self.layer,                  #<- drawable
         self.img.filename, self.img.filename,
      )

   # def SavePDF(self):
   #    pdb.file_pdf_save(
   #       self.img,                    #<- image
   #       self.layer,                  #<- drawable
   #       "/home/tomaqa/"+self.key+".pdf", "/home/tomaqa/"+self.key+".pdf",
   #       True,                   #<- vectorize
   #       True,                   #<- ignore-hidden
   #       True,                   #<- apply-masks
   #    )
########################################
   def PreDrawRootObject(self):
      self.Resize(self.img)
      pdb.gimp_image_set_resolution(self.img, self.Resolution_ppi, self.Resolution_ppi)

   def PreDrawObject(self):
      log.debug("PreDrawObject: " + str(self.ptr) + " " + str(self.img) + " : " + str(self.img.layers))
      log.debug("  " + str(self.img.active_layer) + " >>> " + str(self.layer))
      self.Resize(self.layer)
      log.debug(str(self.layer.width) + "x" + str(self.layer.height))
      self.img.active_layer = self.layer

   def PostDrawObject(self):
      self.ScaleDraw()
      self.layer.set_offsets(*self.AbsBegin_px)
      pdb.gimp_layer_set_opacity(self.layer, self.ptr.opacity)

   def PostDrawRootObject(self):
      self.Save()
      gimp.delete(self.img)
########################################
   ## Scale layer to fit figure object
   ## Call before setting offset
   def ScaleDraw(self, scale=1, layer=None, with_border=True):
      fo.CDrawObjectBase.ScaleDraw(self, scale)
      if layer == None:
         layer = self.layer
      [width, height] = self.Size_px if with_border else self.CanvasSize_px
      layer.scale(max(1,width), max(1,height), False)
########################################
########################################
   def merge_layer_group(self, group):
      for layer in self.img.layers:
         pdb.gimp_item_set_visible(layer, True if layer == group else False)
      res = self.img.merge_visible_layers(EXPAND_AS_NECESSARY)
      for layer in self.img.layers:
         pdb.gimp_item_set_visible(layer, True)
      return res
########################################
   ## Gimp fill functions
   def EffectFillColor(self, color, **dummy):
      gimp.context_push()
      
      gimp.set_background(color)
      pdb.gimp_edit_fill(self.layer, BACKGROUND_FILL)

      gimp.context_pop()

   def EffectFillPattern(self, name, **dummy):
      gimp.context_push()
      
      pdb.gimp_context_set_pattern(name)
      pdb.gimp_edit_fill(self.layer, PATTERN_FILL)

      gimp.context_pop()

   def EffectFillPicture(self, path, **dummy):
      gimp.context_push()
      
      if not os.path.isfile(path):
         path = self.GetEffectTypeAttrDefaults('fill','picture')['path']
      pic = pdb.gimp_file_load_layer(self.img, path)
      self.AddLayer(pic)
      self.ScaleDraw(layer=pic, with_border=False)
      pic.set_offsets(*[self.layer.offsets[idx] + self.Margin_px for idx in range(2)])
      self.layer = pdb.gimp_image_merge_down(self.img, pic, EXPAND_AS_NECESSARY)

      gimp.context_pop()

   def EffectFillGradient(self, color1, color2, angle, ratio=1, **dummy):
      gimp.context_push()
      
      ##! Angle should be taken into consideration
      crosslen = ratio*self.Height_px

      gimp.set_foreground(color1)
      gimp.set_background(color2)

      ## Does not work with alpha layer - have to create a dummy one
      layer = self.CreateLayer(alpha=False)
      pdb.python_layerfx_gradient_overlay(self.img, layer,
         "FG to BG (RGB)",                   #<- gradient name
         GRADIENT_LINEAR,                    #<- gradient type (shape)
         REPEAT_NONE,                        #<- repeat mode
         False,                              #<- reverse gradient
         100,                                #<- opacity
         NORMAL_MODE,                        #<- mode
         self.Width_px/2,self.Height_px/2,   #<- center x,y
         angle,                              #<- angle
         crosslen,                           #<- cross width
         False,                              #<- merge?
      )
      layer = self.merge_layer_group(layer.parent)
      self.layer = pdb.gimp_image_merge_down(self.img, layer, EXPAND_AS_NECESSARY)

      gimp.context_pop()
########################################
   ## Gimp border funtions
   ## Does not work for picture and gradient (yet?)
   def EffectBorderFill(self, f, **args):
      gimp.context_push()
      
      ## Layer has not been moved yet, so offset absence does not matter
      pdb.gimp_image_select_rectangle(self.img, CHANNEL_OP_REPLACE,
         *self.CanvasBegin_px+self.CanvasSize_px
      )
      pdb.gimp_selection_invert(self.img)

      f(self, **args)

      pdb.gimp_selection_none(self.img)
      gimp.context_pop()

   def EffectBorderColor(self, color, **dummy):
      self.EffectBorderFill(self.__class__.EffectFillColor, color=color)

   def EffectBorderPattern(self, name, **dummy):
      self.EffectBorderFill(self.__class__.EffectFillPattern, name=name)

   ## + Edit->Stroke Selection ...
########################################
   ## Gimp text functions
   ##! 'bg_color' ignored
   def EffectText(self, text, size_pt=None, bold=True, fg_color="black", bg_color="white", justify="center", margin_mm=0, fontname="Comic Sans", **dummy):
      gimp.context_push()

      if size_pt == None:
         size_pt = self.SetFontSizeFromObject()

      if bold and "Bold" not in fontname:
         fontname += " Bold"

      ## Size in points does now work, so we have to evaluate it manually
      tl = pdb.gimp_text_fontname(self.img, self.layer,
            0, 0,                      #<- x,y
            text,                      #<- text
            self.mm_to_px(margin_mm),  #<- border size
            True,                      #<- antialiasing
            self.pt_to_px(size_pt),    #<- size in pixels (vv)
            PIXELS,                    #<- size type
            fontname,                  #<- fontname
         )
      [canvas_width, canvas_height] = self.CanvasSize_px
      width = canvas_width
      height = tl.height
      pdb.gimp_text_layer_resize(tl, width, height)
      ## Do not set offsets of object ~ layer, it sets it automatically
      ## when anchoring
      [left, right] = self.CanvasBegin_px
      right += int((canvas_height-tl.height)/2)
      tl.set_offsets(left, right)
      pdb.gimp_text_layer_set_color(tl, fg_color)
      pdb.gimp_text_layer_set_justification(tl, {
         "center": TEXT_JUSTIFY_CENTER,
         "left": TEXT_JUSTIFY_LEFT,
         "right": TEXT_JUSTIFY_RIGHT,
         "fill": TEXT_JUSTIFY_FILL,
      }[justify])
      pdb.gimp_floating_sel_anchor(tl)

      gimp.context_pop()
########################################
   ## Gimp transform functions
   def EffectShear(self, mag_x=0, mag_y=0, **dummy):
      gimp.context_push()

      pdb.gimp_item_transform_shear(self.layer, ORIENTATION_HORIZONTAL, mag_x)
      pdb.gimp_item_transform_shear(self.layer, ORIENTATION_VERTICAL, mag_y)

      gimp.context_pop()
########################################
   ## Gimp mask functions
################################################################################

################################################################################
class CDrawFigureGimp(fig.CDrawFigureBase):
   """
   Class that sets draw figure to draw routines of gimp Python-Fu commands
   """
########################################
   default_draw_object_class = CDrawObjectGimp
########################################
   ## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(fig.CDrawFigureBase.attrDefaults(),{
   })
################################################################################


################################################################################
################################################################################

## Need to run from Gimp Python-fu console or through gimp-console

################################################################################
################################################################################
