#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 11:33:47 2023

@author: ck
"""

import os


class Container:
    def get(self, *args, **kwargs):
        return self.__dict__.get(*args, **kwargs)


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

        if data.get("selected_folder"):
            data["selected_folder"] = os.path.expanduser(data.get("selected_folder"))

        self.conf = Container()
        self.conf.__dict__.update(data)


if __name__== "__main__":

    c = Confloader()

    c.load_settings_from_toml()

    cc = c.conf

    print("\n\n", c.conf, "\n"*2)

    from ipydex import IPS
    IPS()
