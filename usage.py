from base64 import b64decode
import glob
import gzip
import zlib

import flask

import dash_ngl
import dash
from dash.dependencies import Input, Output, State
from dash.dash import no_update

import dash_html_components as html
import dash_core_components as dcc

f_app = flask.Flask(__name__)
app = dash.Dash(__name__, server=f_app)
app.css.config.serve_locally = True

# Preset colors for the shown molecules
color_list = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#ffff33",
    "#a65628",
    "#f781bf",
    "#999999",
]

representations = [
    "axes",
    "axes+box",
    "backbone",
    "ball+stick",
    "cartoon",
    "helixorient",
    "hyperball",
    "licorice",
    "line",
    "ribbon",
    "rope",
    "spacefill",
    "surface",
    "trace",
    "tube",
    "unitcell",
]

# PDB examples
pdbs_list = [
    "1PNK",
    "1KMQ",
    "5L73",
    "4GWM",
    "3L9P",
    "6CHG",
    "3K8P",
    "2MRU",
    "1BNA",
    "6NZK",
    "6OHW",
]

# Placeholder which is loaded if no molecule is selected
data_dict = {
    "uploaded": False,
    "selectedValue": "placeholder",
    "resetView": False,
    "chain": "ALL",
    "range": "ALL",
    "chosen": {"atoms": "", "residues": ""},
    "color": "#e41a1c",
    "filename": "placeholder",
    "ext": "",
    "config": {"type": "", "input": ""},
}


# Canvas container to display the structures
# style is only needed in the tabbed layout
component_id = "nglViewer"
viewer = html.Div(
    id="ngl-biomolecule-viewer",
    children=[dash_ngl.DashNgl(id=component_id, data=[data_dict])],
    style={
        "display": "inline-block",
        "width": "100%",
        "float": "left",
        # "marginTop": "50px",
        # "marginRight": "50px",
        "border": "1px lightgray solid",
    },
)

about_html = [
    html.H4(className="what-is", children="What is Ngl Molecule Viewer?"),
    html.P(
        "Ngl Molecule Viewer is a visualizer that allows you"
        " to view biomolecules in multiple representations."
    ),
    html.P(
        "You can select a preloaded structure, or upload your own,"
        ' in the "Data" tab. Supported formats: .pdb(.gz) / .cif(.gz) '
    ),
    html.P(
        "Additionally you can show multiple structures and (or) specify a chain/"
        " residues range / highlight Cα of chosen residues or single atoms."
    ),
    html.P(
        'In the "View" tab, you can change the style of the viewer.'
        " Like the background color, the chain colors, the render quality etc."
        " On top you can change the molecular representation."
    ),
]

data_tab = [
    html.Div(className="app-controls-name", children="Select structure"),
    dcc.Dropdown(
        id="pdb-dropdown",
        clearable=False,
        options=[{"label": k, "value": k} for k in pdbs_list],
        placeholder="Select a molecule",
    ),
    html.Br(),
    html.Div(
        children=[
            html.P(
                "Show multiple structures and (or) \
                 specify a chain/ residues range/ \
                 highlight chosen residues/ atoms",
                style={"fontSize": "10pt"},
            )
        ]
    ),
    dcc.Input(
        id="pdb-string",
        placeholder="pdbID1.chain:start-end_pdbID2.chain:start-end",
        value="6CHG.A:1-450@a50,a100,a150_3K8P.D",
        style={"width": "100%"},
    ),
    html.Br(),
    html.Button("submit", id="btn-pdbString"),
    html.Button("reset view", id="btn-resetView"),
    html.Br(),
    html.Div(
        title="Upload biomolecule to view here",
        className="app-controls-block",
        id="ngl-upload-container",
        children=[
            dcc.Upload(
                id="ngl-upload-data",
                className="control-upload",
                children=html.Div(
                    ["Drag and drop or click to upload (multiple) pdb/cif file(s).",]
                ),
                # Allow multiple files to be uploaded
                multiple=True,
            ),
            # html.Div(id='uploaded-files', children=html.Div([''])),
            html.Div(id="warning_div", children=html.Div([""])),
        ],
    ),
    html.Div(id="ngl-data-info"),
]

