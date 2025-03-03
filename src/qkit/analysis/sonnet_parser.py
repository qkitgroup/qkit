import numpy as np
import logging
import collections

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("FileParser")


def _parse_parameter_line(line) -> dict[str, float]:
    """
    Takes the line and splits it by spaces. All asignments at the end are taken as parameters.
    """
    parameter_definition = line.split(' ')
    parameter_definition.reverse()
    params = {}
    for candidate in parameter_definition:
        if not '=' in candidate:
            # This is the first non-assignment, starting from the back.
            # This indicates we went through all the assignments and can stop.
            break
        split = candidate.split('=')
        params[split[0]] = float(split[1])
    return params

def _test_parse_parameter_line():
    log.info("Testing _parse_parameter_line")
    test_case = "/home/thilo/nextcloud/Projekt-Promotion/samples/v11-Simulation-update-freq/v11-5-simulation-hot-coupling.son DE_EMBEDDED L=81.5 L2=94.0"
    result = _parse_parameter_line(test_case)
    assert result == {"L": 81.5, "L2": 94.0}, f"Expected {result} to be {{'L': 81.5, 'L2': 94.0}}"

def _parse_data_line(line):
    """
    A data line is a comma separated list of floats.
    """
    return [float(segement) for segement in line.split(',')]

def _test_data_line_parsing():
    log.info("Testing _parse_data_line")
    test_case = "4.82,3.42233e-05"
    result = _parse_data_line(test_case)
    assert result == [4.82, 3.42233e-05], f"Expected {result} to be [4.82, 3.42233e-05]"

def parse_file_lines(lines, optimize_length=False):
    parsing_data = False # We have a simple binary state machine here.
    parameters = []
    # All the data across all parameters
    frequencies = []
    amplitudes = []

    block_frequencies = []
    block_amplitudes = []

    lines_iterator = iter(lines)
    while True:
        try:
            line = next(lines_iterator).strip()
        except StopIteration:
            break
        if not line:
            continue
        if parsing_data:
            try:
                # We are currently parsing data. Try to parse the line as data.
                data = _parse_data_line(line)
                block_frequencies.append(data[0])
                block_amplitudes.append(data[1])
            except ValueError:
                # If parsing as data failed, we are done with the data block.
                parsing_data = False
                # Append to total data
                frequencies.append(block_frequencies)
                amplitudes.append(block_amplitudes)
                log.debug(f"Found data block with {len(block_frequencies)} points")
                # Reset block data
                block_frequencies = []
                block_amplitudes = []
                # Drop down to not parsing data
        
        if not parsing_data:
            header = _parse_parameter_line(line)
            parameters.append(header)
            log.debug(f"Found parameter {header}")
            # Skip the table head
            next(lines_iterator)
            parsing_data = True
    
    # After parsing the file, append the data from the last block.
    frequencies.append(block_frequencies)
    amplitudes.append(block_amplitudes)

    # Sometimes Sonnet is weird and has different lengths for the data. Clean it up.
    if optimize_length:
        # Determine most common line length
        lengths = [len(f) for f in frequencies]
        most_common_length = max(set(lengths), key=lengths.count)
        # Remove all lines that do not have the most common length
        frequencies = [f for f in frequencies if len(f) == most_common_length]
        amplitudes = [a for a in amplitudes if len(a) == most_common_length]
    return np.asarray(parameters), np.asarray(frequencies), np.asarray(amplitudes)

def parse_file(file_path, optimize_length=False):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return parse_file_lines(lines, optimize_length)

def _test_file_parser():
    log.info("Testing file parser")
    import textwrap
    test_case = textwrap.dedent="""\
    /home/thilo/nextcloud/Projekt-Promotion/samples/v11-Simulation-update-freq/v11-5-simulation-hot-coupling.son DE_EMBEDDED L=90.0
    FREQUENCY (GHz) MAG[S21]
    3,1.58932e-05
    3.01,1.62456e-05
    3.02,1.66094e-05
    3.03,1.69852e-05
    """
    e = None
    try:
        parameters, frequencies, amplitudes = parse_file_lines(test_case.split('\n'))
        assert parameters[0] == {"L": 90.0}, f"Expected {parameters[0]} to be {{'L': 90.0}}"
        assert frequencies[0][0] == 3, f"Expected {frequencies[0][0]} to be 3"
        assert amplitudes[0][0] == 1.58932e-05, f"Expected {amplitudes[0][0]} to be 1.58932e-05"
    except Exception as e:
        log.error(e)
        assert e == None, "Expected no exception"

if __name__ == "__main__":
    _test_parse_parameter_line()
    _test_data_line_parsing()
    _test_file_parser()
    log.info("All tests passed.")