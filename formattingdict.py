"""
Extended dictionary class with alternative keys, default values and string
transformations at retrieval time.
"""

# Copyright (C) 2007 Andrew C. Bulhak
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__version__ = "0.2"
__author__  = "Andrew C. Bulhak"
__copyright__ = "Copyright (C) 2007 Andrew C. Bulhak. GNU GPL 2"

import urllib

class UnknownTransform(Exception):
    pass


class FormattingDict(dict):
    """ A superclass of the Python dictionary which can retrieve string values in a more advanced fashion. When retrieving a value, the key can contain not only the dictionary key to look for, but a list of alternative keys to try and a list of string transformations to perform on the retrieved value before returning it.

When retrieving a value from a FormattingDict, it is possible to use a regular key, or an extended key of the form:

    key1|key1|...|keyN:trans1:trans2:..:transN

Where key1 to keyN are alternative keys to try, and trans1 to transN are transforms to apply to the retrieved result. Strictly speaking, everything before the first colon is a key or part of alternate keys, whereas everything afterward is a chain of transformations, separated by colons. If any alternative key starts and ends with the same quote character, that key always will return whatever is inside the quotes. If the key part ends with a '|' (i.e., 'name|id|' or 'name|id|:lower', then if none of the alternative keys matches, the result is returned as an empty string; otherwise, a KeyError is raised.

Valid transformations in this version of FormattingDict are:

 * uc, upper -  transform to uppercase
 * lc, lower -  transform to lowercase
 * urlquote  -  quote for use in a URL; i.e., replace characters with hex codes
 * urlquote+ -  as urlquote, only spaces are replaced with '+'s
 * htmlquote, xmlquote - quote HTML/XML special characters
 * unspace   - remove all spaces
    """

    # transforms are stored in two places:
    # firstly, any method of this class beginning with xform_ will be 
    # considered a transformation function accepting and returning a string
    # (along with the self argument). I.e., xform_FOO will implement the FOO
    # transform. This allows subclasses to be created which add their own 
    # transforms to the available set.

    def xform_lc(self,s): return s.lower()
    def xform_uc(self,s): return s.upper()
    def xform_xmlquote(self,str):
        return str.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    def xform_unspace(self,s):
        return s.replace(' ','')

    # we define aliases for transformation methods, to allow them to be 
    # called by alternative names.
    xform_lower = xform_lc
    xform_upper = xform_uc
    xform_htmlquote = xform_xmlquote


    # the secondary way of implementing transformation methods is to place
    # string->string mapping functions in the 'transforms' dictionary. 
    # this allows functions to have names which aren't legal Python syntax,
    # i.e., 'urlquote+'.  This is not easily extensible through inheritance
    # (without writing a metaclass), and so is not the recommended method.

    # transform name: string->string mapping function
    transforms = {
        'urlquote' :  urllib.quote,
        'urlquote+':  urllib.quote_plus,
    }
    def __init__(self, **kw):
        for k,v in kw.iteritems():
            self.__setitem__(k,v)

    def __getitem__(self,key):
        if self.has_key(key): 
            return super(FormattingDict,self).__getitem__(key)
        else:
            r = key.split(':')
            key = r[0]
            procs = r[1:]
            alts = key.split('|')
            res = None
            for alt in alts:
                if self.has_key(alt):
                    if not res: 
                        res=super(FormattingDict,self).__getitem__(alt)
                elif alt[0]==alt[-1] and alt[0] in '\'"':
                    res = alt[1:-1]  # literal string
                elif alt=='':  # option to return blank
                    return ''
            if not res:
                raise KeyError(', '.join(alts))
            # now apply any string processing
            if procs:
                res = str(res)
            for proc in procs:
                try:
                    res = self.__getattribute__("xform_"+proc)(res)
                except AttributeError:
                    try:
                        res = self.transforms[proc](res)
                    except KeyError:
                        raise UnknownTransform(proc)
            return res