view_tab = [
    html.Div(
        title="select molecule style",
        className="app-controls-block",
        id="ngl-mols-style",
        children=[
            html.P("Style", style={"fontWeight": "bold", "marginBottom": "10px"},),
            dcc.Dropdown(
                id="molecules-representation-style",
                options=[{"label": e, "value": e.lower()} for e in representations],
                placeholder="select molecule style",
                value=["cartoon", "axes+box"],
                multi=True,
            ),
        ],
    ),
    html.Div(
        title="set molecules x-axis spacing",
        className="app-controls-block",
        id="ngl-mols-spacing",
        children=[
            html.P(
                "x-axis spacing", style={"fontWeight": "bold", "marginBottom": "10px"},
            ),
            dcc.Input(
                id="molecules-xaxis-spacing",
                placeholder="set x-axis spacing",
                value=100,
            ),
        ],
    ),
    html.Div(
        title="set chain color",
        className="app-controls-block",
        id="ngl-mols-color",
        children=[
            html.P(
                "Chain colors", style={"fontWeight": "bold", "marginBottom": "10px"},
            ),
            dcc.Input(id="molecules-chain-color", value=",".join(color_list)),
        ],
    ),
    html.Div(
        title="set chosen atoms color",
        className="app-controls-block",
        id="ngl-atom-color",
        children=[
            html.P(
                "Chosen atoms Color",
                style={"fontWeight": "bold", "marginBottom": "10px"},
            ),
            dcc.Input(id="chosen-atoms-color", value="#808080"),
        ],
    ),
    html.Div(
        title="set chosen atoms radius",
        className="app-controls-block",
        id="ngl-atom-radius",
        children=[
            html.P(
                "Chosen atoms radius",
                style={"fontWeight": "bold", "marginBottom": "10px"},
            ),
            dcc.Input(id="chosen-atoms-radius", value="1.1"),
        ],
    ),
    html.Div(
        title="select background color",
        className="app-controls-block",
        id="ngl-style-color",
        children=[
            html.P(
                "Background color",
                style={"fontWeight": "bold", "marginBottom": "10px"},
            ),
            dcc.Dropdown(
                id="stage-bg-color",
                options=[{"label": e, "value": e.lower()} for e in ["black", "white"]],
                value="white",
            ),
        ],
    ),
    html.Div(
        title="Camera settings",
        className="app-controls-block",
        id="ngl-selection-display",
        children=[
            html.P(
                "Camera settings", style={"fontWeight": "bold", "marginBottom": "10px"},
            ),
            dcc.Dropdown(
                id="stage-camera-type",
                options=[
                    {"label": e.capitalize(), "value": e}
                    for e in ["perspective", "orthographic"]
                ],
                value="perspective",
            ),
        ],
    ),
    html.Div(
        title="select render quality",
        className="app-controls-block",
        id="ngl-style",
        children=[
            html.P(
                "Render quality", style={"fontWeight": "bold", "marginBottom": "10px"},
            ),
            dcc.Dropdown(
                id="stage-render-quality",
                options=[
                    {"label": e, "value": e.lower(),}
                    for e in ["auto", "low", "medium", "high"]
                ],
                value="auto",
            ),
        ],
    ),
]


download_tab = [
    html.Button("Download Image", id="btn-downloadImage"),
    html.Div(
        title="antialias",
        className="app-controls-block",
        id="ngl-image-antialias",
        children=[
            html.P("antialias", style={"fontWeight": "bold", "marginBottom": "10px"},),
            dcc.Dropdown(
                id="image-antialias",
                options=[{"label": c, "value": c} for c in ["Yes", "No"]],
                value="Yes",
            ),
        ],
    ),
    html.Div(
        title="trim",
        className="app-controls-block",
        id="ngl-image-trim",
        children=[
            html.P("trim", style={"fontWeight": "bold", "marginBottom": "10px",},),
            dcc.Dropdown(
                id="image-trim",
                options=[{"label": c, "value": c} for c in ["Yes", "No"]],
                value="Yes",
            ),
        ],
    ),
    html.Div(
        title="transparent",
        className="app-controls-block",
        id="ngl-image-transparent",
        children=[
            html.P(
                "transparent", style={"fontWeight": "bold", "marginBottom": "10px"},
            ),
            dcc.Dropdown(
                id="image-transparent",
                options=[{"label": c, "value": c} for c in ["Yes", "No"]],
                value="Yes",
            ),
        ],
    ),
]


