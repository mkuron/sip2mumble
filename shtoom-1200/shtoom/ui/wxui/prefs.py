#!/usr/bin/env python
# originally generated by wxGlade 0.3.1 on Mon Apr 19 22:10:30 2004
# heavily modified since

from wxPython.wx import *
from shtoom.Options import NoDefaultOption

class PreferencesDialog(wxDialog):
    def __init__(self, *args, **kwds):
        self.opts = kwds['opts']

        # begin wxGlade: PreferencesDialog.__init__
        kwds["style"] = wxDEFAULT_DIALOG_STYLE
        wxDialog.__init__(self, None, -1, "Edit Preferences")
        self.prefs_notebook = wxNotebook(self, -1, style=0)
        self.prefs_save = wxButton(self, wxID_OK, "Save", style=wxBU_EXACTFIT)
        self.prefs_cancel = wxButton(self, wxID_CANCEL, "Cancel",
            style=wxBU_EXACTFIT)
        self.__set_properties()
        # end wxGlade

        self.options = {}

        for group in self.opts:
            # probably don't need to have this panel.
            nbpage = wxPanel(self.prefs_notebook, -1)
            nbsizer = wxFlexGridSizer(0, 2, 0, 0)
            nbsizer.AddGrowableCol(1)
            nbpage.SetSizer(nbsizer)

            groupname = group.getName()
            for optnumber, option in enumerate(group):
                optname = option.getName()
                val = option.getValue()

                optlabel = wxStaticText(nbpage, -1, option.getPrettyName())
                nbsizer.Add(optlabel, 0, wxALL|wxALIGN_CENTER_VERTICAL, 5)
                if option.optionType in ( 'String', 'Number', 'Password' ):
                    style = 0
                    if option.optionType == 'Password':
                        style |= wxTE_PASSWORD
                    edit = wxTextCtrl(nbpage, -1, style=style)
                    if val is not NoDefaultOption:
                        edit.SetValue(str(val))
                    get = lambda e=edit: str(e.GetValue())
                elif option.optionType == 'Boolean':
                    edit = wxCheckBox(nbpage, -1, "")
                    if val is not NoDefaultOption:
                        # TODO: boolean types don't seem to be passing their
                        # saved values in correctly
                        print "val %s is %s"%(optname, val)
                    get = lambda e=edit: e.GetValue()
                elif option.optionType == 'Choice':
                    choices = option.getChoices()
                    rbs = [c for c in option.getChoices()]
                    edit = wxRadioBox(nbpage, -1, "", choices=rbs,
                        majorDimension=1, style=wxRA_SPECIFY_ROWS)
                    if val is not NoDefaultOption:
                        print "val is ", val
                        edit.SetStringSelection(val)
                    get = lambda e=edit: e.GetStringSelection()
                else:
                    raise ValueError, "Unknown option %s"%(option.optionType)
                edit.SetToolTipString(option.getDescription())
                nbsizer.Add(edit, 1, wxEXPAND|wxALL|wxALIGN_CENTER_VERTICAL, 5)
                self.options[optname] = (option.optionType, get, edit)
            self.prefs_notebook.AddPage(nbpage, groupname)

        self.__do_layout()

    def __set_properties(self):
        # begin wxGlade: PreferencesDialog.__set_properties
        self.SetTitle("Edit Preferences")
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: PreferencesDialog.__do_layout
        sizer_1 = wxBoxSizer(wxVERTICAL)
        sizer_2 = wxBoxSizer(wxHORIZONTAL)
        sizer_1.Add(wxNotebookSizer(self.prefs_notebook), 1, wxEXPAND, 0)
        sizer_2.Add(self.prefs_save, 1, wxALL|wxALIGN_CENTER_HORIZONTAL|wxALIGN_CENTER_VERTICAL, 5)
        sizer_2.Add(self.prefs_cancel, 1, wxALL|wxALIGN_CENTER_HORIZONTAL|wxALIGN_CENTER_VERTICAL, 5)
        sizer_1.Add(sizer_2, 0, wxEXPAND, 0)
        self.SetAutoLayout(1)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        sizer_1.SetSizeHints(self)
        self.Layout()
        # end wxGlade

    def savePreferences(self, app):
        out = {}
        for k, (type, get, edit) in self.options.items():
            out[k] = get()
        print "save prefs", out
        app.updateOptions(out)

# end of class PreferencesDialog
