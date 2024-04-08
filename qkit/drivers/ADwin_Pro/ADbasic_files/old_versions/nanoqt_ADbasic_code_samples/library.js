/*
 * JavaScript library for NanoQt.
 */


/***********************************************************************
 * General purpose functions.
 */

/*
 * Polyfill for Function.prototype.bind.
 *
 * Among the ES5 additions to JavaScript not implemented in Qt 4.8.1,
 * this is arguably the most useful. The simple implementation below
 * should work for plain functions, but *not* for constructors.
 */
if (!Function.prototype.bind)
    Function.prototype.bind = function(thisObj) {
        var func = this,
            slice = Array.prototype.slice,
            bound_args = slice.call(arguments, 1);
        return function() {
            var args = bound_args.concat(slice.call(arguments));
            return func.apply(thisObj, args);
        };
    };

/*
 * Amend Date.parse() to accept the ISO 8601 format produced by
 * Date.prototype.toISOString, as required by ECMAScript 5. If the
 * provided string does not match the format, fall back to the
 * original Date.parse implementation.
 *
 * Note that this implementation is not fully conformant with
 * ECMAScript 5, as that standard requires support of shortened forms
 * where some fields can be missing, as well as arbitrary time zones.
 */
(function() {
    const original_Date_parse = Date.parse,
          iso_format = /^(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)\.(\d+)Z$/;
    if (Date.parse("1970-01-01T00:00:00.000Z") != 0)
        Date.parse = function(s) {
            var tokens = s.match(iso_format);
            if (!tokens) return original_Date_parse(s);
            var d = new Date(0);
            d.setUTCFullYear(tokens[1]);
            d.setUTCMonth(tokens[2]-1);
            d.setUTCDate(tokens[3]);
            d.setUTCHours(tokens[4]);
            d.setUTCMinutes(tokens[5]);
            d.setUTCSeconds(tokens[6]);
            d.setUTCMilliseconds(tokens[7]);
            return d.getTime();
        };
})();

/* Export Math properties to the global object. */
Object.getOwnPropertyNames(Math).forEach(
    function(k){ this[k] = Math[k]; }, this);
function sq(x) { return x*x; }

/* Recursively copy an object by value. */
function deep_copy(a)
{
    if (typeof a != "object") return a;
    var b = new a.constructor;
    for (var i in a) b[i] = deep_copy(a[i]);
    return b;
}


/***********************************************************************
 * Loadable modules.
 *
 * This is a module system inspired by CommonJS and Node.js.
 */

/*
 * Modules required with no path (no '/' in the name) are searched in
 * the nanoqt_modules directories, then in this path.
 */
const _default_module_path = [];

/*
 * Resolve a module name using base_dir as the base directory for
 * relative paths. Returns a File object or null if the module is not
 * found.
 */