tabs = html.Div(
    id="ngl-control-tabs",
    className="control-tabs",
    children=[
        dcc.Tabs(
            id="ngl-tabs",
            value="what-is",
            children=[
                dcc.Tab(
                    label="About",
                    value="what-is",
                    children=html.Div(className="control-tab", children=about_html),
                ),
                dcc.Tab(
                    label="Data",
                    value="upload-select",
                    children=html.Div(className="control-tab", children=data_tab),
                ),
                dcc.Tab(
                    label="View",
                    value="view-options",
                    children=html.Div(className="control-tab", children=view_tab),
                ),
                dcc.Tab(
                    label="Download",
                    value="download-options",
                    children=html.Div(className="control-tab", children=download_tab),
                ),
            ],
        ),
    ],
)

# tabbed layout to show that switching tabs unmounts the dash component
viewer_tabs = html.Div(
    children=[
        dcc.Tabs(
            children=[
                dcc.Tab(label="viewer", children=viewer),
                dcc.Tab(
                    children=html.Div(
                        ['open the console you will see "component will unmount"']
                    )
                ),
            ]
        )
    ]
)


# LAYOUT
app.layout = html.Div(
    id="main-page",
    children=[
        # looses the data when the browser/tab closes.
        dcc.Store(id="uploaded-files", storage_type="session"),
        html.Div(
            id="app-page-header",
            children=[html.H1("Ngl Molecule Viewer")],
            style={"background": "#e7625f", "color": "white"},
        ),
        html.Div(
            id="app-page-content",
            children=[
                html.Div(
                    id="ngl-body",
                    className="app-body",
                    children=[
                        tabs,
                        # viewer,
                        viewer_tabs,
                        # using dcc.Loading leads to remounting with every selection change
                        # dcc.Loading(viewer),
                    ],
                ),
            ],
        ),
    ],
)


def createDict(
        selection,
        chain,
        aa_range,
        highlight_dic,
        color,
        filename,
        ext,
        contents,
        resetView=False,
        uploaded=False,
):
    print("create dic")
    print(highlight_dic)
    return {
        "filename": filename,
        "ext": ext,
        "selectedValue": selection,
        "chain": chain,
        "range": aa_range,
        "chosen": highlight_dic,
        "color": color,
        "config": {"type": "text/plain", "input": contents},
        "resetView": resetView,
        "uploaded": uploaded,
    }


def getHighlights(string, sep, atom_indicator):
    print("getHighlights")
    residues_list = []
    atoms_list = []

    str_, _str = string.split(sep)
    for e in _str.split(","):
        if atom_indicator in e:
            atoms_list.append(e.replace(atom_indicator, ""))
        else:
            residues_list.append(e)

    print(atoms_list)
    print(residues_list)
    return (str_, {"atoms": ",".join(atoms_list), "residues": ",".join(residues_list),})


# Helper function to load structures from local storage
def getLocalData(selection, pdb_id, color, uploadedFiles, resetView=False):
    print("getLocalData")

    chain = "ALL"
    aa_range = "ALL"
    highlight_dic = {"atoms": "", "residues": ""}

    highlights_sep = "@"
    atom_indicator = "a"
    # Check if only one chain should be shown
    if "." in pdb_id:
        pdb_id, chain = pdb_id.split(".")

        # Check if only a specified amino acids range should be shown:
        if ":" in chain:
            chain, aa_range = chain.split(":")

            # Check if atoms should be highlighted
            if highlights_sep in aa_range:
                aa_range, highlight_dic = getHighlights(
                    aa_range, highlights_sep, atom_indicator
                )

        else:
            if highlights_sep in chain:
                chain, highlight_dic = getHighlights(
                    chain, highlights_sep, atom_indicator
                )

    # print ('highlight_dic')
    # print (highlight_dic)

    if pdb_id not in pdbs_list:
        if pdb_id in uploadedFiles:
            print("Already uploaded")
            # print(files[:-1].split(','))
            fname = [i for i in uploadedFiles[:-1].split(",") if pdb_id in i][0]
            print(fname)

            content = ""
            return createDict(
                selection,
                chain,
                aa_range,
                highlight_dic,
                color,
                fname,
                fname.split(".")[1],
                content,
                resetView,
                uploaded=False,
            )
        return data_dict

    # get path to protein structure
    fname = [f for f in glob.glob("data/" + pdb_id + ".*")][0]

    if "gz" in fname:
        ext = fname.split(".")[-2]
        with gzip.open(fname, "r") as f:
            content = f.read().decode("UTF-8")
    else:
        ext = fname.split(".")[-1]
        with open(fname, "r") as f:
            content = f.read()

    filename = fname.split("/")[-1]

    return createDict(
        selection,
        chain,
        aa_range,
        highlight_dic,
        color,
        filename,
        ext,
        content,
        resetView,
        uploaded=False,
    )


