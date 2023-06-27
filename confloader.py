#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 11:33:47 2023

@author: ck
"""

class Container:
    pass

class Confloader:


    def load_settings_from_toml(self):
        """
        try to open conf.toml and load settings
        """
        try:
            # this comes with python3.11
            import tomllib
        except ImportError:
            import tomli as tomllib


        with open("conf.toml", "rb") as fp:
            data = tomllib.load(fp)
            self.conf = Container()
            self.conf.__dict__.update(data)

        # for key, value in self.conf.items():

        #     if obj := getattr(self, key):
        #         if hasattr(obj, "setText"):
        #             obj.setText(str(value))
        #         else:
        #             setattr(self, key, value)
        #     else:
        #         setattr(self, key, value)


if __name__== "__main__":
    
    c = Confloader()
    
    c.load_settings_from_toml()
    
    cc = c.conf
    
    print("\n\n", c.conf, "\n"*2)
    
    from ipydex import IPS
    IPS()
