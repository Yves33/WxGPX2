#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import logging
from PIL import Image, ImageDraw, ImageFont,ImageColor
import json
import os
import base64
from io import BytesIO

FONTPATH=os.path.dirname(__file__)+'/'

def fonticon(bg,sample,font,fill=(0,0,0)):
    if bg is None:
        bg=bg=Image.new("RGBA",(32,32),(255,255,255,0))
    draw=ImageDraw.Draw(bg)
    width, height = draw.textsize(sample, font=font)
    draw.text((bg.width//2-width//2,bg.height//2-height//2), 
              sample, 
              font=font,
              fill=fill
              )
    return bg

class Glyph:
    def __init__(self,code,font):
        self.code=code
        self.font=font

class FontAwesome:
    def __init__(self):
        ## todo: download fonts and json if they are not present in current folder
        ## https://github.com/FortAwesome/Font-Awesome/blob/6.x/metadata/icons.json
        ## https://github.com/FortAwesome/Font-Awesome/tree/6.x/webfonts/fa-brands-400.ttf
        ## https://github.com/FortAwesome/Font-Awesome/tree/6.x/webfonts/fa-regular-400.ttf
        ## https://github.com/FortAwesome/Font-Awesome/tree/6.x/webfonts/fa-solid-900.ttf
        with open('fontawesome/Font Awesome 6.json', 'r') as f:
            self.fajson = json.load(f)

    def __getattr__(self,a):
        def cvt(sym):
            #return chr(int(self.fajson[sym]['unicode'],base=16))
            return Glyph(chr(int(self.fajson[sym]['unicode'],base=16)),
                          self.fajson[sym]['free'][0]
                        )
        
        ## todo: check if item is in 'solid', 'regular' or 'brands' return correct font
        a=a.replace('_','-')
        if a in self.fajson.keys():
            return cvt(a)
        else:
            matches=[k for k in self.fajson if a in k]
            if len(matches):
                logging.debug(f"\"{a}\" symbol could not be identified in FontAwesome.")
                logging.debug(f"Did you look for: {matches} ?")
                return cvt(matches[0])
            else:
                return cvt("font-awesome")
            
    def solid(self,size):
        return ImageFont.truetype("fontawesome/Font Awesome 6 Free-Solid-900.otf", size)
    
    def regular(self,size):
        return ImageFont.truetype("fontawesome/Font Awesome 6 Free-Regular-400.otf", size)
    
    def brands(self,size):
        return ImageFont.truetype("fontawesome/Font Awesome 6 Brands-Regular-400.otf", size)
        
class MaterialIcon:
    def __init__(self):
        ## todo: download fonts and codepoints if they are not present in current folder
        ## https://github.com/google/material-design-icons/blob/master/font/MaterialIcons-Regular.codepoints
        ## https://github.com/google/material-design-icons/blob/master/font/MaterialIconsOutlined-Regular.ttf
        ## https://github.com/google/material-design-icons/blob/master/font/MaterialIcons-Regular.ttf
        ## https://github.com/google/material-design-icons/blob/master/font/MaterialIconsRound-Regular.ttf
        ## https://github.com/google/material-design-icons/blob/master/font/MaterialIconsSharp-Regular.ttf
        self.mijson={}
        for line in open(FONTPATH+"materialui/MaterialIcons-Regular.codepoints").readlines():
            k,v=line.split(' ')
            self.mijson[k]=v
    def __getattr__(self,a):
        def cvt(sym):
            #return chr(int(self.fajson[sym]['unicode'],base=16))
            return Glyph(chr(int(self.mijson[sym],base=16)), None)
        if a in self.mijson.keys():
            return cvt(a)
        else:
            matches=[k for k in self.mijson if a in k]
            if len(matches):
                logging.debug(f"\"{a}\" symbol could not be identified in MaterialIcons.")
                logging.debug(f"Did you look for: {matches} ?")
                return cvt(matches[0])
            else:
                return cvt("preview_off")
                
    def outlined(self,size):
        return ImageFont.truetype(FONTPATH+"materialui/MaterialIconsOutlined-Regular.otf", size)
        
    def round(self,size):
        return ImageFont.truetype(FONTPATH+"materialui/MaterialIconsRound-Regular.otf", size)
        
    def sharp(self,size):
        return ImageFont.truetype(FONTPATH+"materialui/MaterialIconsSharp-Regular.otf", size)
        
    def twotone(self,size):
        return ImageFont.truetype(FONTPATH+"materialui/MaterialIconsTwoTone-Regular.otf", size)

class ButtonBg:
    def __init__(self,size=(48,48),radius=10,color=(29,161,242,255)):
        self.bg=Image.new("RGBA",size,(255,255,255,0))
        pen=ImageDraw.Draw(self.bg)
        pen.rounded_rectangle((0,0,self.bg.width-1,self.bg.height-1),radius=radius,fill=color)

class FontIcon:
    def __init__(self,bg,glyph,font,fill=(255,255,255,255)):
        if bg is None:
            bg=ButtonBg()
        draw=ImageDraw.Draw(bg)
        width, height = draw.textsize(glyph, font=font)
        draw.text((bg.width//2-width//2,bg.height//2-height//2), 
                  glyph, 
                  font=font,
                  fill=fill
                  )
        self.rgba=bg
        self.mask=bg.convert('L')
        
    def show(self):
        self.rgba.show()
        
    def encode(self,tgt='rgba'):
        buffered = BytesIO()
        if tgt=='rgba':
            self.rgba.save(buffered, format="png")
        elif tgt=='mask':
            self.mask.save(buffered, format="png")
        return base64.b64encode(buffered.getvalue())
        
if __name__=='__main__':
    import base64
    from io import BytesIO
    
    def test():
        fa=FontAwesome()
        mi=MaterialIcon()
        logging.getLogger().setLevel(logging.DEBUG)
        if 0:
            img=FontIcon(ButtonBg().bg,
               fa.magnifying_glass_minus.code,
               fa.solid(44),
               fill=(0,255,0)
               )
        else:
            img=FontIcon(ButtonBg().bg,
               mi.add.code,
               mi.twotone(44),
               fill=(255,255,255)
               )
        print(img.encode())
        img.show()
    
    def generate():
        fa=FontAwesome()
        mi=MaterialIcon()
        pycode=''
        ORANGE=(255,175,62,255)
        BLUE=(29,161,242,255)
        #icons=('add','remove')
        #colors={'up':BLUE,'down':(192,192,192,255)}
        icons=('distance','star','favorite')
        colors={'up':ORANGE,'down':(192,192,192,255)}
        for glyph in icons:
            for name,color in colors.items():
                pycode+=f"ICN_{glyph}_{name}="
                img=FontIcon(ButtonBg(size=(24,24),color=color,radius=7).bg,
                                mi.__getattr__(glyph).code,
                                mi.twotone(20),
                                fill=(255,255,255)
                                )
                pycode+=str(img.encode())+'\n'
        print(pycode)
    
    generate()