# Helper function to load structures from uploaded content
def getUploadedData(uploaded_content):
    data = []
    uploads = []

    ext = "pdb"
    chain = "ALL"
    aa_range = "ALL"

    highlight_dic = {"atoms": "", "residues": ""}

    for i, content in enumerate(uploaded_content):
        content_type, content = str(content).split(",")

        if "gzip" in content_type:
            content = zlib.decompress(b64decode(content), zlib.MAX_WBITS | 16)
        else:
            content = b64decode(content)

        content = content.decode("UTF-8")

        pdb_id = content.split("\n")[0].split()[-1]
        if "data_" in pdb_id:
            pdb_id = pdb_id.split("_")[1]
            ext = "cif"

        print(pdb_id)
        filename = pdb_id + "." + ext
        uploads.append(filename)

        data.append(
            createDict(
                pdb_id,
                chain,
                aa_range,
                highlight_dic,
                color_list[i],
                filename,
                ext,
                content,
                resetView=False,
                uploaded=True,
            )
        )

    return data, uploads


# CB viewport
@app.callback(
    [
        Output(component_id, "data"),
        Output(component_id, "molStyles"),
        Output("pdb-dropdown", "options"),
        Output("uploaded-files", "data"),
        Output("pdb-dropdown", "placeholder"),
        Output("warning_div", "children"),
    ],
    [
        Input("pdb-dropdown", "value"),
        Input("ngl-upload-data", "contents"),
        Input("btn-pdbString", "n_clicks"),
        Input("btn-resetView", "n_clicks"),
        Input("molecules-representation-style", "value"),
    ],
    [
        State("pdb-string", "value"),
        State("pdb-dropdown", "options"),
        State("uploaded-files", "data"),
        State("molecules-chain-color", "value"),
        State("chosen-atoms-color", "value"),
        State("chosen-atoms-radius", "value"),
        State("molecules-xaxis-spacing", "value"),
    ],
)
def display_output(
        selection,
        uploaded_content,
        pdbString_clicks,
        resetView_clicks,
        molStyles_list,
        pdbString,
        dropdown_options,
        files,
        colors,
        chosenAtomsColor,
        chosenAtomsRadius,
        molSpacing_xAxis,
):
    print("selection,pdbString_clicks,pdbString,type uploaded_content", "files")
    print(
        selection,
        molStyles_list,
        pdbString_clicks,
        pdbString,
        type(uploaded_content),
        type(files),
    )

    input_id = None
    options = dropdown_options
    colors_list = colors.split(",")
    # files = files['props']['children'] if isinstance(files, dict) else ''.join(files)
    # print('files', files)

    # Give a default data dict if no files are uploaded
    files = files or {"uploaded": []}
    print("files", files)

    ctx = dash.callback_context
    if ctx.triggered:
        input_id = ctx.triggered[0]["prop_id"].split(".")[0]

    print("triggered", input_id)

    molStyles_dict = {
        "representations": molStyles_list,
        "chosenAtomsColor": chosenAtomsColor,
        "chosenAtomsRadius": float(chosenAtomsRadius),
        "molSpacing_xAxis": float(molSpacing_xAxis),
    }

    if input_id is None:
        return [data_dict], molStyles_dict, options, files, no_update, no_update

    if input_id == "pdb-dropdown":
        print("dropdown changed")
        pdb_id = selection

        uploaded_files = files["uploaded"]
        if pdb_id in ",".join(uploaded_files):
            print("Already uploaded")
            # print(files[:-1].split(','))
            fname = [e for e in uploaded_files if pdb_id in e][0]
            # fname = [i for i in files[:-1].split(',') if pdb_id in i][0]
            print(fname)

            content = ""
            chain = "ALL"
            aa_range = "ALL"
            highlight_dic = {"atoms": "", "residues": ""}

            return (
                [
                    createDict(
                        pdb_id,
                        chain,
                        aa_range,
                        highlight_dic,
                        colors_list[0],
                        fname,
                        fname.split(".")[1],
                        content,
                        resetView=False,
                        uploaded=False,
                    )
                ],
                molStyles_dict,
                options,
                files,
                no_update,
                no_update,
            )

        print("HERE")
        data = [getLocalData(selection, pdb_id, color_list[0], files, resetView=False)]
        return data, molStyles_dict, options, files, no_update, no_update

    # TODO submit and reset view in one button
    # reset view/submit is triggered two times when the mol style is changed
    if input_id in ["btn-pdbString", "btn-resetView"]:
        warning = ""

        if pdbString is None:
            return no_update, no_update, no_update, no_update, no_update, no_update

        resetView = False
        if input_id == "btn-resetView":
            resetView = True

        data = []
        if len(pdbString) > 3:
            pdb_id = pdbString
            if "_" in pdbString:
                for i, pdb_id in enumerate(pdbString.split("_")):
                    if i <= len(colors_list) - 1:
                        data.append(
                            getLocalData(
                                pdbString,
                                pdb_id,
                                color_list[i],
                                files,
                                resetView=resetView,
                            )
                        )
                    else:
                        data.append(data_dict)
                        warning = "more molecules selected as chain colors defined \
                                   either remove one molecule or add a extra color in the view tab \
                                   and reset view before submitting it again."
                        return data, no_update, options, files, no_update, warning
            else:
                data.append(
                    getLocalData(
                        pdbString, pdb_id, color_list[0], files, resetView=resetView
                    )
                )
        else:
            data.append(data_dict)

        return data, molStyles_dict, options, files, "Select a molecule", warning

    if input_id == "ngl-upload-data":
        data, uploads = getUploadedData(uploaded_content)

        for pdb_id, ext in [e.split(".") for e in uploads]:
            if pdb_id not in [e["label"] for e in options]:
                options.append({"label": pdb_id, "value": pdb_id})
                fname = pdb_id + "." + ext
                print("uploaded", pdb_id)
                # files += pdb_id + '.' + ext + ','

                if fname not in files["uploaded"]:
                    files["uploaded"].append(fname)

        return data, molStyles_dict, options, files, pdb_id, no_update

    if input_id == "molecules-representation-style":
        return no_update, molStyles_dict, no_update, no_update, no_update, no_update


# CB change molecule representation
@app.callback(
    Output(component_id, "stageParameters"),
    [
        Input("stage-bg-color", "value"),
        Input("stage-camera-type", "value"),
        Input("stage-render-quality", "value"),
    ],
)
def update_stage(bgcolor, camera_type, quality):
    return {
        "backgroundColor": bgcolor,
        "cameraType": camera_type,
        "quality": quality,
    }


# CB download Image
bool_dict = {"Yes": True, "No": False}


@app.callback(
    [Output(component_id, "downloadImage"), Output(component_id, "imageParameters")],
    [Input("btn-downloadImage", "n_clicks")],
    [
        State("image-antialias", "value"),
        State("image-trim", "value"),
        State("image-transparent", "value"),
    ],
)
def download_image(n_clicks, antialias, trim, transparent):
    if n_clicks is None:
        return False, no_update

    ctx = dash.callback_context
    return (
        bool(ctx.triggered),
        {
            "antialias": bool_dict[antialias],
            "trim": bool_dict[trim],
            "transparent": bool_dict[transparent],
            "defaultFilename": "output",
        },
    )


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=8051, debug=True, use_reloader=False)
