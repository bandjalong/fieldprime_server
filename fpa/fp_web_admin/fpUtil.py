# fpUtil.py
# Michael Kirk 2013,2014
# Utility code for FieldPrime web admin.
#
#

import sys
from cgi import escape

from flask import url_for

###  Constants: ################################################################

htmlBootstrapGumpf = '''
<!-- Latest compiled and minified CSS -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">
<!-- Optional theme -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap-theme.min.css">
<!-- Latest compiled and minified JavaScript -->
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js"></script>
'''

###  Functions: ################################################################

def fpUrl(endpoint, sess, **kwargs):
    print('fooey')
    projId = sess.getProjectId()
    return url_for(endpoint, projId=projId, _external=True, **kwargs)

def hsafe(x):
    return escape(str(x))

def getString(x):
#-----------------------------------------------------------------------
# For when x is a string, or a function returning string
#
    if isinstance(x, str): return x
    return x()

def htmlHorizontalRule():
    return '<hr style="margin:15px 0; border: 1px solid #aaa;">'

def htmlLabelValue(label, value):
    return '<label>{0}: &nbsp;</label>{1}'.format(label, value)


def htmlForm(content, formId=None, post=False, onsubmit='', multipart=False):
#-----------------------------------------------------------------------
# Returns the content surrounded by html form tags.
# NB content can be either a string, or a function returning one.
#
    contentPart = content if isinstance(content, str) else content()
    enctypePart = "enctype='multipart/form-data'" if multipart else ""
    methodPart = "method='{0}'".format('POST' if post else 'GET')
    submitPart = ' onsubmit="{0}"'.format(onsubmit) if onsubmit else ''
    idPart = ' id="{0}"'.format(formId) if formId is not None else ''
    return "<form {0} {1} {2} {3}>\n{4}</form>".format(methodPart, submitPart, enctypePart, idPart, contentPart)


def htmlFieldset(content, legend=None):
#-----------------------------------------------------------------------
# Returns html for a fieldset, with the given content and legend.
# NB content can be either a string, or a function returning one.
#
    cont = content if isinstance(content, str) else content()
    leg = '<legend><h3>{0}</h3></legend>'.format(legend) if legend is not None else ''
    return '<fieldset>{0}{1}</fieldset>'.format(leg, cont)

def htmlDiv(content, divId=None):
#-----------------------------------------------------------------------
# Returns html for a div, with the given content and id.
# NB content can be either a string, or a function returning one.
#
    cont = content if isinstance(content, str) else content()
    did = ' id="{0}"'.format(divId) if divId is not None else ''
    return '<div{0}>{1}</div>'.format(did, cont)

def htmlHeaderFieldset(content, legend):
#-----------------------------------------------------------------------
# Returns html to show legend as a header2 and then the content in a fieldset.
#
    return "<h2>{0}</h2><fieldset>{1}</fieldset>".format(legend, content)


def exit(sess=None):
#-----------------------------------------------------------------------
# Exits script, after closing sess if present
#
    if sess:
        sess.close()
    sys.exit()


def htmlButtonLink(label, click, color='btn-primary'):
#-----------------------------------------------------------------------
    return '''<button type="button" class="btn {2}"
        onClick="window.location='{0}'">{1}</button>'''.format(click, label, color)

def htmlFpButtonLink(label, location, quoteLocation=True):
#-----------------------------------------------------------------------
    if quoteLocation:
        location = '\'{}\''.format(location)
    return '''<button type="button" class="fpButton"
        onClick="window.location={0}">{1}</button>'''.format(location, label)

# def htmlButtonLink3(label, click):
# #-----------------------------------------------------------------------
# # This version has the button inside a form, sometimes (eg when within
# # a table cell), this seems to be necessary.
#     return "<input type='button' onclick=\"window.location.href='{0}'\" value='{1}' />".format(click, label)
#     #return "<form><input type=button style=\"color:red\" onclick=\"window.location.href='{0}'\" value='{1}' /></form>".format(click, label)

def htmlButton(label, id=None, click=None, color='btn-primary', type='button'):
#-----------------------------------------------------------------------
# Standardized button format. Currently bootstrap.
# Could have size parameter, which is class, eg btn-lg.
# NB - malfunction is likely if there are double quotes in the click parameter.
#
    out = '<button type="{0}" class="btn {1}"'.format(type, color)
    if id is not None:
        out += ' id="{0}"'.format(id)
    if click is not None:
        out += ' onclick="{0}"'.format(click)
    out += '>{0}</button>'.format(label)
    return out


