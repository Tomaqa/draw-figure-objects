#!/usr/bin/env python2

## Library that defines Mysteria layouts above 'CLayoutFigureBase'

from __future__ import division
import copy as cp

import fig_object as fo
import figure as fig

################################################################################
################################################################################

################################################################################
class CLayoutMysteriaCard_(fig.CLayout):
   """
   Incomplete layout class of all kinds of Mysteria cards.
   Incomplete within the meaning of that one certainly wants to use some of its subclasses.
   """
########################################
## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(fig.CLayout.attrDefaults(),{
      'flag' : False,

      'mini_height_mm' : 12.5,
      'mini_xloc' : 'right',
      'mini_add_xoffs_mm' : -1,
      'mini_yloc' : 'centerof',

      'mini_2' : False,
      'mini_2_xloc' : 'mirror',
      'mini_2_scale' : 1.2,

      'label_width_mm' : 28,
      'label_height_mm' : 5,
      'label_margin_mm' : 0.4,
      'label_xalign' : 'center',
      'label_xoffs_mm' : 1.1,
      'label_yoffs_mm' : 5,
      'label_draw_object_args' : {
         'effect_fill' : {'type':'gradient', 'color1':"white", 'color2':"lime", 'angle':80, 'ratio':2},
         'effect_border' : {'type':'color', 'color':"black"},
         'effect_text': {'type':'', 'text':"Card name", 'fg_color':"black", 'size_pt':9.5},
         'effect_shear': {'mag_x':-30},
      },

      'picture_width_mm' : 30,
      'picture_height_mm' : 45,
      'picture_xalign' : 'left',
      'picture_xoffs_mm' : 1,
      'picture_yloc' : 'below',
      'picture_add_yoffs_mm' : 10,
      'picture_draw_object_args' : {
         'effect_fill' : {'type':'picture'},
      },
   })

   local_ranks = [0,10]
   ranks_ = None
########################################
   def AddObjectBackMiniToLayout(self, xloc=fo.DEFAULT, add_xoffs_mm=fo.DEFAULT, add_yoffs_mm=fo.DEFAULT,
   ):
      obj = self.AddObjectCopyToLayout(self.back, new_key='mini', new_parent=self.front,
         xloc=xloc, add_xoffs_mm=add_xoffs_mm, add_yoffs_mm=add_yoffs_mm,
         scale=(self.mini_height_mm/self.back.Height_mm)
      )
      return obj
########################################
   def Layout(self, rank=0):
      if rank == 0:
         label = self.AddObjectToLayout('label', parent=self.front)
         pic = self.AddObjectToLayout('picture', parent=self.front)
         pic.SetPosFromObject(label, xloc=None, yloc=self.picture_yloc, add_yoffs_mm=self.picture_add_yoffs_mm)
      elif rank == 10:
         mini = self.AddObjectBackMiniToLayout()
         mini.SetPosFromObject(self.front.GetObjectByKeyBase('label'), xloc=None, yloc=self.mini_yloc)
         if self.mini_2:
            mini_2 = self.AddObjectCopyToLayout(mini, new_key='mini_2')
      return self.ReturnRank(rank)
################################################################################

################################################################################
class CLayoutMysteriaCardHold_(CLayoutMysteriaCard_):
   """
   Incomplete layout class of Mysteria hold cards
   -> all cards that players play with directly
   (they hold them in hand or have them in packs)
   """
########################################
## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(CLayoutMysteriaCard_.attrDefaults(),{
      'flag' : False,

      'back_artifacts_group_xalign' : 'center',
      'back_artifacts_group_add_yoffs_mm' : 4,

      'category_icons_group_xalign' : 'center',
      'category_icons_group_yalign' : 'bottom',
      'category_icons_group_yoffs_mm' : -3,

      'importance_group_xoffs_mm' : 1,
      'importance_group_yoffs_mm' : 1,

      'category_importance' : 1,
      'category_importance_width_mm' : 5,
      'category_importance_height_mm' : 5,
      'category_importance_yalign' : 'center',
      'category_importance_draw_object_args' : {
         'effect_text': {'type':''},
      },

      'class_importance' : 1,
      'class_importance_width_mm' : 4.5,
      'class_importance_height_mm' : 4.5,
      'class_importance_yalign' : 'center',
      'class_importance_xloc' : 'rightof',
      'class_importance_add_xoffs_mm' : 0.2,
      'class_importance_draw_object_args' : {
         'effect_fill': {'type':'picture'},
      },

      'prestige' : 0,
      'prestige_group_xoffs_mm' : 0.5,
      'prestige_group_yalign' : 'bottom',
      'prestige_group_yoffs_mm' : -0.5,
      'prestige_text_width_mm' : 6,
      'prestige_text_height_mm' : 3,
      'prestige_text_draw_object_args' : {
         'effect_text': {'type':''},
      },
      'prestige_class_width_mm' : 3,
      'prestige_class_height_mm' : 3,
      'prestige_class_draw_object_args' : {
         'effect_fill': {'type':'picture'},
      },
   })

   local_ranks = [0]
   ranks_ = None
