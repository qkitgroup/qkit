from qkit.storage.store import Data
from qkit.storage.hdf_dataset import hdf_dataset
from qkit.measure.json_handler import QkitJSONEncoder
import pathlib, typing, json
import pandas as pd

p = pathlib.Path(r"C:\Users\Marius Frohn\Desktop\Qrious\Messungen\ForgeLogs\SPC_TitaniumTest_JH.csv")

ALIAS: dict[str,str] = {
    "synthesium/m600dc/m600dc1_spc/actualCurrent": "dc_sputter_i",
    "synthesium/m600dc/m600dc1_spc/actualVoltage":"dc_sputter_v", 
    "synthesium/m600dc/m600dc1_spc/actualPower":"dc_sputter_p",
    "synthesium/mkses/ar_20_sccm/ActualFlowSccm":"ar_mix_flow",
    "synthesium/mkses/n2/ActualFlowSccm":"n2_flow",
    "synthesium/gaugevalues/spc_bara/value":"spc_pressure_bara",
    "synthesium/gaugevalues/spc_hg/value": "spc_pressure_hg",
    "synthesium/quartzbalances/qb_spc/rate":"qb_rate",
}

def forge_log_converter(csv_path: str|pathlib.Path, override_name: None|str = None, prompt_views: bool|typing.Iterable[typing.Iterable[str, typing.Iterable[int], typing.Iterable[int]]] = True, time_fmt: typing.Literal["abs", "rel"] = "abs", move_csv: bool = True) -> None:
    """
    Turns a .csv file as generated from FORGE viewer 'Chart/Export to cvs' to a qviewkit-compatible .h5 file, stored in the data folder

    csv_path: Path to to be converted file
    override_name: Name for the new .h5 file, if None the name from the .csv is used
    prompt_views: Whether to ask for adding additional views to the file or not. Alternatively the to be added views can be given directly in the format e.g. [["flows", [0,0], [1,2]],...] ordered by csv column number
    time_fmt: Whether time axis is stored as absolute date-time or relative to start
    move_csv: Moves the parsed csv file to the data folder
    """
    # Read csv to pandas
    if type(csv_path) is str:
        csv_path = pathlib.Path(csv_path)
    with open(csv_path, encoding="utf8") as df:
        data = pd.read_csv(df)
        if time_fmt == "abs": # TODO: Infer this automatically from file?
            data["time"] = pd.to_datetime(data['time'])
            init_timestamp = data["time"][0]
            data["time"] = ((data["time"] - init_timestamp) // pd.Timedelta("1ns"))*1e-9
        else:
            init_timestamp = False
    
    # Make new file
    if override_name is None:
        override_name = csv_path.stem
    data_file = Data(override_name, "a")
    settings = data_file.add_textlist("settings")
    if init_timestamp:
        settings.append(json.dumps(obj={"Logging start time":str(init_timestamp)}, cls=QkitJSONEncoder, indent=4, sort_keys=True))
    # TODO: Figure out a way to prompt full forge init-state, then add it similarily

    # Dump pd data into qkit file
    time_ax = data_file.add_coordinate("time", "s")
    time_ax.add(data["time"])
    ax_dict: dict[str,hdf_dataset] = {"time":time_ax}

    col: str
    for col in data:
        if col == "time":
            continue
        try:
            val_name = ALIAS[col.split("[")[0][:-1]]
        except KeyError:
            print(f"'{col.split("[")[0][:-1]}' not found in aliases dict, feel free to add it in the source code. Defaulting to forge device name")
            val_name = "{}_{}_{}".format(*col.split("[")[0][:-1].split("/")[-3:])
        data_ax = data_file.add_value_vector(val_name, time_ax, col.split("[")[-1][:-1])
        data_ax.append(data[col])
        ax_dict[val_name] = data_ax

    # Add views
    if type(prompt_views) == bool:
        if prompt_views:
            print("You can now add views to the .h5 file for conveniently plotting your parameters in qviewkit. The format is 'view_name:x1,x2,...:y1,y2,...' for each to be added window. x1 etc. is a number from the following list. When you're done, enter an empty line.")
            for i, k in enumerate(ax_dict.keys()):
                print(f"{i}: {k}")
            prompt_views = []
            while True:
                rb = input()
                if rb == "":
                    break
                try:
                    buf = rb.split(":")
                    buf[1] = [int(v) for v in buf[1].split(",")]
                    buf[2] = [int(v) for v in buf[2].split(",")]
                    prompt_views += [buf]
                except:
                    print("Invalid format, try again")
        else:
            prompt_views = []
    for view_info in prompt_views:
        view = data_file.add_view(view_info[0], ax_dict[list(ax_dict.keys())[view_info[1][0]]], ax_dict[list(ax_dict.keys())[view_info[2][0]]])
        for i in range(1, len(view_info[1])):
            view.add(ax_dict[list(ax_dict.keys())[view_info[1][i]]], ax_dict[list(ax_dict.keys())[view_info[2][i]]])

    # Cleanup
    if move_csv:
        csv_path = csv_path.move_into(data_file.get_folder())
        csv_path.rename(csv_path.with_stem(data_file._uuid + "_" + csv_path.stem))
    data_file.close_file()