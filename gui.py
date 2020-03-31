import datetime

import pandas as pd
from bokeh.io import curdoc
from bokeh.layouts import column, row, grid
from bokeh.models import ColumnDataSource, DataRange1d, Select
from bokeh.server.server import Server
from bokeh.models.widgets import Div
from bokeh.models.widgets import Button
from bokeh.models.widgets import TextInput
from bokeh.models.widgets import PreText


def test(doc):
    # Create Input controls
    title = PreText(text='SATP')
    satp_bits = [Div(text='<b>31</b>', align='start'), Div(text='<b>31</b>', align='end'), Div(text='<b>30</b>', align='start'), Div(text='<b>22</b>', align='end'), Div(text='<b>21</b>', align='start'), Div(text='<b>0</b>', align='end')]
    satp_bits_texts = {'0 Bare': ['<b>31</b>', '<b>31</b>', '<b>30</b>', '<b>22</b>', '<b>21</b>', '<b>0</b>'],
                       '1 SV32(RV32)': ['<b>31</b>', '<b>31</b>', '<b>30</b>', '<b>22</b>', '<b>21</b>', '<b>0</b>'],
                       '8 SV39(RV64)': ['<b>63</b>', '<b>60</b>', '<b>59</b>', '<b>44</b>', '<b>43</b>', '<b>0</b>'],
                       '9 SV48(RV64)': ['<b>63</b>', '<b>60</b>', '<b>59</b>', '<b>44</b>', '<b>43</b>', '<b>0</b>']}
    satp_sizes = [Div(text='<b>1</b>', align='center'), Div(text='<b>9</b>',align='center'), Div(text='<b>22</b>', align='center')]
    satp_sizes_texts = {'0 Bare': ['<b>1</b>', '<b>9</b>', '<b>22</b>'],
                       '1 SV32(RV32)': ['<b>1</b>', '<b>9</b>', '<b>22</b>'],
                       '8 SV39(RV64)': ['<b>4</b>', '<b>16</b>', '<b>44</b>'],
                       '9 SV48(RV64)': ['<b>4</b>', '<b>16</b>', '<b>44</b>']}

    mode = Select(value="1 SV32(RV32)", options=['0 Bare', '1 SV32(RV32)', '8 SV39(RV64)', '9 SV48(RV64)'])
    asid = Button(label="ASID", disabled=True)
    ppn = TextInput()

    page_size_options = {'0 Bare': [],
                         '1 SV32(RV32)': ['4Kb', '4Mb'],
                         '8 SV39(RV64)': ['4Kb', '2Mb', '1Gb'],
                         '9 SV48(RV64)': ['4Kb', '2Mb', '1Gb', '512Gb']}
    page_size = Select(title='Page Size',value="4Kb", options=page_size_options[mode.value])
    # add_page = Button(label='+', margin=24)
    # align, aspect_ratio, background, button_type, callback, clicks, css_classes, default_size, disabled, height, height_policy, \
    # icon, js_event_callbacks, js_property_callbacks, label, margin, max_height, max_width, min_height, min_width, name, \
    # orientation, sizing_mode, subscribed_events, tags, visible, width or width_policy
    # ERR

    # update labels and values
    def update_titles(attrname, old, new):
        for value, c in zip(satp_bits_texts[mode.value], satp_bits):
            c.text = value
        for value, c in zip(satp_sizes_texts[mode.value], satp_sizes):
            c.text = value
        page_size.options = page_size_options[mode.value]

    mode.on_change('value', update_titles)

    # SATP register control
    SATP_controls = column(title, grid([satp_bits, [mode, asid, ppn], satp_sizes]))
    SATP_controls.background = '#66B2FF'
    SATP_controls.margin = 10

    # page size control
    controls = row(page_size)
    controls.background = 'green'
    controls.margin = 10

    doc.add_root(column(SATP_controls, controls))
    doc.title = "Risc-V Hackathon"


# Setting num_procs here means we can't touch the IOLoop before now, we must
# let Server handle that. If you need to explicitly handle IOLoops then you
# will need to use the lower level BaseServer class.
server = Server({'/': test}, num_procs=1)
server.start()

if __name__ == '__main__':
    print('Opening Bokeh application on http://localhost:5006/')

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()



# # Enum('aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond',
    #      'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue',
    #      'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkgrey',
    #      'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon',
    #      'darkseagreen', 'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise', 'darkviolet', 'deeppink',
    #      'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia',
    #      'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow', 'grey', 'honeydew', 'hotpink',
    #      'indianred', 'indigo', 'ivory', 'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue',
    #      'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgray', 'lightgreen', 'lightgrey', 'lightpink',
    #      'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightslategrey', 'lightsteelblue',
    #      'lightyellow', 'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue',
    #      'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise',
    #      'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite', 'navy', 'oldlace',
    #      'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise',
    #      'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum', 'powderblue', 'purple', 'red', 'rosybrown',
    #      'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue',
    #      'slateblue', 'slategray', 'slategrey', 'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato',
    #      'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen'), Regex(
    #     '^#[0-9a-fA-F]{6}$'), Regex(
    #     '^rgba\\(((25[0-5]|2[0-4]\\d|1\\d{1,2}|\\d\\d?)\\s*,\\s*?){2}(25[0-5]|2[0-4]\\d|1\\d{1,2}|\\d\\d?)\\s*,\\s*([01]\\.?\\d*?)\\)'), Regex(
    #     '^rgb\\(((25[0-5]|2[0-4]\\d|1\\d{1,2}|\\d\\d?)\\s*,\\s*?){2}(25[0-5]|2[0-4]\\d|1\\d{1,2}|\\d\\d?)\\s*?\\)'), Tuple(
    #     Byte(Int, 0, 255), Byte(Int, 0, 255), Byte(Int, 0, 255)), Tuple(Byte(Int, 0, 255), Byte(Int, 0, 255),
    #                                                                     Byte(Int, 0, 255), Percent) or RGB, got
    #'0x66B2FF'