########################################
   def AddObjectIconToLayout(self, key, icons_obj,
      scale=fo.DEFAULT,
      add_xoffs_mm=fo.DEFAULT,
      opacity=fo.DEFAULT,
      **draw_object_args
   ):
      self.SetFunctionAttrDefaults(key,3)
      obj = self.AddObjectToGroup(key, icons_obj,
         xloc='rightof', add_xoffs_mm=add_xoffs_mm,
         opacity=opacity,
         **draw_object_args
      )
      obj.SetSizeFromObject(self.back, scale=self.args.scale)
      obj.AddDrawEffectFromObject(self.back, 'border')
      self.CleanFunctionAttrDefaults()
      return obj

   def AddObjectPrestigeToLayout(self):
      key = 'prestige'
      group = self.AddObjectGroupToLayout(key, parent=self.front)
   
      if self.prestige != 0:
         text_obj = self.AddObjectToGroup(parent=group, key=key+'_text', effect_text={'text':"%+d" % self.prestige, 'fg_color':"lime" if self.prestige > 0 else "red"})
         ##!class_obj ~ prestiz vrstvy

      return group
########################################
   def Layout(self, rank=0):
      CLayoutMysteriaCard_.Layout(self, rank)
      if rank == 0:
         importance_left = self.AddObjectGroupToLayout('importance', parent=self.back)
         category_importance_left = self.AddObjectToGroup('category_importance', parent=importance_left, effect_text={'text':str(self.category_importance)})
         class_importance_left = self.AddObjectToGroup('class_importance', parent=importance_left)
         importance_right = self.AddObjectCopyToLayout(importance_left, xloc='mirror')

         back_artifacts = self.AddObjectGroupToLayout('back_artifacts', parent=self.back)
         back_artifacts.SetPosFromObject(importance_left,
            xloc=None, yloc='below', add_yoffs_mm=self.back_artifacts_group_add_yoffs_mm,
         )

         category_icons = self.AddObjectGroupToLayout('category_icons', self.back)

         prestige_group = self.AddObjectPrestigeToLayout()
      return self.ReturnRank(rank)
################################################################################

################################################################################
class CLayoutMysteriaCardPlay_(CLayoutMysteriaCardHold_):
   """
   Incomplete layout class of Mysteria play cards
   -> all hold cards except units
   """
########################################
## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(CLayoutMysteriaCardHold_.attrDefaults(),{
      'flag' : False,

      'play_with_yloc' : 'below',
      'play_with_add_yoffs_mm' : 1,
      'play_with_scale' : 0.7,
      'play_with_draw_object_args' : {
         'effect_fill' : {'color2':"red"},
         'effect_text': {'text':""},
      },

      'force_play' : False,
      'back_force_play_width_mm' : 9,
      'back_force_play_height_mm' : 22,
      'back_force_play_xalign' : 'center',
      'back_force_play_yloc' : 'below',
      'back_force_play_add_yoffs_mm' : 3,
      'back_force_play_draw_object_args' : {
         'effect_fill' : {'type':'picture'},
      },
   })

   local_ranks = [0,1]
   ranks_ = None
########################################
   def Layout(self, rank=0):
      CLayoutMysteriaCardHold_.Layout(self, rank)
      if rank == 0:
         if self.play_with_draw_object_args['effect_text']['text'] != "":
            play_with = self.AddObjectCopyToLayout(self.front.GetObjectByKeyBase('label'), new_key='play_with')
            play_with.SetDrawEffectAttrs('text', text="+"+play_with.draw.AttrsFromEffects()['effect_text']['text'])
      elif rank == 1:
         if self.force_play:
            back_force_play = self.AddObjectToGroup('back_force_play', parent=self.back.GetObjectByKeyBase('back_artifacts_group'))
      return self.ReturnRank(rank)
################################################################################

################################################################################
class CLayoutMysteriaCardBasic(CLayoutMysteriaCardPlay_):
   """
   Layout class of Mysteria basic cards
   """
########################################
## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(CLayoutMysteriaCardPlay_.attrDefaults(),{
   })

   local_ranks = [0]
   ranks_ = None
########################################
   def Layout(self, rank=0):
      CLayoutMysteriaCardPlay_.Layout(self, rank)
      return self.ReturnRank(rank)
################################################################################