def _htmlDataTableMagic(tableId, extraOptions=''):
#----------------------------------------------------------------------------
# Html required to have a datatable table work, pass in an id to use for the table.
#
# NB this magic doesn't include the link and script imports for datatables.
# These are now in base.html. This is because we use datatables quite a lot,
# and if we imported them here, we would import multiples times if there were
# multiple tables on a page.

    # We need to initialize the jquery datatable, but also a bit of hacking
    # to set the width of the page. We use the datatables scrollX init param
    # to get a horizontal scroll on the table, but it seems very hard in css to
    # get the table to fill the available screen space and not have the right
    # hand edge invisible off to the right of the page. You can set the width
    # of the dataTables_wrapper to a fixed amount and that works, but doesn't
    # reflect the actual window size. If you set the width to 100%, it just doesn't
    # work - partly it seems because we are using css tables (i.e. if I try the
    # same code NOT in these tables 100% does work. So we are doing here at the moment
    # is to (roughly) set the <tableId>_wrapper width to the appropriate size
    # after the datatable is initialized and hook up a handler to redo this whenever
    # the screen is resized. Not very nice or future proof, but it will have to do for
    # the moment..
    #
    # MFK 26/11/14: I've replaced the resize function, which was a call to setTableWrapperWidth()
    # to be instead just a reload. This works better, setTableWrapperWidth() was centering the table
    # rows without also centering the table headers. Hopefully the the reload is coming from the
    # cache rather than the network.
    #
    # NB <tableId>_wrapper is the id of a div surrounding the table (with id tableId) created
    # by the dataTable function.

    r = """
    <script>
    jQuery(
        function() {
            var elId = "#%s"

            function setTableWrapperWidth() {
                var setWidthTo = Math.round($(".fpHeader").width() - 40);
                document.getElementById('%s_wrapper').style.width = setWidthTo + 'px';
                $(elId).dataTable().fnAdjustColumnSizing();
            }

            $(elId).DataTable( {
                %s
                "scrollX": true,
                "scrollY": "60vh",
                "scrollCollapse": true,
                "paging": false,
                //"pageLength":100,
                "fnPreDrawCallback":function(){
                    $(elId).hide();
                },
                "fnDrawCallback":function(){
                    $(elId).show();
                },
                "fnInitComplete": function(oSettings, json) {$(elId).show();}
            });
            setTableWrapperWidth(); // This to force on table scroll bar
            window.addEventListener('resize', setTableWrapperWidth);
            /* Used to be required for nice resize, but the line above now seems to work
            * window.addEventListener('resize', function () {
            *     "use strict";
            *     window.location.reload();
            * });
            */
        }
    );
    // Needed to fix things on reload:
    // NB it only seems to be an issue for first tab
    $(window).load( function () {
        var elId = "#%s"
        $(elId).dataTable().fnAdjustColumnSizing(false);
        //$(elId).dataTable().fnDraw();
    } );
    </script>
    """ % (tableId, tableId, extraOptions, tableId)
    return r

def htmlDatatableByCol(headers, cols, tableId, showFooter=True, extraOptions=''):
#-----------------------------------------------------------------------------
# HTML for Data table with the specified headers and cols.
# The length of these lists should be the same, col[i] being the
# data values for the column with header headers[i]. Each element
# in cols should be a list, and these, ideally, would all be of
# the same length.
#
    numCols = len(headers)
    if numCols <= 0 or numCols != len(cols):
        return ''
    numRows = len(cols[0])
    r = _htmlDataTableMagic(tableId, extraOptions)
    r += '<p><table id="{0}" class="display fptable"  cellspacing="0" width="100%"  >'.format(tableId)
    hdrs = ''
    for h in headers:
        hdrs += '<th>{0}</th>'.format(h)
    r += '<thead><tr>{0}</tr></thead>'.format(hdrs)
    r += '<tfoot><tr>{0}</tr></tfoot>'.format(hdrs)
    r += '<tbody>'
    for rowIndex in range(numRows):
        r += '<tr>'
        for col in cols:
            r += '<td>{0}</td>'.format(col[rowIndex])
        r += '</tr>'
    r += '</tbody>'
    r += '</table>'
    return r

def htmlDatatableByRow(headers, rows, tableId, showFooter=True, extraOptions=''):
# HTML for Data table with the specified headers and rows.
# headers is list of column headers, rows a list of lists,
# each sublist should be same length as headers.
#
    out = _htmlDataTableMagic(tableId, extraOptions)
    out += '<p><table id="{0}" class="display fptable"  cellspacing="0" width="100%"  >'.format(tableId)
    hdrs = ''
    for h in headers:
        hdrs += '<th>{0}</th>'.format(h)
    out += '<thead><tr>{0}</tr></thead>'.format(hdrs)
    if showFooter:
        out += '<tfoot><tr>{0}</tr></tfoot>'.format(hdrs)
    out += '<tbody>'
    for row in rows:
        out += '<tr>'
        for el in row:
            out += '<td>{0}</td>'.format(el)
        out += '</tr>'
    out += '</tbody>'
    out += '</table>'
    return out

def bsRow(contents):
#-----------------------------------------------------------------------
# Return contents wrapped in a bootstrap row.
#
    return '<div class="row">' + contents + '</div>'

def bsCol(contents, size='sm', numCols=1, extra=None):
#-----------------------------------------------------------------------
# Return contents wrapped in a bootstrap column.
#
    divclass = 'col-' + size + '-' + str(numCols)
    return '<div {2}class="{0}">{1}</div>'.format(divclass, contents, '' if extra is None else ' {0} '.format(extra))

def bsSingleColumnRow(contents, topMargin=None):
#-----------------------------------------------------------------------
# Return the contents wrapped as a single column row.
# With the given topMargin (eg "20px") if specified.
#
    if topMargin is not None:
        contents = '<div style="margin-top:{};">{}</div>'.format(topMargin, contents)
    col = bsCol(contents)
    return bsRow(col)

    
    
