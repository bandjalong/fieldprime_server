# datapage.py
# Michael Kirk 2013
#
# Some functions for displaying pages with a common bit (called
# Navigation Content here).
#

from flask import Flask, request, Response, redirect, url_for, render_template, g, make_response
import fp_common.fpsys as fpsys
import fp_common.models as models
import fpUtil

from const import *


def selectorOfURLs(label, promptOptionString, listOfThings, thingValueFunc, thingNameFunc, selectedThingValue):
#-------------------------------------------------------------------------------
# Return html selector representing the items in listOfThings, the values are
# URLs (provided by function thingValueFunc) and selection of an item results
# in loading the associated URL. Presentation names are given by function thingNameFunc.
# If label is not None, the dropdown has this label.
# If promptOptionString is not None then a list item is added with this text
# (eg '..select thing..'). If selectedThingValue is not None then it should
# be one of the item values (URLs) and this will be preselected (in this case
# promptOptionString should be None).
#
    out = ''
    out += '<div style="overflow: hidden; display:inline-block;">'
    out += '''<script>
    function zirptl3(newLocation) {
    sessionStorage.removeItem("fpCurrTrialPageTab"); //MFK hard code test hack
        if (newLocation !== 0) location=newLocation;
    }
    </script>'''

#     if label is not None:
#         out +=   '<div style="display:inline-block;">'
#         out +=     '<label for="tdd">{0}: &nbsp;</label>'.format(label)
#         out +=   '</div>'
#     out += '<div style="display:inline-block;min-width:200px">'
#     out += '<select class="form-control" style="min-width:300" name="tdd" id="tdd" onchange="zirptl3(this.options[this.selectedIndex].value);">'
#     if promptOptionString is not None:
#         out +=     '<option value=0 selected="selected">{0}</option>'.format(promptOptionString)
#     for thing in listOfThings:
#         val = thingValueFunc(thing)
#         out += '<option value="{0}" {1}>{2}</option>'.format(
#             val,
#             'selected="selected"' if val ==  selectedThingValue else '',
#             thingNameFunc(thing))
#     out +=     '</select>'
#     out +=   '</div>'


    sel = '<div style="display:inline-block;min-width:200px">'
    sel += '<select class="form-control" style="min-width:300" name="tdd" id="tdd" onchange="zirptl3(this.options[this.selectedIndex].value);">'
    if promptOptionString is not None:
        sel +=     '<option value=0 selected="selected">{0}</option>'.format(promptOptionString)
    for thing in listOfThings:
        val = thingValueFunc(thing)
        sel += '<option value="{0}" {1}>{2}</option>'.format(
            val,
            'selected="selected"' if val ==  selectedThingValue else '',
            thingNameFunc(thing))
    sel +=     '</select>'
    sel +=   '</div>'

    if label is not None:
        out += fpUtil.htmlLabelValue(label, sel)
    elseout = sel

    out += '</div>'
    return out

def _dataNavigationContent(sess, trialId):
#----------------------------------------------------------------------------
# Return html content for navigation bar on a data page
#
# trialId is only relevant if sess has a current project. If so then..
# If trialId is >=0:
#     The trial select dropdown is shown with the specified trial selected.
# If trialId is None:
#     The trial select dropdown is shown with no trial selected.
# If trialId < 0:
#     The trial select dropdown is not shown.
#
    ### User and user specific buttons:

    # Show current user:
    #nc = '<label>User: &nbsp;</label>' + sess.getUser()
    nc = fpUtil.htmlLabelValue('User', sess.getUser())

    # Show non project specific buttons:
    nc += '<div style="float:right; margin-top:10px">'
    nc +=   '<a href="{0}"><span class="fa fa-download"></span> Download App</a>'.format(url_for("downloadApp"))
    nc +=   '<a href="https://docs.google.com/document/d/1SpKO_lPj0YzhMV6RKlzPgpNDGFhpaF-kCu1-NTmgZmc/pub"><span class="fa fa-question-circle"></span> App User Guide</a>'
    nc += '</div><div style="clear:both"></div>'

    ### Project and project specific buttons:

    # There are currently 2 types of login, ***REMOVED***, and the project login.
    # ***REMOVED*** users may have access rights to multiple project so they get
    # a dropdown project selection. Project logins have access to a single
    # project only, so they don't get a drop down.
    if sess.getLoginType() == LOGIN_TYPE_***REMOVED***:
        # Make select of user's projects.
        # Note we need to construct the URL for retrieving the project page in javascript,
        # and hence cannot use url_for.
        projList, errMsg = fpsys.getProjects(sess.getUser())
        if errMsg or not projList:
            return 'A problem occurred in finding projects for user {0}:{1}'.format(sess.getUser(), errMsg)
        currProj = sess.getProjectName()
        nc += selectorOfURLs('Project', '..Select Project..' if currProj is None else None, projList,
            lambda p: url_for('urlProject', project=p.projectName),
            lambda p: p.projectName,
            None if currProj is None else url_for('urlProject', project=currProj))
    else:
        # Show current project:
        #nc += "<h1 style='float:left; padding-right:20px; margin:0'>Project:{0}</h1>".format(projectSelectorHtml)
        #nc += '<label>Project: &nbsp;</label>' + sess.getProjectName()
        nc += fpUtil.htmlLabelValue('Project', sess.getProjectName())

    # Show project specific buttons:
    if sess.getProjectName() is not None:
        nc += '<div style="float:right; display:inline-block; margin-top:10px">'
        if sess.adminRights():
            nc += '<a href="{0}"><span class="fa fa-user"></span> Administration</a>'.format(url_for('urlUserDetails', projectName=sess.getProjectName()))
        nc += '<a href="{0}"><span class="fa fa-gear"></span> System Traits</a>'.format(url_for('urlSystemTraits', projectName=sess.getProjectName()))
        nc += '<a href="{0}"><span class="fa fa-magic"></span> Create New Trial</a>'.format(url_for("newTrial"))
        nc += '</div><div style="clear:both"></div>'

        # Add trial selector:
        if trialId is None or trialId >= 0:
            nc += selectorOfURLs('Trial', '..Select Trial..' if trialId is None else None, sess.getProject().trials,
                lambda t: url_for('urlTrial', trialId=t.id), lambda t: t.name,
                None if trialId is None else url_for('urlTrial', trialId=trialId))
    nc += fpUtil.htmlHorizontalRule()
    return nc


def dataPage(sess, title, content, trialId=None):
#----------------------------------------------------------------------------
# Return page for user data with given content and title.
# The point of this function is to add the navigation content.
# See comment on _dataNavigationContent for trialId semantics.
#
    nc = _dataNavigationContent(sess, trialId)
    return render_template('dataPage.html', navContent=nc, content=content, title=title)


def dataTemplatePage(sess, template, **kwargs):
#----------------------------------------------------------------------------
# Return page for user data with given template, kwargs are passed through
# to the template. The point of this function is to add the navigation content.
# NB, if trialId is not specified in kwargs, then no trial dropdown is shown.
#
    if 'trialId' in kwargs:
        nc = _dataNavigationContent(sess, trialId=kwargs['trialId'])
    else:
        nc = _dataNavigationContent(sess, trialId=-1)
    return render_template(template, navContent=nc, **kwargs)


def dataErrorPage(sess, errMsg, trialId=None):
#----------------------------------------------------------------------------
# Show error message in user data page.
    return dataPage(sess, content=errMsg, title='Error', trialId=trialId)