function _resolve(name, base_dir)
{
    // Build the list of directories to search.
    var module_path = [];
    if (name[0] == "/") {  // starts with '/': absolute path
        module_path.push("/");
    } else if (name.match(/\//)) {  // contains a '/': relative path
        module_path.push(base_dir);
    } else {  // no path
        var parts = base_dir.split("/");
        while (parts.length) {
            if (parts[parts.lengt-1] == "nanoqt_modules")
                continue;
            module_path.push(parts.join("/") + "/nanoqt_modules");
            parts.pop();
        }
        module_path = module_path.concat(_default_module_path);
    }

    // File extensions to append.
    const extensions = ["", ".js", "/index.js"];

    for (var i = 0; i < module_path.length; i++) {
        var basename = module_path[i] + "/" + name;
        basename = basename.replace(/\/+/g, "/");  // '//' -> '/'
        for (var j = 0; j < extensions.length; j++) {
            var f = new File(basename + extensions[j]);
            if (f.isFile)
                return f;
        }
    }
    return null;  // module not found
}

/*
 * This should be bound as a method of the current module.
 */
function _require(name)
{
    // The base directory for relative paths should be the directory
    // containing the current module or script or, if we are not
    // executing code from a file, the current working directory.
    var base_dir;

    // The module filename should be an absolute path. If it doesn't
    // contain a '/', it's a dummy name created by the editor window for
    // an unsaved script.
    var last_slash_pos = (this.filename || "").lastIndexOf("/");
    if (last_slash_pos != -1)
        base_dir = this.filename.slice(0, last_slash_pos || 1);
    else
        base_dir = Directory.current;

    // Get the required module's file.
    var f = _resolve(name, base_dir);
    if (!f)
        throw new Error("Cannot find module '" + name + "'");
    var filename = f.canonicalName;

    // Search in the cache first.
    var cached = _require_cache[filename];
    if (cached)
        return cached.exports;

    // Create a new module and cache it right away for the sake of
    // dependency cycles.
    var child_module = { exports: {}, filename: filename };
    _require_cache[filename] = child_module;

    // Load the file.
    var compiled = new Function("module", "exports", "require",
        "'use strict'; " + f.read());
    compiled(child_module, child_module.exports, _make_require(child_module));

    // Return the exported object.
    return child_module.exports;
}

/*
 * Build a require() function object suitable for the given module.
 */
function _make_require(new_module)
{
    var require = _require.bind(new_module);
    require.main = module;  // main module
    require.cache = _require_cache;
    require.resolve = _resolve;
    return require;
}

/* Global cache. */
const _require_cache = {};

/*
 * This object is bound to `module' in code executed outside any real
 * module (script code or code typed at the console). It is visible
 * everywhere as `require.main'. The expression
 *
 *   require.main === module
 *
 * is true only in non-module context.
 *
 * Within a module, `module.filename' is the canonical name of the
 * module file, i.e. the full path with symlinks resolved.
 */
const module = { exports: {}, filename: null };

const require = _make_require(module);


/***********************************************************************
 * Compatibility with old stuff.
 */

function plot2D(curve)
{
    echo("<b>Warning:</b> plot2D() is deprecated, use new Plot() instead.");
    return new Plot(curve);
}

function plot(title)
{
    echo("<b>Warning:</b> plot() is deprecated, use new Plot() instead.");
    return new Plot(title);
}

function trace_xy(plot, curve_idx, x, y)
{
    echo("<b>Warning:</b> trace_xy() is deprecated, use .add_point() instead.");
    plot.add_point(curve_idx, x, y);
}

function trace(plot, curve_idx, x, y)
{
    echo("<b>Warning:</b> trace() is deprecated, use .add_point() instead.");
    plot.add_point(curve_idx, x, y);
}

function get_data(plot, curve_idx)
{
    echo("<b>Warning:</b> get_data() is deprecated, use the method instead.");
    return plot.get_data(curve_idx);
}

function auto_xy()
{
    echo("<b>Warning:</b> auto_xy() is deprecated, use .autoscale instead.");
}

function Grapher()
{
    echo("<b>Warning:</b> Grapher() is deprecated, use Plot() instead.");
    return Plot.apply(this, arguments);
}

Grapher.find = function(title)
{
    echo("<b>Warning:</b> Grapher.find() is deprecated, "
            + "use Plot.find() instead.");
    return Plot.find(title);
}

function browser()
{
    echo("<b>Warning:</b> browser() is deprecated, "
            + "use File.choose() instead.");
    return File.choose(arguments);
}

function pwd()
{
    echo("<b>Warning:</b> pwd() is deprecated, "
            + "use Directory.current instead.");
    return Directory.current;
}

function cd(path)
{
    echo("<b>Warning:</b> cd() is deprecated, "
            + "use Directory.current = path instead.");
    return Directory.current = path;
}

function mkdir(path)
{
    echo("<b>Warning:</b> mkdir() is deprecated, "
            + "use Directory.create() instead.");
    return Directory.create(path);
}


/***********************************************************************
 * High level ADwin API.
 */

/*
 * The _adwin object has already been initialized by add_extensions()
 * with the properties:
 *     version (string) from VERSION in version.h
 *     process_frequency (number) from PROCESS_FREQUENCY in NanoQt.pro
 *     initialized (boolen) from ADwin::state().
 * plus a bunch of methods.
 */

/* Private namespace. */
_adwin.inputs = {};
_adwin.outputs = {};
_adwin.metadata = {};

_adwin.init = function() {
    if (_adwin.initialized) return;
    _adwin.boot();
    _adwin.load();
    _adwin.start();
    _adwin.initialized = true;
};

/* Initialize the acquisition process. */
_adwin.initialized_em = false;
_adwin.init_em = function() {
    if (_adwin.initialized_em) return;
    _adwin.boot();
    _adwin.load_em();
    _adwin.start();
    _adwin.initialized_em = true;
};

function init() {
    _adwin.init();
}

_adwin.filters = {
    median: 1,
    linear: 2,
    reset: 8
};

_adwin.modes = {
    "quadratic":            0x0004,
    "lock-in":              0x0010,
    "wait-trigger":         0x0020,
    "electromig":           0x0040,
    "regime_actif":         0x0100,
    "regime_cold":          0x0200,
    "regime_periodic":      0x0400,
    "regime_aperiodic":     0x0800,
    "mode_plan":            0x1000,
    "mode_feedback":        0x2000,
    "mode_reset_feedback":  0x4000,
    "mode_cold":            0x8000,
    "mode_nanosquid":      0x10000,
    "electromig_slow":     0x20000,
    "rf_trigger":          0x40000
};

_adwin.lock_in = {
    input: 8,
    output: 8,
    frequency: 1000,
    amplitude: 1,
    time_constant: .1
};

_adwin.last_outputs = {};

_adwin.find_channel = function(group, name) {
    for (var i in group)
        if (group[i].name == name) return i;
    return null;
};

/*
 * Input: columns = ["Vout", "Vin"]
 * Returns: channels = [
 *      {dir: "out", ch: 0},
 *      {dir: "in", ch:1}
 * ]
 */
_adwin.massage_columns = function(mode, input_mask, output_mask, columns)
{
    var channels = [], ch;
    for (var i in columns) {
        channels[i] = {};
        axis = channels[i];
        if (ch = _adwin.find_channel(_adwin.inputs, columns[i])) {
            axis.dir = "in";
            axis.ch = _adwin.pos_in_mask(ch, input_mask);
            if (axis.ch == -1)
                throw new Error("channel " + columns[i] + " is not read");
        }
        else if (ch = _adwin.find_channel(_adwin.outputs, columns[i])) {
            axis.dir = "out";
            axis.ch = _adwin.pos_in_mask(ch, output_mask);
            if (axis.ch == -1)
                throw new Error("channel " + columns[i] + " is not swept");
        }
        else if (mode & _adwin.modes["lock-in"] && columns[i] == "real") {
            axis.dir = "in";
            axis.ch = _adwin.bits_set(input_mask);
        }
        else if (mode & _adwin.modes["lock-in"] && columns[i] == "imag") {
            axis.dir = "in";
            axis.ch = _adwin.bits_set(input_mask) + 1;
        }
        else throw new Error("channel " + columns[i] + " not found");
    }
    return channels;
}

/* Convert a sweep descriptor into a low level Sweep. */
_adwin.massage_sweep = function(s) {

    // mode
    var mode = 0;
    var filters = s.filters || [];
    if (!(filters instanceof Array)) filters = [filters];
    for (var i = 0; i < filters.length; i++) {
        if (!_adwin.filters[filters[i]])
            throw new Error("No filter named " + filters[i]);
        mode |= _adwin.filters[filters[i]];
    }
    var modes = s.modes || [];
    if (!(modes instanceof Array)) modes = [modes];
    for (var i = 0; i < modes.length; i++) {
        if (!_adwin.modes[modes[i]])
            throw new Error("No mode named " + modes[i]);
        mode |= _adwin.modes[modes[i]];
    }

    // input_mask
    var ins = s.inputs || [];
    if (!(ins instanceof Array)) ins = [ins];
    var input_mask = 0;
    for (i = 0; i < ins.length; i++) {
        var ch = _adwin.find_channel(_adwin.inputs, ins[i]);
        if (!ch)
            throw new Error("Input channel " + ins[i] + " not found");
        input_mask |= 1 << ch - 1;
    }

    // nb_steps
    var duration;
    if (s.speed) {
        if (s.duration)
            throw new Error("Both speed and duration in the same sweep");

        var distance = 0;
        for (var channel in (s.outputs || {})) {
            var output_start = _adwin.last_outputs[channel] || 0;
            distance += sq(s.outputs[channel] - output_start);
        }
        distance = sqrt(distance);

        duration = distance / s.speed;
    }
    else
        duration = s.duration || 1;   // default 1 s
    var nb_steps = duration * _adwin.process_frequency;
    if (nb_steps < 1) nb_steps = 1;

    // subsampling
    var sample_rate = s.sample_rate || 1000;    // default 1 kHz
    if (sample_rate > _adwin.process_frequency)
        sample_rate = _adwin.process_frequency;
    var subsampling = _adwin.process_frequency / sample_rate;

    // label
    var label = s.label;

    // create Sweep
    var sweep;
    if (label !== undefined)
        sweep = new Sweep(mode, input_mask, nb_steps, subsampling, label);
    else
        sweep = new Sweep(mode, input_mask, nb_steps, subsampling);

    // outputs
    var outputs = s.outputs || {};
    var output_mask = 0;
    var all_channels = [];
    for (var channel in outputs) {
        all_channels.push(channel);
        var ch = _adwin.find_channel(_adwin.outputs, channel);
        if (!ch)
            throw new Error("Output channel " + channel + " not found");
        var target = outputs[channel];
        if (!isFinite(target))
            throw new Error("Invalid sweep target: " + target);
        sweep.add_target(ch, target);
        output_mask |= 1 << ch - 1;
    }
    all_channels = all_channels.concat(ins);

    // variable
    var variable = s.variable || [];
    if (!(variable instanceof Array)) variable = [variable];
    for (i = 0; i < variable.length; i++) {
        if (variable[i].name && variable[i].reference)
            throw new Error("variable field has both name and reference");
        var var_ref = variable[i].name || variable[i].reference;
        if (!var_ref)
            throw new Error("No name nor reference in variable field");

        var sink, metadata;
        if (variable[i].metadata) metadata = deep_copy(variable[i].metadata);
        else metadata = {};
        metadata._global = _adwin.metadata;
        metadata.sweep = {
            from: deep_copy(_adwin.last_outputs),
            to: s.outputs,
            duration: duration,
            sample_rate: s.sample_rate
        };
        if (s.speed) metadata.sweep.speed = s.speed;
        else if (s.duration) metadata.sweep.duration = s.duration;
        var columns = variable[i].columns || all_channels;
        if (!columns) throw new Error("no columns in variable");
        if (variable[i].transform && variable[i].output)
            metadata.columns = variable[i].output;
        else
            metadata.columns = columns;
        var channels = _adwin.massage_columns(mode, input_mask,
                output_mask, columns);

        sink = new VarDataSink(var_ref, metadata);
        sink.set_channels(channels);
        if (variable[i].filter) {
            if (variable[i].filter_init)
                sink.set_filter(variable[i].filter, variable[i].filter_init);
            else
                sink.set_filter(variable[i].filter);
        }
        if (variable[i].transform) sink.set_transform(variable[i].transform);
        sweep.add_data_sink(sink);
    }

    // save
    var save = s.save || [];
    if (!(save instanceof Array)) save = [save];
    for (i = 0; i < save.length; i++) {
        if (!save[i].filename) throw new Error("No filename in save field");

        var sink, metadata;
        if (save[i].metadata) metadata = deep_copy(save[i].metadata);
        else metadata = {};
        metadata._global = _adwin.metadata;
        metadata.sweep = {
            from: deep_copy(_adwin.last_outputs),
            to: s.outputs,
            duration: duration,
            sample_rate: s.sample_rate
        };
        if (s.speed) metadata.sweep.speed = s.speed;
        else if (s.duration) metadata.sweep.duration = s.duration;
        var columns = save[i].columns || all_channels;
        if (!columns) throw new Error("no columns in save");
        if (save[i].transform && save[i].output)
            metadata.columns = save[i].output;
        else
            metadata.columns = columns;
        var channels = _adwin.massage_columns(mode, input_mask,
                output_mask, columns);

        if (save[i].format == "ubjson")
            sink = new UBJSON.DataSink(save[i].filename,
                    nb_steps / subsampling,
                    metadata.columns.length,
                    metadata);
        else
            sink = new FileDataSink(save[i].filename, metadata);
        sink.set_channels(channels);
        if (save[i].filter) {
            if (save[i].filter_init)
                sink.set_filter(save[i].filter, save[i].filter_init);
            else
                sink.set_filter(save[i].filter);
        }
        if (save[i].transform) sink.set_transform(save[i].transform);
        sweep.add_data_sink(sink);
    }

    // tsv
    var tsv = s.tsv || [];
    var out_columns;
    if (!(tsv instanceof Array)) tsv = [tsv];
    for (i = 0; i < tsv.length; i++) {
        if (!tsv[i].filename) throw new Error("No filename in tsv field");

        var sink;
        var columns = tsv[i].columns || all_channels;
        if (!columns) throw new Error("no columns in tsv");
        if (tsv[i].transform && tsv[i].output)
            out_columns = tsv[i].output;
        else
            out_columns = columns;
        var channels = _adwin.massage_columns(mode, input_mask,
                output_mask, columns);

        var prelude = tsv[i].prelude != undefined ? tsv[i].prelude :
                      "# " + out_columns.join("\t") + "\n";
        var postlude = tsv[i].postlude != undefined ? tsv[i].postlude : "\n";
        sink = new TsvDataSink(tsv[i].filename, prelude, postlude);
        sink.set_channels(channels);
        if (tsv[i].filter) {
            if (tsv[i].filter_init)
                sink.set_filter(tsv[i].filter, tsv[i].filter_init);
            else
                sink.set_filter(tsv[i].filter);
        }
        if (tsv[i].transform) sink.set_transform(tsv[i].transform);
        sweep.add_data_sink(sink);
    }

    // gnuplot
    var gnuplot = s.gnuplot || [];
    if (!(gnuplot instanceof Array)) gnuplot = [gnuplot];
    var sink;
    for (i = 0; i < gnuplot.length; i++) {
        var plot_ref = gnuplot[i].plot || gnuplot[i].name;
        if (!plot_ref) throw new Error("No plot nor name in gnuplot");
        if (!gnuplot[i].axes) throw new Error("No axes in gnuplot");
        if (!(gnuplot[i].axes instanceof Array))
            throw new Error("gnuplot axes field should be an array");
        if (gnuplot[i].axes.length != 2)
            throw new Error("gnuplot should have two axes");
        var columns;
        if (gnuplot[i].transform && gnuplot[i].columns)
            columns = gnuplot[i].columns;
        else
            columns = gnuplot[i].axes;
        var channels = _adwin.massage_columns(mode, input_mask,
                output_mask, columns);
        var sink = new GnuPlotDataSink(plot_ref, gnuplot[i].axes,
                gnuplot[i].new_curve ? true : false);
        sink.set_channels(channels);
        if (gnuplot[i].filter) {
            if (gnuplot[i].filter_init)
                sink.set_filter(gnuplot[i].filter, gnuplot[i].filter_init);
            else
                sink.set_filter(gnuplot[i].filter);
        }
        if (gnuplot[i].transform) sink.set_transform(gnuplot[i].transform);
        sweep.add_data_sink(sink);
    }

    // plot
    var plot = s.plot || [];
    if (!(plot instanceof Array)) plot = [plot];
    if (s.grapher) {
        echo("<b>Warning:</b> grapher is deprecated, use plot instead.");
        var grapher = s.grapher;
        if (!(grapher instanceof Array)) grapher = [grapher];
        plot = plot.concat(grapher);
    }
    var sink;
    for (i = 0; i < plot.length; i++) {
        var plot_ref = plot[i].plot || plot[i].name;
        if (!plot_ref) throw new Error("No plot nor name in plot");
        if (!plot[i].axes) throw new Error("No axes in plot");
        if (!(plot[i].axes instanceof Array))
            throw new Error("plot axes field should be an array");
        if (plot[i].axes.length != 2)
            throw new Error("plot should have two axes");
        var columns;
        if (plot[i].transform && plot[i].columns)
            columns = plot[i].columns;
        else
            columns = plot[i].axes;
        var options = plot[i].options || null;
        var channels = _adwin.massage_columns(mode, input_mask,
                output_mask, columns);
        var sink = new PlotDataSink(plot_ref, plot[i].axes,
                plot[i].new_curve ? true : false, options);
        sink.set_channels(channels);
        if (plot[i].filter) {
            if (plot[i].filter_init)
                sink.set_filter(plot[i].filter, plot[i].filter_init);
            else
                sink.set_filter(plot[i].filter);
        }
        if (plot[i].transform) sink.set_transform(plot[i].transform);
        sweep.add_data_sink(sink);
    }

    // density_plot
    var density_plot = s.density_plot || [];
    if (!(density_plot instanceof Array)) density_plot = [density_plot];
    var sink;
    for (i = 0; i < density_plot.length; i++) {
        var density_plot_ref = density_plot[i].plot || density_plot[i].name;
        if (!density_plot_ref) throw new Error("No plot nor name in density_plot");
        if (!density_plot[i].axes) throw new Error("No axes in density_plot");
        if (!(density_plot[i].axes instanceof Array))
            throw new Error("density_plot axes field should be an array");
        if (density_plot[i].axes.length != 3)
            throw new Error("density_plot should have two axes");
        var columns;
        if (density_plot[i].transform && density_plot[i].columns)
            columns = density_plot[i].columns;
        else
            columns = density_plot[i].axes;
        var options = density_plot[i].options || null;
        var channels = _adwin.massage_columns(mode, input_mask,
                output_mask, columns);
        var sink = new DensityPlotDataSink(density_plot_ref, density_plot[i].axes,
                density_plot[i].new_map ? true : false, options);
        sink.set_channels(channels);
        if (density_plot[i].filter) {
            if (density_plot[i].filter_init)
                sink.set_filter(density_plot[i].filter, density_plot[i].filter_init);
            else
                sink.set_filter(density_plot[i].filter);
        }
        if (density_plot[i].transform) sink.set_transform(density_plot[i].transform);
        sweep.add_data_sink(sink);
    }

	// voxel_plot
    var voxel_plot = s.voxel_plot || [];
    if (!(voxel_plot instanceof Array)) voxel_plot = [voxel_plot];
    var sink;
    for (i = 0; i < voxel_plot.length; i++) {
        var voxel_plot_ref = voxel_plot[i].plot || voxel_plot[i].name;
        if (!voxel_plot_ref) throw new Error("No plot nor name in voxel_plot");
        if (!voxel_plot[i].axes) throw new Error("No axes in voxel_plot");
        if (!(voxel_plot[i].axes instanceof Array))
            throw new Error("voxel_plot axes field should be an array");
        if (voxel_plot[i].axes.length != 4)
            throw new Error("voxel_plot should have three axes");
        var columns;
        if (voxel_plot[i].transform && voxel_plot[i].columns)
            columns = voxel_plot[i].columns;
        else
            columns = voxel_plot[i].axes;
        var options = voxel_plot[i].options || null;
        var channels = _adwin.massage_columns(mode, input_mask,
                output_mask, columns);
        var sink = new VoxelPlotDataSink(voxel_plot_ref, voxel_plot[i].axes,
                voxel_plot[i].new_map ? true : false, options);
        sink.set_channels(channels);
        if (voxel_plot[i].filter) {
            if (voxel_plot[i].filter_init)
                sink.set_filter(voxel_plot[i].filter, voxel_plot[i].filter_init);
            else
                sink.set_filter(voxel_plot[i].filter);
        }
        if (voxel_plot[i].transform) sink.set_transform(voxel_plot[i].transform);
        sweep.add_data_sink(sink);
    }

    // update _adwin.last_outputs once no more errors can happen
    for (var channel in outputs)
        _adwin.last_outputs[channel] = outputs[channel];

    return sweep;
};

/*
 * mask = (channel 8, channel 7, ... channel 1)
 *
 * if channel not in mask, return -1;
 * else return position of channel in mask, counting only set bits,
 * from 0
 */
_adwin.pos_in_mask = function(channel, mask)
{
    var count = 0;
    if (!(mask & (1<<channel-1))) return -1;
    for (var i = 0; i < channel-1; i++)
        if (mask & (1<<i)) count++;
    return count;
}

_adwin.bits_set = function(mask)
{
    var count = 0;

    while (mask) {
        count += mask & 1;
        mask >>= 1;
    }
    return count;
}

function set_inputs(inputs)
{
    var used_odd = 0, used_even = 0;
    _adwin.init();
    for (var channel in inputs) {
        if (channel != round(channel) || channel < 1 || channel > 11)
            throw new Error("Use only input channels 1 to 11" +
                "(9 to 11 are virtual inpunts for the microSQUID).");
        if (channel <= 8) {
            if (channel % 2) used_odd++;
            else used_even++;
        }
    }
    if (_adwin.type() == "GOLD2" && (used_odd > 1 || used_even > 1))
        throw new Error(
            "At most one odd-numbered and one even-numbered input "
            + "can be used on an ADwin Gold II.");
    _adwin.inputs = inputs;
    _adwin.metadata.inputs = inputs;
    for (var channel in inputs) if (inputs[channel].scale)
        _adwin.set_in_scale(channel, inputs[channel].scale);
}

function set_inputs_em(inputs)
{
    _adwin.init_em();
    _adwin.inputs = inputs;
    _adwin.metadata.inputs = inputs;
    for (var channel in inputs) if (inputs[channel].scale)
        _adwin.set_in_scale(channel, inputs[channel].scale);
}

function set_outputs(outputs)
{
    _adwin.init();
    _adwin.outputs = outputs;
    _adwin.metadata.outputs = outputs;
    for (var channel in outputs) {
        if (outputs[channel].scale)
            _adwin.set_out_scale(channel, outputs[channel].scale);
        _adwin.last_outputs[outputs[channel].name] = 0;
    }
}

function set_outputs_em(outputs)
{
    _adwin.init_em();
    _adwin.outputs = outputs;
    _adwin.metadata.outputs = outputs;
    for (var channel in outputs) {
        if (outputs[channel].scale)
            _adwin.set_out_scale(channel, outputs[channel].scale);
        _adwin.last_outputs[outputs[channel].name] = 0;
    }
}

_adwin.update_last_outputs = function()
{
    for (var i = 0; i < arguments.length; i++) if (_adwin.outputs[i+1])
        _adwin.last_outputs[_adwin.outputs[i+1].name] = arguments[i];
}

function set_io_addresses(ain, aout)
{
    _adwin.init();
    _adwin.set_io_addresses(ain, aout);
}

function set_io_addresses_em(ain, aout)
{
    _adwin.init_em();
    _adwin.set_io_addresses(ain, aout);
}

function set_metadata(metadata)
{
    _adwin.metadata = deep_copy(metadata);
    _adwin.metadata.outputs = _adwin.outputs;
    _adwin.metadata.inputs = _adwin.inputs;
}

function measure_start(sweep_list)
{
    _adwin.init();
    if (!(sweep_list instanceof Array)) sweep_list = [sweep_list];
    for (var i = 0; i < sweep_list.length; i++) {
        var sweep = _adwin.massage_sweep(sweep_list[i]);
        _adwin.submit_path(sweep);
    }
}

function measure_start_em(sweep_list)
{
    if (!(sweep_list instanceof Array)) sweep_list = [sweep_list];
    for (var i = 0; i < sweep_list.length; i++) {
        var sweep = _adwin.massage_sweep(sweep_list[i]);
        _adwin.submit_path(sweep);
    }
}

/* measure_wait([sweep_label]) */
function measure_wait()
{
    /*
     * Pass all the arguments: like measure_wait(), _adwin.measuring()
     * can be called with either 0 or 1 argument.
     */
    while (_adwin.measuring.apply(null, arguments)) sleep(.1);
}

function measure(sweep_list)
{
    measure_start(sweep_list);
    measure_wait();
}

function measure_em(sweep_list)
{
    measure_start_em(sweep_list);
    measure_wait();
}

function set_lock_in(new_lock_in)
{
    /* Support legacy API. */
    if (arguments.length == 3)
        return set_lock_in({
            frequency:     arguments[0],
            amplitude:     arguments[1],
            time_constant: arguments[2]
        });

    if (arguments.length != 1 || typeof new_lock_in != "object")
        throw new Error("set_lock_in(): bad arguments");

    for (var prop in _adwin.lock_in)
        if (new_lock_in[prop]) _adwin.lock_in[prop] = new_lock_in[prop];

    if (typeof _adwin.lock_in.input != "number")
        _adwin.lock_in.input = Number(
                _adwin.find_channel(_adwin.inputs, _adwin.lock_in.input)
                );
    if (!(_adwin.lock_in.input >= 1 && _adwin.lock_in.input <= 8))
        throw new Error("set_lock_in: bad input channel");

    if (typeof _adwin.lock_in.output != "number")
        _adwin.lock_in.output = Number(
                _adwin.find_channel(_adwin.outputs, _adwin.lock_in.output)
                );
    if (!(_adwin.lock_in.output >= 1 && _adwin.lock_in.output <= 8))
        throw new Error("set_lock_in: bad output channel");

    _adwin.init();
    _adwin.set_lock_in(
            _adwin.lock_in.input,
            _adwin.lock_in.output,
            _adwin.lock_in.frequency,
            _adwin.lock_in.amplitude,
            _adwin.lock_in.time_constant
        );
}

function set_electro_mig(params)
{
    if (arguments.length != 1 || typeof params != "object"
            || params.R_lim == undefined
            || params.V_start == undefined)
        throw new Error("set_electro_mig(): bad arguments");

    _adwin.init();
    _adwin.set_electro_mig(params.R_lim, params.V_start);
}

function set_electromig_slow(params)
{
    if (arguments.length != 1 || typeof params != "object")
        throw new Error("set_electromig_slow(): bad arguments");

    var input = 8,
        output = 8,
        tau = params.tau || 0.1,
        dR_lim = params.dR_lim || 0.1,
        V_start = params.V_start || 1;

    if (params.input) {
        input = Number(_adwin.find_channel(_adwin.inputs, params.input));
        if (!input)
            throw new Error("set_electromig_slow(): "
                    + "could not find input channel " + params.input);
    }
    if (params.output) {
        output = Number(_adwin.find_channel(_adwin.outputs, params.output));
        if (!output)
            throw new Error("set_electromig_slow(): "
                    + "could not find output channel " + params.output);
    }

    _adwin.init();
    _adwin.set_electromig_slow(input, output, tau, dR_lim, V_start);
}

function export_data(filename, data)
{
    if (typeof data == "string") return export_data(filename, open(data));
    if (data.measures instanceof Array) data = data.measures;
    if (data instanceof Array && data[0].data) {
        for (var i = 0; i < data.length; i++)
            export_data(filename, data[i]);
        return
    }
    if (data.data) return _adwin.export_data(filename, data);
    if (data instanceof Array && data[0] instanceof Array)
        return _adwin.export_data(filename, {data: data});
}

function get_time()
{
    return new Date();
}


/***********************************************************************
 * Extensions for the plotter.
 */

Plot.properties = [
    "title", "x_label", "y_label", "current_curve", "subsampling",
    "x_min", "x_max", "y_min", "y_max", "autoscale_x",
    "autoscale_y", "logscale_x", "logscale_y", "grid", "max_ticks"
];

Plot._list = [];

Plot.open = function(filename)
{
    var obj = open(filename);
    if (obj.filetype != "NanoQt JSON plot file")
        throw Error("Bad file type.");
    var plot = new Plot();

    // Set global properties.
    for (var i = 0; i < Plot.properties.length; i++)
        plot[Plot.properties[i]] = obj[Plot.properties[i]];

    // Compatibility with old name "max_tics".
    if (obj.max_ticks === undefined && obj.max_tics !== undefined)
        plot.max_ticks = obj.max_tics;

    // Fill the curves.
    for (var i = 0; i < obj.curves.length; i++) {
        if (obj.curves[i] == null)
            plot.new_curve();                       // empty curve
        else
            plot.add_curve(obj.curves[i].data);     // curve with data
        plot.set_curve_options(i, obj.curves[i].options);
    }

    // This has to be done after populating the plot:
    if (obj.displayed_curve !== undefined)
        plot.displayed_curve = obj.displayed_curve;
    return plot;
}

Plot.prototype.add_function = function(f, n) {
    if (n === undefined) n = 1024;
    var idx = this.new_curve();
    for (var i = 0; i <= n; i++) {
        var x;
        if (this.logscale_x)
            x = this.x_min * pow(this.x_max - this.x_min, i / n);
        else
            x = this.x_min + (this.x_max - this.x_min) * (i / n);
        this.add_point(x, f(x));
    }
    return idx;
};


/***********************************************************************
 * ComboBox extensions.
 */

ComboBox.prototype.__defineGetter__("index", function() {
    return this.currentIndex;
});

ComboBox.prototype.__defineSetter__("index", function(i) {
    this.currentIndex = i;
});

// text setter implemented in C++.
ComboBox.prototype.__defineGetter__("text", function() {
    return this.currentText;
});

ComboBox.prototype.__defineSetter__("onchange", function(x) {

    // Save "onchange" without invoking the setter.
    this.__proto__ = null;
    this.onchange = x;
    this.__proto__ = ComboBox.prototype;

    // Connect the signal to its handler.
    var signal = this["currentIndexChanged(int)"];
    signal.connect(this, ComboBox._onchange_handler);
});

ComboBox._onchange_handler = function() {
    if (this.onchange) this.onchange();
};


/***********************************************************************
 * Object + Window constructor
 */

function ObjectWindow(title, description, window_color, font_color) {
    function Control(obj, name, description) {
        var widget;
        if (typeof description != "object") {
            Control.call(this, obj, name, { value: description });
            return;
        }
        switch (typeof description.value) {
        case "function":
            widget = new Button(name, function() {
                    return description.value.call(obj);
                });
            this.action = description.value;
            break;
        case "boolean":
            widget = new CheckBox(name);
            this.getter = function() {
                return widget.checked;
            };
            this.setter = function(value) {
                widget.checked = value;
            };
            break;
        case "number":
            this.label = new Label(name + ":");
            widget = new LineEdit();
            this.getter = function() {
                try {
                    var value = Number(eval(widget.text));
                    if (isFinite(value)) return value;
                    else return 0;
                } catch (err) {
                    return 0;
                }
            };
            this.setter = function(value) {
                widget.text = Number(value);
            };
            break;
        default:
            this.label = new Label(name + ":");
            widget = new LineEdit();
            this.getter = function() {
                return widget.text;
            };
            this.setter = function(value) {
                widget.text = value;
            };
        }
        this.widget = widget;
        if (this.setter) this.setter(description.value);
        if (description.read_only) widget.enabled = false;
        if (description.comment)
            this.comment = new Label(description.comment);
    }
    var ui = new Window(title);
    if (window_color)
        if (font_color)
            ui.styleSheet = "background: " + window_color + "; color: " + font_color;
        else
            ui.styleSheet = "background: " + window_color;
    var control, controls = [];
    var row = 0;
    for (var name in description) {
        control = new Control(this, name, description[name]);
        if (control.label) ui.add(control.label, row, 0);
        ui.add(control.widget, row, 1);
        if (control.comment) ui.add(control.comment, row, 2);
        if (control.getter) this.__defineGetter__(name, control.getter);
        if (control.setter) this.__defineSetter__(name, control.setter);
        if (control.action) this[name] = control.action;
        controls[row++] = control;
    }
    Object.defineProperty(this, "_window", { value: ui });
}


/***********************************************************************
 * File methods.
 */

Object.defineProperties(File, {
    isTSVLine: {
        value: function(line) {
            var pattern =
                /^[\s,]*([+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[\s,]+)+$/;
            return pattern.test(line + " ");
        }
    },
});

Object.defineProperties(File.prototype, {
    read: {
        value: function() {
            var codec = this.codec;
            if (codec == "ubjson") {
                if (!this.isOpen) this.open("read");
                return UBJSON.parse(this);
            }
            var text = this.rawRead(true);
            if (codec == "tsv") {
                var lines = text.split("\n"),
                    skip_empty = this.skipEmptyLines !== false;
                if (lines[lines.length - 1] == "") lines.pop();
                if (skip_empty) lines = lines.filter(File.isTSVLine);
                return lines.map(function(line) {
                        if (skip_empty || File.isTSVLine(line))
                            return line.split(/[\s,]/).map(Number)
                        else return [];
                    });
            }
            else if (codec == "json") return JSON.parse(text);
            else return text;
        }
    },
    readLine: {
        value: function() {
            var codec = this.codec;
            if (codec == "json" || codec == "ubjson")
                throw new Error("File:readLine() "
                        + "does not make sense on (UB)JSON");
            var line = this.rawRead(false),
                skip_empty = this.skipEmptyLines !== false;
            if (codec != "binary") line = line.replace(/\n$/, "");
            if (codec == "tsv") {
                if (skip_empty)
                    while (!File.isTSVLine(line) && !this.atEnd)
                        line = this.rawRead(false).replace(/\n$/, "");
                if (File.isTSVLine(line))
                    return line.split(/[\s,]/).map(Number);
                else return [];
            }
            else return line;
        }
    },
    write: {
        value: function(data) {
            var codec = this.codec;
            if (codec == "tsv")
                data = data.map(function(line) {
                    return line.join("\t");
                }).join("\n") + "\n";
            else if (codec == "json")
                data = JSON.stringify(data) + "\n";
            else if (codec == "ubjson") {
                if (!this.isOpen) this.open("truncate");
                UBJSON.serialize(data, this);
                return;
            }
            this.rawWrite(data);
        }
    },
    writeLine: {
        value: function(data) {
            var codec = this.codec;
            if (codec == "tsv")
                data = data.join("\t");
            else if (codec == "json")
                data = JSON.stringify(data);
            else if (codec == "ubjson") return this.write(data);
            this.rawWrite(data + "\n");
        }
    }
});