################################################################################
class CLayoutMysteriaCardClass(CLayoutMysteriaCardPlay_):
   """
   Layout class of Mysteria class cards
   -> ordinary, special, shared and risc cards
   """
########################################
## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(CLayoutMysteriaCardPlay_.attrDefaults(),{
      'front_class_width_mm' : 10.8,
      'front_class_height_mm' : 10.8,
      'front_class_draw_object_args' : {
         'effect_fill' : {'type':'picture'},
      },

      'back_class_width_mm' : 18,
      'back_class_height_mm' : 18,
      'back_class_xalign' : 'center',
      'back_class_yloc' : 'below',
      'back_class_add_yoffs_mm' : 6,
      'back_class_draw_object_args' : {
         'effect_fill' : {'type':'picture'},
      },
   })

   local_ranks = [0,11]
   ranks_ = None
########################################
   def Layout(self, rank=0):
      CLayoutMysteriaCardPlay_.Layout(self, rank)
      if rank == 0:
         back_class = self.AddObjectToGroup('back_class', parent=self.back.GetObjectByKeyBase('back_artifacts_group'))
      elif rank == 11:
         front_class = self.AddObjectToLayout('front_class', parent=self.front)
         front_class.SetPosFromObject(self.front.GetObjectByKeyBase('mini'), xloc='mirror', yloc=None)
         front_class.SetPosFromObject(self.front.GetObjectByKeyBase('label'), xloc=None, yloc='centerof')
      return self.ReturnRank(rank)
################################################################################

################################################################################
class CLayoutMysteriaCardSpell(CLayoutMysteriaCardPlay_):
   """
   Layout class of Mysteria spell cards
   """
########################################
## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(CLayoutMysteriaCardPlay_.attrDefaults(),{
      'spell_class' : 1,
      'spell_class_width_mm' : 20,
      'spell_class_height_mm' : 20,
      'spell_class_xalign' : 'center',
      'spell_class_yloc' : 'below',
      'spell_class_add_yoffs_mm' : 6,
      'spell_class_draw_object_args' : {
         'effect_fill' : {'type':'picture'},
         'effect_text' : {'size_pt':24, 'fg_color':"black"},
      },

      'spell_mana' : 2,
      'spell_mana_draw_object_args' : {
         'effect_fill' : {'type':'color', 'color':"blue"},
         'effect_text' : {'size_pt':12, 'fg_color':"white"},
      },
   })

   local_ranks = [0,11]
   ranks_ = None
########################################
   def Layout(self, rank=0):
      CLayoutMysteriaCardPlay_.Layout(self, rank)
      if rank == 0:
         spell_class = self.AddObjectToGroup('spell_class', parent=self.back.GetObjectByKeyBase('back_artifacts_group'),
            effect_text={'text':str(self.spell_class)}
         )
      elif rank == 11:
         spell_mana = self.AddObjectToLayout('spell_mana', parent=self.front, effect_text={'text':str(self.spell_mana)})
         mini = self.front.GetObjectByKeyBase('mini')
         spell_mana.SetSizeFromObject(mini, set_margin=False)
         spell_mana.SetPosFromObject(mini, xloc='mirror')
      return self.ReturnRank(rank)
################################################################################

################################################################################
class CLayoutMysteriaCardMana(CLayoutMysteriaCardPlay_):
   """
   Layout class of Mysteria mana cards
   """
########################################
## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(CLayoutMysteriaCardPlay_.attrDefaults(),{
      'mini_2' : True,
   })

   local_ranks = [0]
   ranks_ = None
########################################
   def Layout(self, rank=0):
      CLayoutMysteriaCardPlay_.Layout(self, rank)
      return self.ReturnRank(rank)
################################################################################


################################################################################
class CLayoutMysteriaCardAddKind(CLayoutMysteriaCardPlay_):
   """
   Additional (it does not inherit behaviour) layout class of Mysteria kind cards
   -> kind, basic and unit cards
   """
########################################
## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(CLayoutMysteriaCardPlay_.attrDefaults(),{
      'kind_label_add_yoffs_mm' : -0.5,
      'kind_label_new_width_mm' : 15,
      'kind_label_scale' : 0.75,
      'kind_label_draw_object_args' : {
         'effect_fill' : {'color2':"cyan"},
         'effect_text': {'text':"Kind name"},
      },
      
      'back_kind_label_xalign' : 'center',
      'back_kind_label_yloc' : 'below',
      'back_kind_label_add_yoffs_mm' : 5,
      'back_kind_label_scale' : 1.5,

      'no_steal_scale' : 0.15,
      'no_steal_add_xoffs_mm' : 1,
      'no_steal_draw_object_args' : {
         'effect_fill' : {'type':'picture'},
      },

      'no_dump' : True,
      'no_dump_scale' : 0.15,
      'no_dump_add_xoffs_mm' : 1,
      'no_dump_draw_object_args' : {
         'effect_fill' : {'type':'picture'},
      },
   })

   local_ranks = [0]
   ranks_ = None
########################################
   def AddObjectKindLabelToLayout(self, label_obj,
      add_yoffs_mm=fo.DEFAULT,
      scale=fo.DEFAULT,
      **draw_object_args
   ):
      key = 'kind_label'
      obj = self.AddObjectCopyToLayout(label_obj, new_key=key,
         yloc='above', add_yoffs_mm=add_yoffs_mm,
         scale=scale,
         **draw_object_args
      )
      return obj
########################################
   def Layout(self, rank=0):
      if rank == 0:
         front_kind_label_obj = self.AddObjectKindLabelToLayout(self.front.GetObjectByKeyBase('label'))
         back_kind_label_obj = self.AddObjectCopyToLayout(front_kind_label_obj,
            new_key='back_kind_label',
            new_parent=self.back,
            xloc=None, add_xoffs_mm=0, yloc=None, add_yoffs_mm=0,
         )
         self.addObjectToGroup(parent=self.back.GetObjectByKeyBase('back_artifacts_group'), object_=back_kind_label_obj)

         no_steal_obj = self.AddObjectIconToLayout('no_steal', self.back.GetObjectByKeyBase('category_icons_group'))
         if self.no_dump:
            no_dump_obj = self.AddObjectIconToLayout('no_dump', self.back.GetObjectByKeyBase('category_icons_group'))
      return self.ReturnRank(rank)
################################################################################

################################################################################
################################################################################

################################################################################
class CLayoutFigureMysteriaCard(fig.CLayoutFigureBase):
   """
   Layout class of all kinds of Mysteria cards
   """
########################################
## All default values off class' possible attributes should be defined
   attr_defaults = fo.merge_dicts(fig.CLayoutFigureBase.attrDefaults(),{
      'layout_front' : {
         'front_margin_mm' : 3,
         'front_draw_object_args' : {
               'effect_fill' : {'type':'gradient', 'color1':"black", 'color2':"white", 'angle':90, 'ratio':1.2},
               'effect_border' : {'type':'color', 'color':"white"},
            },
         },
      'layout_back' : {
         'back_margin_mm' : 7.5,
         'back_draw_object_args' : {
               'effect_fill' : {'type':'pattern'},
               'effect_border' : {'type':'color', 'color':"white"},
            },
         },

      'layout_mysteria_card_basic' : {
         'flag' : False,
         'rank' : 5,
         'module' : __name__,
      },
      'layout_mysteria_card_class' : {
         'flag' : False,
         'rank' : 5,
         'module' : __name__,
      },
      'layout_mysteria_card_spell' : {
         'flag' : False,
         'rank' : 5,
         'module' : __name__,
      },
      'layout_mysteria_card_mana' : {
         'flag' : False,
         'rank' : 5,
         'module' : __name__,
      },

      'layout_mysteria_card_add_kind' : {
         'flag' : False,
         'rank' : 7,
         'module' : __name__,
      },
   })
################################################################################

################################################################################
################################################################################

if __name__ == "__main__":
   x = fig.CFigure(300, height_mm=80, width_mm=58)
   ## Only for simple test purpose, one may not have any reason to use this incomplete layout
   x.Set(layout_figure_class=CLayoutFigureMysteriaCard, layout_figure_args={
      'layout_mysteria_card_play_':{'flag':True, 'rank':3, 'module':__name__},
   })
   print "Apply all layouts gradually:"
   while x.Do(layout_step=1):
      print
   print
   print "-"*20

   print "Add text effect for back (previous 'mini' unaffected):"
   x.back.AddDrawEffect('text', text="Back side", fg_color="magenta")
   x.Do(force_draw=True)
   print "-"*20

   print "Add mini object and copy of label and mini"
   m1 = x.layout.layouts['mysteria_card_play_'].AddObjectBackMiniToLayout(add_xoffs_mm=1, add_yoffs_mm=20)
   l = x.layout.AddObjectCopyToLayout(x.front.GetObjectByKeyBase('label'), effect_text={'text':"Card name", 'bg_color':"yellow"})
   m2 = x.layout.AddObjectCopyToLayout(m1, xloc='mirror')
   x.Do(force_draw=True)
   print "-"*20

   print "Front unordered:"
   for m in  x.front.objects.values():
      print m
   print "-"*20

   print "Front ordered:"
   for m in  x.front.objects_ordered:
      print m
   print "-"*20

   print "Front effects as attributes: ", x.front.draw.AttrsFromEffects()
   print "Back effects as attributes: ", x.back.draw.AttrsFromEffects()

################################################################################
################################################################################
